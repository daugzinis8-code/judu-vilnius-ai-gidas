
import os, json, math, random, threading, datetime
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN=os.getenv("BOT_TOKEN","").strip()
app=Flask(__name__)
@app.route("/")
def home(): return "JUDU V5 SMART LIVE"
@app.route("/health")
def health(): return "OK",200
def run_web():
    port=int(os.getenv("PORT",10000))
    app.run(host="0.0.0.0",port=port)

def haversine(lat1,lon1,lat2,lon2):
    R=6371
    dlat=math.radians(lat2-lat1)
    dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c=2*math.atan2(math.sqrt(a),math.sqrt(1-a))
    return R*c

PLACES={}
try:
    with open('places.json','r',encoding='utf-8') as f:
        PLACES=json.load(f)
except:
    PLACES={}

USER_DATA={}  # chat_id -> {age, stroller, location, weather}

def get_user(chat_id):
    if chat_id not in USER_DATA:
        USER_DATA[chat_id]={"age":None,"stroller":None,"lat":None,"lon":None}
    return USER_DATA[chat_id]

def score_place(place, user, hour):
    score=0
    # 1. Amzius logika
    age=user.get("age")
    if age:
        if age=="0-2" and "baby" in place.get("tags",[]) or "stroller" in place.get("tags",[]): score+=10
        if age=="0-2" and "baby_table" in place.get("tags",[]): score+=5
        if age=="3-5" and "toddler" in place.get("tags",[]): score+=10
        if age=="6-12" and "interactive" in place.get("tags",[]): score+=8
        if age=="0-2" and place.get("age","")=="0-5": score+=7
        if age=="3-5" and "0-5" in place.get("age","") or "3-10" in place.get("age",""): score+=7
    
    # 2. Laikas logika
    if 6 <= hour < 11 and place.get("time")=="morning": score+=5
    if 11 <= hour < 14 and place.get("time")=="lunch": score+=5
    if 14 <= hour < 18 and place.get("time")=="afternoon": score+=5
    if place.get("time")=="all": score+=2
    
    # 3. Lokacija logika - kuo arciau, tuo geriau
    if user.get("lat") and "lat" in place:
        dist=haversine(user["lat"],user["lon"],place["lat"],place["lon"])
        score+= max(0, 10 - dist*2)  # 0km=+10, 5km=0
    
    # 4. Vežimėlis
    if user.get("stroller") and "stroller" in place.get("tags",[]): score+=6
    
    # 5. Random siek tiek kad nesikartotu
    score+=random.random()*2
    return score

