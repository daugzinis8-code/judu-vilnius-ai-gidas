import os
import threading
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN", "").strip()

app = Flask(__name__)

@app.route("/")
def home():
    return "JUDU BOT LIVE - OK"

@app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if not TOKEN:
    print("KLAIDA: BOT_TOKEN nerastas!")
else:
    bot = telebot.TeleBot(TOKEN, threaded=False)

    def get_menu():
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("📅 Šiandienos planas"), KeyboardButton("🍦 Kur ledų?"))
        markup.add(KeyboardButton("🛝 Žaidimų aikštelės"), KeyboardButton("🍽️ Kur pavalgyt?"))
        markup.add(KeyboardButton("🏛️ Muziejai"), KeyboardButton("🗺️ Maršrutas"))
        return markup

    @bot.message_handler(commands=['start'])
    def start_cmd(message):
        bot.send_message(message.chat.id,
            "👋 JUDU - Vilniaus šeimų gidas!\n\n"
            "Pasirink apačioje arba rašyk: Kur ledų?, Kur pavalgyt?, Žaidimų aikštelės\n"
            "Sugeneruosiu maršrutą per Google Maps!",
            reply_markup=get_menu())

    def send_places(chat_id, places, title):
        text = f"{title}\n\n"
        markup = InlineKeyboardMarkup()
        for p in places:
            text += f"📍 {p['name']} - {p['addr']}\n"
            markup.add(InlineKeyboardButton(f"🗺️ {p['name']}", url=p['url']))
        multi = "https://www.google.com/maps/dir/" + "/".join([p['name'].replace(' ', '+') for p in places])
        markup.add(InlineKeyboardButton("🗺️ VISAS MARŠRUTAS", url=multi))
        bot.send_message(chat_id, text, reply_markup=markup)

    @bot.message_handler(func=lambda m: True)
    def all_msg(message):
        t = message.text.lower() if message.text else ""
        chat_id = message.chat.id
        
        ledi = [
            {"name": "Sugamour", "addr": "Vilniaus g. 18", "url": "https://maps.google.com/?q=Sugamour+Vilnius"},
            {"name": "Halės turgus", "addr": "Pylimo g. 58", "url": "https://maps.google.com/?q=Hales+turgus"},
            {"name": "Vanille", "addr": "Pilies g. 10", "url": "https://maps.google.com/?q=Vanille+Vilnius"},
        ]
        zaidimai = [
            {"name": "Bernardinų sodas", "addr": "Maironio g. 1", "url": "https://maps.google.com/?q=Bernardinu+sodas"},
            {"name": "Reformatų parkas", "addr": "Reformatų g.", "url": "https://maps.google.com/?q=Reformatu+parkas"},
            {"name": "Vingio parkas", "addr": "M.K. Čiurlionio 100", "url": "https://maps.google.com/?q=Vingio+parkas"},
        ]
        maistas = [
            {"name": "Etno Dvaras", "addr": "Pilies g. 16", "url": "https://maps.google.com/?q=Etno+Dvaras"},
            {"name": "Sugamour", "addr": "Vilniaus g. 18", "url": "https://maps.google.com/?q=Sugamour"},
        ]
        muziejai = [
            {"name": "Mo Muziejus", "addr": "Pylimo g. 17", "url": "https://maps.google.com/?q=Mo+muzejus"},
            {"name": "Iliuzijų muziejus", "addr": "Vokiečių g. 13", "url": "https://maps.google.com/?q=Iliuziju+muzejus"},
        ]

        if "led" in t or "🍦" in t:
            send_places(chat_id, ledi, "🍦 Kur ledų Vilniuje:")
        elif "zaid" in t or "aikšt" in t or "🛝" in t:
            send_places(chat_id, zaidimai, "🛝 Žaidimų aikštelės:")
        elif "pavalgy" in t or "valgy" in t or "🍽️" in t:
            send_places(chat_id, maistas, "🍽️ Kur pavalgyt su vaikais:")
        elif "muziej" in t or "🏛️" in t:
            send_places(chat_id, muziejai, "🏛️ Muziejai vaikams:")
        elif "planas" in t or "📅" in t or "šiandien" in t or "maršrut" in t or "🗺️" in t:
            text = "📅 ŠIANDIENOS PLANAS:\n\n🛝 10:00 Bernardinų sodas\n🍽️ 12:30 Etno Dvaras\n🏛️ 15:00 Mo Muziejus\n🍦 16:30 Sugamour"
            url = "https://www.google.com/maps/dir/Bernardinu+sodas/Etno+Dvaras/Mo+Muziejus/Sugamour"
            mk = InlineKeyboardMarkup()
            mk.add(InlineKeyboardButton("🗺️ ATIDARYTI VISĄ MARŠRUTĄ", url=url))
            bot.send_message(chat_id, text, reply_markup=mk)
        else:
            bot.send_message(chat_id, f"Gavau: {message.text}\nSpausk mygtuką apačioje 👇", reply_markup=get_menu())

    # Start web in background
    threading.Thread(target=run_web, daemon=True).start()
    print("JUDU BOT V2 - TELEBOT - LIVE")
    bot.infinity_polling(skip_pending=True)
