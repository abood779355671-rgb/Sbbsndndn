from pyrogram import Client, filters
from pyrogram.types import Message
from helpers import filters as F
from helpers.decorators import guard
from database.chats import add_chat
from database.users import add_user

START_TEXT = (
    "👋 **أهلاً بك في بوت تشغيل الأغاني**\n\n"
    "أضفني إلى مجموعتك وافتح المكالمة الصوتية، ثم اكتب:\n"
    "`تشغيل اسم الأغنية`\n\n"
    "اكتب **مساعدة** لعرض كل الأوامر."
)

HELP_TEXT = (
    "📖 **أوامر البوت** (بدون /):\n\n"
    "• تشغيل [اسم/رابط] — تشغيل أغنية\n"
    "• تخطي — تخطي الحالية (مشرف)\n"
    "• ايقاف — إيقاف ومغادرة (مشرف)\n"
    "• استئناف — استئناف (مشرف)\n"
    "• كتم / الغاء الكتم — (مشرف)\n"
    "• قائمة — عرض قائمة الانتظار\n"
    "• تنظيف — مسح القائمة (مشرف)\n"
    "• ريبورت — مزامنة المشرفين (مشرف)\n"
    "• مساعدة — هذه القائمة"
)


def register(app: Client, calls):

    @app.on_message(filters.command("start"))
    async def start_cmd(client, message: Message):
        await add_chat(message.chat.id, message.chat.title or "")
        if message.from_user:
            await add_user(message.from_user.id, message.from_user.first_name or "")
        await message.reply(START_TEXT)

    @app.on_message(filters.command("help"))
    async def help_cmd(client, message: Message):
        await message.reply(HELP_TEXT)

    @app.on_message(F.HELP)
    @guard
    async def help_h(client, message: Message):
        await add_chat(message.chat.id, message.chat.title or "")
        await add_user(message.from_user.id, message.from_user.first_name or "")
        await message.reply(HELP_TEXT)
