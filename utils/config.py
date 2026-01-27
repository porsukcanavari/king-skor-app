# utils/config.py

SHEET_URL = "https://docs.google.com/spreadsheets/d/1wTEdK-MvfaYMvgHmUPAjD4sCE7maMDNOhs18tgLSzKg/edit"

# ELO (KKD) AYARLARI
STARTING_ELO = 1000
K_FACTOR = 32
SOLO_MULTIPLIER = 1.5

# YOUTUBE
PLAYLIST_LINK = "https://www.youtube.com/playlist?list=PLsBHfG2XM8K1atYDUI4BQmv2rz1WysjwA"
VIDEO_MAP = {
    "Rıfkı": PLAYLIST_LINK, "Kız Almaz": PLAYLIST_LINK, "Erkek Almaz": PLAYLIST_LINK,
    "Kupa Almaz": PLAYLIST_LINK, "El Almaz": PLAYLIST_LINK, "Son İki": PLAYLIST_LINK, 
    "Koz (Tümü)": PLAYLIST_LINK, "KING": PLAYLIST_LINK
}

# OYUN KURALLARI
OYUN_KURALLARI = {
    "Rıfkı":        {"puan": -320, "adet": 1,  "limit": 2, "renk": "#FF0000"}, 
    "Kız Almaz":    {"puan": -100, "adet": 4,  "limit": 2, "renk": "#FF6B6B"},
    "Erkek Almaz":  {"puan": -60,  "adet": 8,  "limit": 2, "renk": "#4ECDC4"},
    "Kupa Almaz":   {"puan": -30,  "adet": 13, "limit": 2, "renk": "#FFD166"},
    "El Almaz":     {"puan": -50,  "adet": 13, "limit": 2, "renk": "#06D6A0"},
    "Son İki":      {"puan": -180, "adet": 2,  "limit": 2, "renk": "#118AB2"},
    "Koz (Tümü)":   {"puan": 50,   "adet": 104,"limit": 1, "renk": "#073B4C"}
}
OYUN_SIRALAMASI = list(OYUN_KURALLARI.keys())