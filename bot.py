def kur_pavalgyt_visada_3_artimiausias(user_lat, user_lon):
    # BE ISTORIJOS - visada tik atstumas
    for v in MAISTAS_DB:
        v['km'] = atstumas(user_lat, user_lon, v['lat'], v['lon'])
    
    MAISTAS_DB.sort(key=lambda x: x['km'])
    return MAISTAS_DB[:3] # visada tos pačios 3 artimiausios

def muziejai_su_rotacija(user_lat, user_lon, user_id):
    # SU ISTORIJA - kad nesikartotų
    aplankyti = db.gauti_aplankytus(user_id, tipas='muziejus', dienos=30)
    
    laisvi = [m for m in MUZIEJAI_DB if m['id'] not in aplankyti]
    
    if len(laisvi) < 3: # jei viską aplankė - pradedam iš naujo
        laisvi = MUZIEJAI_DB
        db.isvalyti_istorija(user_id, tipas='muziejus')
    
    for m in laisvi:
        m['km'] = atstumas(user_lat, user_lon, m['lat'], m['lon'])
    
    laisvi.sort(key=lambda x: x['km'])
    # imam 3 artimiausius IŠ TŲ kur dar nebuvo - taip rotuojasi
    return laisvi[:3]