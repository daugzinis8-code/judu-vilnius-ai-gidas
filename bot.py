
import math, sqlite3, os, json, asyncio, logging, threading
from datetime import datetime, timedelta
from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

# ===== WEB SERVER KAD RENDER NEMIGTU =====
app = Flask(__name__)
@app.route('/')
def home():
    return "Vilnius Seimu Gidas gyvas! Bot polling veikia ✅"
@app.route('/health')
def health():
    return "OK", 200

def run_web():
    # Render duoda PORT env, default 10000
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ===== BOT SETUP =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN", "123456:PLACEHOLDER")

try:
    with open("places_full_vilnius.json","r",encoding='utf-8') as f:
        ALL_PLACES = json.load(f)
    MAISTAS_DB = [p for p in ALL_PLACES if p['type']=='maistas']
    LEDAI_DB = [p for p in ALL_PLACES if p['type']=='ledai']
    MUZIEJAI_DB = [p for p in ALL_PLACES if p['type']=='muziejus']
    AIKSTELES_DB = [p for p in ALL_PLACES if p['type']=='zaidimu_aiksteles']
except Exception as e:
    logger.warning(f"places_full_vilnius.json nerastas: {e}, naudoju fallback")
    MAISTAS_DB = [
        {"id":1,"pav":"Stebuklai","adresas":"Gedimino pr. 30","lat":54.6868,"lon":25.2828,"reklama":True},
        {"id":4,"pav":"Etno Dvaras","adresas":"Pilies g. 16","lat":54.6822,"lon":25.2886,"reklama":False},
        {"id":5,"pav":"Momo Grill","adresas":"Vokieciu g. 8","lat":54.6815,"lon":25.284,"reklama":True},
    ]
    LEDAI_DB = [
        {"id":101,"pav":"Sugamour","adresas":"Vilniaus g. 18","lat":54.685,"lon":25.281,"reklama":True},
        {"id":106,"pav":"il trottolino","adresas":"Upės g. 6","lat":54.69335,"lon":25.2733,"reklama":False},
    ]
    MUZIEJAI_DB = [
        {"id":203,"pav":"MO muziejus","adresas":"Pylimo g. 17","lat":54.6763,"lon":25.2778},
        {"id":202,"pav":"Energetikos muziejus","adresas":"Rinktines g. 2","lat":54.6902,"lon":25.2881},
    ]
    AIKSTELES_DB = [
        {"id":301,"pav":"Bernardinų aikštelė","adresas":"Bernardinų sodas","lat":54.6825,"lon":25.294},
        {"id":302,"pav":"Lukiškių aikštelė","adresas":"Lukiškių aikštė","lat":54.69039,"lon":25.27088},
    ]

def atstumas_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def _init_db_sync():
    conn = sqlite3.connect("seimu_gidas.db", check_same_thread=False, timeout=10)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS aplankyti (user_id INTEGER, vieta_id INTEGER, data TEXT, tipas TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_tipas ON aplankyti(user_id, tipas, data)")
    conn.commit()
    conn.close()

async def init_db():
    await asyncio.to_thread(_init_db_sync)

def _gauti_sync(user_id, tipas, dienos):
    conn = sqlite3.connect("seimu_gidas.db", timeout=10)
    c = conn.cursor()
    riba = (datetime.now() - timedelta(days=dienos)).isoformat()
    c.execute("SELECT vieta_id FROM aplankyti WHERE user_id=? AND tipas=? AND data > ?", (user_id, tipas, riba))
    rez = [r[0] for r in c.fetchall()]
    conn.close()
    return rez

async def gauti_aplankytus(user_id, tipas, dienos=30):
    return await asyncio.to_thread(_gauti_sync, user_id, tipas, dienos)

def _issaugoti_sync(user_id, vietos, tipas):
    conn = sqlite3.connect("seimu_gidas.db", timeout=10)
    c = conn.cursor()
    dabar = datetime.now().isoformat()
    for v in vietos:
        c.execute("INSERT INTO aplankyti VALUES (?,?,?,?)", (user_id, v['id'], dabar, tipas))
    conn.commit()
    conn.close()

async def issaugoti_aplankytus(user_id, vietos, tipas):
    await asyncio.to_thread(_issaugoti_sync, user_id, vietos, tipas)

def _isvalyti_sync(user_id, tipas):
    conn = sqlite3.connect("seimu_gidas.db", timeout=10)
    c = conn.cursor()
    c.execute("DELETE FROM aplankyti WHERE user_id=? AND tipas=?", (user_id, tipas))
    conn.commit()
    conn.close()

async def isvalyti_istorija(user_id, tipas):
    await asyncio.to_thread(_isvalyti_sync, user_id, tipas)

def kur_3_artimiausias_su_reklama(db, user_lat, user_lon):
    result = []
    for v in db:
        km = atstumas_km(user_lat, user_lon, v['lat'], v['lon'])
        result.append({**v, 'km': km})
    result.sort(key=lambda x: (0 if x.get('reklama') else 1, x['km']))
    return result[:3]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp["user_locs"] = {}

keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Dalintis lokacija", request_location=True)],
        [KeyboardButton(text="Kur pavalgyt?"), KeyboardButton(text="Kur ledu?")],
        [KeyboardButton(text="Muziejai"), KeyboardButton(text="Zaidimu aiksteles")],
    ],
    resize_keyboard=True
)

