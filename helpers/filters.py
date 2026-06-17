from pyrogram import filters


def cmd(*phrases):
    """يطابق الجملة كاملة من بداية الرسالة."""
    patterns = [p.strip() for p in phrases]

    def func(_, __, message):
        if not message.text:
            return False
        text = message.text.strip()
        for p in patterns:
            if text == p or text.startswith(p + " "):
                return True
        return False
    return filters.create(func)


PLAY = cmd("تشغيل")
SKIP = cmd("تخطي")
STOP = cmd("ايقاف", "إيقاف")
RESUME = cmd("استئناف")
MUTE = cmd("كتم")
UNMUTE = cmd("الغاء الكتم", "إلغاء الكتم")
QUEUE = cmd("قائمة")
CLEAN = cmd("تنظيف")
REPORT = cmd("ريبورت")
HELP = cmd("مساعدة")
