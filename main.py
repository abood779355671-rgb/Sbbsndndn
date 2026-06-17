import asyncio
import signal
from pyrogram import Client
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamAudioEnded

from config import config, validate_config
from helpers.logger import LOGGER, set_log_bot, log_to_group
from helpers.assistant_pool import AssistantPool
from helpers.call import CallManager
from database.mongo import init_db, close_db

from plugins import play, controls, queue_cmds, report, start
from plugins.sudo import panel, broadcast, manage, backup

bot = Client(
    "music_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

pool = AssistantPool()
calls = CallManager(pool)

_stop_event = asyncio.Event()


def register_all():
    for mod in (play, controls, queue_cmds, report, start,
                panel, broadcast, manage, backup):
        mod.register(bot, calls)


def _make_stream_end_handler():
    async def stream_end(_, update: Update):
        if isinstance(update, StreamAudioEnded):
            nxt = await calls.on_end(update.chat_id)
            if nxt:
                try:
                    await bot.send_message(
                        update.chat_id,
                        f"🎵 **تم بدء التشغيل**\n\n"
                        f"الاغنية: {nxt['title']}\n"
                        f"المدة: {nxt['duration']}\n"
                        f"بواسطة: {nxt.get('requester', '-')}",
                    )
                except Exception as e:
                    LOGGER.warning(e)
    return stream_end


def attach_stream_end():
    handler = _make_stream_end_handler()
    for pc in pool.iter_calls():
        pc.on_update()(handler)


async def _watch_restart():
    """يراقب علم إعادة التشغيل من اللوحة ويُوقف بأمان."""
    while not _stop_event.is_set():
        if panel.SHUTDOWN["flag"]:
            LOGGER.info("طلب إعادة تشغيل من اللوحة.")
            _stop_event.set()
            break
        await asyncio.sleep(2)


async def _shutdown():
    LOGGER.info("⏹ إيقاف نظيف جارٍ...")
    await log_to_group("⏹ البوت يُغلق بأمان.")
    try:
        await pool.stop()
    except Exception as e:
        LOGGER.warning(e)
    try:
        await bot.stop()
    except Exception as e:
        LOGGER.warning(e)
    close_db()
    LOGGER.info("✅ تم الإغلاق النظيف.")


async def run():
    validate_config()
    await init_db()
    pool.build()

    register_all()
    attach_stream_end()

    await bot.start()
    set_log_bot(bot)
    await pool.start()
    calls.bot = bot

    LOGGER.info("✅ البوت يعمل")
    await log_to_group("✅ تم تشغيل البوت.")
    await calls.cleanup_stale_queues()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop_event.set)
        except NotImplementedError:
            pass  # غير مدعوم على Windows

    asyncio.create_task(_watch_restart())
    await _stop_event.wait()
    await _shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit) as e:
        LOGGER.info(f"خروج: {e}")
