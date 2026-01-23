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
import re

# Matplotlib kontrolü
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

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

# KOMİK UNVANLAR
FUNNY_TITLES = {
    "Rıfkı": "🩸 Rıfkızede",
    "Kız Almaz": "💔 Kızların Sevgilisi",
    "Erkek Almaz": "👨‍❤️‍👨 Erkek Koleksiyoncusu",
    "Kupa Almaz": "🍷 Kupa Canavarı",
    "El Almaz": "🤲 El Arsızı", 
    "Son İki": "🛑 Son Durak",
    "Koz (Tümü)": "♠️ Koz Baronu" 
}

# OYUN KURALLARI
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

def get_users_map():
    try:
        sheet = get_sheet_by_url().worksheet("Users")
        data = sheet.get_all_records()
        id_to_name = {}
        name_to_id = {}
        full_data = []
        for row in data:
            u_id = row.get('UserID')
            u_name = str(row.get('Username')).strip()
            if u_id is not None and str(u_id).isdigit():
                u_id = int(u_id)
                id_to_name[u_id] = u_name
                name_to_id[u_name] = u_id
                full_data.append(row)
        return id_to_name, name_to_id, pd.DataFrame(full_data)
    except: return {}, {}, pd.DataFrame()

def save_elos_to_users_sheet(elo_data_by_id):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        all_values = sheet.get_all_values()
        if not all_values: return False
        headers = all_values[0]
        try:
            uid_idx = headers.index("UserID")
            kkd_idx = headers.index("KKD")
        except: return False
        updated_data = [headers]
        for row in all_values[1:]:
            try:
                current_id = int(row[uid_idx])
                while len(row) <= kkd_idx: row.append("")
                if current_id in elo_data_by_id:
                    row[kkd_idx] = int(elo_data_by_id[current_id])
            except: pass
            updated_data.append(row)
        sheet.clear()
        sheet.update(updated_data)
        return True
    except: return False

def update_user_in_sheet(old_username, new_username, password, role, delete=False):
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        all_data = sheet.get_all_values()
        if not all_data: 
            sheet.append_row(["Username", "Password", "Role", "UserID", "KKD"])
            all_data = sheet.get_all_values()
        headers = all_data[0]
        try:
            user_idx = headers.index("Username")
            pass_idx = headers.index("Password")
            role_idx = headers.index("Role")
            uid_idx = headers.index("UserID")
        except: return False
        found_row_idx = -1
        for i, row in enumerate(all_data):
            if i == 0: continue
            if str(row[user_idx]).strip() == old_username.strip():
                found_row_idx = i
                break
        if found_row_idx != -1:
            if delete:
                sheet.delete_rows(found_row_idx + 1)
                return "deleted"
            else:
                sheet.update_cell(found_row_idx + 1, user_idx + 1, new_username)
                sheet.update_cell(found_row_idx + 1, pass_idx + 1, password)
                sheet.update_cell(found_row_idx + 1, role_idx + 1, role)
                return "updated"
        else:
            if not delete:
                current_ids = []
                for row in all_data[1:]:
                    try: current_ids.append(int(row[uid_idx]))
                    except: pass
                new_id = max(current_ids) + 1 if current_ids else 0
                sheet.append_row([new_username, password, role, new_id, STARTING_ELO])
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
        start = -1; end = -1
        for i, row in enumerate(all_values):
            if row and str(row[0]) == match_title:
                start = i + 1 
                for j in range(i, len(all_values)):
                    if all_values[j] and str(all_values[j][0]).startswith("----------------"):
                        end = j + 1; break
                break
        if start != -1 and end != -1:
            sheet.delete_rows(start, end)
            return True
        return False
    except: return False

# =============================================================================
# 2. İSTATİSTİK MOTORU
# =============================================================================

def calculate_expected_score(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 400))

def parse_date_from_header(header_str):
    try:
        date_part = header_str.split('(')[-1].split(')')[0]
        return datetime.strptime(date_part.strip(), "%d.%m.%Y")
    except: return datetime.now()

def extract_id_from_cell(cell_value, name_to_id_map):
    s = str(cell_value).strip()
    match = re.search(r'\(uid:(\d+)\)', s)
    if match: return int(match.group(1))
    clean_name = s.split('(')[0].strip()
    if clean_name in name_to_id_map: return name_to_id_map[clean_name]
    return None

