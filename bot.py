import os
import json
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DATA_FILE = Path("birthdays.json")

def load_data():
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот «Пивко та їдло» 🍺🍗\n\n"
        "Команди:\n"
        "/add Ім'я 25.07 — додати день народження\n"
        "/list — список днів народження\n"
        "/remove Ім'я — видалити\n"
        "/test — перевірити бота\n"
        "/chatid — показати ID цієї групи"
    )

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ID цього чату: {update.effective_chat.id}")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот працює ✅ Пивко охолоджується, їдло готується 🍺🍗")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Приклад: /add Іван 25.07")
        return

    name = " ".join(context.args[:-1]).strip()
    date = context.args[-1].strip()

    try:
        datetime.strptime(date, "%d.%m")
    except ValueError:
        await update.message.reply_text("Дата має бути у форматі 25.07")
        return

    data = load_data()
    data[name] = date
    save_data(data)
    await update.message.reply_text(f"Додано: {name} — {date} 🎂")

async def list_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("Список поки порожній.")
        return

    lines = sorted(data.items(), key=lambda item: item[1][3:5] + item[1][:2])
    text = "🎂 Список днів народження:\n\n" + "\n".join(f"{name} — {date}" for name, date in lines)
    await update.message.reply_text(text)

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Приклад: /remove Іван")
        return

    name = " ".join(context.args).strip()
    data = load_data()

    if name not in data:
        await update.message.reply_text("Не знайшов таке ім'я.")
        return

    del data[name]
    save_data(data)
    await update.message.reply_text(f"Видалено: {name}")

async def check_birthdays(app):
    if not CHAT_ID:
        print("CHAT_ID не заданий")
        return

    today = datetime.now().strftime("%d.%m")
    data = load_data()

    for name, date in data.items():
        if date == today:
            await app.bot.send_message(
                chat_id=CHAT_ID,
                text=(
                    f"🎉 Сьогодні день народження у {name}!\n\n"
                    f"Вітаємо від душі! Нехай буде здоров'я, щастя, "
                    f"пивко холодне 🍺, їдло смачне 🍗 і настрій бомбезний! 🎂🥳"
                )
            )

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не заданий")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_birthdays))
    app.add_handler(CommandHandler("remove", remove))

    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(check_birthdays, "cron", hour=9, minute=0, args=[app])
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()