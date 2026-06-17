from pyrogram import Client
from pytgcalls import PyTgCalls
from config import config
from helpers.logger import LOGGER
from database.redis_cache import cache_get, cache_set

_ASSIGNMENT_TTL = 86400 * 30  # 30 يوماً — طويل بما يكفي للحفاظ على الإسناد


class AssistantPool:
    def __init__(self):
        self.clients = []
        self.calls = []
        # إصلاح: الإسناد يُخزّن في Redis ليبقى ثابتاً عبر إعادات التشغيل.
        # _local_cache بُعد ثانوي للأداء فقط (يتزامن مع Redis عند أول طلب).
        self._local_cache: dict[int, int] = {}

    def build(self):
        for i, session in enumerate(config.ASSISTANT_SESSIONS):
            client = Client(
                f"assistant_{i}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=session,
            )
            self.clients.append(client)
            self.calls.append(PyTgCalls(client))
        if not self.clients:
            raise RuntimeError("لا يوجد أي ASSISTANT_SESSIONS في .env")

    async def start(self):
        for c in self.clients:
            await c.start()
        for pc in self.calls:
            await pc.start()
        LOGGER.info(f"✅ تم تشغيل {len(self.clients)} حساب مساعد")

    async def stop(self):
        for pc in self.calls:
            try:
                active = getattr(pc, "calls", None)
                if isinstance(active, dict):
                    for chat_id in list(active.keys()):
                        try:
                            await pc.leave_call(chat_id)
                        except Exception:
                            pass
            except Exception as e:
                LOGGER.warning(f"pytgcalls stop: {e}")
        for c in self.clients:
            try:
                await c.stop()
            except Exception as e:
                LOGGER.warning(f"assistant stop: {e}")

    async def get_calls(self, chat_id: int) -> PyTgCalls:
        """يعيد PyTgCalls المُسنَد لهذه المجموعة.
        الإسناد يُحفظ في Redis ليظل ثابتاً حتى بعد restart.
        """
        if not self.calls:
            raise RuntimeError("لا توجد حسابات مساعدة مهيّأة (استدعِ build/start أولاً).")

        # 1. تحقق من الكاش المحلي أولاً (أسرع)
        if chat_id in self._local_cache:
            return self.calls[self._local_cache[chat_id]]

        # 2. تحقق من Redis (يبقى بعد restart)
        redis_key = f"pool_assign:{chat_id}"
        stored = await cache_get(redis_key)
        if stored is not None:
            idx = int(stored) % len(self.calls)  # % للحماية إن تغيّر عدد الحسابات
            self._local_cache[chat_id] = idx
            return self.calls[idx]

        # 3. إسناد جديد — hash ثابت على chat_id لتوزيع متساوٍ
        idx = abs(chat_id) % len(self.calls)
        self._local_cache[chat_id] = idx
        await cache_set(redis_key, idx, _ASSIGNMENT_TTL)
        return self.calls[idx]

    def iter_calls(self):
        return self.calls
