import os
import logging
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "").strip()

app = Flask(__name__)

@app.route("/")
def home():
    return "JUDU Vilnius Bot V2 LIVE"

@app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

PLACES = {
    "ledi": [
        {"name": "Sugamour - Ledai & Desertas", "addr": "Vilniaus g. 18", "map": "https://maps.google.com/?q=Sugamour+Vilnius"},
        {"name": "Geles turgus - Halės", "addr": "Pylimo g. 58", "map": "https://maps.google.com/?q=Hales+turgus+Vilnius"},
        {"name": "Vanille", "addr": "Pilies g. 10", "map": "https://maps.google.com/?q=Vanille+Vilnius"},
    ],
    "zaidimai": [
        {"name": "Bernardinu sodas - zaidimu aikstele", "addr": "Maironio g. 1", "map": "https://maps.google.com/?q=Bernardinu+sodas"},
        {"name": "Reformatu parkas", "addr": "Reformatu g.", "map": "https://maps.google.com/?q=Reformatu+parkas+Vilnius"},
        {"name": "Vingio parkas", "addr": "M. K. Ciurlionio g. 100", "map": "https://maps.google.com/?q=Vingio+parkas"},
    ],
    "maistas": [
        {"name": "Etno Dvaras - seimai draugiskas", "addr": "Pilies g. 16", "desc": "Kedes vaikams, keitimo stalas"},
        {"name": "Sugamour", "addr": "Vilniaus g. 18", "desc": "Desertai, vaiku kampas"},
        {"name": "Grill London", "addr": "Gedimino pr. 44", "desc": "Greita, nebrangu"},
    ],
    "muziejai": [
        {"name": "Mo Muziejus - seimos bilietas 12E", "addr": "Pylimo g. 17", "desc": "Vaikams interaktyvu"},
        {"name": "Iliuziju muziejus", "addr": "Vokieciu g. 13", "desc": "Super vaikams!"},
        {"name": "Energetikos muziejus", "addr": "Rinktines g. 2", "desc": "Technika, eksperimentai"},
    ]
}

def get_keyboard():
    keyboard = [
        [KeyboardButton("Siandienos planas"), KeyboardButton("Kur ledu?")],
        [KeyboardButton("Zaidimu aiksteles"), KeyboardButton("Kur pavalgyt su vaikais?")],
        [KeyboardButton("Muziejai vaikams"), KeyboardButton("Generuoti marsruta")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Sveikas! As JUDU - Vilniaus AI gidas seimoms!\n\n"
        "As sugeneruoju tau DIENOS PLANA su vaikais:\n"
        "Rytas - zaidimu aikstele\n"
        "Pietus - kur pavalgyt su vezimeliu\n"
        "Popiete - muziejus vaikams\n\n"
        "Pasirink apacioje arba parasyk laisvai, pvz.: 'Kur ledu senamiestyje?'"
    )
    await update.message.reply_text(text, reply_markup=get_keyboard())

async def send_places(update: Update, key, title):
    places = PLACES.get(key, [])
    text = f"{title}\n\n"
    keyboard = []
    for p in places:
        text += f"{p['name']}\n{p['addr']}\n\n"
        keyboard.append([InlineKeyboardButton(f"{p['name']}", url=p['map'])])
    if len(places) >= 2:
        multi_url = "https://www.google.com/maps/dir/" + "/".join([p['name'].replace(' ', '+') for p in places])
        keyboard.append([InlineKeyboardButton("RODYTI VISUS MAPSE", url=multi_url)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def daily_plan(update: Update):
    text = (
        "SIANDIENOS SEIMOS PLANAS Vilniuje:\n\n"
        "9:30 RYTAS: Bernardinu sodas\n"
        "Vezimeliui OK, Tualetas su stalu OK\n\n"
        "12:30 PIETUS: Etno Dvaras, Pilies g. 16\n"
        "Seimos draugiskas, vaiku kedutes, 8-12E patiekalai\n\n"
        "15:00 POPIETE: Mo Muziejus\n"
        "Seimos bilietas 12E, interaktyvu vaikams\n\n"
        "16:30 DESERTAS: Sugamour ledai - Vilniaus g. 18\n\n"
        "Bendra kaina: ~25-35E seimai"
    )
    multi_url = "https://www.google.com/maps/dir/Bernardinu+sodas/Etno+Dvaras+Pilies+16/Mo+Muziejus/Sugamour+Vilnius"
    keyboard = [[InlineKeyboardButton("ATIDARYTI VISA MARSRUTA MAPSE", url=multi_url)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def generate_route(update: Update):
    text = (
        "GENERUOJU MARSRUTA...\n\n"
        "Parinkau 4 TOP vietas siandien:\n"
        "1. Bernardinu sodas (zaidimai)\n"
        "2. Etno Dvaras (pietus)\n"
        "3. Mo Muziejus\n"
        "4. Ledai Sugamour\n\n"
        "Spausk atidaryti Google Maps su visais stopais!"
    )
    url = "https://www.google.com/maps/dir/Bernardinu+sodas/Etno+Dvaras,+Pilies+g.+16/Mo+Muziejus/Sugamour+Vilniaus+g.+18"
    keyboard = [[InlineKeyboardButton("ATIDARYTI GOOGLE MAPS", url=url)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    if "led" in msg:
        await send_places(update, "ledi", "Geriausi ledai Vilniuje:")
    elif "zaidim" in msg or "aikste" in msg:
        await send_places(update, "zaidimai", "Zaidimu aiksteles:")
    elif "pavalgy" in msg or "valgy" in msg or "maist" in msg or "eat" in msg:
        await send_places(update, "maistas", "Kur pavalgyt su vaikais:")
    elif "muziej" in msg:
        await send_places(update, "muziejai", "Muziejai vaikams:")
    elif "marsrut" in msg or "route" in msg or "generuot" in msg:
        await generate_route(update)
    elif "dienos" in msg or "planas" in msg or "siandien" in msg:
        await daily_plan(update)
    else:
        await update.message.reply_text(
            f"Supratau: '{update.message.text}'\n\nKol kas suprantu raktazodzius: ledai, zaidimai, pavalgyt, muziejus, marsrutas\nPaspausk mygtuka apacioje",
            reply_markup=get_keyboard()
        )

def main():
    threading.Thread(target=run_web, daemon=True).start()
    print("V2 Botas su visom durim paleistas!")
    if not TOKEN:
        print("KLAIDA: BOT_TOKEN nenustatytas!")
        import time
        while True:
            time.sleep(60)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
