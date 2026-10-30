import os, json, random, threading, time
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Try import requests, if not available fallback
try:
    import requests
    HAS_REQUESTS = True
except:
    HAS_REQUESTS = False

TOKEN = os.getenv("BOT_TOKEN", "").strip()
SHEET_URL = os.getenv("SHEET_URL", "").strip()  # Google Sheets CSV link

app = Flask(__name__)
@app.route("/")
def home(): return "JUDU BOT V3 B - SHEETS LIVE"
@app.route("/health")
def health(): return "OK", 200
def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

PLACES = {"ledi":[],"zaidimai":[],"maistas":[],"muziejai":[]}

def load_places():
    global PLACES
    # 1. Try Google Sheets
    if SHEET_URL and HAS_REQUESTS:
        try:
            print(f"Loading from Google Sheets: {SHEET_URL}")
            r = requests.get(SHEET_URL, timeout=10)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                # Expect header: category,name,addr,url,price,tags
                new_places = {"ledi":[],"zaidimai":[],"maistas":[],"muziejai":[]}
                for line in lines[1:]:  # skip header
                    if not line.strip(): continue
                    # Simple CSV split - assumes no commas in fields, use | as separator recommended
                    # Support both , and | - we will try |
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|")]
                    else:
                        parts = [p.strip() for p in line.split(",")]
                    if len(parts) < 4: continue
                    category = parts[0].lower()
                    name = parts[1]
                    addr = parts[2]
                    url = parts[3] if len(parts) > 3 else f"https://maps.google.com/?q={name.replace(' ','+')}"
                    price = parts[4] if len(parts) > 4 else ""
                    tags = parts[5] if len(parts) > 5 else ""
                    
                    # Map category names
                    if category in ["ledi","ledai","ice","icecream"]: cat = "ledi"
                    elif category in ["zaidimai","play","park","aiksteles"]: cat = "zaidimai"
                    elif category in ["maistas","food","eat","pavalgyt","restaurant"]: cat = "maistas"
                    elif category in ["muziejai","museum","muziejus"]: cat = "muziejai"
                    else: continue
                    
                    new_places[cat].append({"name":name,"addr":addr,"url":url,"price":price,"tags":tags})
                
                if sum(len(v) for v in new_places.values()) > 0:
                    PLACES = new_places
                    print(f"Loaded {sum(len(v) for v in PLACES.values())} places from Sheets")
                    return
        except Exception as e:
            print(f"Sheets load error: {e}")

    # 2. Try places.json file
    try:
        with open('places.json','r',encoding='utf-8') as f:
            PLACES = json.load(f)
            print(f"Loaded {sum(len(v) for v in PLACES.values())} places from places.json")
            return
    except Exception as e:
        print(f"places.json error: {e}")

    # 3. Fallback hardcoded minimal
    PLACES = {
        "ledi": [{"name":"Sugamour","addr":"Vilniaus g. 18","url":"https://maps.google.com/?q=Sugamour","price":"3€","tags":""}],
        "zaidimai": [{"name":"Bernardinu sodas","addr":"Maironio g. 1","url":"https://maps.google.com/?q=Bernardinu+sodas","price":"free","tags":""}],
        "maistas": [{"name":"Etno Dvaras","addr":"Pilies g. 16","url":"https://maps.google.com/?q=Etno+Dvaras","price":"8-12€","tags":""}],
        "muziejai": [{"name":"Mo Muziejus","addr":"Pylimo g. 17","url":"https://maps.google.com/?q=Mo+muzejus","price":"12€","tags":""}],
    }

def auto_reload_loop():
    while True:
        time.sleep(3600)  # kas valanda
        print("Auto-reload places from Sheets...")
        load_places()

# Initial load
load_places()

