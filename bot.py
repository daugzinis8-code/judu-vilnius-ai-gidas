
import math, sqlite3, random
from datetime import datetime, timedelta

# pip install aiogram==3.7.0
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

BOT_TOKEN = "DEK_SAVO_TOKENA_CIA"

# ================= VILNIUS DB - TIKROS VIETOS =================
# Seimas: 54.6860, 25.2820

MAISTAS_DB = [
    {"id": 1, "pav": "Stebuklai", "adresas": "Gedimino pr. 30", "lat": 54.6868, "lon": 25.2828, "kids": True, "reklama": True},
    {"id": 2, "pav": "Jurgis ir Drakonas", "adresas": "Gedimino pr. 22", "lat": 54.6870, "lon": 25.2790, "kids": True, "reklama": False},
    {"id": 3, "pav": "Rose & Basilic", "adresas": "J. Jasinskio g. 2", "lat": 54.6889, "lon": 25.2748, "kids": True, "reklama": False},
    {"id": 4, "pav": "Etno Dvaras", "adresas": "Pilies g. 16", "lat": 54.6822, "lon": 25.2886, "kids": True, "reklama": False},
    {"id": 5, "pav": "Momo Grill", "adresas": "Vokieciu g. 8", "lat": 54.6815, "lon": 25.2840, "kids": True, "reklama": True},
    {"id": 6, "pav": "Kristoforas", "adresas": "Didzioji g. 31", "lat": 54.6780, "lon": 25.2869, "kids": False, "reklama": False},
]

LEDAI_DB = [
    {"id": 101, "pav": "Valentino ledai", "adresas": "Gedimino pr. 45", "lat": 54.6875, "lon": 25.2780, "reklama": True},
    {"id": 102, "pav": "Holy Donut - ledai", "adresas": "Didzioji g. 13", "lat": 54.6795, "lon": 25.2860, "reklama": False},
    {"id": 103, "pav": "Gelateria Vilnius", "adresas": "Vokieciu g. 10", "lat": 54.6805, "lon": 25.2845, "reklama": False},
]

MUZIEJAI_DB = [
    {"id": 201, "pav": "Vytauto Kasiulio muziejus", "adresas": "A. Gostauto g. 1", "lat": 54.6901, "lon": 25.2781, "edukacinis": True},
    {"id": 202, "pav": "Energetikos ir technikos muziejus", "adresas": "Rinktines g. 2", "lat": 54.6902, "lon": 25.2881, "edukacinis": True},
    {"id": 203, "pav": "MO muziejus", "adresas": "Pylimo g. 17", "lat": 54.6763, "lon": 25.2778, "edukacinis": True},
    {"id": 204, "pav": "Iliuziju muziejus", "adresas": "Vokieciu g. 6", "lat": 54.6808, "lon": 25.2845, "edukacinis": True},
    {"id": 205, "pav": "Pinigu muziejus", "adresas": "Totoriu g. 2", "lat": 54.6845, "lon": 25.2815, "edukacinis": True},
]

# ================= PAGALBINES FUNKCIJOS =================
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

# ================= LOGIKA KURIOS NOREJAI =================
def kur_pavalgyt_visada_3_artimiausias(user_lat, user_lon):
    # BE ROTACIJOS - visada artimiausios
    for v in MAISTAS_DB:
        v['km'] = atstumas_km(user_lat, user_lon, v['lat'], v['lon'])
    MAISTAS_DB.sort(key=lambda x: x['km'])
    return MAISTAS_DB[:3]

def kur_ledu_visada_3_artimiausias(user_lat, user_lon):
    for v in LEDAI_DB:
        v['km'] = atstumas_km(user_lat, user_lon, v['lat'], v['lon'])
    LEDAI_DB.sort(key=lambda x: x['km'])
    return LEDAI_DB[:3]

def muziejai_su_rotacija(user_lat, user_lon, user_id):
    aplankyti = gauti_aplankytus(user_id, 'muziejus', 30)
    laisvi = [m for m in MUZIEJAI_DB if m['id'] not in aplankyti]
    if len(laisvi) < 3:
        laisvi = MUZIEJAI_DB
        isvalyti_istorija(user_id, 'muziejus')
    
    for m in laisvi:
        m['km'] = atstumas_km(user_lat, user_lon, m['lat'], m['lon'])
    laisvi.sort(key=lambda x: x['km'])
    return laisvi[:3]

# ================= TELEGRAM BOT =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Dalintis lokacija", request_location=True)],
        [KeyboardButton(text="Kur pavalgyt?"), KeyboardButton(text="Kur ledu?")],
        [KeyboardButton(text="Muziejai"), KeyboardButton(text="Zaidimu aiksteles")],
        [KeyboardButton(text="Siandienos planas")]
    ],
    resize_keyboard=True
)

def make_inline(vietos):
    buttons = []
    for v in vietos:
        badge = " ⭐" if v.get('reklama') else ""
        buttons.append([InlineKeyboardButton(text=f"{v['pav']} - {v['km']:.2f}km{badge}", url=f"https://www.google.com/maps/search/?api=1&query={v['lat']},{v['lon']}")])
    buttons.append([InlineKeyboardButton(text="🗺️ VISAS MARSUTAS per 3 vietas", callback_data="marsrutas")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(m: Message):
    init_db()
    await m.answer("Sveiki! Esu Vilnius Seimu Gidas. Pasidalink lokacija kad parodyciau 3 artimiausias vietas.", reply_markup=keyboard_main)

@dp.message(F.location)
async def lokacija(m: Message):
    lat = m.location.latitude
    lon = m.location.longitude
    await m.answer(f"Gavau lokacija! {lat:.4f}, {lon:.4f}. Dabar spausk ka nori rasti:", reply_markup=keyboard_main)
    # issaugom i atminti - galima naudoti global dict
    dp["user_locs"] = dp.get("user_locs", {})
    dp["user_locs"][m.from_user.id] = (lat, lon)

def get_user_loc(user_id):
    locs = dp.get("user_locs", {})
    return locs.get(user_id, (54.6860, 25.2820)) # default Seimas

@dp.message(F.text == "Kur pavalgyt?")
async def pavalgyt(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_pavalgyt_visada_3_artimiausias(lat, lon)
    tekstas = "🍽️ 3 ARTIMIAUSIOS kur pavalgyt su vaikais (visada artimiausios):\n\n"
    for v in trys:
        tekstas += f"📍 {v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n\n"
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Kur ledu?")
async def ledu(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_ledu_visada_3_artimiausias(lat, lon)
    tekstas = "🍦 3 ARTIMIAUSIOS kur ledu:\n\n"
    for v in trys:
        tekstas += f"📍 {v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n\n"
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Muziejai")
async def muziejai(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = muziejai_su_rotacija(lat, lon, m.from_user.id)
    tekstas = "🏛️ 3 MUZIEJAI (rotuojasi, nesikartoja 30d):\n\n"
    for v in trys:
        tekstas += f"📍 {v['pav']} - {v['km']:.2f} km\n{v['adresas']}\n\n"
    await m.answer(tekstas, reply_markup=make_inline(trys))
    issaugoti_aplankytus(m.from_user.id, trys, 'muziejus')

# Paleidimas: python bot_vilnius_final.py
if __name__ == "__main__":
    import asyncio
    init_db()
    dp["user_locs"] = {}
    asyncio.run(dp.start_polling(bot))