def make_inline(vietos):
    buttons = []
    for v in vietos:
        badge = " ⭐" if v.get('reklama') else ""
        buttons.append([InlineKeyboardButton(text=f"{v['pav']} {v['km']:.2f}km{badge}", url=f"https://www.google.com/maps/search/?api=1&query={v['lat']},{v['lon']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer(f"👨‍👩‍👧‍👦 Vilnius Šeimų Gidas FAST + WEB! {len(MAISTAS_DB+LEDAI_DB+MUZIEJAI_DB+AIKSTELES_DB)} vietų. Siųsk lokaciją!", reply_markup=keyboard_main)

@dp.message(F.location)
async def lokacija(m: Message):
    lat = m.location.latitude
    lon = m.location.longitude
    dp["user_locs"][m.from_user.id] = (lat, lon)
    logger.info(f"Location {m.from_user.id}: {lat},{lon}")
    await m.answer(f"📍 Gavau! {lat:.4f} {lon:.4f} - rinkis!", reply_markup=keyboard_main)

def get_user_loc(user_id):
    return dp["user_locs"].get(user_id, (54.6860, 25.2820))

@dp.message(F.text == "Kur pavalgyt?")
async def pavalgyt(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_3_artimiausias_su_reklama(MAISTAS_DB, lat, lon)
    tekstas = "🍽️ 3 ARTIMIAUSIOS:\n\n" + "\n".join([f"{'⭐' if v.get('reklama') else '📍'} {v['pav']} {v['km']:.2f}km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Kur ledu?")
async def ledu(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_3_artimiausias_su_reklama(LEDAI_DB, lat, lon)
    tekstas = "🍦 3 LEDAI:\n\n" + "\n".join([f"{'⭐' if v.get('reklama') else '📍'} {v['pav']} {v['km']:.2f}km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Zaidimu aiksteles")
async def aiksteles(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    trys = kur_3_artimiausias_su_reklama(AIKSTELES_DB, lat, lon)
    tekstas = "🛝 3 AIKŠTELĖS:\n\n" + "\n".join([f"📍 {v['pav']} {v['km']:.2f}km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))

@dp.message(F.text == "Muziejai")
async def muziejai(m: Message):
    lat, lon = get_user_loc(m.from_user.id)
    aplankyti = await gauti_aplankytus(m.from_user.id, 'muziejus', 30)
    laisvi = [mm for mm in MUZIEJAI_DB if mm['id'] not in aplankyti]
    if len(laisvi) < 3:
        laisvi = MUZIEJAI_DB.copy()
        await isvalyti_istorija(m.from_user.id, 'muziejus')
    else:
        laisvi = laisvi.copy()
    for mm in laisvi:
        mm['km'] = atstumas_km(lat, lon, mm['lat'], mm['lon'])
    laisvi.sort(key=lambda x: x['km'])
    trys = laisvi[:3]
    tekstas = "🏛️ 3 MUZIEJAI:\n\n" + "\n".join([f"📍 {v['pav']} {v['km']:.2f}km\n{v['adresas']}\n" for v in trys])
    await m.answer(tekstas, reply_markup=make_inline(trys))
    asyncio.create_task(issaugoti_aplankytus(m.from_user.id, trys, 'muziejus'))

async def main():
    await init_db()
    logger.info(f"Bot FAST+WEB paleistas: {len(MAISTAS_DB)} maistas, {len(LEDAI_DB)} ledai, {len(AIKSTELES_DB)} aiksteles, {len(MUZIEJAI_DB)} muziejai")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if "PLACEHOLDER" in BOT_TOKEN:
        print("KLAIDA: BOT_TOKEN nerastas")
    else:
        asyncio.run(main())