if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)

    def get_menu():
        m = ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(KeyboardButton("📅 Šiandienos planas"), KeyboardButton("🍦 Kur ledų?"))
        m.add(KeyboardButton("🛝 Žaidimų aikštelės"), KeyboardButton("🍽️ Kur pavalgyt?"))
        m.add(KeyboardButton("🏛️ Muziejai"), KeyboardButton("🗺️ Maršrutas"))
        return m

    def send_random(chat_id, key, title, count=3):
        all_places = PLACES.get(key, [])
        if not all_places:
            bot.send_message(chat_id, "Tuoj papildysim vietas!")
            return
        selected = random.sample(all_places, min(count, len(all_places)))
        text = f"{title}\n\n"
        markup = InlineKeyboardMarkup()
        for p in selected:
            price = f" ({p.get('price','')})" if p.get('price') else ""
            text += f"📍 {p['name']} - {p['addr']}{price}\n"
            markup.add(InlineKeyboardButton(f"🗺️ {p['name']}", url=p['url']))
        multi = "https://www.google.com/maps/dir/" + "/".join([p['name'].replace(' ','+') for p in selected])
        markup.add(InlineKeyboardButton("🗺️ VISAS MARŠRUTAS", url=multi))
        bot.send_message(chat_id, text, reply_markup=markup)

    @bot.message_handler(commands=['start'])
    def start_cmd(message):
        total = sum(len(v) for v in PLACES.values())
        bot.send_message(message.chat.id,
            f"👋 JUDU V3 B - {total} vietų šeimoms Vilniuje!\n\n"
            f"🔄 Auto atsinaujina iš Google Sheets kas valandą!\n\n"
            f"Pasirink apačioje 👇", reply_markup=get_menu())

    @bot.message_handler(func=lambda m: True)
    def all_msg(message):
        t = (message.text or "").lower()
        chat_id = message.chat.id
        if "led" in t or "🍦" in t:
            send_random(chat_id, "ledi", "🍦 Kur ledų?")
        elif "zaid" in t or "aikšt" in t or "🛝" in t:
            send_random(chat_id, "zaidimai", "🛝 Žaidimų aikštelės:")
        elif "pavalgy" in t or "valgy" in t or "🍽️" in t:
            send_random(chat_id, "maistas", "🍽️ Kur pavalgyt su vaikais:")
        elif "muziej" in t or "🏛️" in t:
            send_random(chat_id, "muziejai", "🏛️ Muziejai vaikams:")
        else:
            # Full day plan
            p1 = random.choice(PLACES.get("zaidimai", [{"name":"Bernardinu sodas"}])) if PLACES.get("zaidimai") else {"name":"Bernardinu sodas","url":""}
            p2 = random.choice(PLACES.get("maistas", [{"name":"Etno Dvaras"}])) if PLACES.get("maistas") else {"name":"Etno Dvaras","url":""}
            p3 = random.choice(PLACES.get("muziejai", [{"name":"Mo Muziejus"}])) if PLACES.get("muziejai") else {"name":"Mo Muziejus","url":""}
            p4 = random.choice(PLACES.get("ledi", [{"name":"Sugamour"}])) if PLACES.get("ledi") else {"name":"Sugamour","url":""}
            text = f"📅 ŠIANDIENOS PLANAS (auto):\n\n🛝 10:00 {p1['name']}\n🍽️ 12:30 {p2['name']}\n🏛️ 15:00 {p3['name']}\n🍦 16:30 {p4['name']}"
            url = f"https://www.google.com/maps/dir/{p1['name'].replace(' ','+')}/{p2['name'].replace(' ','+')}/{p3['name'].replace(' ','+')}/{p4['name'].replace(' ','+')}"
            mk = InlineKeyboardMarkup()
            mk.add(InlineKeyboardButton("🗺️ ATIDARYTI VISĄ MARŠRUTĄ", url=url))
            bot.send_message(chat_id, text, reply_markup=mk)

    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=auto_reload_loop, daemon=True).start()
    print("JUDU V3 B LIVE - SHEETS MODE")
    bot.infinity_polling(skip_pending=True)
else:
    print("No BOT_TOKEN")
    threading.Thread(target=run_web, daemon=True).start()
    while True: time.sleep(60)
