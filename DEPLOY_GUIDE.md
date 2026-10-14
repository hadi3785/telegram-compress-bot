# 🚀 راهنمای سریع دیپلوی روی Railway

## مرحله 1: ساخت ربات تلگرام

1. به [@BotFather](https://t.me/BotFather) پیام بدید
2. `/newbot` رو بزنید
3. یک نام و username انتخاب کنید
4. **توکن** رو کپی کنید (مثل: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## مرحله 2: آپلود کد روی GitHub (اختیاری)

```bash
cd telegram-compress-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo>
git push -u origin main
```

## مرحله 3: دیپلوی روی Railway

### گزینه A: از طریق وب (ساده‌تر)

1. به [railway.app](https://railway.app) برید و لاگین کنید
2. روی **"New Project"** کلیک کنید
3. **"Deploy from GitHub repo"** رو انتخاب کنید
4. ریپوی خودتون رو انتخاب کنید
5. بعد از شروع دیپلوی:
   - به تب **"Variables"** برید
   - روی **"New Variable"** کلیک کنید
   - Key: `BOT_TOKEN`
   - Value: توکنی که از BotFather گرفتید
   - روی **"Add"** کلیک کنید
6. ربات خودکار restart میشه و شروع به کار می‌کنه!

### گزینه B: با Railway CLI

```bash
# نصب CLI
npm i -g @railway/cli

# لاگین
railway login

# رفتن به پوشه پروژه
cd telegram-compress-bot

# ایجاد پروژه جدید
railway init

# تنظیم توکن
railway variables set BOT_TOKEN=توکن_شما_از_BotFather

# دیپلوی
railway up
```

## مرحله 4: چک کردن لاگ‌ها

در Railway:
1. به پروژه خود برید
2. تب **"Deployments"** رو باز کنید
3. روی آخرین deployment کلیک کنید
4. تب **"Logs"** رو ببینید
5. باید پیام `Bot started!` رو ببینید

## مرحله 5: تست ربات

1. به ربات خودتون در تلگرام پیام بدید
2. `/start` رو بزنید
3. اگر ربات جواب داد، همه چیز درسته! ✅

## ⚠️ نکات مهم

- **Railway Trial**: پلن رایگان Railway محدودیت زمانی داره (500 ساعت/ماه)
- **حجم فایل**: حداکثر 2GB برای هر فایل
- **Timeout**: برای فایل‌های بزرگممکنه زمان بیشتری لازم باشه

## 🐛 مشکلات رایج

### ربات آنلاین نیست
- چک کنید `BOT_TOKEN` درست تنظیم شده
- لاگ‌های Railway رو ببینید

### خطای "Bot token is invalid"
- توکن رو دوباره از BotFather بگیرید
- مطمئن بشید فاصله اضافی نداره

### Railway کار نمی‌کنه
- مطمئن بشید Dockerfile وجود داره
- چک کنید railway.toml درست باشه

## 📞 پشتیبانی

اگه مشکلی داشتید، Issue باز کنید!

---

موفق باشید! 🎉
