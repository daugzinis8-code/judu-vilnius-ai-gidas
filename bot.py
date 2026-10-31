
import os
import logging
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    logger.error("BOT_TOKEN nerastas! Nustatyk Environment Variable Render.")
    
# --- WEB SERVER FOR RENDER WEB SERVICE ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ JUDU Vilnius Botas V2 LIVE - veikia su visom durim!"

@app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- DATA: 6 durys ---
PLACES = {
    "ledi": [
        {"name": "Sugamour - Ledai & Desertas", "addr": "Vilniaus g. 18", "map": "https://maps.google.com/?q=Sugamour+Vilnius"},
        {"name": "Gelato & Grill - Halės Turgus", "addr": "Pylimo g. 58", "map": "https://maps.google.com/?q=Hales+turgus+Vilnius"},
        {"name": "Vanille", "addr": "Pilies g. 10", "map": "https://maps.google.com/?q=Vanille+Vilnius"},
    ],
    "zaidimai": [
        {"name": "Bernardinų sodas - žaidimų aikštelė", "addr": "Maironio g. 1", "map": "https://maps.google.com/?q=Bernardinu+sodas"},
        {"name": "Reformatų parkas", "addr": "Reformatų g.", "map": "https://maps.google.com/?q=Reformatu+parkas+Vilnius"},
        {"name": "Vingio parkas - didelė aikštelė", "addr": "M. K. Čiurlionio g. 100", "map": "https://maps.google.com/?q=Vingio+parkas"},
    ],
    "maistas": [
        {"name": "Etno Dvaras - šeimai draugiškas", "addr": "Pilies g. 16", "desc": "Kėdės vaikams, keitimo stalas"},
        {"name": "Sugamour", "addr": "Vilniaus g. 18", "desc": "Desertai, vaikų kampas"},
        {"name": "Grill London", "addr": "Gedimino pr. 44", "desc": "Greita, nebrangu"},
    ],
    "muziejai": [
        {"name": "Mo Muziejus - šeimos bilietas 12€", "addr": "Pylimo g. 17", "desc": "Vaikams interaktyvu"},
        {"name": "Iliuzijų muziejus", "addr": "Vokiečių g. 13", "desc": "Super vaikams!"},
        {"name": "Energetikos muziejus", "addr": "Rinktinės g. 2", "desc": "Technika, eksperimentai"},
    ]
}

