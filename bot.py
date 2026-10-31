import os
import threading
from datetime import datetime
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()

app = Flask(__name__)

@app.route("/")
def home():
    return "JUDU BOT V4 FIXED - OK"

@app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def log_user(message):
    try:
        user = message.from_user
        log_line = f"{datetime.now()} | ID:{user.id} | @{user.username}"
        print(log_line)
        with open("/tmp/judu_users.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
        if ADMIN_ID:
            try:
                bot.send_message(int(ADMIN_ID), f"New user: {log_line}")
            except:
                pass
    except Exception as e:
        print(f"Log error: {e}")

if not TOKEN:
    print("KLAIDA: BOT_TOKEN nerastas!")
else:
    bot = telebot.TeleBot(TOKEN, threaded=False)

    def get_menu():
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Siandienos planas"), KeyboardButton("Kur ledu?"))
        markup.add(KeyboardButton("Zaidimu aiksteles"), KeyboardButton("Kur pavalgyt?"))
        markup.add(KeyboardButton("Muziejai"), KeyboardButton("Marsrutas"))
        return markup

    @bot.message_handler(commands=['start'])
    def start_cmd(message):
        log_user(message)
        txt = "JUDU - Vilniaus seimu gidas!\n\nPasirink apacioje: Kur ledu?, Kur pavalgyt?, Zaidimu aiksteles\n\nBotas: @vilnius_seimoms_bot"
        bot.send_message(message.chat.id, txt, reply_markup=get_menu())

    def send_places(chat_id, places, title):
        text = f"{title}\n\n"
        markup = InlineKeyboardMarkup()
        for p in places:
            text += f"{p['name']} - {p['addr']}\n"
            markup.add(InlineKeyboardButton(p['name'], url=p['url']))
        multi = "https://www.google.com/maps/dir/" + "/".join([p['name'].replace(' ', '+') for p in places])
        markup.add(InlineKeyboardButton("VISAS MARSUTAS", url=multi))
        bot.send_message(chat_id, text, reply_markup=markup)

    @bot.message_handler(func=lambda m: True)
    def all_msg(message):
        log_user(message)
        t = message.text.lower() if message.text else ""
        chat_id = message.chat.id
        ledi = [
            {"name": "Sugamour", "addr": "Vilniaus g. 18", "url": "https://maps.google.com/?q=Sugamour+Vilnius"},
            {"name": "Hales turgus", "addr": "Pylimo g. 58", "url": "https://maps.google.com/?q=Hales+turgus"},
        ]
        zaidimai = [
            {"name": "Bernardinu sodas", "addr": "Maironio g. 1", "url": "https://maps.google.com/?q=Bernardinu+sodas"},
            {"name": "Vingio parkas", "addr": "M.K. Ciurlionio 100", "url": "https://maps.google.com/?q=Vingio+parkas"},
        ]
        maistas = [
            {"name": "Etno Dvaras", "addr": "Pilies g. 16", "url": "https://maps.google.com/?q=Etno+Dvaras"},
        ]
        muziejai = [
            {"name": "Mo Muziejus", "addr": "Pylimo g. 17", "url": "https://maps.google.com/?q=Mo+muzejus"},
        ]
        if "led" in t:
            send_places(chat_id, ledi, "Kur ledu Vilniuje:")
        elif "zaid" in t or "aikst" in t:
            send_places(chat_id, zaidimai, "Zaidimu aiksteles:")
        elif "pavalgy" in t or "valgy" in t:
            send_places(chat_id, maistas, "Kur pavalgyt su vaikais:")
        elif "muziej" in t:
            send_places(chat_id, muziejai, "Muziejai vaikams:")
        elif "planas" in t or "siandien" in t or "marsrut" in t:
            text = "SIANDIENOS PLANAS:\n\n10:00 Bernardinu sodas\n12:30 Etno Dvaras\n15:00 Mo Muziejus\n16:30 Sugamour"
            url = "https://www.google.com/maps/dir/Bernardinu+sodas/Etno+Dvaras/Mo+Muziejus/Sugamour"
            mk = InlineKeyboardMarkup()
            mk.add(InlineKeyboardButton("ATIDARYTI VISA MARSUTA", url=url))
            bot.send_message(chat_id, text, reply_markup=mk)
        else:
            bot.send_message(chat_id, f"Gavau: {message.text}", reply_markup=get_menu())

    def keep_alive_loop():
        import time
        print("Keep-alive started")
        while True:
            time.sleep(240)
            print(f"Keep-alive ping {datetime.now()}")

    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=keep_alive_loop, daemon=True).start()
    print("JUDU BOT V4 FIXED - LIVE")
    bot.infinity_polling(skip_pending=True)