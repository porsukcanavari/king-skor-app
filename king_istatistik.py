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

# EĞİTİM VİDEOLARI (Playlist Linkleri)
# Not: Eğer video "Kullanılamıyor" derse alttaki butondan açılacak.
PLAYLIST_LINK = "https://www.youtube.com/playlist?list=PLsBHfG2XM8K1atYDUI4BQmv2rz1WysjwA"

VIDEO_MAP = {
    "Rıfkı": PLAYLIST_LINK, 
    "Kız Almaz": PLAYLIST_LINK,
    "Erkek Almaz": PLAYLIST_LINK,
    "Kupa Almaz": PLAYLIST_LINK,
    "El Almaz": PLAYLIST_LINK,
    "Son İki": PLAYLIST_LINK,
    "Koz (Tümü)": PLAYLIST_LINK
}

# =============================================================================
# 0. GÖRSEL AYARLAR VE CSS
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
        /* --- GENEL --- */
        .stApp { background-color: #0e1117; }
        h1 { color: #FFD700 !important; text-align: center; text-shadow: 2px 2px 4px #000000; font-family: 'Arial Black', sans-serif; margin-bottom: 5px; }
        h2, h3 { color: #ff4b4b !important; border-bottom: 2px solid #333; padding-bottom: 10px; }
        
        /* BUTONLAR */
        .stButton > button { width: 100% !important; background-color: #990000; color: white; border-radius: 8px; border: 1px solid #330000; font-weight: bold; }
        .stButton > button:hover { background-color: #ff0000; border-color: white; transform: scale(1.01); }
        
        /* LİNK BUTONU (Video İçin) */
        .stLinkButton > a { 
            width: 100% !important; 
            background-color: #262730 !important; 
            color: #FFD700 !important; 
            border: 1px solid #FFD700 !important; 
            font-weight: bold !important;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .stLinkButton > a:hover {
            background-color: #FFD700 !important;
            color: black !important;
        }

        /* YATAY MENÜ */
        div[role="radiogroup"] {
            background-color: #262730;
            padding: 10px;
            border-radius: 15px;
            display: flex;
            justify-content: center;
            overflow-x: auto;
            white-space: nowrap;
        }
        div[role="radiogroup"] label {
            color: white !important;
            font-weight: bold !important;
            font-size: 16px !important;
            padding: 0 15px;
            cursor: pointer;
        }
        
        /* KARTLAR */
        div[data-testid="stMetric"] { background-color: #262730; padding: 10px; border-radius: 10px; border: 1px solid #444; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        div[data-testid="stDataFrame"] { border: 1px solid #444; border-radius: 5px; }

        /* --- ARAYÜZ TEMİZLİĞİ --- */
        header {visibility: hidden !important; display: none !important;}
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
        footer {visibility: hidden !important; display: none !important;}
        section[data-testid="stSidebar"] {visibility: hidden !important; display: none !important;}
        .viewerBadge_container__1QSob { display: none !important; }
        
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
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
# 1. GOOGLE SHEETS BAĞLANTISI
# =============================================================================

@st.cache_resource
def get_google_sheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
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
    except Exception as e:
        return pd.DataFrame()

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
            if u_name in elo_data:
                row[kkd_idx] = int(elo_data[u_name])
            updated_data.append(row)
        sheet.clear()
        sheet.update(updated_data)
        return True
    except Exception as e:
        return False

def update_match_history_names(old_name, new_name):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        all_values = sheet.get_all_values()
        updated_data = []
        is_changed = False
        for row in all_values:
            new_row = []
            for cell in row:
                cell_str = str(cell).strip()
                if cell_str == old_name.strip():
                    new_row.append(new_name)
                    is_changed = True
                elif "KING" in cell_str and f"({old_name})" in cell_str:
                    new_cell = cell_str.replace(f"({old_name})", f"({new_name})")
                    new_row.append(new_cell)
                    is_changed = True
                else:
                    new_row.append(cell)
            updated_data.append(new_row)
        if is_changed:
            sheet.clear()
            sheet.update(updated_data)
            return True
        return False
    except Exception as e: return False

def update_user_in_sheet(old_username, new_username, password, role, delete=False):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        if not sheet.get_all_values():
            sheet.append_row(["Username", "Password", "Role", "UserID", "KKD"])
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
                    if old_username != new_username:
                        update_match_history_names(old_username, new_username)
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
        except:
            if not delete:
                sheet.append_row([new_username, password, role, 0, STARTING_ELO])
                return "added"
        return False
    except Exception as e:
        st.error(f"Hata: {e}")
        return False

def delete_match_from_sheet(match_title):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        all_values = sheet.get_all_values()
        start_index = -1
        end_index = -1
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
    except Exception as e:
        st.error(f"Silme Hatası: {e}")
        return False

# =============================================================================
# 2. İSTATİSTİK MOTORU
# =============================================================================

def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def istatistikleri_hesapla():
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        raw_data = sheet.get_all_values()
    except: return None, None

    if not raw_data: return None, None

    player_stats = {}
    elo_ratings = {} 
    match_history = [] 
    current_players = []
    current_match_data = {} 
    
    is_king_game = False
    king_winner_name = None

    for row in raw_data:
        if not row: continue
        first_cell = str(row[0])
        
        if first_cell.startswith("--- MAÇ:"):
            current_players = []
            current_match_data = {"baslik": first_cell, "skorlar": [], "oyuncular": []}
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
                            "kkd": STARTING_ELO
                        }
                    if p_name not in elo_ratings:
                        elo_ratings[p_name] = STARTING_ELO
            continue

        base_name = first_cell.split(" #")[0]
        
        if "KING" in first_cell:
            is_king_game = True
            try: king_winner_name = first_cell.split("(")[1].split(")")[0]
            except: king_winner_name = None 
        
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
                            if score < 0 and base_name in OYUN_KURALLARI and not is_king_game:
                                if base_name not in stats["cezalar"]: stats["cezalar"][base_name] = 0
                                birim = OYUN_KURALLARI[base_name]['puan']
                                stats["cezalar"][base_name] += int(score/birim)
                except: continue

        if first_cell == "TOPLAM":
            current_match_data["toplamlar"] = row
            match_history.append(current_match_data)
            
            match_elos = {p: elo_ratings.get(p, STARTING_ELO) for p in current_players}
            match_scores = {} 
            winners_count = 0
            losers_count = 0
            
            for p_name in current_players:
                mac_puani = player_stats[p_name]["gecici_mac_puani"]
                is_win = False
                if is_king_game:
                    if p_name == king_winner_name: is_win = True
                else:
                    if mac_puani >= 0: is_win = True
                
                if is_win: winners_count += 1
                else: losers_count += 1
                match_scores[p_name] = 1 if is_win else 0
                
                stats = player_stats[p_name]
                stats["mac_sayisi"] += 1
                if is_win: stats["pozitif_mac_sayisi"] += 1
                
                if not is_king_game:
                    if mac_puani > stats["rekor_max"]: stats["rekor_max"] = mac_puani
                    if mac_puani < stats["rekor_min"]: stats["rekor_min"] = mac_puani
                
                others = [op for op in current_players if op != p_name]
                for op in others:
                    if op not in stats["partnerler"]:
                        stats["partnerler"][op] = {"birlikte_mac": 0, "beraber_kazanma": 0, "beraber_kaybetme": 0, "puan_toplami": 0}
                    p_stat = stats["partnerler"][op]
                    p_stat["birlikte_mac"] += 1
                    p_stat["puan_toplami"] += mac_puani
                    if is_win: p_stat["beraber_kazanma"] += 1
                    else: p_stat["beraber_kaybetme"] += 1

            new_elo_values = {}
            for p_name in current_players:
                my_current_elo = match_elos[p_name]
                actual_score = match_scores[p_name]
                opponents = [match_elos[op] for op in current_players if op != p_name]
                if opponents: avg_opponent_elo = sum(opponents) / len(opponents)
                else: avg_opponent_elo = STARTING_ELO 
                
                expected_score = calculate_expected_score(my_current_elo, avg_opponent_elo)
                change = K_FACTOR * (actual_score - expected_score)
                
                if actual_score == 1 and winners_count == 1:
                    change = change * SOLO_MULTIPLIER
                elif actual_score == 0 and losers_count == 1:
                    change = change * SOLO_MULTIPLIER
                
                new_elo_values[p_name] = my_current_elo + change
            
            for p_name, val in new_elo_values.items():
                elo_ratings[p_name] = val
                player_stats[p_name]["kkd"] = val 

            for p in player_stats: player_stats[p]["gecici_mac_puani"] = 0
            current_players = []

    return player_stats, match_history

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
                if users_df.empty:
                     st.error("⚠️ HATA: 'Users' tablosu okunamadı.")
                     return
                if 'Username' in users_df.columns:
                    user_match = users_df[users_df['Username'].astype(str).str.strip() == username.strip()]
                    if not user_match.empty:
                        stored_pass = str(user_match.iloc[0]['Password']).strip()
                        if stored_pass == str(password).strip():
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["role"] = user_match.iloc[0]['Role']
                            st.success("Giriş Başarılı!")
                            st.rerun()
                        else: st.error("Hatalı şifre!")
                    else: st.error("Kullanıcı bulunamadı!")
                else: st.error("Tablo formatı hatalı!")

def logout():
    st.session_state.clear()
    st.rerun()

# =============================================================================
# 4. OYUN ARAYÜZÜ
# =============================================================================

def game_interface():
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
        if is_past:
            selected_date = c2.date_input("Maç Tarihi", value=datetime.now())
            mac_tarihi_str = selected_date.strftime("%d.%m.%Y")
        else:
            mac_tarihi_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        secilenler = st.multiselect("4 oyuncu seçin:", options=tum_oyuncular, default=tum_oyuncular[:4] if len(tum_oyuncular) >= 4 else None)
        
        if len(secilenler) == 4:
            if st.button("Masayı Kur ve Başlat", type="primary"):
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
        tarih_goster = st.session_state["match_date"]
        
        st.success(f"Maç: **{st.session_state['current_match_name']}** ({tarih_goster})")
        st.dataframe(df.style.format("{:.0f}"), use_container_width=True)
        
        total_limit = sum([k['limit'] for k in OYUN_KURALLARI.values()])
        oynanan_satir_sayisi = len(df)
        
        if oynanan_satir_sayisi >= total_limit or st.session_state["king_mode"]:
            st.success("🏁 OYUN BİTTİ!")
            cols = st.columns(4)
            totals = df.sum()
            for i, p in enumerate(secili_oyuncular):
                cols[i].metric(p, f"{totals[p]}", delta_color="normal" if totals[p]>0 else "inverse")
                
            if st.button("💾 Maçı Arşivle ve KKD Güncelle", type="primary"):
                with st.spinner("İşleniyor..."):
                    try:
                        wb = get_sheet_by_url()
                        sheet = wb.worksheet("Maclar")
                        tarih = st.session_state["match_date"]
                        sheet.append_row([""] * 5)
                        header_title = f"--- MAÇ: {st.session_state['current_match_name']} ({tarih}) ---"
                        sheet.append_row([header_title, "", "", "", ""])
                        sheet.append_row(["OYUN TÜRÜ"] + secili_oyuncular)
                        for idx, row in df.iterrows():
                            row_data = [idx] + [int(row[p]) for p in secili_oyuncular]
                            sheet.append_row(row_data)
                        total_row = ["TOPLAM"] + [int(totals[p]) for p in secili_oyuncular]
                        sheet.append_row(total_row)
                        sheet.append_row(["----------------------------------------"] * 5)
                        
                        stats, _ = istatistikleri_hesapla()
                        if stats:
                            elo_dict = {name: data['kkd'] for name, data in stats.items()}
                            save_elos_to_users_sheet(elo_dict)
                        
                        st.balloons()
                        st.success("✅ Başarılı!")
                        st.session_state["game_active"] = False
                        st.session_state["king_mode"] = False
                        st.session_state["temp_df"] = pd.DataFrame()
                        del st.session_state["players"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
            return

        st.markdown("---")
        if st.button("👑 KING YAPILDI (OYUNU BİTİR)", type="secondary"):
             st.session_state["show_king_dialog"] = True

        if st.session_state.get("show_king_dialog", False):
            st.warning("Bu işlem oyunu anında bitirecek!")
            king_maker = st.selectbox("King'i kim yaptı?", secili_oyuncular)
            if st.button("Onayla ve Bitir"):
                king_scores = {p: 0 for p in secili_oyuncular}
                row_name = f"👑 KING ({king_maker})"
                new_row = pd.DataFrame([king_scores], index=[row_name])
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
        remaining_rounds = rules['limit'] - current_count
        st.info(f"Oynanan: **{secilen_oyun}** | Kalan Hak: **{remaining_rounds}**")
        
        cols = st.columns(4)
        inputs = {}
        row_key_base = f"{secilen_oyun}_{current_count}"
        current_sum = 0
        for p in secili_oyuncular:
            key = f"val_{row_key_base}_{p}"
            current_sum += st.session_state.get(key, 0)
        remaining_total_for_row = rules['adet'] - current_sum
        
        for i, p in enumerate(secili_oyuncular):
            key = f"val_{row_key_base}_{p}"
            my_val = st.session_state.get(key, 0)
            my_max = my_val + remaining_total_for_row
            if my_max < 0: my_max = 0
            val = cols[i].number_input(f"{p}", min_value=0, max_value=int(my_max), step=1, key=key)
            inputs[p] = val

        final_sum = sum(inputs.values())
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("Kaydet ve İlerle", type="primary"):
            if final_sum != rules['adet']:
                st.error(f"Hata: Toplam {rules['adet']} olmalı, şu an {final_sum}.")
            else:
                row_name = f"{secilen_oyun} #{current_count + 1}"
                row_data = {p: inputs[p] * rules['puan'] for p in secili_oyuncular}
                new_row = pd.DataFrame([row_data], index=[row_name])
                st.session_state["temp_df"] = pd.concat([st.session_state["temp_df"], new_row])
                yeni_sayac = len([x for x in st.session_state["temp_df"].index if secilen_oyun in x])
                if yeni_sayac >= rules['limit'] and st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
                    st.session_state["game_index"] += 1
                st.rerun()
        if col_btn2.button("⚠️ Son Satırı Sil"):
            if not st.session_state["temp_df"].empty:
                st.session_state["temp_df"] = st.session_state["temp_df"][:-1]
                st.rerun()

# =============================================================================
# 5. KKD LİDERLİK
# =============================================================================

def kkd_leaderboard_interface():
    st.markdown("<h2>🏆 KKD Liderlik Tablosu</h2>", unsafe_allow_html=True)
    stats, _ = istatistikleri_hesapla()
    if not stats:
        st.warning("Henüz maç verisi yok.")
        return
    df_stats = pd.DataFrame.from_dict(stats, orient='index')
    if not df_stats.empty:
        df_stats['win_rate'] = (df_stats['pozitif_mac_sayisi'] / df_stats['mac_sayisi']) * 100
        elo_table = df_stats[['mac_sayisi', 'kkd', 'win_rate']].sort_values('kkd', ascending=False)
        elo_table.columns = ['Toplam Maç', 'KKD Puanı (ELO)', 'Başarı Oranı (%)']
        st.dataframe(elo_table.style.format({'Başarı Oranı (%)': "{:.1f}%", 'KKD Puanı (ELO)': "{:.0f}"}), use_container_width=True)
        st.info("Puanlar dinamik olarak güncellenmektedir.")

# =============================================================================
# 6. İSTATİSTİK ARAYÜZÜ
# =============================================================================

def stats_interface():
    st.markdown("<h2>📊 Detaylı İstatistik Merkezi</h2>", unsafe_allow_html=True)
    stats, match_history = istatistikleri_hesapla()
    if not stats:
        st.warning("Henüz maç verisi yok.")
        return
    tabs = st.tabs(["🏆 Genel Durum", "📜 Maç Geçmişi", "🚫 Ceza Analizi", "🤝 Komanditlik"])
    df_stats = pd.DataFrame.from_dict(stats, orient='index')
    with tabs[0]:
        st.subheader("🏆 Genel Puan")
        if not df_stats.empty:
            st.dataframe(df_stats[['mac_sayisi', 'toplam_puan']].sort_values('toplam_puan', ascending=False), use_container_width=True)
            st.divider()
            col_rec1, col_rec2 = st.columns(2)
            col_rec1.success(f"🚀 **En Yüksek Çıkış:**\n# {df_stats['rekor_max'].idxmax()} ({df_stats['rekor_max'].max()})")
            col_rec2.error(f"⚓ **En Büyük Batış:**\n# {df_stats['rekor_min'].idxmin()} ({df_stats['rekor_min'].min()})")
    with tabs[1]:
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
    with tabs[2]:
        st.subheader("🚫 Ceza Analizi")
        ceza_list = [k for k in OYUN_KURALLARI.keys() if OYUN_KURALLARI[k]['puan'] < 0]
        selected_ceza = st.selectbox("Ceza Türü Seç:", ceza_list)
        ceza_data = {p: stats[p]['cezalar'].get(selected_ceza, 0) / stats[p]['mac_sayisi'] if stats[p]['mac_sayisi']>0 else 0 for p in stats}
        st.bar_chart(pd.Series(ceza_data))
    with tabs[3]:
        st.subheader("🤝 Komanditlik")
        me = st.session_state["username"]
        if me in stats and stats[me]['partnerler']:
            p_list = [{"Komandit": p, "Maç": d['birlikte_mac'], "Kazanma %": d['beraber_kazanma']/d['birlikte_mac']*100} for p, d in stats[me]['partnerler'].items()]
            st.dataframe(pd.DataFrame(p_list).sort_values(by="Kazanma %", ascending=False), use_container_width=True)

# =============================================================================
# 7. PROFİL EKRANI (KARİYER MODU - DÜZELTİLDİ)
# =============================================================================

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    
    stats, match_history = istatistikleri_hesapla()
    my_name = st.session_state['username']
    
    # 1. KİŞİSEL İSTATİSTİK KARTLARI
    if stats and my_name in stats:
        my_stats = stats[my_name]
        
        # En çok yenen ceza bulma
        cezalar = my_stats['cezalar']
        fav_ceza = "Temiz"
        fav_oran = 0
        if cezalar:
            fav_ceza = max(cezalar, key=cezalar.get)
            toplam_ceza_sayisi = sum(cezalar.values())
            fav_oran = (cezalar[fav_ceza] / toplam_ceza_sayisi * 100) if toplam_ceza_sayisi > 0 else 0

        win_rate = (my_stats['pozitif_mac_sayisi'] / my_stats['mac_sayisi']) * 100 if my_stats['mac_sayisi'] > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Maç", my_stats['mac_sayisi'])
        c2.metric("KKD (ELO)", f"{my_stats['kkd']:.0f}")
        c3.metric("Win Rate", f"%{win_rate:.1f}")
        c4.metric("Baş Belası", f"{fav_ceza}", f"%{fav_oran:.0f}")
        
        st.divider()
        
        # 2. AKILLI KOÇ (VİDEO VE LİNK ÖNERİSİ)
        st.subheader("🎓 Akıllı Koç Analizi")
        if fav_ceza in VIDEO_MAP:
            st.info(f"Koç diyor ki: **{fav_ceza}** cezasını çok yiyorsun (%{fav_oran:.0f}). Bu konuda zayıfsın, şu dersi izle:")
            
            # YouTube Linki
            video_url = VIDEO_MAP[fav_ceza]
            
            # Embed'i göstermeye çalış
            try:
                st.video(video_url)
            except:
                st.warning("Video önizlemesi yüklenemedi.")
                
            # YEDEK BUTON: Eğer embed çalışmazsa bu butona basılır
            st.link_button(label="📺 Videoyu YouTube'da İzlemek İçin Tıkla", url=video_url)
            
        else:
            st.success("Harika! Belirgin bir zayıflığın yok gibi görünüyor. Şimdilik temiz oyun!")
            
    st.divider()

    # 3. KİŞİSEL MAÇ GEÇMİŞİ (TABLO)
    st.subheader("📜 Kişisel Maç Karnesi")
    if match_history:
        my_match_log = []
        # Geçmişi tersten tara (En yeni en üstte)
        for m in reversed(match_history):
            if my_name in m['oyuncular']:
                # Puanı bul
                idx = m['oyuncular'].index(my_name)
                try:
                    score = int(m['toplamlar'][idx+1]) # +1 çünkü ilk kolon başlık
                    sonuc = "KAZANDI" if score >= 0 else "KAYBETTİ"
                    
                    # King maçı kontrolü
                    if "KING" in m['toplamlar'][0]:
                        winner = m['toplamlar'][0].split("(")[1].split(")")[0]
                        sonuc = "KAZANDI 👑" if winner == my_name else "KAYBETTİ"
                    
                    my_match_log.append({
                        "Tarih / Maç": m['baslik'].replace("--- MAÇ: ", "").replace(" ---", ""),
                        "Puan": score,
                        "Sonuç": sonuc
                    })
                except: pass
        
        if my_match_log:
            df_log = pd.DataFrame(my_match_log)
            # Renkli gösterme (Pandas Styler)
            def color_result(val):
                color = 'green' if 'KAZANDI' in val else 'red'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(df_log.style.applymap(color_result, subset=['Sonuç']), use_container_width=True)
        else:
            st.info("Henüz oynanmış maçınız yok.")

    st.divider()
    
    # 4. GÜNCELLEME ALANI
    with st.expander("⚙️ Ayarlar (İsim/Şifre Değiştir)"):
        new_username = st.text_input("Yeni Kullanıcı Adı", value=my_name)
        new_pass = st.text_input("Yeni Şifre", type="password")
        if st.button("Bilgileri Güncelle"):
            result = update_user_in_sheet(my_name, new_username, new_pass if new_pass else "1234", st.session_state["role"])
            if result == "updated":
                st.success("Profil güncellendi! Çıkış yapılıyor...")
                time.sleep(1)
                st.session_state["logged_in"] = False
                st.rerun()

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
        if current_user_role == "patron":
            u_role = c3.selectbox("Yetki", ["user", "admin", "patron"])
        else: u_role = "user" 
        
        if st.form_submit_button("Kaydet"):
            if u_name:
                target_user_row = users_df[users_df['Username'] == u_name]
                target_role = "user"
                if not target_user_row.empty: target_role = target_user_row.iloc[0]['Role']
                
                if current_user_role == "admin" and target_role in ["patron", "admin"] and not target_user_row.empty:
                    st.error("Yetkisiz işlem.")
                else:
                    pwd = u_pass if u_pass else "1234"
                    res = update_user_in_sheet(u_name, u_name, pwd, u_role, delete=False)
                    if res == "added": st.success("Eklendi.")
                    elif res == "updated": st.success("Güncellendi.")
                    st.rerun()

    st.divider()
    st.subheader("🗑️ Maç Yönetimi")
    _, match_history = istatistikleri_hesapla()
    if match_history:
        match_options = [f"{m['baslik']}" for m in match_history][::-1]
        selected_delete_match = st.selectbox("Silinecek Maç:", match_options, key="del_match")
        if st.button("Seçili Maçı Sil", type="primary"):
            st.session_state["pending_delete_match"] = selected_delete_match
            st.rerun()
        if "pending_delete_match" in st.session_state and st.session_state["pending_delete_match"]:
            st.error(f"{st.session_state['pending_delete_match']} silinecek!")
            if st.button("✅ Onayla"):
                delete_match_from_sheet(st.session_state["pending_delete_match"])
                del st.session_state["pending_delete_match"]
                st.success("Silindi.")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    st.subheader("📋 Kullanıcılar")
    if "pending_delete_user" in st.session_state and st.session_state["pending_delete_user"]:
        target = st.session_state["pending_delete_user"]
        st.error(f"{target} silinecek!")
        if st.button("✅ Onayla", key="conf_usr"):
            update_user_in_sheet(target, target, "x", "user", delete=True)
            del st.session_state["pending_delete_user"]
            st.rerun()

    if not users_df.empty and 'Username' in users_df.columns:
        for index, row in users_df.iterrows():
            c1, c2 = st.columns([4,1])
            c1.write(f"**{row['Username']}** ({row['Role']})")
            if current_user_role == "patron" and row['Username'] != st.session_state["username"]:
                if c2.button("Sil", key=f"del_{row['Username']}"):
                    st.session_state["pending_delete_user"] = row['Username']
                    st.rerun()

# =============================================================================
# 9. ANA UYGULAMA ÇATISI
# =============================================================================

st.set_page_config(page_title="King İstatistik Kurumu", layout="wide", page_icon="👑")
inject_custom_css()

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    st.markdown(f"<h3 style='text-align: center;'>👑 {st.session_state['username']}</h3>", unsafe_allow_html=True)
    menu_options = ["📊 İstatistikler", "🏆 KKD Liderlik", "👤 Profilim"] 
    if st.session_state["role"] in ["admin", "patron"]:
        menu_options = ["🎮 Oyun Ekle", "🛠️ Yönetim Paneli"] + menu_options
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
