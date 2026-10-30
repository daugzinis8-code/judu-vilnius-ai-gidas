import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# SKAITO TOKENĄ IŠ RENDER Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("KLAIDA: Nėra BOT_TOKEN environment variable! Įdėk į Render.")
    exit(1)

DAILY_PLANS = {
    "lt": {
        "rytas": "🛝 10:00 - Vaikų žaidimų aikštelė prie Baltojo tilto\n📍 Upės g. 6, nemokamai, vežimėliui draugiška",
        "pietus": "🍕 12:30 - Beigelistai, Literatų g. 7\n💰 Beigeliai vaikams 3€, yra kėdutės, persirengimo stalas",
        "popiete": "🔬 14:30 - Energetikos ir technikos muziejus, Rinktinės g. 2\n💰 Vaikams iki 7m nemokamai"
    },
    "ru": {
        "rytas": "🛝 10:00 - Детская площадка у Белого моста\n📍 Upės g. 6, бесплатно, для колясок",
        "pietus": "🍕 12:30 - Beigelistai, Literatų g. 7\n💰 Бейглы для детей 3€, есть стульчики",
        "popiete": "🔬 14:30 - Музей энергетики, Rinktinės g. 2\n💰 Детям до 7 лет бесплатно"
    },
    "en": {
        "rytas": "🛝 10:00 - Kids Playground at White Bridge\n📍 Upės g. 6, free, stroller friendly",
        "pietus": "🍕 12:30 - Beigelistai, Literatų g. 7\n💰 Bagels for kids 3€, high chairs available",
        "popiete": "🔬 14:30 - Energy and Technology Museum\n💰 Free for kids under 7"
    },
    "ua": {
        "rytas": "🛝 10:00 - Дитячий майданчик біля Білого мосту\n📍 Upės g. 6, безкоштовно, для візочків",
        "pietus": "🍕 12:30 - Beigelistai, Literatų g. 7\n💰 Бейгли для дітей 3€, є стільчики",
        "popiete": "🔬 14:30 - Музей енергетики, Rinktinės g. 2\n💰 Дітям до 7 років безкоштовно"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇱🇹 Lietuviškai", callback_data='lt'),
         InlineKeyboardButton("🇷🇺 Русский", callback_data='ru')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='en'),
         InlineKeyboardButton("🇺🇦 Українська", callback_data='ua')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Sveiki! Esu VILNIUS ŠEIMŲ GIDAS\n\n"
        "Kasdien 9:00 siųsiu 3 vietas kur eiti su vaikais šiandien.\n"
        "Pasirink kalbą / Choose language / Выбери язык:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    if lang not in DAILY_PLANS:
        lang = "lt"
    plan = DAILY_PLANS[lang]
    text = f"☀️ ŠIANDIENOS PLANAS ŠEIMAI (Vilnius, 16°C)\n\n{plan['rytas']}\n\n{plan['pietus']}\n\n{plan['popiete']}\n\n📍 Spausti 'Gauti maršrutą' - atsiųsiu Google Maps"
    
    keyboard = [[InlineKeyboardButton("📍 Gauti maršrutą visai dienai", url="https://maps.google.com/?q=Vilnius+Old+Town")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Botas paleistas... /start Telegram'e")
    app.run_polling()

if __name__ == '__main__':
    main()
