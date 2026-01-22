import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json
import time
import math
import uuid

# =============================================================================
# 🚨 SABİT AYARLAR VE LİNKLER
# =============================================================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wTEdK-MvfaYMvgHmUPAjD4sCE7maMDNOhs18tgLSzKg/edit"

# ELO (KKD) AYARLARI
STARTING_ELO = 1000
K_FACTOR = 32
SOLO_MULTIPLIER = 1.5

# YOUTUBE OYNATMA LİSTESİ
PLAYLIST_LINK = "https://www.youtube.com/playlist?list=PLsBHfG2XM8K1atYDUI4BQmv2rz1WysjwA"
VIDEO_MAP = {
    "Rıfkı": PLAYLIST_LINK, "Kız Almaz": PLAYLIST_LINK, "Erkek Almaz": PLAYLIST_LINK,
    "Kupa Almaz": PLAYLIST_LINK, "El Almaz": PLAYLIST_LINK, "Son İki": PLAYLIST_LINK, "Koz (Tümü)": PLAYLIST_LINK
}

# =============================================================================
# 0. GÖRSEL AYARLAR VE CSS
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        h1 { color: #FFD700 !important; text-align: center; text-shadow: 2px 2px 4px #000000; font-family: 'Arial Black', sans-serif; margin-bottom: 5px; }
        h2, h3 { color: #ff4b4b !important; border-bottom: 2px solid #333; padding-bottom: 10px; }
        
        .stButton > button { width: 100% !important; background-color: #990000; color: white; border-radius: 8px; border: 1px solid #330000; font-weight: bold; }
        .stButton > button:hover { background-color: #ff0000; border-color: white; transform: scale(1.01); }
        
        .stLinkButton > a { width: 100% !important; background-color: #262730 !important; color: #FFD700 !important; border: 1px solid #FFD700 !important; font-weight: bold !important; display: flex; justify-content: center; align-items: center; }
        
        div[role="radiogroup"] { background-color: #262730; padding: 10px; border-radius: 15px; display: flex; justify-content: center; overflow-x: auto; white-space: nowrap; }
        div[role="radiogroup"] label { color: white !important; font-weight: bold !important; font-size: 16px !important; padding: 0 15px; cursor: pointer; }
        
        div[data-testid="stMetric"] { background-color: #262730; padding: 10px; border-radius: 10px; border: 1px solid #444; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        div[data-testid="stDataFrame"] { border: 1px solid #444; border-radius: 5px; }

        header {visibility: hidden !important; display: none !important;}
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
        footer {visibility: hidden !important; display: none !important;}
        section[data-testid="stSidebar"] {visibility: hidden !important; display: none !important;}
        .viewerBadge_container__1QSob { display: none !important; }
        
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# King Oyun Kuralları
OYUN_KURALLARI = {
    "Rıfkı":        {"puan": -320, "adet": 1,  "limit": 2}, 
    "Kız Almaz":    {"puan": -100, "adet": 4,  "limit": 2},
    "Erkek Almaz":  {"puan": -60,  "adet": 8,  "limit": 2},
    "Kupa Almaz":   {"puan": -30,  "adet": 13, "limit": 2},
    "El Almaz":     {"puan": -50,  "adet": 13, "limit": 2},
    "Son İki":      {"puan": -180, "adet": 2,  "limit": 2},
    "Koz (Tümü)":   {"puan": 50,   "adet": 104,"limit": 1}
}
OYUN_SIRALAMASI = list(OYUN_KURALLARI.keys())

# =============================================================================
# 1. GOOGLE SHEETS
# =============================================================================

@st.cache_resource
def get_google_sheet_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

def get_sheet_by_url():
    client = get_google_sheet_client()
    return client.open_by_url(SHEET_URL)

def check_and_fix_sheet_structure():
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        all_data = sheet.get_all_values()
        if not all_data: return 
        headers = all_data[0]
        is_changed = False
        if "UserID" not in headers:
            headers.append("UserID")
            for i, row in enumerate(all_data[1:]): row.append(i)
            is_changed = True
        if "KKD" not in headers:
            headers.append("KKD")
            for row in all_data[1:]: row.append(STARTING_ELO)
            is_changed = True
        if is_changed:
            new_data = [headers] + all_data[1:]
            sheet.clear()
            sheet.update(new_data)
            return True
    except: pass
    return False

def get_users_from_sheet():
    try:
        check_and_fix_sheet_structure() 
        sheet = get_sheet_by_url().worksheet("Users")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e: return pd.DataFrame()

def save_elos_to_users_sheet(elo_data):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        all_values = sheet.get_all_values()
        if not all_values: return False
        headers = all_values[0]
        try:
            username_idx = headers.index("Username")
            kkd_idx = headers.index("KKD")
        except ValueError: return False 
        updated_data = [headers]
        for row in all_values[1:]:
            u_name = row[username_idx]
            while len(row) <= kkd_idx: row.append("")
            if u_name in elo_data: row[kkd_idx] = int(elo_data[u_name])
            updated_data.append(row)
        sheet.clear()
        sheet.update(updated_data)
        return True
    except: return False

def update_user_in_sheet(old_username, new_username, password, role, delete=False):
    # (Önceki fonksiyonun aynısı - Yer tasarrufu için kısaltıldı, mantık aynı)
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        if not sheet.get_all_values(): sheet.append_row(["Username", "Password", "Role", "UserID", "KKD"])
        try:
            cell = sheet.find(old_username)
            if cell:
                if delete:
                    sheet.delete_rows(cell.row)
                    return "deleted"
                else:
                    sheet.update_cell(cell.row, 1, new_username)
                    sheet.update_cell(cell.row, 2, password)
                    sheet.update_cell(cell.row, 3, role)
                    return "updated"
            else:
                if not delete:
                    all_values = sheet.get_all_values()
                    current_ids = []
                    if len(all_values) > 1:
                        headers = all_values[0]
                        try:
                            uid_idx = headers.index("UserID")
                            for row in all_values[1:]:
                                if len(row) > uid_idx and str(row[uid_idx]).isdigit():
                                    current_ids.append(int(row[uid_idx]))
                        except: pass
                    new_id = max(current_ids) + 1 if current_ids else 0
                    sheet.append_row([new_username, password, role, new_id, STARTING_ELO])
                    return "added"
        except: return False
    except: return False

def delete_match_from_sheet(match_title):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        all_values = sheet.get_all_values()
        start_index = -1; end_index = -1
        for i, row in enumerate(all_values):
            if row and str(row[0]) == match_title:
                start_index = i + 1 
                for j in range(i, len(all_values)):
                    if all_values[j] and str(all_values[j][0]).startswith("----------------"):
                        end_index = j + 1
                        break
                break
        if start_index != -1 and end_index != -1:
            sheet.delete_rows(start_index, end_index)
            return True
        else: return False
    except: return False

# =============================================================================
# 2. İSTATİSTİK MOTORU (TARİH, SERİLER VE REWIND)
# =============================================================================

def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def parse_date_from_header(header_str):
    # Beklenen format: "--- MAÇ: İsim (23.01.2026) ---"
    try:
        # Parantez içini al
        date_part = header_str.split('(')[-1].split(')')[0]
        # Tarih objesine çevir
        return datetime.strptime(date_part.strip(), "%d.%m.%Y")
    except:
        return datetime.now() # Hata olursa bugünü al

def istatistikleri_hesapla():
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        raw_data = sheet.get_all_values()
    except: return None, None, None

    if not raw_data: return None, None, None

    player_stats = {}
    elo_ratings = {} 
    
    # Yeni: Detaylı Maç Geçmişi (Tarihli ve Ham Verili)
    all_matches_chronological = []
    
    current_players = []
    current_match_data = {} 
    current_date = datetime.now()
    
    is_king_game = False
    king_winner_name = None

    for row in raw_data:
        if not row: continue
        first_cell = str(row[0])
        
        # --- MAÇ BAŞLANGICI ---
        if first_cell.startswith("--- MAÇ:"):
            current_players = []
            # Tarihi parse et
            current_date = parse_date_from_header(first_cell)
            current_match_data = {
                "baslik": first_cell, 
                "tarih": current_date, 
                "skorlar": [], 
                "oyuncular": [],
                "ceza_detaylari": {} # Kim hangi cezadan kaç puan yedi
            }
            is_king_game = False
            king_winner_name = None
            continue
            
        if first_cell == "OYUN TÜRÜ":
            for col_idx in range(1, len(row)):
                p_name = row[col_idx].strip()
                if p_name:
                    current_players.append(p_name)
                    current_match_data["oyuncular"].append(p_name)
                    if p_name not in player_stats:
                        player_stats[p_name] = {
                            "mac_sayisi": 0, "toplam_puan": 0, "pozitif_mac_sayisi": 0,
                            "cezalar": {}, "partnerler": {}, "gecici_mac_puani": 0,
                            "rekor_max": -9999, "rekor_min": 9999,
                            "kkd": STARTING_ELO,
                            "win_streak": 0, "loss_streak": 0, # Anlık seri
                            "max_win_streak": 0, "max_loss_streak": 0 # Rekor seri
                        }
                    if p_name not in elo_ratings: elo_ratings[p_name] = STARTING_ELO
            continue

        base_name = first_cell.split(" #")[0]
        if "KING" in first_cell:
            is_king_game = True
            try: king_winner_name = first_cell.split("(")[1].split(")")[0]
            except: king_winner_name = None 
        
        # --- SKORLAR ---
        if (base_name in OYUN_KURALLARI or "KING" in first_cell) and current_players:
            current_match_data["skorlar"].append(row)
            for i, p_name in enumerate(current_players):
                try:
                    if (i + 1) < len(row):
                        score_str = row[i+1]
                        if score_str == "" or score_str == " ": continue
                        score = int(score_str)
                        
                        if p_name in player_stats:
                            stats = player_stats[p_name]
                            stats["toplam_puan"] += score
                            stats["gecici_mac_puani"] += score
                            
                            # Ceza Analizi (Genel ve Maç Özel)
                            if score < 0 and base_name in OYUN_KURALLARI and not is_king_game:
                                # Genel İstatistik
                                if base_name not in stats["cezalar"]: stats["cezalar"][base_name] = 0
                                birim = OYUN_KURALLARI[base_name]['puan']
                                count = int(score/birim)
                                stats["cezalar"][base_name] += count
                                
                                # Maç Detayına Ekle (Rewind İçin)
                                if p_name not in current_match_data["ceza_detaylari"]:
                                    current_match_data["ceza_detaylari"][p_name] = {}
                                if base_name not in current_match_data["ceza_detaylari"][p_name]:
                                    current_match_data["ceza_detaylari"][p_name][base_name] = 0
                                current_match_data["ceza_detaylari"][p_name][base_name] += count
                                
                except: continue

        # --- MAÇ SONU ---
        if first_cell == "TOPLAM":
            current_match_data["toplamlar"] = row
            
            # ELO ve Seri Hesapları için veriyi hazırla
            match_elos = {p: elo_ratings.get(p, STARTING_ELO) for p in current_players}
            match_results = {} # {isim: puan}
            
            winners_count = 0
            losers_count = 0
            
            for i, p_name in enumerate(current_players):
                try:
                    total_score = int(row[i+1])
                    match_results[p_name] = total_score
                    
                    # Seri Hesaplama Mantığı (Anlık değil, tarihsel işlenecek)
                    current_match_data["sonuclar"] = match_results
                    
                    # Win/Loss Durumu
                    is_win = False
                    if is_king_game:
                        if p_name == king_winner_name: is_win = True
                    else:
                        if total_score >= 0: is_win = True
                    
                    if is_win: winners_count += 1
                    else: losers_count += 1
                    
                    # Genel İstatistik Güncelleme
                    stats = player_stats[p_name]
                    stats["mac_sayisi"] += 1
                    if is_win: stats["pozitif_mac_sayisi"] += 1
                    if not is_king_game:
                        if total_score > stats["rekor_max"]: stats["rekor_max"] = total_score
                        if total_score < stats["rekor_min"]: stats["rekor_min"] = total_score
                        
                    # Partner Analizi
                    others = [op for op in current_players if op != p_name]
                    for op in others:
                        if op not in stats["partnerler"]:
                            stats["partnerler"][op] = {"birlikte_mac": 0, "beraber_kazanma": 0, "beraber_kaybetme": 0, "puan_toplami": 0}
                        p_stat = stats["partnerler"][op]
                        p_stat["birlikte_mac"] += 1
                        p_stat["puan_toplami"] += total_score
                        if is_win: p_stat["beraber_kazanma"] += 1
                        else: p_stat["beraber_kaybetme"] += 1
                        
                except: pass

            # ELO GÜNCELLEME
            new_elo_values = {}
            for p_name in current_players:
                my_current_elo = match_elos[p_name]
                actual_score = 1 if (match_results.get(p_name, -1) >= 0 or (is_king_game and p_name == king_winner_name)) else 0
                
                opponents = [match_elos[op] for op in current_players if op != p_name]
                if opponents: avg_opponent_elo = sum(opponents) / len(opponents)
                else: avg_opponent_elo = STARTING_ELO 
                
                expected_score = calculate_expected_score(my_current_elo, avg_opponent_elo)
                change = K_FACTOR * (actual_score - expected_score)
                
                if actual_score == 1 and winners_count == 1: change *= SOLO_MULTIPLIER
                elif actual_score == 0 and losers_count == 1: change *= SOLO_MULTIPLIER
                
                new_elo_values[p_name] = my_current_elo + change
            
            for p_name, val in new_elo_values.items():
                elo_ratings[p_name] = val
                player_stats[p_name]["kkd"] = val
            
            # Maçı listeye ekle (Tarihli olarak)
            all_matches_chronological.append(current_match_data)
            match_history.append(current_match_data) # Görüntüleme için
            
            for p in player_stats: player_stats[p]["gecici_mac_puani"] = 0
            current_players = []

    # --- SERİLERİ (STREAKS) TARİHSEL HESAPLA ---
    # Maçları tarihe göre sırala (Eskiden yeniye)
    all_matches_chronological.sort(key=lambda x: x['tarih'])
    
    # Geçici sayaçlar (Kod her çalıştığında baştan hesaplar)
    temp_streaks = {} # {isim: {'current_win': 0, 'current_loss': 0}}
    
    for match in all_matches_chronological:
        for p_name in match['oyuncular']:
            if p_name not in temp_streaks:
                temp_streaks[p_name] = {'win': 0, 'loss': 0}
            
            score = match['sonuclar'].get(p_name, 0)
            is_win = score >= 0
            
            # King özel durumu
            if "KING" in match['baslik']:
                king_winner = match['toplamlar'][0].split("(")[1].split(")")[0] if "(" in match['toplamlar'][0] else None
                is_win = (p_name == king_winner)

            if is_win:
                temp_streaks[p_name]['win'] += 1
                temp_streaks[p_name]['loss'] = 0
            else:
                temp_streaks[p_name]['loss'] += 1
                temp_streaks[p_name]['win'] = 0
            
            # Rekor Kontrolü
            if temp_streaks[p_name]['win'] > player_stats[p_name]['max_win_streak']:
                player_stats[p_name]['max_win_streak'] = temp_streaks[p_name]['win']
            if temp_streaks[p_name]['loss'] > player_stats[p_name]['max_loss_streak']:
                player_stats[p_name]['max_loss_streak'] = temp_streaks[p_name]['loss']
            
            # Güncel serileri de işle
            player_stats[p_name]['win_streak'] = temp_streaks[p_name]['win']
            player_stats[p_name]['loss_streak'] = temp_streaks[p_name]['loss']

    return player_stats, match_history, all_matches_chronological

# =============================================================================
# 3. GİRİŞ EKRANI
# =============================================================================

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1>King İstatistik Kurumu Giriş</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Sisteme Gir"):
                users_df = get_users_from_sheet()
                if users_df.empty: st.error("Hata: Tablo okunamadı."); return
                if 'Username' in users_df.columns:
                    user_match = users_df[users_df['Username'].astype(str).str.strip() == username.strip()]
                    if not user_match.empty and str(user_match.iloc[0]['Password']).strip() == str(password).strip():
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.session_state["role"] = user_match.iloc[0]['Role']
                        st.success("Giriş Başarılı!")
                        st.rerun()
                    else: st.error("Hatalı giriş!")
                else: st.error("Tablo formatı hatalı!")

def logout(): st.session_state.clear(); st.rerun()

# =============================================================================
# 4. OYUN YÖNETİMİ
# =============================================================================

def game_interface():
    # (Önceki fonksiyonun aynısı - yer tasarrufu)
    if "game_active" not in st.session_state: st.session_state["game_active"] = False
    if "temp_df" not in st.session_state: st.session_state["temp_df"] = pd.DataFrame()
    if "king_mode" not in st.session_state: st.session_state["king_mode"] = False

    if not st.session_state["game_active"]:
        st.info("Yeni maç başlatın veya geçmiş bir maçı sisteme girin.")
        users_df = get_users_from_sheet()
        tum_oyuncular = users_df['Username'].tolist() if not users_df.empty and 'Username' in users_df.columns else []
        c1, c2 = st.columns(2)
        match_name_input = c1.text_input("Maç İsmi:", value="King_Maci")
        is_past = c2.checkbox("Geçmiş Tarihli Maç?")
        if is_past: selected_date = c2.date_input("Maç Tarihi", value=datetime.now())
        else: selected_date = datetime.now()
        mac_tarihi_str = selected_date.strftime("%d.%m.%Y")

        secilenler = st.multiselect("4 oyuncu seçin:", options=tum_oyuncular, default=tum_oyuncular[:4] if len(tum_oyuncular) >= 4 else None)
        if len(secilenler) == 4 and st.button("Masayı Kur ve Başlat", type="primary"):
            st.session_state["temp_df"] = pd.DataFrame(columns=secilenler)
            st.session_state["current_match_name"] = match_name_input
            st.session_state["match_date"] = mac_tarihi_str 
            st.session_state["game_index"] = 0 
            st.session_state["players"] = secilenler
            st.session_state["game_active"] = True
            st.session_state["king_mode"] = False
            st.rerun()
        return 

    else:
        df = st.session_state["temp_df"]
        secili_oyuncular = st.session_state["players"]
        st.success(f"Maç: **{st.session_state['current_match_name']}** ({st.session_state['match_date']})")
        st.dataframe(df.style.format("{:.0f}"), use_container_width=True)
        
        total_limit = sum([k['limit'] for k in OYUN_KURALLARI.values()])
        oynanan_satir_sayisi = len(df)
        
        if oynanan_satir_sayisi >= total_limit or st.session_state["king_mode"]:
            st.success("🏁 OYUN BİTTİ!")
            cols = st.columns(4)
            totals = df.sum()
            for i, p in enumerate(secili_oyuncular): cols[i].metric(p, f"{totals[p]}", delta_color="normal" if totals[p]>0 else "inverse")
            if st.button("💾 Maçı Arşivle ve KKD Güncelle", type="primary"):
                with st.spinner("Kaydediliyor..."):
                    try:
                        wb = get_sheet_by_url()
                        sheet = wb.worksheet("Maclar")
                        sheet.append_row([""] * 5)
                        sheet.append_row([f"--- MAÇ: {st.session_state['current_match_name']} ({st.session_state['match_date']}) ---", "", "", "", ""])
                        sheet.append_row(["OYUN TÜRÜ"] + secili_oyuncular)
                        for idx, row in df.iterrows(): sheet.append_row([idx] + [int(row[p]) for p in secili_oyuncular])
                        sheet.append_row(["TOPLAM"] + [int(totals[p]) for p in secili_oyuncular])
                        sheet.append_row(["----------------------------------------"] * 5)
                        stats, _, _ = istatistikleri_hesapla()
                        if stats: save_elos_to_users_sheet({name: data['kkd'] for name, data in stats.items()})
                        st.balloons()
                        st.session_state["game_active"] = False; st.session_state["king_mode"] = False; st.session_state["temp_df"] = pd.DataFrame(); del st.session_state["players"]; st.rerun()
                    except Exception as e: st.error(f"Hata: {e}")
            return

        st.markdown("---")
        if st.button("👑 KING YAPILDI (OYUNU BİTİR)", type="secondary"): st.session_state["show_king_dialog"] = True
        if st.session_state.get("show_king_dialog", False):
            king_maker = st.selectbox("King'i kim yaptı?", secili_oyuncular)
            if st.button("Onayla ve Bitir"):
                new_row = pd.DataFrame([{p: 0 for p in secili_oyuncular}], index=[f"👑 KING ({king_maker})"])
                st.session_state["temp_df"] = pd.concat([st.session_state["temp_df"], new_row])
                st.session_state["king_mode"] = True
                st.session_state["show_king_dialog"] = False
                st.rerun()

        st.markdown("---")
        mevcut_oyun_index = st.session_state["game_index"]
        if mevcut_oyun_index >= len(OYUN_SIRALAMASI): mevcut_oyun_index = len(OYUN_SIRALAMASI) - 1
        secilen_oyun = st.selectbox("Sıradaki Oyun:", OYUN_SIRALAMASI, index=mevcut_oyun_index, disabled=True)
        rules = OYUN_KURALLARI[secilen_oyun]
        current_count = len([x for x in df.index if secilen_oyun in x])
        cols = st.columns(4)
        inputs = {}
        row_key_base = f"{secilen_oyun}_{current_count}"
        current_sum = sum([st.session_state.get(f"val_{row_key_base}_{p}", 0) for p in secili_oyuncular])
        remaining_total = rules['adet'] - current_sum
        
        for i, p in enumerate(secili_oyuncular):
            my_max = st.session_state.get(f"val_{row_key_base}_{p}", 0) + remaining_total
            inputs[p] = cols[i].number_input(f"{p}", min_value=0, max_value=int(max(0, my_max)), step=1, key=f"val_{row_key_base}_{p}")

        if st.button("Kaydet ve İlerle", type="primary"):
            if sum(inputs.values()) != rules['adet']: st.error(f"Toplam {rules['adet']} olmalı.")
            else:
                new_row = pd.DataFrame([{p: inputs[p] * rules['puan'] for p in secili_oyuncular}], index=[f"{secilen_oyun} #{current_count + 1}"])
                st.session_state["temp_df"] = pd.concat([st.session_state["temp_df"], new_row])
                if len([x for x in st.session_state["temp_df"].index if secilen_oyun in x]) >= rules['limit'] and st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1: st.session_state["game_index"] += 1
                st.rerun()
        if st.button("⚠️ Son Satırı Sil"):
            if not st.session_state["temp_df"].empty: st.session_state["temp_df"] = st.session_state["temp_df"][:-1]; st.rerun()

# =============================================================================
# 5. KKD LİDERLİK
# =============================================================================

def kkd_leaderboard_interface():
    st.markdown("<h2>🏆 KKD Liderlik Tablosu</h2>", unsafe_allow_html=True)
    stats, _, _ = istatistikleri_hesapla()
    if not stats: st.warning("Veri yok."); return
    df_stats = pd.DataFrame.from_dict(stats, orient='index')
    if not df_stats.empty:
        df_stats['win_rate'] = (df_stats['pozitif_mac_sayisi'] / df_stats['mac_sayisi']) * 100
        elo_table = df_stats[['mac_sayisi', 'kkd', 'win_rate']].sort_values('kkd', ascending=False)
        elo_table.columns = ['Toplam Maç', 'KKD Puanı', 'Başarı %']
        st.dataframe(elo_table.style.format({'Başarı %': "{:.1f}%", 'KKD Puanı': "{:.0f}"}), use_container_width=True)

# =============================================================================
# 6. İSTATİSTİK ARAYÜZÜ (REWIND & STREAK EKLENDİ)
# =============================================================================

def stats_interface():
    st.markdown("<h2>📊 Detaylı İstatistik Merkezi</h2>", unsafe_allow_html=True)
    stats, match_history, chronological_matches = istatistikleri_hesapla()
    if not stats: st.warning("Henüz tamamlanmış maç verisi yok."); return

    tabs = st.tabs(["🔥 Seriler (Streak)", "📅 Rewind (Özet)", "🏆 Genel", "📜 Arşiv", "🚫 Cezalar", "🤝 Komandit"])
    df_stats = pd.DataFrame.from_dict(stats, orient='index')

    # 1. SERİLER
    with tabs[0]:
        st.subheader("🔥 Galibiyet ve Mağlubiyet Serileri")
        st.caption("Maç tarihine göre hesaplanan üst üste kazanma/kaybetme rekorları.")
        
        # En iyi ve En Kötü Serileri Bul
        max_win = df_stats['max_win_streak'].max()
        max_loss = df_stats['max_loss_streak'].max()
        best_streaker = df_stats['max_win_streak'].idxmax()
        worst_streaker = df_stats['max_loss_streak'].idxmax()
        
        c1, c2 = st.columns(2)
        c1.success(f"🚀 **En Uzun Galibiyet Serisi:**\n\n# {best_streaker} ({max_win} Maç)")
        c2.error(f"💀 **En Uzun Mağlubiyet Serisi:**\n\n# {worst_streaker} ({max_loss} Maç)")
        
        st.divider()
        st.write("**Detaylı Seri Tablosu**")
        streak_table = df_stats[['win_streak', 'max_win_streak', 'loss_streak', 'max_loss_streak']].sort_values('win_streak', ascending=False)
        streak_table.columns = ['Mevcut Win', 'Rekor Win', 'Mevcut Loss', 'Rekor Loss']
        st.dataframe(streak_table, use_container_width=True)

    # 2. REWIND (ZAMAN TÜNELİ)
    with tabs[1]:
        st.subheader("📅 Zaman Tüneli: Kim Ne Yaptı?")
        
        # Tarihleri Çıkar
        all_dates = sorted([m['tarih'] for m in chronological_matches], reverse=True)
        if not all_dates: st.info("Tarih verisi yok."); return
        
        years = sorted(list(set([d.year for d in all_dates])), reverse=True)
        months = ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        c_filter1, c_filter2 = st.columns(2)
        selected_year = c_filter1.selectbox("Yıl Seç", ["Tüm Zamanlar"] + years)
        selected_month = c_filter2.selectbox("Ay Seç", months)
        
        # Filtreleme Mantığı
        filtered_matches = []
        for m in chronological_matches:
            match_date = m['tarih']
            if selected_year != "Tüm Zamanlar":
                if match_date.year != selected_year: continue
                if selected_month != "Tümü":
                    if match_date.month != months.index(selected_month): continue
            filtered_matches.append(m)
            
        if filtered_matches:
            st.info(f"Seçilen dönemde toplam **{len(filtered_matches)}** maç bulundu.")
            
            # Dönem İstatistiklerini Hesapla
            period_stats = {} # {isim: {puan, rıfkı_count, kız_count, erkek_count...}}
            
            for m in filtered_matches:
                for p_name in m['oyuncular']:
                    if p_name not in period_stats: period_stats[p_name] = {'puan': 0, 'Rıfkı': 0, 'Kız Almaz': 0, 'Erkek Almaz': 0, 'El Almaz': 0}
                    
                    # Puan Topla
                    idx = m['oyuncular'].index(p_name)
                    try:
                        score = int(m['toplamlar'][idx+1])
                        period_stats[p_name]['puan'] += score
                    except: pass
                    
                    # Ceza Sayılarını Topla
                    if p_name in m['ceza_detaylari']:
                        for c_type, count in m['ceza_detaylari'][p_name].items():
                            if c_type in period_stats[p_name]:
                                period_stats[p_name][c_type] += count

            # Şampiyonlar ve Kurbanlar
            if period_stats:
                df_period = pd.DataFrame.from_dict(period_stats, orient='index')
                
                king_of_period = df_period['puan'].idxmax()
                loser_of_period = df_period['puan'].idxmin()
                most_rifki = df_period['Rıfkı'].idxmax()
                most_kiz = df_period['Kız Almaz'].idxmax()
                most_erkek = df_period['Erkek Almaz'].idxmax()
                
                cc1, cc2, cc3 = st.columns(3)
                cc1.success(f"👑 **Dönemin Kralı**\n\n{king_of_period} ({df_period['puan'].max()})")
                cc2.error(f"🩸 **Rıfkızede**\n\n{most_rifki} ({df_period['Rıfkı'].max()} Adet)")
                cc3.warning(f"💔 **Kızların Sevgilisi**\n\n{most_kiz} ({df_period['Kız Almaz'].max()} Adet)")
                
                st.divider()
                st.write(f"**{selected_month}/{selected_year} Dönemi Detaylı Tablo**")
                st.dataframe(df_period.sort_values('puan', ascending=False), use_container_width=True)
                
        else:
            st.warning("Bu dönemde maç bulunamadı.")

    with tabs[2]:
        st.subheader("🏆 Genel Puan")
        if not df_stats.empty:
            st.dataframe(df_stats[['mac_sayisi', 'toplam_puan']].sort_values('toplam_puan', ascending=False), use_container_width=True)
    with tabs[3]:
        st.subheader("📜 Arşiv")
        if match_history:
            match_names = [f"{m['baslik']}" for m in match_history][::-1]
            selected_match = st.selectbox("Maç Seç:", match_names)
            selected_data = next((m for m in match_history if m['baslik'] == selected_match), None)
            if selected_data:
                cols = ["OYUN TÜRÜ"] + selected_data["oyuncular"]
                rows = [s[:len(cols)] for s in selected_data["skorlar"]]
                rows.append(selected_data["toplamlar"][:len(cols)])
                st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
    with tabs[4]:
        st.subheader("🚫 Ceza Analizi")
        ceza_list = [k for k in OYUN_KURALLARI.keys() if OYUN_KURALLARI[k]['puan'] < 0]
        selected_ceza = st.selectbox("Ceza Türü Seç:", ceza_list)
        ceza_data = {p: stats[p]['cezalar'].get(selected_ceza, 0) / stats[p]['mac_sayisi'] if stats[p]['mac_sayisi']>0 else 0 for p in stats}
        st.bar_chart(pd.Series(ceza_data))
    with tabs[5]:
        st.subheader("🤝 Komanditlik")
        me = st.session_state["username"]
        if me in stats and stats[me]['partnerler']:
            p_list = [{"Komandit": p, "Maç": d['birlikte_mac'], "Kazanma %": d['beraber_kazanma']/d['birlikte_mac']*100} for p, d in stats[me]['partnerler'].items()]
            st.dataframe(pd.DataFrame(p_list).sort_values(by="Kazanma %", ascending=False), use_container_width=True)

# =============================================================================
# 7. PROFİL EKRANI
# =============================================================================

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    stats, match_history, _ = istatistikleri_hesapla()
    my_name = st.session_state['username']
    
    if stats and my_name in stats:
        my_stats = stats[my_name]
        cezalar = my_stats['cezalar']
        fav_ceza = "Temiz"; fav_oran = 0
        if cezalar:
            fav_ceza = max(cezalar, key=cezalar.get)
            toplam_ceza = sum(cezalar.values())
            fav_oran = (cezalar[fav_ceza] / toplam_ceza * 100) if toplam_ceza > 0 else 0

        win_rate = (my_stats['pozitif_mac_sayisi'] / my_stats['mac_sayisi']) * 100 if my_stats['mac_sayisi'] > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Maç", my_stats['mac_sayisi'])
        c2.metric("KKD (ELO)", f"{my_stats['kkd']:.0f}")
        c3.metric("Win Rate", f"%{win_rate:.1f}")
        c4.metric("Baş Belası", f"{fav_ceza}", f"%{fav_oran:.0f}")
        
        st.divider()
        st.subheader("🎓 Akıllı Koç Analizi")
        if fav_ceza in VIDEO_MAP:
            st.info(f"Koç diyor ki: **{fav_ceza}** cezasını çok yiyorsun (%{fav_oran:.0f}). Bu konuda zayıfsın, şu dersi izle:")
            st.link_button(label="📺 Videoyu YouTube'da İzlemek İçin Tıkla", url=VIDEO_MAP[fav_ceza])
        else: st.success("Harika! Belirgin bir zayıflığın yok.")
            
    st.divider()
    st.subheader("📜 Kişisel Maç Karnesi")
    if match_history:
        my_match_log = []
        for m in reversed(match_history):
            if my_name in m['oyuncular']:
                idx = m['oyuncular'].index(my_name)
                try:
                    score = int(m['toplamlar'][idx+1])
                    sonuc = "KAZANDI" if score >= 0 else "KAYBETTİ"
                    if "KING" in m['toplamlar'][0]:
                        winner = m['toplamlar'][0].split("(")[1].split(")")[0]
                        sonuc = "KAZANDI 👑" if winner == my_name else "KAYBETTİ"
                    my_match_log.append({"Tarih / Maç": m['baslik'].replace("--- MAÇ: ", "").replace(" ---", ""), "Puan": score, "Sonuç": sonuc})
                except: pass
        
        if my_match_log:
            df_log = pd.DataFrame(my_match_log)
            def color_result(val): return f'color: {"green" if "KAZANDI" in val else "red"}; font-weight: bold'
            st.dataframe(df_log.style.applymap(color_result, subset=['Sonuç']), use_container_width=True)
        else: st.info("Maç yok.")

    st.divider()
    with st.expander("⚙️ Ayarlar"):
        new_username = st.text_input("Yeni Kullanıcı Adı", value=my_name)
        new_pass = st.text_input("Yeni Şifre", type="password")
        if st.button("Bilgileri Güncelle"):
            if update_user_in_sheet(my_name, new_username, new_pass if new_pass else "1234", st.session_state["role"]):
                st.success("Güncellendi!"); time.sleep(1); st.session_state["logged_in"] = False; st.rerun()

# =============================================================================
# 8. YÖNETİM PANELİ
# =============================================================================

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim Paneli</h2>", unsafe_allow_html=True)
    users_df = get_users_from_sheet()
    current_user_role = st.session_state["role"]
    
    with st.form("user_add_update"):
        st.subheader("Kullanıcı Ekle / Güncelle")
        c1, c2, c3 = st.columns(3)
        u_name = c1.text_input("Kullanıcı Adı")
        u_pass = c2.text_input("Şifre")
        u_role = c3.selectbox("Yetki", ["user", "admin", "patron"]) if current_user_role == "patron" else "user"
        if st.form_submit_button("Kaydet"):
            if u_name:
                target_user_row = users_df[users_df['Username'] == u_name]
                target_role = "user"
                if not target_user_row.empty: target_role = target_user_row.iloc[0]['Role']
                if current_user_role == "admin" and target_role in ["patron", "admin"] and not target_user_row.empty: st.error("Yetkisiz.")
                else: 
                    pwd = u_pass if u_pass else "1234"
                    if update_user_in_sheet(u_name, u_name, pwd, u_role, delete=False): st.success("İşlem Başarılı."); st.rerun()

    st.divider()
    st.subheader("🗑️ Maç Yönetimi")
    _, match_history, _ = istatistikleri_hesapla()
    if match_history:
        selected_delete_match = st.selectbox("Silinecek Maç:", [f"{m['baslik']}" for m in match_history][::-1])
        if st.button("Sil"): st.session_state["pending_delete_match"] = selected_delete_match; st.rerun()
        if "pending_delete_match" in st.session_state and st.session_state["pending_delete_match"]:
            if st.button("✅ Onayla", key="conf_del_match"):
                delete_match_from_sheet(st.session_state["pending_delete_match"])
                del st.session_state["pending_delete_match"]
                st.rerun()
    
    st.divider()
    st.subheader("📋 Kullanıcılar")
    if not users_df.empty and 'Username' in users_df.columns:
        for index, row in users_df.iterrows():
            c1, c2 = st.columns([4,1])
            c1.write(f"**{row['Username']}** ({row['Role']})")
            if current_user_role == "patron" and row['Username'] != st.session_state["username"]:
                if c2.button("Sil", key=f"del_{row['Username']}"):
                    update_user_in_sheet(row['Username'], row['Username'], "x", "x", delete=True)
                    st.rerun()

# =============================================================================
# 9. ANA UYGULAMA
# =============================================================================

st.set_page_config(page_title="King İstatistik Kurumu", layout="wide", page_icon="👑")
inject_custom_css()

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    st.markdown(f"<h3 style='text-align: center;'>👑 {st.session_state['username']}</h3>", unsafe_allow_html=True)
    menu_options = ["📊 İstatistikler", "🏆 KKD Liderlik", "👤 Profilim"] 
    if st.session_state["role"] in ["admin", "patron"]: menu_options = ["🎮 Oyun Ekle", "🛠️ Yönetim Paneli"] + menu_options
    selected_page = st.radio("", menu_options, horizontal=True, label_visibility="collapsed")
    
    col_x1, col_x2 = st.columns([6, 1])
    with col_x2:
        if st.button("Çıkış Yap"): logout()
    st.markdown("---")

    if selected_page == "🎮 Oyun Ekle": game_interface()
    elif selected_page == "📊 İstatistikler": stats_interface()
    elif selected_page == "🏆 KKD Liderlik": kkd_leaderboard_interface() 
    elif selected_page == "👤 Profilim": profile_interface()
    elif selected_page == "🛠️ Yönetim Paneli": admin_panel()
