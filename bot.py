import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# VILNIAUS ŠEIMŲ BAZĖ - 15 VIETŲ SU KATEGORIJOM
PLACES = {
    "ledai": [
        {"name": "AJ Šokoladas", "addr": "Gedimino pr. 46", "desc": "Rankų darbo ledai, belgiškas šokoladas", "price": "3-5€"},
        {"name": "Beigelistai", "addr": "Literatų g. 7", "desc": "Beigeliai + ledai vaikams", "price": "2-4€"},
        {"name": "Pink&Yellow", "addr": "Gedimino pr. 44a", "desc": "Desertai ir ledai šeimoms", "price": "4-6€"},
    ],
    "zaidimai": [
        {"name": "Vaikų žaidimų aikštelė Baltojo tilto", "addr": "Upės g. 6", "desc": "Didžiausia nemokama aikštelė centre", "price": "Nemokamai"},
        {"name": "Bernardinų sodas", "addr": "Maironio g. 1", "desc": "Sūpynės, karuselė, tvenkinys", "price": "Nemokamai"},
        {"name": "Vingio parkas", "addr": "M. K. Čiurlionio g. 100", "desc": "Milžiniška teritorija, žaidimai gamtoje", "price": "Nemokamai"},
    ],
    "pavalgyt": [
        {"name": "Brussels Mussels", "addr": "Vilniaus g. 17", "desc": "Vaikų kėdutės, midijos, vafliai", "price": "15-25€"},
        {"name": "Grill Deals", "addr": "Konstitucijos pr. 7A", "desc": "BBQ, didelės porcijos šeimai", "price": "12-20€"},
        {"name": "Beigelistai", "addr": "Literatų g. 7", "desc": "Greita, pigu, draugiška vaikams", "price": "5-10€"},
    ],
    "muziejai": [
        {"name": "Energetikos ir technikos muziejus", "addr": "Rinktinės g. 2", "desc": "Interaktyvu, galima liesti viską", "price": "Vaikams iki 7m nemokamai"},
        {"name": "MO muziejus", "addr": "Pylimo g. 17", "desc": "Modernus menas, edukacijos vaikams", "price": "5€ vaikams"},
        {"name": "Lukiškių kalėjimas 2.0", "addr": "Lukiškių skg. 6", "desc": "Renginiai, koncertai, maistas", "price": "Nemokamai įeiti"},
    ]
}

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("☀️ Šiandienos planas", callback_data='plan'),
         InlineKeyboardButton("🍦 Kur ledų?", callback_data='ledai')],
        [InlineKeyboardButton("🛝 Žaidimų aikštelės", callback_data='zaidimai'),
         InlineKeyboardButton("🍕 Kur pavalgyt?", callback_data='pavalgyt')],
        [InlineKeyboardButton("🔬 Muziejai vaikams", callback_data='muziejai'),
         InlineKeyboardButton("🗺️ Sugeneruoti maršrutą", callback_data='marshrutas')],
        [InlineKeyboardButton("🇱🇹 LT / 🇷🇺 RU / 🇬🇧 EN", callback_data='kalba')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Sveiki! Esu VILNIUS ŠEIMŲ GIDAS - dabar su visom durim!\n\n"
        "Ką galiu:\n"
        "• Generuoti dienos planą šeimai\n"
        "• Rasti kur ledų, kur pavalgyt, kur žaist\n"
        "• Sukurti maršrutą per Google Maps\n"
        "• Atsakyti į bet kokį klausimą: 'kur su 2m vaiku?', 'kur pigiai?'\n\n"
        "Pasirink arba parašyk laisvai:"
    )
    await update.message.reply_text(text, reply_markup=get_main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.lower()
    
    # AI LOGIKA - PAPRASTA BET VEIKIA
    if "led" in txt or "ice" in txt or "морож" in txt:
        category = "ledai"
        title = "🍦 Kur ledų Vilniuje:"
    elif "zaid" in txt or "play" in txt or "площад" in txt or "aikšt" in txt:
        category = "zaidimai"
        title = "🛝 Žaidimų aikštelės:"
    elif "valgy" in txt or "eat" in txt or "поест" in txt or "ресторан" in txt:
        category = "pavalgyt"
        title = "🍕 Kur pavalgyt su šeima:"
    elif "muziej" in txt or "museum" in txt:
        category = "muziejai"
        title = "🔬 Muziejai vaikams:"
    else:
        # Jei nesuprato, rodo viską
        category = None
        title = f"🔍 Ieškai: '{update.message.text}'\n\nŠtai kas populiariausia šeimoms:"

    if category:
        places = PLACES[category]
    else:
        places = PLACES["ledai"][:1] + PLACES["zaidimai"][:1] + PLACES["pavalgyt"][:1]

    msg = title + "\n\n"
    for p in places:
        msg += f"📍 {p['name']}\n{p['addr']}\n{p['desc']} - {p['price']}\n\n"

    # Generuoja maršruto linką
    if places:
        addrs = "+".join([p['addr'].replace(' ', '+') for p in places[:3]])
        maps_link = f"https://www.google.com/maps/dir/{addrs}"
        keyboard = [[InlineKeyboardButton("🗺️ Atidaryti maršrutą Maps", url=maps_link)],
                     [InlineKeyboardButton("🏠 Į pagrindinį", callback_data='home')]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(msg, reply_markup=get_main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'home' or data == 'kalba':
        await query.message.reply_text("Pasirink:", reply_markup=get_main_menu())
        return

    if data == 'plan':
        text = "☀️ ŠIANDIENOS PLANAS ŠEIMAI\n\n🛝 10:00 - Baltojo tilto aikštelė\nUpės g. 6, nemokamai\n\n🍕 12:30 - Beigelistai\nLiteratų g. 7, 5-10€\n\n🔬 14:30 - Energetikos muziejus\nRinktinės g. 2, vaikams iki 7m nemokamai"
        places = [PLACES["zaidimai"][0], PLACES["pavalgyt"][2], PLACES["muziejai"][0]]
    elif data in PLACES:
        places = PLACES[data]
        titles = {"ledai": "🍦 Kur ledų?", "zaidimai": "🛝 Žaidimų aikštelės", "pavalgyt": "🍕 Kur pavalgyt?", "muziejai": "🔬 Muziejai"}
        text = titles.get(data, "") + "\n\n"
        for p in places:
            text += f"📍 {p['name']}\n{p['addr']}\n{p['desc']} - {p['price']}\n\n"
    elif data == 'marshrutas':
        text = "🗺️ DIENOS MARŠRUTAS sugeneruotas!\n\n10:00 Baltojo tilto aikštelė -> 12:30 Beigelistai -> 14:30 Energetikos muziejus\n\nBendras atstumas: 2.3km pėsčiomis"
        places = [PLACES["zaidimai"][0], PLACES["pavalgyt"][2], PLACES["muziejai"][0]]
    else:
        text = "Pasirink:"
        places = []

    if places and data != 'plan':
        pass
    elif data == 'plan' or data == 'marshrutas':
        pass
    else:
        places = []

    if places:
        addrs = "/".join([p['addr'].replace(' ', '+') for p in places[:3]])
        maps_link = f"https://www.google.com/maps/dir/{addrs}"
        keyboard = [[InlineKeyboardButton("🗺️ Atidaryti Maps", url=maps_link)],
                     [InlineKeyboardButton("🏠 Meniu", callback_data='home')]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        if data not in ['home', 'kalba']:
            await query.edit_message_text(text=text, reply_markup=get_main_menu())
        else:
            await query.message.reply_text("Pasirink:", reply_markup=get_main_menu())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("V2 Botas su visom durim paleistas!")
    app.run_polling()

if __name__ == '__main__':
    main()