def istatistikleri_hesapla():
    id_to_name, name_to_id, _ = get_users_map()
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        raw_data = sheet.get_all_values()
    except: return None, None, None, None

    if not raw_data: return None, None, None, None

    player_stats = {}
    elo_ratings = {} 
    all_matches_chronological = []
    match_history_display = []
    
    current_match_ids = [] 
    current_match_data = {} 
    is_king_game = False
    king_winner_id = None

    for row in raw_data:
        if not row: continue
        first_cell = str(row[0]).strip()
        
        if first_cell.startswith("--- MAÇ:"):
            current_match_ids = []
            current_match_data = {
                "baslik": first_cell, "tarih": parse_date_from_header(first_cell),
                "skorlar": [], "ids": [], "ceza_detaylari": {} 
            }
            is_king_game = False
            king_winner_id = None
            continue
            
        if first_cell == "OYUN TÜRÜ":
            for col_idx in range(1, len(row)):
                raw_val = row[col_idx]
                if not raw_val: continue
                p_id = extract_id_from_cell(raw_val, name_to_id)
                if p_id is not None:
                    current_match_ids.append(p_id)
                    current_match_data["ids"].append(p_id)
                    if p_id not in player_stats:
                        player_stats[p_id] = {
                            "mac_sayisi": 0, "toplam_puan": 0, "pozitif_mac_sayisi": 0,
                            "cezalar": {k: 0 for k in OYUN_KURALLARI}, "partnerler": {}, 
                            "rekor_max": -9999, "rekor_min": 9999, "kkd": STARTING_ELO,
                            "win_streak": 0, "loss_streak": 0, "max_win_streak": 0, "max_loss_streak": 0,
                            "toplam_ceza_puani": 0, "toplam_koz_puani": 0
                        }
                    if p_id not in elo_ratings: elo_ratings[p_id] = STARTING_ELO
            continue

        base_name = first_cell.split(" #")[0]
        if "KING" in first_cell:
            is_king_game = True
            extracted = extract_id_from_cell(first_cell, name_to_id)
            if extracted is not None: king_winner_id = extracted
        
        if (base_name in OYUN_KURALLARI or "KING" in first_cell) and current_match_ids:
            if "skorlar" in current_match_data: current_match_data["skorlar"].append(row)
            for i, p_id in enumerate(current_match_ids):
                try:
                    if (i + 1) < len(row):
                        score_val = row[i+1]
                        if score_val == "" or score_val == " ": continue
                        score = int(score_val)
                        stats = player_stats[p_id]
                        stats["toplam_puan"] += score
                        
                        if "Koz" in base_name: stats["toplam_koz_puani"] += score
                        elif score < 0 and not is_king_game: stats["toplam_ceza_puani"] += score
                        
                        if score < 0 and base_name in OYUN_KURALLARI and not is_king_game:
                            birim = OYUN_KURALLARI[base_name]['puan']
                            count = int(score/birim)
                            stats["cezalar"][base_name] += count
                            if p_id not in current_match_data["ceza_detaylari"]: current_match_data["ceza_detaylari"][p_id] = {}
                            if base_name not in current_match_data["ceza_detaylari"][p_id]: current_match_data["ceza_detaylari"][p_id][base_name] = 0
                            current_match_data["ceza_detaylari"][p_id][base_name] += count
                except: continue

        if first_cell == "TOPLAM":
            if not current_match_data: continue
            current_match_data["toplamlar"] = row
            match_elos = {pid: elo_ratings.get(pid, STARTING_ELO) for pid in current_match_ids}
            match_results = {}; winners = 0; losers = 0
            
            for i, p_id in enumerate(current_match_ids):
                try:
                    total = int(row[i+1])
                    match_results[p_id] = total
                    is_win = False
                    if is_king_game:
                        if p_id == king_winner_id: is_win = True
                    else:
                        if total >= 0: is_win = True
                    
                    if is_win: winners += 1
                    else: losers += 1
                    
                    stats = player_stats[p_id]
                    stats["mac_sayisi"] += 1
                    if is_win: stats["pozitif_mac_sayisi"] += 1
                    if not is_king_game:
                        if total > stats["rekor_max"]: stats["rekor_max"] = total
                        if total < stats["rekor_min"]: stats["rekor_min"] = total
                    
                    for op_id in current_match_ids:
                        if op_id != p_id:
                            if op_id not in stats["partnerler"]: stats["partnerler"][op_id] = {"birlikte_mac": 0, "beraber_kazanma": 0}
                            p_stat = stats["partnerler"][op_id]
                            p_stat["birlikte_mac"] += 1
                            if is_win: p_stat["beraber_kazanma"] += 1
                except: pass
            
            current_match_data["sonuclar"] = match_results
            new_elos = {}
            for p_id in current_match_ids:
                my_elo = match_elos[p_id]
                actual = 1 if match_results.get(p_id, -1) >= 0 else 0
                opponents = [match_elos[op] for op in current_match_ids if op != p_id]
                avg_opp = sum(opponents)/len(opponents) if opponents else STARTING_ELO
                exp = calculate_expected_score(my_elo, avg_opp)
                change = K_FACTOR * (actual - exp)
                if actual == 1 and winners == 1: change *= SOLO_MULTIPLIER
                elif actual == 0 and losers == 1: change *= SOLO_MULTIPLIER
                new_elos[p_id] = my_elo + change
            
            for pid, val in new_elos.items():
                elo_ratings[pid] = val
                player_stats[pid]["kkd"] = val
            
            display_copy = current_match_data.copy()
            display_copy['oyuncular'] = [id_to_name.get(uid, f"Bilinmeyen({uid})") for uid in current_match_ids]
            match_history_display.append(display_copy)
            all_matches_chronological.append(current_match_data)
            current_match_ids = []

    all_matches_chronological.sort(key=lambda x: x['tarih'])
    temp_streaks = {} 
    for match in all_matches_chronological:
        for p_id in match['ids']:
            if p_id not in temp_streaks: temp_streaks[p_id] = {'win': 0, 'loss': 0}
            score = match['sonuclar'].get(p_id, -1)
            is_win = score >= 0
            if is_win:
                temp_streaks[p_id]['win'] += 1; temp_streaks[p_id]['loss'] = 0
            else:
                temp_streaks[p_id]['loss'] += 1; temp_streaks[p_id]['win'] = 0
            
            if temp_streaks[p_id]['win'] > player_stats[p_id]['max_win_streak']: player_stats[p_id]['max_win_streak'] = temp_streaks[p_id]['win']
            if temp_streaks[p_id]['loss'] > player_stats[p_id]['max_loss_streak']: player_stats[p_id]['max_loss_streak'] = temp_streaks[p_id]['loss']
            player_stats[p_id]['win_streak'] = temp_streaks[p_id]['win']
            player_stats[p_id]['loss_streak'] = temp_streaks[p_id]['loss']

    return player_stats, match_history_display, all_matches_chronological, id_to_name