def get_keyboard(lang="lt"):
    keyboard = [
        [KeyboardButton("📅 Šiandienos planas"), KeyboardButton("🍦 Kur ledų?")],
        [KeyboardButton("🛝 Žaidimų aikštelės"), KeyboardButton("🍽️ Kur pavalgyt su vaikais?")],
        [KeyboardButton("🏛️ Muziejai vaikams"), KeyboardButton("🗺️ Generuoti maršrutą")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Sveikas! Aš JUDU - Vilniaus AI gidas šeimoms!

"
        "Aš sugeneruoju tau DIENOS PLANĄ su vaikais:
"
        "☀️ Rytas - žaidimų aikštelė
"
        "🍽️ Pietūs - kur pavalgyt su vežimėliu
"
        "🏛️ Popietė - muziejus vaikams

"
        "Pasirink apačioje arba parašyk laisvai, pvz.: 'Kur ledų senamiestyje?'"
    )
    await update.message.reply_text(text, reply_markup=get_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    
    if "ledi" in msg or "ledų" in msg or "ice" in msg:
        await send_places(update, "ledi", "🍦 Geriausi ledai Vilniuje:")
    elif "zaidim" in msg or "aikštel" in msg or "play" in msg or "🛝" in msg:
        await send_places(update, "zaidimai", "🛝 Žaidimų aikštelės:")
    elif "pavalgy" in msg or "valgyt" in msg or "maist" in msg or "🍽️" in msg or "eat" in msg:
        await send_places(update, "maistas", "🍽️ Kur pavalgyt su vaikais:")
    elif "muziej" in msg or "🏛️" in msg:
        await send_places(update, "muziejai", "🏛️ Muziejai vaikams:")
    elif "maršrut" in msg or "route" in msg or "🗺️" in msg or "generuot" in msg:
        await generate_route(update)
    elif "dienos" in msg or "planas" in msg or "📅" in msg or "siandien" in msg:
        await daily_plan(update)
    else:
        # Free text understanding
        await update.message.reply_text(
            f"Supratau: '{update.message.text}' 🤖

"
            f"Kol kas geriausiai suprantu šiuos raktažodžius:
"
            f"🍦 ledai, 🛝 žaidimai, 🍽️ pavalgyt, 🏛️ muziejus, 🗺️ maršrutas

"
            f"Bet tuoj prijungsim AI! Kol kas paspausk mygtuką apačioje 👇",
            reply_markup=get_keyboard()
        )

async def send_places(update: Update, key, title):
    places = PLACES.get(key, [])
    text = f"{title}

"
    keyboard = []
    for p in places:
        text += f"📍 *{p['name']}*
{p['addr']}

"
        keyboard.append([InlineKeyboardButton(f"🗺️ {p['name']}", url=p['map'])])
    
    # Add multi-stop route button
    if len(places) >= 2:
        multi_url = f"https://www.google.com/maps/dir/" + "/".join([p['name'].replace(' ', '+') for p in places])
        keyboard.append([InlineKeyboardButton("🗺️ RODYTI VISUS MAPS'E", url=multi_url)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def daily_plan(update: Update):
    text = (
        "📅 *ŠIANDIENOS ŠEIMOS PLANAS Vilniuje:*

"
        "🌤️ *9:30 RYTAS:* Bernardinų sodas
"
        "Vežimėliui ✅, Tualetas su stalu ✅
"
        "Puiku pavarginti vaikus ryte!

"
        "🍽️ *12:30 PIETŪS:* Etno Dvaras, Pilies g. 16
"
        "Šeimos draugiškas, vaikų kėdutės, 8-12€ patiekalai

"
        "🏛️ *15:00 POPIETĖ:* Mo Muziejus
"
        "Šeimos bilietas 12€, interaktyvu vaikams

"
        "🍦 *16:30 DESERTAS:* Sugamour ledai - Vilniaus g. 18

"
        "Bendra kaina: ~25-35€ šeimai
"
        "Maršrutas pėsčiomis Senamiestyje - viskas šalia!"
    )
    multi_url = "https://www.google.com/maps/dir/Bernardin%C5%B3+sodas/Etno+Dvaras+Pilies+16/Mo+Muziejus/Sugamour+Vilnius"
    keyboard = [[InlineKeyboardButton("🗺️ ATIDARYTI VISĄ MARŠRUTĄ MAPS'E", url=multi_url)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def generate_route(update: Update):
    text = (
        "🗺️ *GENERUOJU MARŠRUTĄ...*

"
        "Parinkau 4 TOP vietas šiandien:
"
        "1. Bernardinų sodas (žaidimai)
"
        "2. Etno Dvaras (pietūs)
"
        "3. Mo Muziejus
"
        "4. Ledai Sugamour

"
        "Spausk žemiau atidaryti Google Maps su visais stopais!"
    )
    url = "https://www.google.com/maps/dir/Bernardin%C5%B3+sodas/Etno+Dvaras,+Pilies+g.+16/Mo+Muziejus/Sugamour+Vilniaus+g.+18"
    keyboard = [[InlineKeyboardButton("🗺️ ATIDARYTI GOOGLE MAPS", url=url)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def main():
    # Start web server in background thread
    threading.Thread(target=run_web, daemon=True).start()
    print("V2 Botas su visom durim paleistas!")
    print("Web server paleistas ant PORT - Render matys Open Port")
    
    if not TOKEN:
        print("KLAIDA: BOT_TOKEN nenustatytas!")
        # Keep web server alive even without token
        while True:
            import time; time.sleep(60)
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
