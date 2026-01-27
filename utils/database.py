# utils/database.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime
from utils.config import SHEET_URL, STARTING_ELO

@st.cache_resource(show_spinner=False)
def get_google_sheet_client():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # secrets.toml dosyasından okuyacak
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Google Sheets bağlantı hatası: {str(e)}")
        return None

def get_sheet_by_url():
    client = get_google_sheet_client()
    if client:
        try:
            return client.open_by_url(SHEET_URL)
        except Exception as e:
            st.error(f"Sheet erişim hatası: {str(e)}")
            return None
    return None

@st.cache_data(ttl=120, show_spinner=False)
def fetch_all_data():
    try:
        wb = get_sheet_by_url()
        if not wb: return [], []
        users_data = wb.worksheet("Users").get_all_records()
        matches_data = wb.worksheet("Maclar").get_all_values()
        return users_data, matches_data
    except Exception as e:
        st.error(f"Veri çekme hatası: {str(e)}")
        return [], []

def clear_cache():
    fetch_all_data.clear()
    st.cache_data.clear()

def get_users_map():
    users_data, _ = fetch_all_data()
    id_to_name = {}
    name_to_id = {}
    full_data = []
    
    if not users_data: return {}, {}, pd.DataFrame()

    for row in users_data:
        try:
            u_id = int(row.get('UserID', 0))
            u_name = str(row.get('Username', '')).strip()
            u_role = str(row.get('Role', 'user')).strip()
            u_kkd = int(row.get('KKD', STARTING_ELO))
            
            if u_name:
                id_to_name[u_id] = u_name
                name_to_id[u_name] = u_id
                full_data.append({'UserID': u_id, 'Username': u_name, 'Password': row.get('Password', ''), 'Role': u_role, 'KKD': u_kkd})
        except: continue
    
    return id_to_name, name_to_id, pd.DataFrame(full_data)

def update_user_in_sheet(old_username, new_username, password, role, delete=False):
    try:
        wb = get_sheet_by_url()
        if not wb: return False
        sheet = wb.worksheet("Users")
        all_data = sheet.get_all_values()
        
        if not all_data: return False
        headers = all_data[0]
        
        try:
            user_idx = headers.index("Username")
            pass_idx = headers.index("Password")
            role_idx = headers.index("Role")
            uid_idx = headers.index("UserID")
        except: return False
        
        found_idx = -1
        for i, row in enumerate(all_data):
            if i == 0: continue
            if str(row[user_idx]).strip() == old_username.strip():
                found_idx = i
                break
        
        if found_idx != -1:
            if delete:
                sheet.delete_rows(found_idx + 1)
                clear_cache()
                return "deleted"
            else:
                sheet.update_cell(found_idx + 1, user_idx + 1, new_username)
                sheet.update_cell(found_idx + 1, pass_idx + 1, password)
                sheet.update_cell(found_idx + 1, role_idx + 1, role)
                clear_cache()
                return "updated"
        else:
            if not delete:
                c_ids = [int(row[uid_idx]) for row in all_data[1:] if row[uid_idx].isdigit()]
                new_id = max(c_ids) + 1 if c_ids else 1
                sheet.append_row([new_username, password, role, new_id, STARTING_ELO])
                clear_cache()
                return "added"
        return False
    except Exception as e:
        st.error(f"Kullanıcı işlemi hatası: {str(e)}")
        return False

def delete_match_from_sheet(match_title):
    try:
        wb = get_sheet_by_url()
        if not wb: return False
        sheet = wb.worksheet("Maclar")
        all_values = sheet.get_all_values()
        start, end = -1, -1
        
        for i, row in enumerate(all_values):
            if row and str(row[0]).strip() == match_title.strip():
                start = i
                for j in range(i + 1, len(all_values)):
                    if all_values[j] and str(all_values[j][0]).startswith("--- MAÇ:"):
                        end = j
                        break
                if end == -1: end = len(all_values)
                break
        
        if start != -1 and end != -1:
            sheet.delete_rows(start + 1, end)
            clear_cache()
            return True
        return False
    except Exception as e:
        st.error(f"Maç silme hatası: {str(e)}")
        return False

def save_match_to_sheet(header_row, data_rows, total_row):
    # Döngüsel importu önlemek için fonksiyon içinde import ediyoruz
    from utils.stats import istatistikleri_hesapla
    try:
        wb = get_sheet_by_url()
        if not wb: return False
        sheet_maclar = wb.worksheet("Maclar")
        
        match_title = f"--- MAÇ: {st.session_state.get('current_match_name', 'Maç')} ({st.session_state.get('match_date', datetime.now().strftime('%d.%m.%Y'))}) ---"
        append_data = [[match_title, "", "", "", ""], header_row]
        for dr in data_rows: append_data.append(dr)
        append_data.append(total_row)
        append_data.append(["", "", "", "", ""])
        
        sheet_maclar.append_rows(append_data)
        clear_cache()
        time.sleep(2)
        
        # ELO Güncelleme
        stats, _, _, _ = istatistikleri_hesapla()
        elo_dict = {uid: data['kkd'] for uid, data in stats.items()}
        
        sheet_users = wb.worksheet("Users")
        all_data = sheet_users.get_all_values()
        if len(all_data) > 0:
            headers = all_data[0]
            try:
                uid_idx = headers.index("UserID")
                kkd_idx = headers.index("KKD")
                updated_data = [headers]
                for row in all_data[1:]:
                    if len(row) <= kkd_idx: row.extend([""] * (kkd_idx - len(row) + 1))
                    try:
                        curr_id = int(row[uid_idx])
                        if curr_id in elo_dict: row[kkd_idx] = int(elo_dict[curr_id])
                    except: pass
                    updated_data.append(row)
                sheet_users.clear()
                sheet_users.update(updated_data)
            except: pass
            
        return True
    except Exception as e:
        st.error(f"Kayıt hatası: {str(e)}")
        return False