# =============================================================================
# 3. KULLANICI ARAYÜZ FONKSİYONLARI
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
                _, _, users_df = get_users_map()
                if users_df.empty: st.error("⚠️ HATA: 'Users' tablosu okunamadı."); return
                user_match = users_df[users_df['Username'].astype(str).str.strip() == username.strip()]
                if not user_match.empty and str(user_match.iloc[0]['Password']).strip() == str(password).strip():
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = user_match.iloc[0]['Role']
                    st.session_state["user_id"] = int(user_match.iloc[0]['UserID'])
                    st.success("Giriş Başarılı!")
                    st.rerun()
                else: st.error("Hatalı giriş!")

def logout(): st.session_state.clear(); st.rerun()

def game_interface():
    id_to_name, name_to_id, _ = get_users_map()
    
    if "game_active" not in st.session_state: st.session_state["game_active"] = False
    if "temp_df" not in st.session_state: st.session_state["temp_df"] = pd.DataFrame()
    if "game_index" not in st.session_state: st.session_state["game_index"] = 0
    if "king_mode" not in st.session_state: st.session_state["king_mode"] = False

    if not st.session_state["game_active"]:
        st.info("Yeni maç başlatın veya geçmiş bir maçı sisteme girin.")
        user_names = list(name_to_id.keys())
        c1, c2 = st.columns(2)
        match_name = c1.text_input("Maç İsmi:", "King_Maci")
        is_past = c2.checkbox("Geçmiş Maç?")
        date_val = c2.date_input("Tarih", datetime.now()) if is_past else datetime.now()
        
        selected_names = st.multiselect("Kadro (4 Kişi):", user_names)
        if len(selected_names) == 4 and st.button("Masayı Kur", type="primary"):
            st.session_state["temp_df"] = pd.DataFrame(columns=selected_names)
            st.session_state["current_match_name"] = match_name
            st.session_state["match_date"] = date_val.strftime("%d.%m.%Y")
            st.session_state["players"] = selected_names 
            st.session_state["game_active"] = True
            st.session_state["game_index"] = 0
            st.session_state["king_mode"] = False
            st.rerun()
        return

    df = st.session_state["temp_df"]
    players = st.session_state["players"]
    
    st.success(f"Maç: **{st.session_state['current_match_name']}** ({st.session_state['match_date']})")
    st.dataframe(df.style.format("{:.0f}"), use_container_width=True)
    
    total_limit = sum([k['limit'] for k in OYUN_KURALLARI.values()])
    if len(df) >= total_limit or st.session_state["king_mode"]:
        st.success("🏁 OYUN BİTTİ!")
        totals = df.sum()
        cols = st.columns(4)
        for i, p in enumerate(players): cols[i].metric(p, f"{totals[p]:.0f}")
        
        if st.button("💾 Arşivle (ID ile Kaydet)", type="primary"):
            with st.spinner("Kaydediliyor..."):
                try:
                    wb = get_sheet_by_url()
                    sheet = wb.worksheet("Maclar")
                    sheet.append_row([""] * 5)
                    sheet.append_row([f"--- MAÇ: {st.session_state['current_match_name']} ({st.session_state['match_date']}) ---", "", "", "", ""])
                    header_row = ["OYUN TÜRÜ"]
                    for p in players:
                        pid = name_to_id.get(p, "?")
                        header_row.append(f"{p} (uid:{pid})")
                    sheet.append_row(header_row)
                    for idx, row in df.iterrows(): sheet.append_row([idx] + [int(row[p]) for p in players])
                    sheet.append_row(["TOPLAM"] + [int(totals[p]) for p in players])
                    sheet.append_row(["----------------------------------------"] * 5)
                    stats, _, _, _ = istatistikleri_hesapla()
                    if stats: save_elos_to_users_sheet({uid: d['kkd'] for uid, d in stats.items()})
                    st.balloons()
                    st.session_state["game_active"] = False
                    st.session_state["temp_df"] = pd.DataFrame()
                    st.rerun()
                except Exception as e: st.error(f"Hata: {e}")
        return

    st.markdown("---")
    if st.button("👑 KING YAPILDI"): st.session_state["show_king_dialog"] = True
    if st.session_state.get("show_king_dialog"):
        km = st.selectbox("Kim Yaptı?", players)
        if st.button("Onayla"):
            st.session_state["temp_df"] = pd.concat([df, pd.DataFrame([{p:0 for p in players}], index=[f"👑 KING ({km})"])])
            st.session_state["king_mode"] = True
            st.session_state["show_king_dialog"] = False
            st.rerun()

    # Oyun Seçimi ve İlerleme Mantığı
    current_idx = st.session_state["game_index"]
    if current_idx >= len(OYUN_SIRALAMASI): current_idx = len(OYUN_SIRALAMASI) - 1
    
    selected_game = st.selectbox("Oyun Seç:", OYUN_SIRALAMASI, index=current_idx)
    rules = OYUN_KURALLARI[selected_game]
    played_count = len([x for x in df.index if selected_game in x])
    rem = rules['limit'] - played_count
    
    # Otomatik oyun değiştirme kontrolü
    if rem <= 0 and not st.session_state["king_mode"]:
        # Eğer bu oyunun limiti dolduysa ve manuel seçilmediyse bir sonrakine geçmeyi dene
        if current_idx < len(OYUN_SIRALAMASI) - 1:
             # Kullanıcı elle değiştirmediyse state'i güncelle
             if OYUN_SIRALAMASI[st.session_state["game_index"]] == selected_game:
                 st.session_state["game_index"] += 1
                 st.rerun()

    st.info(f"Kalan Hak: {rem} | Toplam Puan: {rules['puan'] * rules['adet']}")
    
    cols = st.columns(4)
    inputs = {}
    row_key_base = f"{selected_game}_{played_count}"
    
    # Daha önce girilen toplam (Bu oyun türü için bu turda)
    # Burada basit mantık: Her oyuncu için input al
    current_row_sum = 0
    for p in players:
        # Kalan toplam adedi hesapla
        current_inputs_sum = sum(inputs.values())
        max_possible = rules['adet'] - current_inputs_sum
        val = cols[players.index(p)].number_input(f"{p}", min_value=0, max_value=int(rules['adet']), step=1, key=f"in_{row_key_base}_{p}")
        inputs[p] = val

    if st.button("Kaydet ve İlerle", type="primary"):
        if sum(inputs.values()) != rules['adet']: st.error(f"Toplam {rules['adet']} olmalı!")
        else:
            row_data = {p: inputs[p] * rules['puan'] for p in players}
            st.session_state["temp_df"] = pd.concat([df, pd.DataFrame([row_data], index=[f"{selected_game} #{played_count+1}"])])
            
            # Eğer bu oyunun limiti dolduysa indexi artır
            new_played_count = played_count + 1
            if new_played_count >= rules['limit'] and st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
                st.session_state["game_index"] += 1
            
            st.rerun()
            
    if st.button("Son Satırı Sil"):
        if not df.empty:
            st.session_state["temp_df"] = df[:-1]
            # Silince indexi geri al (gerekirse)
            # Basitlik için indexi elle geri alması daha güvenli veya sabit kalabilir
            st.rerun()

