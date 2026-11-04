
import math, sqlite3, os, json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "123456:PLACEHOLDER"

# ================ PILNA DB IS JSON (34 vietos) ================
# Jei JSON failas egzistuoja - kraunam iš jo, jei ne - fallback į hardcoded
try:
    with open("places_full_vilnius.json","r",encoding="utf-8") as f:
        ALL_PLACES = json.load(f)
    MAISTAS_DB = [p for p in ALL_PLACES if p['type']=='maistas']
    LEDAI_DB = [p for p in ALL_PLACES if p['type']=='ledai']
    MUZIEJAI_DB = [p for p in ALL_PLACES if p['type']=='muziejus']
    AIKSTELES_DB = [p for p in ALL_PLACES if p['type']=='zaidimu_aiksteles']
    print(f"Loaded {len(ALL_PLACES)} places from JSON")
except:
    # Fallback - tavo original
    MAISTAS_DB = [
        {"id": 1, "pav": "Stebuklai", "adresas": "Gedimino pr. 30", "lat": 54.6868, "lon": 25.2828, "reklama": True},
        {"id": 2, "pav": "Jurgis ir Drakonas", "adresas": "Gedimino pr. 22", "lat": 54.6870, "lon": 25.2790, "reklama": False},
        {"id": 3, "pav": "Rose & Basilic", "adresas": "J. Jasinskio g. 2", "lat": 54.6889, "lon": 25.2748, "reklama": False},
        {"id": 4, "pav": "Etno Dvaras", "adresas": "Pilies g. 16", "lat": 54.6822, "lon": 25.2886, "reklama": False},
        {"id": 5, "pav": "Momo Grill", "adresas": "Vokieciu g. 8", "lat": 54.6815, "lon": 25.2840, "reklama": True},
        {"id": 6, "pav": "OSH halal", "adresas": "L. Stuokos-Gucevičiaus g. 7-1", "lat": 54.68455536, "lon": 25.28440684, "reklama": False},
        {"id": 9, "pav": "Bernelių Užeiga", "adresas": "M. Valančiaus g. 9", "lat": 54.684, "lon": 25.289, "reklama": True},
    ]
    LEDAI_DB = [
        {"id": 101, "pav": "Valentino ledai", "adresas": "Gedimino pr. 45", "lat": 54.6875, "lon": 25.2780, "reklama": True},
        {"id": 102, "pav": "Holy Donut", "adresas": "Didzioji g. 13", "lat": 54.6795, "lon": 25.2860, "reklama": False},
        {"id": 106, "pav": "il trottolino", "adresas": "Upės g. 6", "lat": 54.69335167, "lon": 25.27331095, "reklama": False},
        {"id": 101, "pav": "Sugamour", "adresas": "Vilniaus g. 18", "lat": 54.685, "lon": 25.281, "reklama": True},
    ]
    MUZIEJAI_DB = [
        {"id": 201, "pav": "Vytauto Kasiulio muziejus", "adresas": "A. Gostauto g. 1", "lat": 54.6901, "lon": 25.2781},
        {"id": 202, "pav": "Energetikos ir technikos muziejus", "adresas": "Rinktines g. 2", "lat": 54.6902, "lon": 25.2881},
        {"id": 203, "pav": "MO muziejus", "adresas": "Pylimo g. 17", "lat": 54.6763, "lon": 25.2778},
        {"id": 204, "pav": "Iliuziju muziejus", "adresas": "Vokieciu g. 6", "lat": 54.6808, "lon": 25.2845},
        {"id": 205, "pav": "Pinigu muziejus", "adresas": "Totoriu g. 2", "lat": 54.6845, "lon": 25.2815},
    ]
    AIKSTELES_DB = [
        {"id": 301, "pav": "Bernardinų sodo aikštelė", "adresas": "Bernardinų sodas", "lat": 54.6825, "lon": 25.294, "reklama": False},
        {"id": 302, "pav": "Lukiškių aikštės playground", "adresas": "Lukiškių aikštė", "lat": 54.69039591, "lon": 25.27088766, "reklama": False},
        {"id": 303, "pav": "Baltojo tilto aikštynas", "adresas": "Upės g. 6", "lat": 54.69300532, "lon": 25.27483221, "reklama": False},
    ]

