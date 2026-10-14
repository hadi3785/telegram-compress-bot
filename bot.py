import os
import logging
import zipfile
import rarfile
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode
import shutil

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
TEMP_DIR = Path('/tmp/compress_bot')
TEMP_DIR.mkdir(exist_ok=True)

# User sessions to store files temporarily
user_sessions = {}


def cleanup_user_files(user_id: int):
    """Clean up temporary files for a user"""
    user_dir = TEMP_DIR / str(user_id)
    if user_dir.exists():
        shutil.rmtree(user_dir)
        logger.info(f"Cleaned up files for user {user_id}")


def get_user_dir(user_id: int) -> Path:
    """Get or create user's temporary directory"""
    user_dir = TEMP_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)
    return user_dir


def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_text = """
سلام! 👋

من یک ربات فشرده‌سازی و استخراج فایل هستم.

📌 امکانات:
• فشرده‌سازی چندین فایل به ZIP
• استخراج فایل‌های ZIP و RAR
• پشتیبانی از فایل‌های تا 2GB

🔹 دستورات:
/start - شروع
/compress - فشرده‌سازی فایل‌ها
/extract - استخراج فایل
/cancel - لغو عملیات
/help - راهنما

برای شروع، یکی از دستورات بالا رو بزن!
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
📖 راهنمای استفاده:

*فشرده‌سازی فایل‌ها:*
1️⃣ دستور /compress رو بزن
2️⃣ فایل‌هایی که می‌خوای فشرده کنی رو ارسال کن
3️⃣ وقتی تموم شد /done رو بزن
4️⃣ فایل ZIP آماده میشه!

*استخراج فایل:*
1️⃣ دستور /extract رو بزن  
2️⃣ فایل ZIP یا RAR رو ارسال کن
3️⃣ فایل‌های داخلش استخراج میشن!

*لغو عملیات:*
هر موقع خواستی می‌تونی /cancel رو بزنی

⚠️ حداکثر حجم: 2GB
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def compress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start compress mode"""
    user_id = update.effective_user.id
    cleanup_user_files(user_id)
    
    user_sessions[user_id] = {
        'mode': 'compress',
        'files': []
    }
    
    keyboard = [[InlineKeyboardButton("✅ تموم شد - فشرده‌سازی", callback_data='done_compress')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📦 حالت فشرده‌سازی فعال شد!\n\n"
        "فایل‌هایی که می‌خوای فشرده کنی رو ارسال کن.\n"
        "وقتی تموم شد، دکمه زیر رو بزن:",
        reply_markup=reply_markup
    )


async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start extract mode"""
    user_id = update.effective_user.id
    cleanup_user_files(user_id)
    
    user_sessions[user_id] = {
        'mode': 'extract',
        'files': []
    }
    
    await update.message.reply_text(
        "📂 حالت استخراج فعال شد!\n\n"
        "فایل ZIP یا RAR خودت رو ارسال کن."
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    user_id = update.effective_user.id
    cleanup_user_files(user_id)
    
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text("❌ عملیات لغو شد و فایل‌ها پاک شدند.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming documents"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text(
            "لطفاً ابتدا یکی از دستورات زیر رو انتخاب کن:\n"
            "/compress - فشرده‌سازی\n"
            "/extract - استخراج"
        )
        return
    
    document = update.message.document
    file_size = document.file_size
    
    if file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            f"❌ حجم فایل زیادی بزرگه!\n"
            f"حجم فایل: {get_human_readable_size(file_size)}\n"
            f"حداکثر مجاز: {get_human_readable_size(MAX_FILE_SIZE)}"
        )
        return
    
    mode = user_sessions[user_id]['mode']
    user_dir = get_user_dir(user_id)
    
    status_msg = await update.message.reply_text(
        f"⏳ در حال دانلود {document.file_name}...\n"
        f"حجم: {get_human_readable_size(file_size)}"
    )
    
    try:
        file = await context.bot.get_file(document.file_id)
        file_path = user_dir / document.file_name
        await file.download_to_drive(file_path)
        
        user_sessions[user_id]['files'].append({
            'name': document.file_name,
            'path': str(file_path),
            'size': file_size
        })
        
        if mode == 'compress':
            total_files = len(user_sessions[user_id]['files'])
            total_size = sum(f['size'] for f in user_sessions[user_id]['files'])
            
            await status_msg.edit_text(
                f"✅ {document.file_name} دانلود شد!\n\n"
                f"📊 وضعیت:\n"
                f"تعداد فایل‌ها: {total_files}\n"
                f"حجم کل: {get_human_readable_size(total_size)}\n\n"
                f"می‌تونی فایل‌های بیشتری ارسال کنی یا دکمه 'تموم شد' رو بزنی."
            )
        
        elif mode == 'extract':
            await status_msg.edit_text("⏳ در حال استخراج فایل...")
            await extract_file(update, context, file_path)
            cleanup_user_files(user_id)
            del user_sessions[user_id]
    
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        await status_msg.edit_text(f"❌ خطا در پردازش فایل: {str(e)}")


async def extract_file(update: Update, context: ContextTypes.DEFAULT_TYPE, archive_path: Path):
    """Extract ZIP or RAR file"""
    user_id = update.effective_user.id
    extract_dir = get_user_dir(user_id) / 'extracted'
    extract_dir.mkdir(exist_ok=True)
    
    try:
        file_ext = archive_path.suffix.lower()
        
        if file_ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        
        elif file_ext == '.rar':
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
        
        else:
            await update.message.reply_text("❌ فقط فایل‌های ZIP و RAR پشتیبانی میشن!")
            return
        
        # Get extracted files
        extracted_files = list(extract_dir.rglob('*'))
        extracted_files = [f for f in extracted_files if f.is_file()]
        
        if not extracted_files:
            await update.message.reply_text("❌ هیچ فایلی در آرشیو پیدا نشد!")
            return
        
        await update.message.reply_text(
            f"✅ استخراج موفق!\n\n"
            f"تعداد فایل‌ها: {len(extracted_files)}\n\n"
            f"در حال ارسال فایل‌ها..."
        )
        
        # Send extracted files
        for file_path in extracted_files[:20]:  # Limit to 20 files
            try:
                file_size = file_path.stat().st_size
                if file_size < 50 * 1024 * 1024:  # Skip files larger than 50MB for sending
                    with open(file_path, 'rb') as f:
                        await update.message.reply_document(
                            document=f,
                            filename=file_path.name
                        )
            except Exception as e:
                logger.error(f"Error sending file {file_path.name}: {e}")
        
        if len(extracted_files) > 20:
            await update.message.reply_text(
                f"⚠️ فقط 20 فایل اول ارسال شد.\n"
                f"کل فایل‌ها: {len(extracted_files)}"
            )
    
    except Exception as e:
        logger.error(f"Error extracting file: {e}")
        await update.message.reply_text(f"❌ خطا در استخراج فایل: {str(e)}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == 'done_compress':
        if user_id not in user_sessions or not user_sessions[user_id]['files']:
            await query.message.reply_text("❌ هیچ فایلی برای فشرده‌سازی وجود نداره!")
            return
        
        await query.message.reply_text("⏳ در حال فشرده‌سازی فایل‌ها...")
        await compress_files(update, context)


async def compress_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compress files into a ZIP"""
    user_id = update.effective_user.id
    user_dir = get_user_dir(user_id)
    zip_path = user_dir / 'compressed.zip'
    
    try:
        files = user_sessions[user_id]['files']
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_info in files:
                file_path = Path(file_info['path'])
                zipf.write(file_path, file_path.name)
        
        zip_size = zip_path.stat().st_size
        
        # Send the ZIP file
        with open(zip_path, 'rb') as f:
            await update.effective_message.reply_document(
                document=f,
                filename='compressed.zip',
                caption=f"✅ فشرده‌سازی انجام شد!\n\n"
                        f"تعداد فایل‌ها: {len(files)}\n"
                        f"حجم نهایی: {get_human_readable_size(zip_size)}"
            )
        
        # Cleanup
        cleanup_user_files(user_id)
        del user_sessions[user_id]
    
    except Exception as e:
        logger.error(f"Error compressing files: {e}")
        await update.effective_message.reply_text(f"❌ خطا در فشرده‌سازی: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("compress", compress_command))
    application.add_handler(CommandHandler("extract", extract_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