def kkd_leaderboard_interface():
    st.markdown("<h2>🏆 KKD Liderlik</h2>", unsafe_allow_html=True)
    stats, _, _, id_map = istatistikleri_hesapla()
    if not stats: st.warning("Veri yok."); return
    
    data_list = []
    for uid, s in stats.items():
        name = id_map.get(uid, f"Unknown({uid})")
        wr = (s['pozitif_mac_sayisi']/s['mac_sayisi']*100) if s['mac_sayisi'] > 0 else 0
        data_list.append({"Oyuncu": name, "Maç": s['mac_sayisi'], "KKD": s['kkd'], "Win Rate": wr})
        
    df = pd.DataFrame(data_list).sort_values("KKD", ascending=False)
    st.dataframe(df.style.format({"Win Rate": "{:.1f}%", "KKD": "{:.0f}"}), use_container_width=True)

def stats_interface():
    st.markdown("<h2>📊 İstatistik Merkezi</h2>", unsafe_allow_html=True)
    stats, match_hist, chrono_matches, id_map = istatistikleri_hesapla()
    if not stats: st.warning("Veri yok."); return
    
    rows = []
    for uid, s in stats.items():
        name = id_map.get(uid, f"Unknown({uid})")
        row = s.copy()
        row['Oyuncu'] = name
        row['averaj'] = row['toplam_puan'] / row['mac_sayisi'] if row['mac_sayisi'] > 0 else 0
        rows.append(row)
    df_main = pd.DataFrame(rows).set_index("Oyuncu")

    tabs = st.tabs(["🔥 Seriler", "⚖️ Averaj", "📅 Rewind", "🏆 Genel", "📜 Arşiv", "🚫 Cezalar", "🤝 Komandit"])

    with tabs[0]: 
        st.subheader("🔥 Seriler")
        best = df_main['max_win_streak'].idxmax(); worst = df_main['max_loss_streak'].idxmax()
        c1, c2 = st.columns(2)
        c1.success(f"🚀 **En İyi:** {best} ({df_main.loc[best, 'max_win_streak']})")
        c2.error(f"💀 **En Kötü:** {worst} ({df_main.loc[worst, 'max_loss_streak']})")
        st.dataframe(df_main[['win_streak', 'max_win_streak', 'loss_streak', 'max_loss_streak']].sort_values('win_streak', ascending=False), use_container_width=True)

    with tabs[1]:
        st.subheader("⚖️ Averaj Liderlik (Ort. Puan)")
        disp = df_main[['mac_sayisi', 'toplam_puan', 'averaj']].sort_values('averaj', ascending=False)
        disp.columns = ["Maç Sayısı", "Toplam Puan", "Ortalama"]
        st.dataframe(disp.style.format({'Ortalama': "{:.1f}"}), use_container_width=True)

    with tabs[2]:
        st.subheader("📅 Zaman Tüneli")
        if not chrono_matches: st.info("Tarih verisi yok."); return
        dates = sorted([m['tarih'] for m in chrono_matches], reverse=True)
        years = sorted(list(set([d.year for d in dates])), reverse=True)
        c1, c2 = st.columns(2)
        sy = c1.selectbox("Yıl", ["Tümü"] + years)
        sm = c2.selectbox("Ay", ["Tümü"] + list(range(1, 13)))
        
        filtered = []
        for m in chrono_matches:
            d = m['tarih']
            if sy != "Tümü" and d.year != sy: continue
            if sm != "Tümü" and d.month != sm: continue
            filtered.append(m)
            
        if filtered:
            p_stats = {}
            for m in filtered:
                for uid in m['ids']:
                    if uid not in p_stats: p_stats[uid] = {'wins':0, 'matches':0, 'puan':0, **{k:0 for k in FUNNY_TITLES}}
                    p_stats[uid]['matches'] += 1
                    sc = m['sonuclar'].get(uid, 0)
                    p_stats[uid]['puan'] += sc
                    if sc >= 0 or ("KING" in m['baslik'] and m.get("winner_id") == uid): p_stats[uid]['wins'] += 1
                    if uid in m['ceza_detaylari']:
                        for c, v in m['ceza_detaylari'][uid].items():
                            if c in p_stats[uid]: p_stats[uid][c] += v
            
            res = []
            for uid, dat in p_stats.items():
                dat['Oyuncu'] = id_map.get(uid, str(uid))
                dat['wr'] = dat['wins']/dat['matches']*100
                res.append(dat)
            df_r = pd.DataFrame(res).set_index("Oyuncu")
            
            king = df_r.sort_values(['wr', 'puan'], ascending=False).index[0]
            st.success(f"👑 **Dönem Kralı:** {king} (%{df_r.loc[king, 'wr']:.1f})")
            
            cols = st.columns(3)
            idx = 0
            for k, title in FUNNY_TITLES.items():
                vic = df_r[k].idxmax()
                cnt = df_r.loc[vic, k]
                if cnt > 0:
                    cols[idx%3].error(f"**{title}**\n\n{vic} ({cnt})")
                    idx+=1
            st.dataframe(df_r[['matches', 'wins', 'wr', 'puan']].sort_values('wr', ascending=False), use_container_width=True)
        else: st.warning("Maç yok.")

    with tabs[3]:
        st.subheader("🏆 Genel")
        disp = df_main[['mac_sayisi', 'toplam_puan']].sort_values('toplam_puan', ascending=False)
        st.dataframe(disp, use_container_width=True)

    with tabs[4]:
        if match_hist:
            sel = st.selectbox("Maç:", [m['baslik'] for m in match_hist][::-1])
            found = next((m for m in match_hist if m['baslik'] == sel), None)
            if found:
                st.dataframe(pd.DataFrame(found['skorlar'] + [found['toplamlar']], columns=["OYUN"] + found['oyuncular']), use_container_width=True)

    with tabs[5]:
        ceza_list = []
        for uid, s in stats.items():
            r = s['cezalar'].copy()
            for k in OYUN_KURALLARI: 
                if k not in r: r[k] = 0
            fr = {}
            for k, v in r.items():
                rt = v/s['mac_sayisi'] if s['mac_sayisi'] > 0 else 0
                fr[k] = f"{v} ({rt:.1f})"
            fr['Oyuncu'] = id_map.get(uid, str(uid))
            ceza_list.append(fr)
            
        if ceza_list:
            st.write("### 🟥 Ceza Karnesi (Toplam & Ort)")
            st.dataframe(pd.DataFrame(ceza_list).set_index("Oyuncu"), use_container_width=True)
            loss_data = {}
            for uid, s in stats.items():
                name = id_map.get(uid, str(uid))
                loss_data[name] = {}
                for k, v in s['cezalar'].items():
                    if k in OYUN_KURALLARI:
                        loss_data[name][k] = v * abs(OYUN_KURALLARI[k]['puan'])
            st.write("### 💸 Puan Kaybı")
            st.bar_chart(pd.DataFrame(loss_data).T)

    with tabs[6]:
        my_id = st.session_state.get("user_id")
        if my_id and my_id in stats:
            p_list = []
            for pid, d in stats[my_id]['partnerler'].items():
                name = id_map.get(pid, str(pid))
                rt = d['beraber_kazanma']/d['birlikte_mac']*100 if d['birlikte_mac'] > 0 else 0
                p_list.append({"Partner": name, "Maç": d['birlikte_mac'], "Win%": rt})
            st.dataframe(pd.DataFrame(p_list).sort_values("Win%", ascending=False), use_container_width=True)

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    stats, _, _, id_map = istatistikleri_hesapla()
    uid = st.session_state.get("user_id")
    
    if uid in stats:
        s = stats[uid]
        wr = s['pozitif_mac_sayisi']/s['mac_sayisi']*100 if s['mac_sayisi'] > 0 else 0
        avg_c = s['toplam_ceza_puani']/s['mac_sayisi'] if s['mac_sayisi'] > 0 else 0
        avg_k = s['toplam_koz_puani']/s['mac_sayisi'] if s['mac_sayisi'] > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Maç", s['mac_sayisi'])
        c2.metric("KKD", int(s['kkd']))
        c3.metric("Win Rate", f"%{wr:.1f}")
        
        c4, c5 = st.columns(2)
        c4.metric("Ort. Ceza Puanı", f"{avg_c:.1f}")
        c5.metric("Ort. Koz Puanı", f"{avg_k:.1f}")
        
        st.divider()
        st.subheader("🎓 Akıllı Koç")
        fav_ceza = max(s['cezalar'], key=s['cezalar'].get) if s['cezalar'] else "Yok"
        if fav_ceza in VIDEO_MAP:
            st.info(f"⚠️ Zayıf Yön: **{fav_ceza}**. Bunu geliştirmelisin:")
            st.link_button("📺 Dersi İzle", VIDEO_MAP[fav_ceza])
            
        st.divider()
        st.write("**Son Maçlar**")
        # Maç geçmişini buraya eklemek için istatistikleri_hesapla'dan match_history çekilmeli
        # Ancak performans için burada basitleştirilmiş gösterim yapabiliriz
        pass

    st.divider()
    with st.expander("Ayarlar"):
        u = st.text_input("Kullanıcı Adı", st.session_state['username'])
        p = st.text_input("Şifre", type="password")
        if st.button("Güncelle"):
            if update_user_in_sheet(st.session_state['username'], u, p if p else "1234", st.session_state['role']):
                st.success("Tamamlandı."); time.sleep(1); st.session_state['logged_in']=False; st.rerun()

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim</h2>", unsafe_allow_html=True)
    _, _, users = get_users_map()
    current_role = st.session_state.get("role", "user")
    
    with st.form("add_user"):
        c1, c2, c3 = st.columns(3)
        u = c1.text_input("Kullanıcı")
        p = c2.text_input("Şifre")
        r = c3.selectbox("Yetki", ["user", "admin", "patron"]) if current_role == "patron" else "user"
        if st.form_submit_button("Ekle/Güncelle"):
            if update_user_in_sheet(u, u, p if p else "1234", r): st.success("OK"); st.rerun()
            
    # Kullanıcı Listesi ve Silme Butonu
    st.write("### Kullanıcı Listesi")
    if not users.empty:
        for idx, row in users.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{row['Username']}** ({row['Role']}) - ID: {row['UserID']}")
            with col2:
                # Kendi kendini silemez
                if row['Username'] != st.session_state['username'] and current_role == "patron":
                    if st.button("🗑️ Sil", key=f"del_user_{row['UserID']}"):
                        if update_user_in_sheet(row['Username'], "", "", "", delete=True) == "deleted":
                            st.success(f"{row['Username']} silindi.")
                            time.sleep(1)
                            st.rerun()

# =============================================================================
# 9. ANA UYGULAMA (EN ALTTA)
# =============================================================================
st.set_page_config(page_title="King İstatistik Kurumu", layout="wide", page_icon="👑")
inject_custom_css()

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    st.markdown(f"<h3 style='text-align: center;'>👑 {st.session_state['username']}</h3>", unsafe_allow_html=True)
    menu = ["📊 İstatistikler", "🏆 KKD Liderlik", "👤 Profilim"]
    if st.session_state["role"] in ["admin", "patron"]: menu = ["🎮 Oyun Ekle", "🛠️ Yönetim Paneli"] + menu
    page = st.radio("", menu, horizontal=True, label_visibility="collapsed")
    
    if st.button("Çıkış Yap"): logout()
    st.markdown("---")

    if page == "🎮 Oyun Ekle": game_interface()
    elif page == "📊 İstatistikler": stats_interface()
    elif page == "🏆 KKD Liderlik": kkd_leaderboard_interface()
    elif page == "👤 Profilim": profile_interface()
    elif page == "🛠️ Yönetim Paneli": admin_panel()