def atstumas_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def init_db():
    conn = sqlite3.connect("seimu_gidas.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS aplankyti (user_id INTEGER, vieta_id INTEGER, data TEXT, tipas TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_seen TEXT, last_loc TEXT)")
    conn.commit()
    conn.close()

def gauti_aplankytus(user_id, tipas, dienos=30):
    conn = sqlite3.connect("seimu_gidas.db")
    c = conn.cursor()
    riba = (datetime.now() - timedelta(days=dienos)).isoformat()
    c.execute("SELECT vieta_id FROM aplankyti WHERE user_id=? AND tipas=? AND data > ?", (user_id, tipas, riba))
    rez = [r[0] for r in c.fetchall()]
    conn.close()
    return rez

def issaugoti_aplankytus(user_id, vietos, tipas):
    conn = sqlite3.connect("seimu_gidas.db")
    c = conn.cursor()
    dabar = datetime.now().isoformat()
    for v in vietos:
        c.execute("INSERT INTO aplankyti VALUES (?,?,?,?)", (user_id, v['id'], dabar, tipas))
    conn.commit()
    conn.close()

def isvalyti_istorija(user_id, tipas):
    conn = sqlite3.connect("seimu_gidas.db")
    c = conn.cursor()
    c.execute("DELETE FROM aplankyti WHERE user_id=? AND tipas=?", (user_id, tipas))
    conn.commit()
    conn.close()

# ============ UPGRADED: reklama + atstumas ============
def kur_3_artimiausias_su_reklama(db, user_lat, user_lon):
    for v in db:
        v['km'] = atstumas_km(user_lat, user_lon, v['lat'], v['lon'])
    # Rūšiuojam: pirma reklama=True, tada pagal atstumą
    db_sorted = sorted(db, key=lambda x: (0 if x.get('reklama') else 1, x['km']))
    return db_sorted[:3]

def kur_pavalgyt_3_artimiausias(user_lat, user_lon):
    return kur_3_artimiausias_su_reklama(MAISTAS_DB.copy(), user_lat, user_lon)

def kur_ledu_3_artimiausias(user_lat, user_lon):
    return kur_3_artimiausias_su_reklama(LEDAI_DB.copy(), user_lat, user_lon)

def kur_aiksteliu_3_artimiausias(user_lat, user_lon):
    return kur_3_artimiausias_su_reklama(AIKSTELES_DB.copy(), user_lat, user_lon)

def muziejai_su_rotacija(user_lat, user_lon, user_id):
    aplankyti = gauti_aplankytus(user_id, 'muziejus', 30)
    laisvi = [m for m in MUZIEJAI_DB if m['id'] not in aplankyti]
    if len(laisvi) < 3:
        laisvi = MUZIEJAI_DB.copy()
        isvalyti_istorija(user_id, 'muziejus')
    else:
        laisvi = laisvi.copy()
    for m in laisvi:
        m['km'] = atstumas_km(user_lat, user_lon, m['lat'], m['lon'])
    laisvi.sort(key=lambda x: x['km'])
    return laisvi[:3]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Dalintis lokacija", request_location=True)],
        [KeyboardButton(text="Kur pavalgyt?"), KeyboardButton(text="Kur ledu?")],
        [KeyboardButton(text="Muziejai"), KeyboardButton(text="Zaidimu aiksteles")],
        [KeyboardButton(text="Siandienos planas")],
    ],
    resize_keyboard=True
)

