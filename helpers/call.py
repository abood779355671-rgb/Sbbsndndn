import asyncio
from collections import defaultdict
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall
from database import queue as q
from database.queue import DuplicateTrack
from database.mongo import stats_col
from helpers.youtube import stream_url
from helpers.logger import LOGGER


class VoiceChatClosed(Exception):
    pass


def _audio_stream(link: str) -> MediaStream:
    try:
        return MediaStream(link, video_flags=MediaStream.Flags.IGNORE)
    except Exception:
        return MediaStream(link)


class CallManager:
    def __init__(self, pool):
        self.pool = pool
        self.bot = None
        self._locks = defaultdict(asyncio.Lock)

    async def _stream(self, chat_id: int, track: dict):
        # الرابط يُجلب لحظة التشغيل فقط (روابط يوتيوب قصيرة الصلاحية)
        link = await stream_url(track["video_id"])
        calls = await self.pool.get_calls(chat_id)
        await calls.play(chat_id, _audio_stream(link))
        await stats_col.update_one({"_id": "global"}, {"$inc": {"played": 1}}, upsert=True)

    async def play_or_queue(self, chat_id: int, track: dict) -> int:
        async with self._locks[chat_id]:
            current = await q.load_queue(chat_id)
            try:
                await q.save_track(chat_id, track)
            except DuplicateTrack:
                return -1
            if not current:
                try:
                    await self._stream(chat_id, track)
                except Exception as e:
                    await q.pop_first(chat_id)
                    msg = str(e).lower()
                    if isinstance(e, NoActiveGroupCall) or \
                            "group call" in msg or "no active" in msg or "not found" in msg:
                        raise VoiceChatClosed()
                    raise
                return 0
            return len(current) + 1

    async def _next(self, chat_id: int):
        # إصلاح: نحذف العنصر الأول (المُشغَّل حالياً) ثم نشغّل التالي.
        # السلوك القديم: يُبقي [0] في القائمة أثناء التشغيل، فعندما ينتهي
        # on_end يحذف [0] ويستدعي _next من جديد — فيُشغَّل [0] مرةً أخرى.
        await q.pop_first(chat_id)
        remaining = await q.load_queue(chat_id)
        if remaining:
            track = dict(remaining[0])
            try:
                await self._stream(chat_id, track)
            except Exception as e:
                LOGGER.warning(f"_next stream error: {e}")
                return None
            return track
        await self._stop_internal(chat_id)
        return None

    async def skip(self, chat_id: int):
        # محمي بالقفل — تخطٍّ متزامن مع انتهاء تلقائي لا يحذف عنصرين
        async with self._locks[chat_id]:
            # _next تحذف الحالية [0] وتشغّل التالية
            return await self._next(chat_id)

    async def on_end(self, chat_id: int):
        async with self._locks[chat_id]:
            # الأغنية المنتهية لا تزال في [0]، _next ستحذفها وتشغّل التالية
            return await self._next(chat_id)

    async def stop(self, chat_id: int):
        async with self._locks[chat_id]:
            await self._stop_internal(chat_id)

    async def _stop_internal(self, chat_id: int):
        await q.clear_queue(chat_id)
        try:
            calls = await self.pool.get_calls(chat_id)
            await calls.leave_call(chat_id)
        except Exception as e:
            LOGGER.warning(f"leave_call: {e}")

    async def pause(self, chat_id: int):
        calls = await self.pool.get_calls(chat_id)
        await calls.pause_stream(chat_id)

    async def resume(self, chat_id: int):
        calls = await self.pool.get_calls(chat_id)
        await calls.resume_stream(chat_id)

    async def mute(self, chat_id: int):
        calls = await self.pool.get_calls(chat_id)
        await calls.mute_stream(chat_id)

    async def unmute(self, chat_id: int):
        calls = await self.pool.get_calls(chat_id)
        await calls.unmute_stream(chat_id)

    async def cleanup_stale_queues(self):
        for chat_id in await q.all_active_chats():
            await q.clear_queue(chat_id)
        LOGGER.info("تم تنظيف قوائم الانتظار القديمة عند الإقلاع.")
