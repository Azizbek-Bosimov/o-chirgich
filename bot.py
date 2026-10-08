import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ⚠️ Token va Admin ID Railway Variables-dan o'qiladi
TOKEN = os.environ.get("8460009727:AAEWnGEGYf0iPabPB8lsxJvkeOMUhSnEaUc")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

if not TOKEN:
    raise ValueError("BOT_TOKEN o'rnatilmagan! Railway Variables-ga qo'shing.")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID o'rnatilmagan! Railway Variables-ga qo'shing.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id == ADMIN_ID:
        await update.message.reply_text("👑 Admin panel tayyor.")
        return
    await update.message.reply_text(
        f"Salom {user.full_name}! 👋\n\n"
        "Rasm, video, dumaloq video, hujjat yoki joylashuv yuboring — "
        "adminga yetib boradi."
    )


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user.id == ADMIN_ID:
        return

    # Joylashuv
    if message.location:
        loc = message.location
        info = (
            f"📍 **Joylashuv**\n👤 {user.full_name}\n"
            f"🔗 @{user.username or 'yoq'}\n🆔 `{user.id}`\n\n"
            f"🗺️ {loc.latitude:.5f}, {loc.longitude:.5f}"
        )
        if loc.live_period:
            info += f"\n🔴 Jonli ({loc.live_period}s)"
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=info)
            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=message.chat_id,
                message_id=message.message_id,
            )
            await message.reply_text("✅ Joylashuv adminga yuborildi!")
        except Exception as e:
            logger.error(f"Joylashuv xatolik: {e}")
        return

    file_obj = None
    file_type = "📎 Fayl"
    is_self_destruct = False

    if message.photo:
        file_type = "🖼️ Rasm"
        file_obj = message.photo[-1]
        if getattr(message, "has_media_spoiler", False):
            is_self_destruct = True
    elif message.video:
        file_type = "🎬 Video"
        file_obj = message.video
        if getattr(message, "has_media_spoiler", False):
            is_self_destruct = True
    elif message.video_note:
        file_type = "⭕ Dumaloq video"
        file_obj = message.video_note
    elif message.document:
        file_type = "📎 Hujjat"
        file_obj = message.document
    elif message.audio:
        file_type = "🎵 Audio"
        file_obj = message.audio
    elif message.voice:
        file_type = "🎤 Ovozli xabar"
        file_obj = message.voice

    if file_obj is None:
        return

    header = (
        f"📥 **{file_type}**\n👤 {user.full_name}\n"
        f"🔗 @{user.username or 'yoq'}\n🆔 `{user.id}`"
    )
    if is_self_destruct:
        header += "\n🔥 Self-destruct (1 marta ko'rish)"

    try:
        if is_self_destruct:
            await context.bot.send_message(
                chat_id=ADMIN_ID, text=header + "\n\n⚠️ Yuklab olinmoqda..."
            )
            file = await file_obj.get_file()
            file_bytes = await file.download_as_bytearray()

            if message.photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=bytes(file_bytes),
                    caption=f"🔥 Self-destruct rasm\n👤 {user.full_name}",
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=ADMIN_ID,
                    video=bytes(file_bytes),
                    caption=f"🔥 Self-destruct video\n👤 {user.full_name}",
                )
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=header)
            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=message.chat_id,
                message_id=message.message_id,
            )

        await message.reply_text(f"✅ {file_type} adminga yuborildi!")
        logger.info(f"Uzatildi: {user.full_name} -> {file_type}")
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.reply_text("❌ Xatolik yuz berdi.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Xatolik: {context.error}")


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE |
        filters.Document.ALL | filters.AUDIO | filters.VOICE |
        filters.LOCATION,
        handle_media,
    ))
    application.add_error_handler(error_handler)
    print("🤖 Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()