def make_inline(vietos):
    buttons = []
    for v in vietos:
        badge = " ⭐ REKLAMA" if v.get('reklama') else ""
        # Tekstas su atstumu
        buttons.append([InlineKeyboardButton(text=f"{v['pav']} - {v['km']:.2f}km{badge}", url=f"https://www.google.com/maps/search/?api=1&query={v['lat']},{v['lon']}")])
    # Visas maršrutas mygtukas
    if len(vietos)>=2:
        # Sukuriam maršrutą per visas 3 vietas
        waypoints = "|".join([f"{v['lat']},{v['lon']}" for v in vietos])
        buttons.append([InlineKeyboardButton(text="🗺️ VISAS MARŠRUTAS (3 vietos)", url=f"https://www.google.com/maps/dir/?api=1&destination={vietos[-1]['lat']},{vietos[-1]['lon']}&waypoints={waypoints}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(m: Message):
    init_db()
    # Log user
    conn = sqlite3.connect("seimu_gidas.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_seen) VALUES (?,?,?)", (m.from_user.id, m.from_user.username, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    await m.answer(f"Sveiki! Vilnius Šeimų Gidas 👨‍👩‍👧‍👦\n\nTuriu {len(MAISTAS_DB)} vietas pavalgyt, {len(LEDAI_DB)} ledų, {len(AIKSTELES_DB)} aikštelių, {len(MUZIEJAI_DB)} muziejų.\n\n📍 Pasidalink lokacija kad parodyčiau 3 artimiausias vietas!", reply_markup=keyboard_main)

@dp.message(F.location)
async def lokacija(m: Message):
    lat = m.location.latitude
    lon = m.location.longitude
    dp["user_locs"] = dp.get("user_locs", {})
    dp["user_locs"][m.from_user.id] = (lat, lon)
    await m.answer(f"📍 Gavau! {lat:.4f}, {lon:.4f}.\nDabar spausk ką nori rasti - parodysiu 3 artimiausias su atstumais! ⭐ = rekomenduojama", reply_markup=keyboard_main)

def get_user_loc(user_id):
    locs = dp.get("user_locs", {})
    return locs.get(user_id, (54.6860, 25.2820))  # Default: Gedimino pr.

@dp.message(F.text == "Kur pavalgyt?")
async def pavalgyt(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_pavalgyt_3_artimiausias(lat, lon)
    tekstas = "🍽️ 3 ARTIMIAUSIOS kur pavalgyt (⭐ = reklama, prioritetas):\n\n" + "\n".join([f"{'⭐ ' if v.get('reklama') else '📍 '}{v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Kur ledu?")
async def ledu(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_ledu_3_artimiausias(lat, lon)
    tekstas = "🍦 3 ARTIMIAUSIOS kur ledų:\n\n" + "\n".join([f"{'⭐ ' if v.get('reklama') else '📍 '}{v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Muziejai")
async def muziejai(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = muziejai_su_rotacija(lat, lon, m.from_user.id)
    tekstas = "🏛️ 3 MUZIEJAI (rotuojasi 30d, kad neatsibostų):\n\n" + "\n".join([f"📍 {v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))
    issaugoti_aplankytus(m.from_user.id, trys, 'muziejus')

@dp.message(F.text == "Zaidimu aiksteles")
async def aiksteles(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_aiksteliu_3_artimiausias(lat, lon)
    tekstas = "🛝 3 ARTIMIAUSIOS žaidimų aikštelės:\n\n" + "\n".join([f"📍 {v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Siandienos planas")
async def planas(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    # Auto planas: 1 aikštelė + 1 maistas + 1 muziejus + 1 ledai = diena
    a = kur_aiksteliu_3_artimiausias(lat, lon)[0]
    ma = kur_pavalgyt_3_artimiausias(lat, lon)[0]
    mu = muziejai_su_rotacija(lat, lon, m.from_user.id)[0]
    l = kur_ledu_3_artimiausias(lat, lon)[0]
    tekstas = f"🗓️ ŠIANDIENOS PLANAS (pagal tavo lokaciją):\n\n10:00 🛝 {a['pav']} - {a['km']:.2f}km\n{a['adresas']}\n\n12:30 🍽️ {ma['pav']} - {ma['km']:.2f}km\n{ma['adresas']}\n\n15:00 🏛️ {mu['pav']} - {mu['km']:.2f}km\n{mu['adresas']}\n\n16:30 🍦 {l['pav']} - {l['km']:.2f}km\n{l['adresas']}\n"
    await m.answer(tekstas)

if __name__ == "__main__":
    import asyncio
    init_db()
    dp["user_locs"] = {}
    if "PLACEHOLDER" in BOT_TOKEN:
        print("KLAIDA: BOT_TOKEN nerastas Render Environment.")
    else:
        print(f"Botas paleistas Vilniui FINAL, vietų: maistas={len(MAISTAS_DB)}, ledai={len(LEDAI_DB)}, aiksteles={len(AIKSTELES_DB)}, muziejai={len(MUZIEJAI_DB)}")
    asyncio.run(dp.start_polling(bot))