if TOKEN:
    bot=telebot.TeleBot(TOKEN,threaded=False)

    def get_main_menu():
        m=ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(KeyboardButton("🧠 Protingas planas šeimai"), KeyboardButton("📍 Artimiausi prie manęs", request_location=True))
        m.add(KeyboardButton("🛝 Žaidimų aikštelės"), KeyboardButton("🍽️ Kur pavalgyt?"))
        m.add(KeyboardButton("🏛️ Muziejai"), KeyboardButton("🍦 Kur ledų?"))
        return m

    def get_age_menu():
        m=ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(KeyboardButton("👶 0-2 metai (kūdikis)"), KeyboardButton("🧒 3-5 metai"))
        m.add(KeyboardButton("👦 6-9 metai"), KeyboardButton("🧑 10+ metų"))
        m.add(KeyboardButton("⏭️ Praleisti"))
        return m

    @bot.message_handler(commands=['start'])
    def start_cmd(msg):
        get_user(msg.chat.id)
        bot.send_message(msg.chat.id,"👋 JUDU V5 - PROTINGAS gidas!\n\nNe random, o LOGIŠKAI pagal šeimą.\n\nPirmiausia - kiek metų vaikui?", reply_markup=get_age_menu())

    @bot.message_handler(content_types=['location'])
    def loc_handle(msg):
        u=get_user(msg.chat.id)
        u["lat"]=msg.location.latitude
        u["lon"]=msg.location.longitude
        bot.send_message(msg.chat.id,f"📍 Gavau vietą! Dabar parenku LOGIŠKAI arčiausiai + pagal amžių.", reply_markup=get_main_menu())
        send_smart_plan(msg.chat.id)

    def send_smart_plan(chat_id):
        u=get_user(chat_id)
        hour=datetime.datetime.now().hour
        # Parenkam logiskai kiekviena kategorija
        all_scored=[]
        for cat in PLACES:
            for p in PLACES[cat]:
                s=score_place(p,u,hour)
                all_scored.append((s,p,cat))
        all_scored.sort(key=lambda x: x[0], reverse=True)
        
        # Logiskas dienos planas pagal laika
        morning=[x for x in all_scored if x[1].get("time") in ["morning","all"] and x[2]=="zaidimai"][:1]
        lunch=[x for x in all_scored if x[1].get("time") in ["lunch","all"] and x[2]=="maistas"][:1]
        afternoon=[x for x in all_scored if x[1].get("time") in ["afternoon","all"] and x[2]=="muziejai"][:1]
        ice=[x for x in all_scored if x[2]=="ledi"][:1]
        
        plan=morning+lunch+afternoon+ice
        if not plan:
            plan=all_scored[:4]
        
        text=f"🧠 PROTINGAS PLANAS tavo šeimai ({u.get('age','')}):\n\n"
        mk=InlineKeyboardMarkup()
        route_parts=[]
        for score,p,cat in plan:
            dist_txt=""
            if u.get("lat") and "lat" in p:
                d=haversine(u["lat"],u["lon"],p["lat"],p["lon"])
                dist_txt=f" - {d:.1f}km"
                route_parts.append(f"{p['lat']},{p['lon']}")
            emoji={"zaidimai":"🛝","maistas":"🍽️","muziejai":"🏛️","ledi":"🍦"}.get(cat,"📍")
            text+=f"{emoji} {p['name']}{dist_txt} - {p['addr']} [{','.join(p.get('tags',[])[:2])}]\n"
            if u.get("lat"):
                mk.add(InlineKeyboardButton(f"🧭 {p['name']}{dist_txt} - VESTI", url=f"https://www.google.com/maps/dir/{u['lat']},{u['lon']}/{p['lat']},{p['lon']}"))
            else:
                mk.add(InlineKeyboardButton(f"🗺️ {p['name']}", url=p['url']))
        
        if route_parts and u.get("lat"):
            mk.add(InlineKeyboardButton("🗺️ VISAS LOGIŠKAS MARŠRUTAS", url=f"https://www.google.com/maps/dir/{u['lat']},{u['lon']}/{'/'.join(route_parts)}"))
        
        text+="\nLogika: rytas=aikštelė, pietūs=maistas su kėdute, popiet=muziejus (vidus jei lietus), ledai pabaigai. Arčiausiai + pagal amžių."
        bot.send_message(chat_id,text,reply_markup=mk)

    def send_category_smart(chat_id, cat_key):
        u=get_user(chat_id)
        hour=datetime.datetime.now().hour
        lst=PLACES.get(cat_key,[])
        scored=[(score_place(p,u,hour),p) for p in lst]
        scored.sort(key=lambda x: x[0], reverse=True)
        top=[p for s,p in scored[:3]]
        if not top:
            bot.send_message(chat_id,"Tuoj papildysim!")
            return
        cat_names={"ledi":"🍦 Ledai","zaidimai":"🛝 Aikštelės","maistas":"🍽️ Maistas","muziejai":"🏛️ Muziejai"}
        text=f"{cat_names.get(cat_key,cat_key)} LOGIŠKAI tavo šeimai ({u.get('age','')}):\n\n"
        mk=InlineKeyboardMarkup()
        for p in top:
            dist_txt=""
            if u.get("lat") and "lat" in p:
                d=haversine(u["lat"],u["lon"],p["lat"],p["lon"])
                dist_txt=f" {d:.1f}km"
            text+=f"📍 {p['name']}{dist_txt} - {p['addr']} - {','.join(p.get('tags',[])[:3])}\n"
            if u.get("lat"):
                mk.add(InlineKeyboardButton(f"🧭 {p['name']}{dist_txt}", url=f"https://www.google.com/maps/dir/{u['lat']},{u['lon']}/{p['lat']},{p['lon']}"))
            else:
                mk.add(InlineKeyboardButton(f"🗺️ {p['name']}", url=p['url']))
        bot.send_message(chat_id,text,reply_markup=mk)

    @bot.message_handler(func=lambda m: True)
    def all_msg(msg):
        t=(msg.text or "").lower()
        chat_id=msg.chat.id
        u=get_user(chat_id)
        
        if "0-2" in msg.text or "kūdikis" in t:
            u["age"]="0-2"; u["stroller"]=True
            bot.send_message(chat_id,"👶 Supratau - kūdikis 0-2m, su vežimėliu. Rinksiu vietas su vystymo stalu, vežimėliui, ramias.", reply_markup=get_main_menu())
            send_smart_plan(chat_id); return
        if "3-5" in msg.text:
            u["age"]="3-5"
            bot.send_message(chat_id,"🧒 3-5m - aktyvus amžius! Rinksiu aikšteles, interaktyvius muziejus, ledus.", reply_markup=get_main_menu())
            send_smart_plan(chat_id); return
        if "6-9" in msg.text or "10+" in msg.text:
            u["age"]="6-12"
            bot.send_message(chat_id,"👦 Vyresnis - įdomūs muziejai, energetika, iliuzijos!", reply_markup=get_main_menu())
            send_smart_plan(chat_id); return
        if "praleisti" in t:
            bot.send_message(chat_id,"Gerai, rodau bendrą planą:", reply_markup=get_main_menu())
            send_smart_plan(chat_id); return

        if "protingas" in t or "šeimai" in t:
            if not u.get("age"):
                bot.send_message(chat_id,"Pirmiausia pasakyk amžių:", reply_markup=get_age_menu())
            else:
                send_smart_plan(chat_id)
        elif "artimiausi" in t or "📍" in msg.text:
            bot.send_message(chat_id,"📍 Spausk 'Artimiausi prie manęs' apačioje ir atsiųsk lokaciją:", reply_markup=get_main_menu())
        elif "led" in t or "🍦" in t:
            send_category_smart(chat_id,"ledi")
        elif "zaid" in t or "aikšt" in t or "🛝" in t:
            send_category_smart(chat_id,"zaidimai")
        elif "pavalgy" in t or "valgy" in t or "🍽️" in t:
            send_category_smart(chat_id,"maistas")
        elif "muziej" in t or "🏛️" in t:
            send_category_smart(chat_id,"muziejai")
        else:
            send_smart_plan(chat_id)

    threading.Thread(target=run_web,daemon=True).start()
    print("JUDU V5 SMART LIVE")
    bot.infinity_polling(skip_pending=True)
else:
    print("No token")
    threading.Thread(target=run_web,daemon=True).start()
    import time
    while True: time.sleep(60)
