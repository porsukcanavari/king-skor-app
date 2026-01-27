import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import time
from collections import defaultdict

# Matplotlib kontrolü - GELİŞTİRİLMİŞ
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except (ImportError, RuntimeError) as e:
    HAS_MATPLOTLIB = False
    st.warning(f"⚠️ Matplotlib kullanılamıyor: {str(e)}. Grafikler gösterilemeyecek.")

# =============================================================================
# 🚨 SABİT AYARLAR VE LİNKLER
# =============================================================================
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

# KOMİK UNVANLAR
FUNNY_TITLES = {
    "Rıfkı": "🩸 Rıfkızede",
    "Kız Almaz": "💔 Kızların Sevgilisi",
    "Erkek Almaz": "👨‍❤️‍👨 Erkek Koleksiyoncusu",
    "Kupa Almaz": "🍷 Kupa Canavarı",
    "El Almaz": "🤲 El Arsızı", 
    "Son İki": "🛑 Son Durak",
    "Koz (Tümü)": "♠️ Koz Baronu",
    "KING": "👑 King Ustası"
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

# =============================================================================
# 0. GÖRSEL AYARLAR VE CSS
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { 
            background: linear-gradient(135deg, #0e1117 0%, #1a1d2e 100%);
            background-attachment: fixed;
        }
        
        h1 { 
            color: #FFD700 !important; 
            text-align: center; 
            text-shadow: 2px 2px 8px rgba(255, 215, 0, 0.5); 
            font-family: 'Arial Black', sans-serif; 
            margin-bottom: 5px; 
            padding: 15px;
            background: linear-gradient(90deg, rgba(153,0,0,0.3) 0%, rgba(255,75,75,0.3) 100%);
            border-radius: 15px;
            border: 2px solid #FFD700;
        }
        
        h2, h3 { 
            color: #ff4b4b !important; 
            border-bottom: 3px solid #333; 
            padding-bottom: 10px;
            background: rgba(30, 30, 40, 0.7);
            padding: 10px;
            border-radius: 10px;
        }
        
        .stButton > button { 
            width: 100% !important; 
            background: linear-gradient(90deg, #990000 0%, #cc0000 100%) !important; 
            color: white !important; 
            border-radius: 10px !important; 
            border: 2px solid #FFD700 !important; 
            font-weight: bold !important;
            font-size: 16px !important;
            padding: 10px 20px !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover { 
            background: linear-gradient(90deg, #cc0000 0%, #ff0000 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.4) !important;
        }
        
        div[role="radiogroup"] { 
            background: linear-gradient(90deg, #262730 0%, #363740 100%); 
            padding: 15px; 
            border-radius: 15px; 
            border: 2px solid #444;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        div[role="radiogroup"] label { 
            color: white !important; 
            font-weight: bold !important; 
            font-size: 16px !important; 
            padding: 8px 20px !important;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            margin: 0 5px;
            transition: all 0.3s ease;
        }
        
        div[role="radiogroup"] label:hover { 
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetric"] { 
            background: linear-gradient(135deg, #262730 0%, #363740 100%);
            padding: 20px 15px !important;
            border-radius: 15px;
            border: 2px solid #444;
            box-shadow: 0 6px 10px rgba(0,0,0,0.4);
        }
        
        div[data-testid="stMetricValue"] { 
            color: #FFD700 !important;
            font-size: 32px !important;
            font-weight: bold !important;
        }
        
        div[data-testid="stMetricLabel"] { 
            color: #ff4b4b !important;
            font-size: 14px !important;
            font-weight: bold !important;
        }
        
        .stDataFrame { 
            border: 2px solid #444 !important; 
            border-radius: 10px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .stAlert { 
            border-radius: 10px !important;
            border: 2px solid !important;
        }
        
        .stSuccess { border-color: #28a745 !important; }
        .stWarning { border-color: #ffc107 !important; }
        .stError { border-color: #dc3545 !important; }
        .stInfo { border-color: #17a2b8 !important; }
        
        .custom-card {
            background: linear-gradient(135deg, rgba(40, 40, 60, 0.9) 0%, rgba(30, 30, 50, 0.9) 100%);
            border-radius: 15px;
            padding: 20px;
            border: 2px solid #444;
            margin: 10px 0;
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        
        .king-badge {
            background: linear-gradient(45deg, #FFD700, #FFA500);
            color: #000 !important;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin: 5px;
            border: 2px solid #fff;
        }
        
        .stats-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 5px solid #ff4b4b;
        }
        
        /* Scrollbar düzenleme */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1a2e;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(45deg, #990000, #ff4b4b);
            border-radius: 10px;
        }
        
        /* Hide Streamlit elements */
        header {visibility: hidden !important; height: 0 !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        footer {visibility: hidden !important;}
        section[data-testid="stSidebar"] {visibility: hidden !important;}
        .viewerBadge_container__1QSob { display: none !important; }
        .st-emotion-cache-1dp5vir {display: none !important;}
        
        .block-container { 
            padding-top: 2rem !important; 
            padding-bottom: 2rem !important;
            max-width: 1200px !important;
        }
        
        /* Animasyonlar */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fadeIn {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* Tab düzenlemeleri */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #262730;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            border: 1px solid #444;
            margin: 0 2px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #990000 !important;
            color: white !important;
            border-color: #FFD700 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# YARDIMCI FONKSİYONLAR - GRAFİK ve STİL
# =============================================================================

def apply_dataframe_styling(df, gradient_columns=None, cmap='RdYlGn'):
    """
    DataFrame'e stil uygula, matplotlib yoksa basit stil kullan
    """
    styled_df = df.style
    
    # Format ayarları
    if hasattr(df, 'columns'):
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'float']:
                styled_df = styled_df.format({col: '{:.1f}'})
            elif df[col].dtype in ['int64', 'int32', 'int']:
                styled_df = styled_df.format({col: '{:.0f}'})
    
    # Gradient uygula (sadece matplotlib varsa)
    if HAS_MATPLOTLIB and gradient_columns:
        try:
            styled_df = styled_df.background_gradient(
                subset=gradient_columns,
                cmap=cmap
            )
        except Exception as e:
            pass  # Gradienti uygulayamazsak geç
    
    return styled_df

def apply_simple_gradient(df, subset=None):
    """
    Basit renklendirme uygula (matplotlib olmadan)
    """
    def color_negative_red(val):
        try:
            num = float(val)
            if num < 0:
                color = '#ff6b6b'
            elif num > 0:
                color = '#06d6a0'
            else:
                color = 'white'
            return f'color: {color}; font-weight: bold;'
        except:
            return ''
    
    styled_df = df.style
    
    # Format ayarları
    if hasattr(df, 'columns'):
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'float']:
                styled_df = styled_df.format({col: '{:.1f}'})
            elif df[col].dtype in ['int64', 'int32', 'int']:
                styled_df = styled_df.format({col: '{:.0f}'})
    
    # Renklendirme uygula
    if subset:
        styled_df = styled_df.applymap(color_negative_red, subset=subset)
    
    return styled_df

def create_bar_chart(labels, values, title, colors=None):
    """Basit bar chart oluştur"""
    if not HAS_MATPLOTLIB:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if colors is None:
        colors = ['#28a745'] * len(labels)
    
    bars = ax.bar(range(len(labels)), values, color=colors)
    
    # Değerleri üzerine yaz
    for i, v in enumerate(values):
        ax.text(i, v + (max(values) * 0.01), f"{v:.1f}", 
               ha='center', va='bottom', fontweight='bold')
    
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel('Değer')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    return fig

def create_pie_chart(labels, sizes, title, colors=None):
    """Basit pie chart oluştur"""
    if not HAS_MATPLOTLIB:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    if colors is None:
        colors = plt.cm.Set3.colors
    
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
          startangle=90, wedgeprops={'edgecolor': 'white'})
    ax.set_title(title)
    
    return fig

def create_line_chart(x_values, y_values, title, color='#FFD700'):
    """Basit line chart oluştur"""
    if not HAS_MATPLOTLIB:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(x_values, y_values, marker='o', linewidth=3, color=color, markersize=8)
    ax.set_xlabel('Maç')
    ax.set_ylabel('Puan')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    # Noktaları renklendir
    for i, y in enumerate(y_values):
        point_color = '#28a745' if y >= 0 else '#dc3545'
        ax.plot(i, y, 'o', color=point_color, markersize=10)
    
    return fig

# =============================================================================
# 1. GOOGLE SHEETS - GELİŞTİRİLMİŞ
# =============================================================================

@st.cache_resource(show_spinner=False)
def get_google_sheet_client():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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
        if not wb:
            return [], []
            
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
    
    if not users_data: 
        return {}, {}, pd.DataFrame()

    for row in users_data:
        try:
            u_id = int(row.get('UserID', 0))
            u_name = str(row.get('Username', '')).strip()
            u_role = str(row.get('Role', 'user')).strip()
            u_kkd = int(row.get('KKD', STARTING_ELO))
            
            if u_name:  # Boş isimleri atla
                id_to_name[u_id] = u_name
                name_to_id[u_name] = u_id
                full_data.append({
                    'UserID': u_id,
                    'Username': u_name,
                    'Password': row.get('Password', ''),
                    'Role': u_role,
                    'KKD': u_kkd
                })
        except Exception as e:
            continue
    
    full_df = pd.DataFrame(full_data) if full_data else pd.DataFrame()
    return id_to_name, name_to_id, full_df

def save_match_to_sheet(header_row, data_rows, total_row):
    try:
        wb = get_sheet_by_url()
        if not wb:
            return False
            
        sheet_maclar = wb.worksheet("Maclar")
        
        # Maç başlığı ekle
        match_title = f"--- MAÇ: {st.session_state.get('current_match_name', 'Bilinmeyen Maç')} ({st.session_state.get('match_date', datetime.now().strftime('%d.%m.%Y'))}) ---"
        
        append_data = [
            [match_title, "", "", "", ""],
            header_row
        ]
        
        for dr in data_rows:
            append_data.append(dr)
        
        append_data.append(total_row)
        append_data.append(["", "", "", "", ""])  # Boşluk
        
        sheet_maclar.append_rows(append_data)
        
        # KKD güncelleme için önce cache'i temizle ve bekle
        clear_cache()
        time.sleep(2)  # Google Sheets'in güncellenmesi için bekle
        
        # Yeni verilere göre KKD'leri hesapla
        stats, _, _, _ = istatistikleri_hesapla()
        elo_dict = {}
        if stats:
            for uid, data in stats.items():
                elo_dict[uid] = data['kkd']
        
        # KKD'leri sheet'e yaz
        sheet_users = wb.worksheet("Users")
        all_data = sheet_users.get_all_values()
        
        if len(all_data) > 0:
            headers = all_data[0]
            try:
                uid_idx = headers.index("UserID")
                kkd_idx = headers.index("KKD")
                
                updated_data = [headers]
                for row in all_data[1:]:
                    if len(row) <= kkd_idx:
                        row.extend([""] * (kkd_idx - len(row) + 1))
                    
                    try:
                        current_id = int(row[uid_idx])
                        if current_id in elo_dict:
                            row[kkd_idx] = int(elo_dict[current_id])
                    except:
                        pass
                    updated_data.append(row)
                
                sheet_users.clear()
                sheet_users.update(updated_data)
            except ValueError:
                pass
        
        st.toast("✅ Maç başarıyla kaydedildi!", icon="✅")
        return True
        
    except Exception as e:
        st.error(f"Kayıt hatası: {str(e)}")
        return False

def update_user_in_sheet(old_username, new_username, password, role, delete=False):
    try:
        wb = get_sheet_by_url()
        if not wb:
            return False
            
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
            kkd_idx = headers.index("KKD")
        except ValueError:
            return False
        
        found_idx = -1
        for i, row in enumerate(all_data):
            if i == 0: 
                continue
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
                c_ids = []
                for row in all_data[1:]:
                    try:
                        c_ids.append(int(row[uid_idx]))
                    except:
                        c_ids.append(0)
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
        if not wb:
            return False
            
        sheet = wb.worksheet("Maclar")
        all_values = sheet.get_all_values()
        
        start = -1
        end = -1
        
        for i, row in enumerate(all_values):
            if row and str(row[0]).strip() == match_title.strip():
                start = i
                # Sonraki ayırıcıyı bul
                for j in range(i + 1, len(all_values)):
                    if all_values[j] and str(all_values[j][0]).startswith("--- MAÇ:"):
                        end = j
                        break
                if end == -1:
                    end = len(all_values)
                break
        
        if start != -1 and end != -1:
            sheet.delete_rows(start + 1, end)  # 1-based index
            clear_cache()
            st.toast("🗑️ Maç silindi!", icon="🗑️")
            return True
        return False
    except Exception as e:
        st.error(f"Maç silme hatası: {str(e)}")
        return False

# =============================================================================
# 2. İSTATİSTİK MOTORU - DÜZELTİLMİŞ ve HATA DÜZELTMELERİ
# =============================================================================

def calculate_expected_score(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 400))

def parse_date_from_header(header_str):
    try:
        date_str = header_str.split('(')[-1].split(')')[0].strip()
        return datetime.strptime(date_str, "%d.%m.%Y")
    except:
        return datetime.now()

def extract_id_from_cell(cell_value, name_to_id_map):
    if not cell_value:
        return None
    s = str(cell_value).strip()
    
    # (uid:123) formatını kontrol et
    match = re.search(r'\(uid:(\d+)\)', s)
    if match:
        return int(match.group(1))
    
    # Sadece isim kontrolü
    clean_name = s.split('(')[0].strip()
    if clean_name in name_to_id_map:
        return name_to_id_map[clean_name]
    
    return None

def istatistikleri_hesapla():
    id_to_name, name_to_id, _ = get_users_map()
    _, raw_data = fetch_all_data()
    
    if not raw_data:
        return None, None, None, None
    
    player_stats = {}
    elo_ratings = {}
    all_matches_chronological = []
    match_history_display = []
    
    current_match_ids = []
    current_match_data = None
    king_winner_id = None
    
    # Oyuncuların başlangıç KKD'lerini al
    for uid, name in id_to_name.items():
        player_stats[uid] = {
            "mac_sayisi": 0,
            "toplam_puan": 0,
            "pozitif_mac_sayisi": 0,
            "cezalar": {k: 0 for k in OYUN_KURALLARI},
            "ceza_puanlari": {k: 0 for k in OYUN_KURALLARI},
            "ceza_detay": defaultdict(int),
            "partnerler": {},
            "rekor_max": -9999,
            "rekor_min": 9999,
            "kkd": STARTING_ELO,
            "win_streak": 0,
            "loss_streak": 0,
            "max_win_streak": 0,
            "max_loss_streak": 0,
            "toplam_ceza_puani": 0,
            "toplam_koz_puani": 0,
            "king_sayisi": 0,
            "king_kazanma": 0,
            "son_5_mac": [],
            "aylik_performans": defaultdict(lambda: {'mac': 0, 'puan': 0})
        }
        elo_ratings[uid] = STARTING_ELO
    
    # Tüm maçları işle
    for row_idx, row in enumerate(raw_data):
        if not row or not any(row):
            continue
            
        first_cell = str(row[0]).strip()
        
        # Yeni maç başlangıcı
        if first_cell.startswith("--- MAÇ:"):
            if current_match_data and current_match_ids:
                # Önceki maçı tamamla
                all_matches_chronological.append(current_match_data)
            
            # Yeni maç başlat
            current_match_ids = []
            current_match_data = {
                "baslik": first_cell,
                "tarih": parse_date_from_header(first_cell),
                "skorlar": [],
                "ids": [],
                "ceza_detaylari": defaultdict(lambda: defaultdict(int)),
                "ceza_puan_detaylari": defaultdict(lambda: defaultdict(float)),
                "oyun_tipi": "Normal",
                "king_winner": None
            }
            king_winner_id = None
            continue
        
        # Eğer current_match_data yoksa atla
        if current_match_data is None:
            continue
        
        # Oyuncu listesi
        if first_cell == "OYUN TÜRÜ":
            for col_idx in range(1, len(row)):
                raw_val = row[col_idx]
                if not raw_val:
                    continue
                    
                p_id = extract_id_from_cell(raw_val, name_to_id)
                if p_id is not None and p_id in player_stats:
                    current_match_ids.append(p_id)
            
            current_match_data["ids"] = current_match_ids.copy()
            continue
        
        # King oyunu kontrolü
        is_king_game = "KING" in first_cell.upper()
        if is_king_game and current_match_ids:
            current_match_data["oyun_tipi"] = "KING"
            extracted = extract_id_from_cell(first_cell, name_to_id)
            if extracted is not None:
                king_winner_id = extracted
                current_match_data["king_winner"] = extracted
                if extracted in player_stats:
                    player_stats[extracted]["king_sayisi"] += 1
        
        # Oyun skorları
        base_name = first_cell.split(" #")[0].split(" (")[0]
        if (base_name in OYUN_KURALLARI or is_king_game) and current_match_ids and current_match_data:
            # current_match_data["skorlar"]'ın var olduğundan emin ol
            if "skorlar" not in current_match_data:
                current_match_data["skorlar"] = []
            current_match_data["skorlar"].append(row)
            
            for i, p_id in enumerate(current_match_ids):
                if i + 1 >= len(row):
                    continue
                    
                try:
                    score_val = row[i + 1]
                    if score_val in ["", " ", "-"]:
                        continue
                        
                    score = int(score_val)
                    
                    if p_id not in player_stats:
                        continue
                        
                    stats = player_stats[p_id]
                    
                    # King oyunu değilse ceza/koz hesapla
                    if not is_king_game:
                        if "Koz" in base_name:
                            stats["toplam_koz_puani"] += score
                        elif score < 0:
                            stats["toplam_ceza_puani"] += score
                            
                            # Ceza detayları
                            birim = OYUN_KURALLARI[base_name]['puan']
                            if birim != 0:
                                count = int(score / birim)
                                if count > 0:  # Sadece pozitif ceza sayıları
                                    stats["cezalar"][base_name] += count
                                    stats["ceza_puanlari"][base_name] += score
                                    stats["ceza_detay"][base_name] += count
                                    current_match_data["ceza_detaylari"][p_id][base_name] += count
                                    current_match_data["ceza_puan_detaylari"][p_id][base_name] += score
                    
                except (ValueError, TypeError):
                    continue
        
        # Toplam satırı
        if first_cell == "TOPLAM" and current_match_ids and current_match_data:
            current_match_data["toplamlar"] = row
            match_results = {}
            winners = []
            losers = []
            
            for i, p_id in enumerate(current_match_ids):
                try:
                    if i + 1 < len(row):
                        total_val = row[i + 1]
                        if total_val in ["", " ", "-"]:
                            continue
                        total = int(total_val)
                        match_results[p_id] = total
                        
                        # Kazanan/kaybeden belirle
                        if current_match_data["oyun_tipi"] == "KING":
                            is_win = (p_id == king_winner_id)
                        else:
                            is_win = (total >= 0)
                        
                        if is_win:
                            winners.append(p_id)
                        else:
                            losers.append(p_id)
                        
                        # İstatistikleri güncelle
                        if p_id in player_stats:
                            stats = player_stats[p_id]
                            stats["mac_sayisi"] += 1
                            stats["toplam_puan"] += total  # Toplam puanı burada ekle
                            
                            if is_win:
                                stats["pozitif_mac_sayisi"] += 1
                                if current_match_data["oyun_tipi"] == "KING":
                                    stats["king_kazanma"] += 1
                            
                            # Son 5 maç
                            stats["son_5_mac"].append({
                                "tarih": current_match_data["tarih"],
                                "puan": total,
                                "kazandi": is_win,
                                "tur": current_match_data["oyun_tipi"]
                            })
                            if len(stats["son_5_mac"]) > 5:
                                stats["son_5_mac"].pop(0)
                            
                            # Aylık performans - SADECE BURADA GÜNCELLE
                            month_key = current_match_data["tarih"].strftime("%Y-%m")
                            stats["aylik_performans"][month_key]["mac"] += 1
                            stats["aylik_performans"][month_key]["puan"] += total
                            
                except (ValueError, TypeError):
                    continue
            
            current_match_data["sonuclar"] = match_results
            current_match_data["kazananlar"] = winners
            current_match_data["kaybedenler"] = losers
            
            # ELO hesaplama
            match_elos = {pid: elo_ratings.get(pid, STARTING_ELO) for pid in current_match_ids}
            new_elos = {}
            
            for p_id in current_match_ids:
                my_elo = match_elos[p_id]
                my_score = match_results.get(p_id, 0)
                
                # King için özel kural
                if current_match_data["oyun_tipi"] == "KING":
                    actual = 1 if p_id == king_winner_id else 0
                else:
                    actual = 1 if my_score >= 0 else 0
                
                # Rakip ortalaması
                opponents = [match_elos[op] for op in current_match_ids if op != p_id]
                avg_opp = sum(opponents) / len(opponents) if opponents else STARTING_ELO
                
                # Beklenen skor
                exp = calculate_expected_score(my_elo, avg_opp)
                
                # ELO değişimi
                change = K_FACTOR * (actual - exp)
                
                # Solo kazanma/kaybetme bonusu
                if current_match_data["oyun_tipi"] == "KING":
                    if actual == 1 and len(winners) == 1:
                        change *= SOLO_MULTIPLIER
                    elif actual == 0 and len(losers) == 1:
                        change *= SOLO_MULTIPLIER
                else:
                    if actual == 1 and len(winners) == 1:
                        change *= SOLO_MULTIPLIER
                    elif actual == 0 and len(losers) == 1:
                        change *= SOLO_MULTIPLIER
                
                new_elos[p_id] = round(my_elo + change)
            
            # ELO'ları güncelle
            for pid, new_elo in new_elos.items():
                elo_ratings[pid] = new_elo
                if pid in player_stats:
                    player_stats[pid]["kkd"] = new_elo
            
            # Görüntü için kopya oluştur
            display_copy = current_match_data.copy()
            display_copy['oyuncular'] = [id_to_name.get(uid, f"Bilinmeyen({uid})") for uid in current_match_ids]
            display_copy['kazanan_isimler'] = [id_to_name.get(uid, f"Bilinmeyen({uid})") for uid in winners]
            display_copy['kaybeden_isimler'] = [id_to_name.get(uid, f"Bilinmeyen({uid})") for uid in losers]
            
            match_history_display.append(display_copy)
            all_matches_chronological.append(current_match_data)
            
            # Sıfırla
            current_match_ids = []
            current_match_data = None
    
    # Son maçı ekle (eğer varsa)
    if current_match_data and current_match_ids:
        all_matches_chronological.append(current_match_data)
    
    # Streak hesaplama - DÜZELTİLMİŞ
    all_matches_chronological.sort(key=lambda x: x['tarih'])
    
    # Her oyuncu için geçici streak durumu
    streak_tracker = {uid: {'current_win': 0, 'current_loss': 0} for uid in id_to_name.keys()}
    
    for match in all_matches_chronological:
        for p_id in match.get('ids', []):
            if p_id not in player_stats:
                continue
                
            is_winner = p_id in match.get('kazananlar', [])
            
            if is_winner:
                streak_tracker[p_id]['current_win'] += 1
                streak_tracker[p_id]['current_loss'] = 0
            else:
                streak_tracker[p_id]['current_loss'] += 1
                streak_tracker[p_id]['current_win'] = 0
            
            # Maksimum streak'leri güncelle
            if streak_tracker[p_id]['current_win'] > player_stats[p_id]['max_win_streak']:
                player_stats[p_id]['max_win_streak'] = streak_tracker[p_id]['current_win']
            
            if streak_tracker[p_id]['current_loss'] > player_stats[p_id]['max_loss_streak']:
                player_stats[p_id]['max_loss_streak'] = streak_tracker[p_id]['current_loss']
            
            # Mevcut streak'leri kaydet
            player_stats[p_id]['win_streak'] = streak_tracker[p_id]['current_win']
            player_stats[p_id]['loss_streak'] = streak_tracker[p_id]['current_loss']
    
    return player_stats, match_history_display, all_matches_chronological, id_to_name

# =============================================================================
# 4. UI BİLEŞENLERİ
# =============================================================================

def create_metric_card(title, value, delta=None, icon="📊"):
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"<h1 style='font-size: 2.5em; margin: 0;'>{icon}</h1>", unsafe_allow_html=True)
    with col2:
        st.metric(title, value, delta)

def create_player_card(player_name, stats, rank=1):
    with st.container():
        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: #FFD700;">#{rank} {player_name}</h3>
                    <p style="margin: 5px 0; color: #ccc;">KKD: <strong>{stats['kkd']}</strong></p>
                </div>
                <div style="text-align: right;">
                    <span style="background: #28a745; padding: 3px 10px; border-radius: 15px; font-weight: bold;">
                        {stats['pozitif_mac_sayisi']}/{stats['mac_sayisi']} (%{(stats['pozitif_mac_sayisi']/stats['mac_sayisi']*100 if stats['mac_sayisi'] > 0 else 0):.1f})
                    </span>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.9em;">
                    <span>🔥 Seri: {stats['win_streak']}</span>
                    <span>📊 Ortalama: {(stats['toplam_puan']/stats['mac_sayisi'] if stats['mac_sayisi'] > 0 else 0):.1f}</span>
                    <span>👑 King: {stats.get('king_kazanma', 0)}/{stats.get('king_sayisi', 0)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Logo/başlık
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #FFD700; font-size: 3em; margin-bottom: 10px;">👑</h1>
            <h1 style="color: #FFD700;">King İstatistik Kurumu</h1>
            <p style="color: #aaa;">Resmi Oyun İstatistik ve Takip Sistemi</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Giriş formu
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center;'>Sisteme Giriş</h3>", unsafe_allow_html=True)
            
            username = st.text_input("👤 Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
            password = st.text_input("🔒 Şifre", type="password", placeholder="Şifrenizi girin")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit = st.form_submit_button("🔓 Giriş Yap", type="primary", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Lütfen kullanıcı adı ve şifre girin!")
                    return
                
                _, _, users_df = get_users_map()
                if users_df.empty:
                    st.error("⚠️ HATA: Kullanıcı veritabanına ulaşılamıyor!")
                    return
                
                # Kullanıcı kontrolü
                user_match = users_df[
                    (users_df['Username'].astype(str).str.strip() == username.strip()) &
                    (users_df['Password'].astype(str).str.strip() == str(password).strip())
                ]
                
                if not user_match.empty:
                    user_data = user_match.iloc[0]
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = user_data['Role']
                    st.session_state["user_id"] = int(user_data['UserID'])
                    
                    # Hoş geldin mesajı
                    st.success(f"Hoş geldiniz, **{username}**! 🎉")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Hatalı kullanıcı adı veya şifre!")

def logout():
    st.session_state.clear()
    st.success("Çıkış yapıldı! 👋")
    time.sleep(1)
    st.rerun()

# =============================================================================
# 5. ANA SAYFALAR
# =============================================================================

def game_interface():
    st.markdown("<h2>🎮 Yeni Maç Başlat</h2>", unsafe_allow_html=True)
    
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session state kontrolleri
    if "game_active" not in st.session_state:
        st.session_state["game_active"] = False
    if "temp_df" not in st.session_state:
        st.session_state["temp_df"] = pd.DataFrame()
    if "game_index" not in st.session_state:
        st.session_state["game_index"] = 0
    if "king_mode" not in st.session_state:
        st.session_state["king_mode"] = False
    if "show_king_dialog" not in st.session_state:
        st.session_state["show_king_dialog"] = False
    
    if not st.session_state["game_active"]:
        st.info("Yeni bir maç başlatmak için aşağıdaki bilgileri doldurun.")
        
        # Form alanları
        col1, col2 = st.columns(2)
        with col1:
            match_name = st.text_input("🏷️ Maç İsmi:", "King_Macı", help="Maçın kaydedileceği isim")
            user_names = list(name_to_id.keys())
            
            if not user_names:
                st.error("Kayıtlı oyuncu bulunamadı!")
                return
                
        with col2:
            is_past = st.checkbox("📅 Geçmiş Maç?", help="Geçmiş bir tarih için maç eklemek için işaretleyin")
            if is_past:
                date_val = st.date_input("Tarih Seç", datetime.now() - timedelta(days=1))
            else:
                date_val = datetime.now()
        
        # Oyuncu seçimi
        st.subheader("👥 Kadro Seçimi (4 Kişi)")
        selected_names = st.multiselect(
            "Oyuncuları seçin:",
            user_names,
            max_selections=4,
            help="Tam olarak 4 oyuncu seçmelisiniz"
        )
        
        # Başlat butonu
        if len(selected_names) == 4:
            if st.button("🎯 Masayı Kur ve Oyunu Başlat", type="primary", use_container_width=True):
                st.session_state["temp_df"] = pd.DataFrame(columns=selected_names)
                st.session_state["current_match_name"] = match_name
                st.session_state["match_date"] = date_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected_names
                st.session_state["game_active"] = True
                st.session_state["game_index"] = 0
                st.session_state["king_mode"] = False
                st.session_state["show_king_dialog"] = False
                st.rerun()
        elif len(selected_names) > 0:
            st.warning(f"{len(selected_names)} oyuncu seçtiniz. Tam olarak 4 oyuncu seçmelisiniz.")
        
        return
    
    # Aktif oyun arayüzü
    df = st.session_state["temp_df"]
    players = st.session_state["players"]
    
    # Maç başlığı
    st.markdown(f"""
    <div class="custom-card">
        <h3 style="margin: 0; color: #FFD700;">🎮 Aktif Maç</h3>
        <p style="margin: 5px 0; color: #aaa;">
            <strong>Maç:</strong> {st.session_state['current_match_name']}<br>
            <strong>Tarih:</strong> {st.session_state['match_date']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Geçerli skor tablosu
    if not df.empty:
        st.subheader("📊 Mevcut Skorlar")
        
        # Formatlı DataFrame gösterimi
        display_df = df.copy()
        display_df.index = [idx if not pd.isna(idx) else "" for idx in display_df.index]
        
        styled_display_df = display_df.style.format("{:.0f}")
        
        if HAS_MATPLOTLIB:
            try:
                styled_display_df = styled_display_df.background_gradient(cmap="RdYlGn", axis=None)
            except:
                pass  # Gradienti uygulayamazsak geç
        
        styled_display_df = styled_display_df.set_properties(**{'text-align': 'center'})
        
        st.dataframe(
            styled_display_df,
            use_container_width=True,
            height=min(400, 50 + len(df) * 35)
        )
    
    # Toplamlar
    if not df.empty:
        totals = df.sum()
        st.subheader("🏁 Toplam Puanlar")
        
        cols = st.columns(4)
        for i, p in enumerate(players):
            with cols[i]:
                delta = None
                if len(df) > 1:
                    prev_total = df.iloc[:-1].sum().get(p, 0)
                    if prev_total != 0:
                        delta = f"{totals[p] - prev_total:+.0f}"
                
                st.metric(
                    label=p,
                    value=f"{totals[p]:.0f}",
                    delta=delta
                )
    
    # Oyun bitirme kontrolü - GELİŞTİRİLMİŞ
    # Tüm cezaların limitlerinin dolup dolmadığını kontrol et
    all_limits_reached = True
    for game_name, rules in OYUN_KURALLARI.items():
        played_count = len([x for x in df.index if game_name in str(x)])
        if played_count < rules['limit']:
            all_limits_reached = False
            break
    
    total_limit = sum([k['limit'] for k in OYUN_KURALLARI.values()])
    game_complete = len(df) >= total_limit or st.session_state["king_mode"] or all_limits_reached
    
    if game_complete:
        st.success("🏁 OYUN BİTTİ!")
        
        if st.button("💾 Maçı Arşivle ve Kaydet", type="primary", use_container_width=True):
            with st.spinner("Kaydediliyor..."):
                try:
                    # Header satırı
                    header_row = ["OYUN TÜRÜ"]
                    for p in players:
                        uid = name_to_id.get(p, "?")
                        header_row.append(f"{p} (uid:{uid})")
                    
                    # Data satırları
                    rows_to_save = []
                    for idx, row in df.iterrows():
                        row_data = [str(idx)]
                        for p in players:
                            row_data.append(int(row[p]))
                        rows_to_save.append(row_data)
                    
                    # Toplam satırı
                    total_row = ["TOPLAM"] + [int(totals[p]) for p in players]
                    
                    # Kaydet
                    if save_match_to_sheet(header_row, rows_to_save, total_row):
                        st.session_state["game_active"] = False
                        st.session_state["temp_df"] = pd.DataFrame()
                        st.rerun()
                except Exception as e:
                    st.error(f"Kayıt sırasında hata: {str(e)}")
        
        if st.button("🔄 Yeni Maç Başlat", use_container_width=True):
            st.session_state["game_active"] = False
            st.session_state["temp_df"] = pd.DataFrame()
            st.rerun()
        
        return
    
    # Oyun devam ediyor
    st.markdown("---")
    st.subheader("🎯 Sonraki Oyun")
    
    # King butonu
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("👑 KING YAPILDI", use_container_width=True, help="King yapıldıysa tıklayın"):
            st.session_state["show_king_dialog"] = True
    
    if st.session_state.get("show_king_dialog"):
        with st.container():
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.warning("👑 KING OYUNU")
            
            km = st.selectbox("Kim King Yaptı?", players)
            
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Onayla", type="primary"):
                    king_row = {p: 0 for p in players}
                    king_row[km] = 1  # King yapan için işaret
                    
                    new_row = pd.DataFrame([king_row], index=[f"👑 KING ({km})"])
                    st.session_state["temp_df"] = pd.concat([df, new_row])
                    st.session_state["king_mode"] = True
                    st.session_state["show_king_dialog"] = False
                    st.rerun()
            
            with col_no:
                if st.button("❌ İptal"):
                    st.session_state["show_king_dialog"] = False
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Normal oyun seçimi
    current_idx = st.session_state["game_index"]
    if current_idx >= len(OYUN_SIRALAMASI):
        current_idx = len(OYUN_SIRALAMASI) - 1
    
    selected_game = st.selectbox(
        "Oyun Türü Seçin:",
        OYUN_SIRALAMASI,
        index=current_idx,
        help="Sıradaki oyunu seçin"
    )
    
    rules = OYUN_KURALLARI[selected_game]
    
    # Oynanma sayısını hesapla
    played_count = len([x for x in df.index if selected_game in str(x)])
    remaining = rules['limit'] - played_count
    
    # Eğer bu oyun için limit dolduysa, kullanıcıyı uyar
    if remaining <= 0:
        st.error(f"❌ Bu oyun için limit doldu! Maksimum {rules['limit']} kez oynanabilir.")
        
        # Otomatik olarak sonraki oyuna geç
        if st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
            st.info("Sonraki oyun türüne geçiliyor...")
            next_idx = st.session_state["game_index"] + 1
            # Tüm oyunlar bitene kadar kontrol et
            while next_idx < len(OYUN_SIRALAMASI):
                next_game = OYUN_SIRALAMASI[next_idx]
                next_played = len([x for x in df.index if next_game in str(x)])
                if next_played < OYUN_KURALLARI[next_game]['limit']:
                    st.session_state["game_index"] = next_idx
                    st.rerun()
                next_idx += 1
        
        return
    
    st.info(f"""
    **Oyun Bilgileri:**
    - Kalan Hak: **{remaining}** / {rules['limit']}
    - Birim Puan: **{rules['puan']}**
    - Toplam Kart: **{rules['adet']}**
    - Maksimum Puan: **{rules['puan'] * rules['adet']}**
    """)
    
    # Oyuncu girişleri
    st.subheader("📝 Oyuncu Dağılımı")
    st.write(f"Toplam {rules['adet']} kartı oyuncular arasında dağıtın:")
    
    cols = st.columns(4)
    inputs = {}
    row_key = f"{selected_game}_{played_count}"
    
    # Toplam kontrolü için
    total_entered = 0
    
    for i, p in enumerate(players):
        with cols[i]:
            max_val = rules['adet']
            key = f"input_{row_key}_{p}"
            
            # Mevcut değeri al
            current_val = st.session_state.get(key, 0)
            
            # Input - ARTIK DOĞRUDAN ENTER'A BASMAKLA DEĞİŞMEYECEK
            val = st.number_input(
                p,
                min_value=0,
                max_value=max_val,
                value=current_val,
                key=key,
                help=f"{p} için kart sayısı (0-{max_val})",
                step=1
            )
            inputs[p] = val
            total_entered += val
    
    # Toplam kontrolü
    st.write(f"**Toplam Girilen:** {total_entered} / {rules['adet']}")
    
    if total_entered != rules['adet']:
        st.error(f"⚠️ Toplam kart sayısı {rules['adet']} olmalı! ({total_entered} girildi)")
        # Kaydet butonunu devre dışı bırak
        save_disabled = True
    else:
        # Oranları göster
        st.write("**Oranlar:**")
        ratio_cols = st.columns(4)
        for i, p in enumerate(players):
            with ratio_cols[i]:
                percentage = (inputs[p] / rules['adet']) * 100
                st.metric(p, f"%{percentage:.1f}")
        save_disabled = False
    
    # Kaydet butonları
    col_save, col_undo, col_reset = st.columns([2, 1, 1])
    
    with col_save:
        if st.button("💾 Skoru Kaydet", type="primary", use_container_width=True,
                    disabled=save_disabled):
            # Puanları hesapla
            row_data = {p: inputs[p] * rules['puan'] for p in players}
            
            # Yeni satır ekle
            new_row = pd.DataFrame([row_data], index=[f"{selected_game} #{played_count + 1}"])
            st.session_state["temp_df"] = pd.concat([df, new_row])
            
            # Inputları sıfırla
            for p in players:
                st.session_state.pop(f"input_{row_key}_{p}", None)
            
            # Limit kontrolü
            if played_count + 1 >= rules['limit']:
                # Sonraki oyunu bul
                next_idx = current_idx
                found_next = False
                for idx in range(current_idx + 1, len(OYUN_SIRALAMASI)):
                    next_game = OYUN_SIRALAMASI[idx]
                    next_played = len([x for x in st.session_state["temp_df"].index if next_game in str(x)])
                    if next_played < OYUN_KURALLARI[next_game]['limit']:
                        next_idx = idx
                        found_next = True
                        break
                
                if found_next:
                    st.session_state["game_index"] = next_idx
                else:
                    # Tüm oyunlar doldu
                    st.session_state["game_index"] = len(OYUN_SIRALAMASI) - 1
            
            st.rerun()
    
    with col_undo:
        if st.button("↩️ Son Hamleyi Sil", use_container_width=True):
            if not df.empty:
                st.session_state["temp_df"] = df.iloc[:-1]
                st.rerun()
    
    with col_reset:
        if st.button("🔄 Girişleri Sıfırla", use_container_width=True):
            for p in players:
                st.session_state.pop(f"input_{row_key}_{p}", None)
            st.rerun()

def kkd_leaderboard_interface():
    st.markdown("<h2>🏆 KKD Liderlik Tablosu</h2>", unsafe_allow_html=True)
    
    try:
        stats, _, _, id_map = istatistikleri_hesapla()
        if not stats:
            st.warning("Henüz yeterli veri bulunmuyor.")
            return
        
        # KKD sıralaması
        data_list = []
        for uid, s in stats.items():
            name = id_map.get(uid, f"Bilinmeyen({uid})")
            if s['mac_sayisi'] > 0:
                wr = (s['pozitif_mac_sayisi'] / s['mac_sayisi'] * 100)
                avg_score = s['toplam_puan'] / s['mac_sayisi']
                data_list.append({
                    "Oyuncu": name,
                    "Maç": s['mac_sayisi'],
                    "KKD": int(s['kkd']),
                    "Win Rate": wr,
                    "Ortalama": avg_score,
                    "Seri": s['win_streak'],
                    "King": s.get('king_kazanma', 0)
                })
        
        if not data_list:
            st.warning("Oyuncu verisi bulunamadı.")
            return
        
        df = pd.DataFrame(data_list).sort_values("KKD", ascending=False)
        
        # Filtreler
        col1, col2, col3 = st.columns(3)
        with col1:
            min_matches = st.slider("Minimum Maç Sayısı", 0, 100, 0, help="En az bu kadar maç yapanları göster")
        
        df_filtered = df[df['Maç'] >= min_matches]
        
        # Top 3 ödülleri
        if len(df_filtered) >= 3:
            st.markdown("""
            <div style="display: flex; justify-content: center; gap: 20px; margin: 30px 0;">
                <div style="text-align: center; background: linear-gradient(45deg, #FFD700, #FFA500); padding: 20px; border-radius: 15px; width: 120px;">
                    <h1 style="margin: 0; color: #000;">🥇</h1>
                    <h3 style="margin: 5px 0; color: #000;">{}</h3>
                    <p style="margin: 0; color: #000;">KKD: {}</p>
                </div>
                <div style="text-align: center; background: linear-gradient(45deg, #C0C0C0, #A0A0A0); padding: 20px; border-radius: 15px; width: 120px;">
                    <h1 style="margin: 0; color: #000;">🥈</h1>
                    <h3 style="margin: 5px 0; color: #000;">{}</h3>
                    <p style="margin: 0; color: #000;">KKD: {}</p>
                </div>
                <div style="text-align: center; background: linear-gradient(45deg, #CD7F32, #A0522D); padding: 20px; border-radius: 15px; width: 120px;">
                    <h1 style="margin: 0; color: #000;">🥉</h1>
                    <h3 style="margin: 5px 0; color: #000;">{}</h3>
                    <p style="margin: 0; color: #000;">KKD: {}</p>
                </div>
            </div>
            """.format(
                df_filtered.iloc[0]['Oyuncu'], df_filtered.iloc[0]['KKD'],
                df_filtered.iloc[1]['Oyuncu'], df_filtered.iloc[1]['KKD'],
                df_filtered.iloc[2]['Oyuncu'], df_filtered.iloc[2]['KKD']
            ), unsafe_allow_html=True)
        
        # Detaylı tablo
        st.subheader("📊 Detaylı Sıralama")
        
        # Formatlı gösterim
        if HAS_MATPLOTLIB:
            styled_df = df_filtered.style.format({
                'KKD': '{:.0f}',
                'Win Rate': '{:.1f}%',
                'Ortalama': '{:.1f}',
                'Seri': '{:.0f}',
                'King': '{:.0f}'
            })
            styled_df = styled_df.background_gradient(
                subset=['KKD', 'Win Rate', 'Ortalama'],
                cmap='RdYlGn'
            )
        else:
            styled_df = apply_simple_gradient(df_filtered, subset=['KKD', 'Win Rate', 'Ortalama'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=min(600, 150 + len(df_filtered) * 35)
        )
        
        # İstatistikler
        st.subheader("📈 Genel İstatistikler")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_kkd = df_filtered['KKD'].mean()
            st.metric("Ortalama KKD", f"{avg_kkd:.0f}")
        
        with col2:
            top_kkd = df_filtered['KKD'].max()
            st.metric("En Yüksek KKD", f"{top_kkd:.0f}")
        
        with col3:
            avg_wr = df_filtered['Win Rate'].mean()
            st.metric("Ortalama Win Rate", f"{avg_wr:.1f}%")
        
        with col4:
            total_matches = df_filtered['Maç'].sum()
            st.metric("Toplam Maç", f"{total_matches}")
    except Exception as e:
        st.error(f"KKD liderlik tablosu yüklenirken hata oluştu: {str(e)}")

def stats_interface():
    st.markdown("<h2>📊 İstatistik Merkezi</h2>", unsafe_allow_html=True)
    
    # Açıklama metni
    st.markdown("""
    <div class="custom-card">
        <h3>📖 Nasıl Kullanılır?</h3>
        <p>Bu sayfada oyun istatistiklerinizi detaylı olarak inceleyebilirsiniz.</p>
        <ul>
            <li><strong>🔥 Seriler</strong>: En uzun kazanma/kaybetme serilerinizi görün.</li>
            <li><strong>⚖️ Averaj</strong>: Oyuncuların ortalama puanlarını karşılaştırın.</li>
            <li><strong>📅 Rewind</strong>: Belirli bir dönemdeki performansı analiz edin.</li>
            <li><strong>🏆 Genel</strong>: Tüm istatistikleri bir arada görün.</li>
            <li><strong>📜 Arşiv</strong>: Geçmiş maçları inceleyin.</li>
            <li><strong>🚫 Cezalar</strong>: Ceza dağılımlarını ve karnelerini görün.</li>
            <li><strong>🤝 Komandit</strong>: Partnerlerinizle olan performansınızı analiz edin.</li>
        </ul>
        <p><em>Not: Tüm istatistikler gerçek zamanlı olarak güncellenmektedir.</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        stats, match_hist, chrono_matches, id_map = istatistikleri_hesapla()
        if not stats:
            st.warning("Henüz tamamlanmış maç verisi bulunmuyor.")
            return
        
        # Toplam maç sayısı: kronolojik maç sayısı (her toplantı 1 maç)
        total_matches_all = len(chrono_matches)
        
        # Ana veri yapısı
        rows = []
        for uid, s in stats.items():
            if s['mac_sayisi'] == 0:
                continue
                
            name = id_map.get(uid, f"Bilinmeyen({uid})")
            row = s.copy()
            row['Oyuncu'] = name
            row['averaj'] = row['toplam_puan'] / row['mac_sayisi'] if row['mac_sayisi'] > 0 else 0
            row['win_rate'] = (row['pozitif_mac_sayisi'] / row['mac_sayisi'] * 100) if row['mac_sayisi'] > 0 else 0
            row['king_orani'] = (row.get('king_kazanma', 0) / max(row.get('king_sayisi', 1), 1)) * 100
            
            # Ceza puanı oranları (toplam puan içindeki yüzdesi)
            total_score = row['toplam_puan']
            total_penalty = abs(row['toplam_ceza_puani'])
            row['ceza_orani'] = (total_penalty / abs(total_score) * 100) if total_score < 0 else 0
            
            rows.append(row)
        
        if not rows:
            st.warning("İşlenebilir veri bulunamadı.")
            return
        
        df_main = pd.DataFrame(rows).set_index("Oyuncu")
        
        # Sekmeler
        tabs = st.tabs([
            "🔥 Seriler", "⚖️ Averaj", "📅 Rewind", 
            "🏆 Genel", "📜 Arşiv", "🚫 Cezalar", "🤝 Komandit"
        ])
        
        # 1. SERİLER
        with tabs[0]:
            st.subheader("🔥 En Uzun Kazanma/Kaybetme Serileri")
            
            # En iyi seriler
            col1, col2 = st.columns(2)
            with col1:
                best_win = df_main['max_win_streak'].idxmax()
                best_win_val = df_main.loc[best_win, 'max_win_streak']
                st.success(f"""
                **🚀 En İyi Seri: {best_win}**
                {best_win_val} maç üst üste kazanma!
                """)
                
                # Aktif seriler
                st.subheader("⚡ Aktif Seriler")
                active_wins = df_main[df_main['win_streak'] > 0].sort_values('win_streak', ascending=False)
                if not active_wins.empty:
                    for player, row in active_wins.head(5).iterrows():
                        st.write(f"**{player}**: {int(row['win_streak'])} maç kazanma serisi")
            
            with col2:
                worst_loss = df_main['max_loss_streak'].idxmax()
                worst_loss_val = df_main.loc[worst_loss, 'max_loss_streak']
                st.error(f"""
                **💀 En Kötü Seri: {worst_loss}**
                {worst_loss_val} maç üst üste kaybetme!
                """)
                
                # Aktif kaybetme serileri
                active_losses = df_main[df_main['loss_streak'] > 0].sort_values('loss_streak', ascending=False)
                if not active_losses.empty:
                    for player, row in active_losses.head(5).iterrows():
                        st.write(f"**{player}**: {int(row['loss_streak'])} maç kaybetme serisi")
            
            # Detaylı tablo
            st.subheader("📊 Seri İstatistikleri")
            display_df = df_main[['win_streak', 'max_win_streak', 'loss_streak', 'max_loss_streak']].copy()
            display_df.columns = ['Aktif Kazanma', 'En İyi Seri', 'Aktif Kaybetme', 'En Kötü Seri']
            
            st.dataframe(
                display_df.sort_values('En İyi Seri', ascending=False).style.format("{:.0f}"),
                use_container_width=True
            )
        
        # 2. AVERAJ
        with tabs[1]:
            st.subheader("⚖️ Averaj Liderlik (Ortalama Puan)")
            
            # En iyi 5
            top_avg = df_main.sort_values('averaj', ascending=False).head(10)
            
            # Grafik
            if HAS_MATPLOTLIB and not top_avg.empty:
                try:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(range(len(top_avg)), top_avg['averaj'], 
                                 color=['#FFD700', '#C0C0C0', '#CD7F32'] + ['#28a745'] * 7)
                    
                    # Değerleri üzerine yaz
                    for i, (idx, row) in enumerate(top_avg.iterrows()):
                        ax.text(i, row['averaj'] + 0.5, f"{row['averaj']:.1f}", 
                               ha='center', va='bottom', fontweight='bold')
                    
                    ax.set_xticks(range(len(top_avg)))
                    ax.set_xticklabels(top_avg.index, rotation=45, ha='right')
                    ax.set_ylabel('Ortalama Puan')
                    ax.set_title('En Yüksek Ortalamaya Sahip Oyuncular')
                    ax.grid(True, alpha=0.3)
                    
                    st.pyplot(fig)
                    plt.close(fig)
                except Exception as e:
                    st.warning(f"Grafik oluşturulamadı: {str(e)}")
            
            # Detaylı tablo
            disp = df_main[['mac_sayisi', 'toplam_puan', 'averaj', 'win_rate']].sort_values('averaj', ascending=False)
            disp.columns = ["Maç Sayısı", "Toplam Puan", "Ortalama", "Win Rate %"]
            
            if HAS_MATPLOTLIB:
                styled_disp = disp.style.format({
                    'Ortalama': '{:.1f}',
                    'Win Rate %': '{:.1f}%'
                }).background_gradient(subset=['Ortalama'], cmap='RdYlGn')
            else:
                styled_disp = apply_simple_gradient(disp, subset=['Ortalama'])
            
            st.dataframe(
                styled_disp,
                use_container_width=True
            )
        
        # 3. REWIND
        with tabs[2]:
            st.subheader("📅 Zaman Tüneli - Dönemsel Analiz")
            
            if not chrono_matches:
                st.info("Tarih verisi bulunmuyor.")
                return
            
            # Filtreler
            dates = sorted([m['tarih'] for m in chrono_matches], reverse=True)
            years = sorted(list(set([d.year for d in dates])), reverse=True)
            months = list(range(1, 13))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_year = st.selectbox("Yıl Seç", ["Tümü"] + years, key="year_select")
            with col2:
                selected_month = st.selectbox("Ay Seç", ["Tümü"] + months, key="month_select")
            with col3:
                show_type = st.selectbox("Oyun Tipi", ["Tümü", "Normal", "KING"], key="type_select")
            
            # Maçları filtrele
            filtered_matches = []
            for m in chrono_matches:
                d = m['tarih']
                
                # Yıl filtresi
                if selected_year != "Tümü" and d.year != selected_year:
                    continue
                
                # Ay filtresi
                if selected_month != "Tümü" and d.month != selected_month:
                    continue
                
                # Oyun tipi filtresi
                if show_type != "Tümü" and m.get('oyun_tipi') != show_type:
                    continue
                
                filtered_matches.append(m)
            
            if not filtered_matches:
                st.warning("Seçilen kriterlere uygun maç bulunamadı.")
                return
            
            # İstatistikleri hesapla
            period_stats = {}
            
            for match in filtered_matches:
                # Tarih için ay-yıl anahtarı
                month_key = match['tarih'].strftime("%Y-%m")
                
                for uid in match.get('ids', []):
                    if uid not in id_map:
                        continue
                        
                    if uid not in period_stats:
                        period_stats[uid] = {
                            'isim': id_map[uid],
                            'matches': 0,
                            'wins': 0,
                            'total_score': 0,
                            'cezalar': defaultdict(int),
                            'ceza_puanlari': defaultdict(float),
                            'king_wins': 0,
                            'king_games': 0,
                            'monthly': defaultdict(lambda: {'matches': 0, 'wins': 0, 'score': 0})
                        }
                    
                    ps = period_stats[uid]
                    ps['matches'] += 1
                    
                    # Skor ve kazanma durumu
                    score = match.get('sonuclar', {}).get(uid, 0)
                    ps['total_score'] += score
                    
                    is_winner = uid in match.get('kazananlar', [])
                    if is_winner:
                        ps['wins'] += 1
                    
                    # King istatistikleri
                    if match.get('oyun_tipi') == 'KING':
                        ps['king_games'] += 1
                        if uid == match.get('king_winner'):
                            ps['king_wins'] += 1
                    
                    # Ceza istatistikleri (puan bazında)
                    if uid in match.get('ceza_puan_detaylari', {}):
                        for ceza_type, puan in match['ceza_puan_detaylari'][uid].items():
                            ps['ceza_puanlari'][ceza_type] += puan
                            # Sayı olarak da tutalım
                            if ceza_type in match.get('ceza_detaylari', {}).get(uid, {}):
                                ps['cezalar'][ceza_type] += match['ceza_detaylari'][uid][ceza_type]
                    
                    # Aylık istatistikler
                    ps['monthly'][month_key]['matches'] += 1
                    ps['monthly'][month_key]['score'] += score
                    if is_winner:
                        ps['monthly'][month_key]['wins'] += 1
            
            # En iyi performans
            if period_stats:
                # En çok kazanan
                most_wins = max(period_stats.items(), key=lambda x: x[1]['wins'])
                best_player = most_wins[1]['isim']
                win_rate = (most_wins[1]['wins'] / most_wins[1]['matches'] * 100) if most_wins[1]['matches'] > 0 else 0
                
                st.success(f"""
                **👑 Dönem Kralı: {best_player}**
                {most_wins[1]['wins']} kazanma / {most_wins[1]['matches']} maç (%{win_rate:.1f})
                """)
                
                # En çok ceza puanı alan (toplam ceza puanı)
                most_penalty_points = max(period_stats.items(), 
                                        key=lambda x: sum(x[1]['ceza_puanlari'].values()))
                worst_player = most_penalty_points[1]['isim']
                total_penalty_points = sum(most_penalty_points[1]['ceza_puanlari'].values())
                
                st.error(f"""
                **🚫 Ceza Kralı: {worst_player}**
                Toplam {total_penalty_points:.0f} ceza puanı
                """)
                
                # Her ceza türü için en çok puan alanı bul
                st.subheader("🏆 Ceza Türü Liderleri")
                
                # Tüm ceza türlerini topla
                all_penalty_types = set()
                for data in period_stats.values():
                    all_penalty_types.update(data['ceza_puanlari'].keys())
                
                if all_penalty_types:
                    # Her ceza türü için en çok puan alanı bul
                    penalty_leaders = {}
                    for ceza_type in all_penalty_types:
                        leader = max(period_stats.items(), 
                                   key=lambda x: x[1]['ceza_puanlari'].get(ceza_type, 0))
                        penalty_leaders[ceza_type] = {
                            'oyuncu': leader[1]['isim'],
                            'puan': leader[1]['ceza_puanlari'].get(ceza_type, 0)
                        }
                    
                    # 3 kolon halinde göster
                    cols = st.columns(3)
                    for i, (ceza_type, leader_info) in enumerate(penalty_leaders.items()):
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div class="stats-card">
                                <h4>{ceza_type}</h4>
                                <p><strong>{leader_info['oyuncu']}</strong></p>
                                <p>{leader_info['puan']:.0f} puan</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Ceza dağılımı (puan bazında)
                st.subheader("🚫 Ceza Dağılımı (Puan)")
                
                # Tüm cezaları topla (puan)
                all_penalties = defaultdict(float)
                for uid, data in period_stats.items():
                    for ceza_type, puan in data['ceza_puanlari'].items():
                        all_penalties[ceza_type] += puan
                
                if all_penalties:
                    # Tablo olarak göster
                    penalty_df = pd.DataFrame({
                        'Ceza Türü': list(all_penalties.keys()),
                        'Toplam Puan': list(all_penalties.values())
                    }).sort_values('Toplam Puan')
                    
                    st.dataframe(penalty_df, use_container_width=True)
                    
                    # Grafik (matplotlib varsa)
                    if HAS_MATPLOTLIB and all_penalties:
                        try:
                            fig, ax = plt.subplots(figsize=(10, 6))
                            labels = list(all_penalties.keys())
                            values = list(all_penalties.values())
                            colors = [OYUN_KURALLARI.get(k, {}).get('renk', '#FF0000') for k in labels]
                            
                            bars = ax.bar(labels, values, color=colors)
                            ax.set_xticks(range(len(labels)))
                            ax.set_xticklabels(labels, rotation=45, ha='right')
                            ax.set_ylabel('Toplam Ceza Puanı')
                            ax.set_title('Ceza Türlerine Göre Toplam Ceza Puanı Dağılımı')
                            ax.grid(True, alpha=0.3)
                            
                            st.pyplot(fig)
                            plt.close(fig)
                        except Exception as e:
                            st.warning(f"Grafik oluşturulamadı: {str(e)}")
                
                # Detaylı tablo
                st.subheader("📊 Dönemsel Performans")
                
                table_data = []
                for uid, data in period_stats.items():
                    if data['matches'] > 0:
                        win_rate = (data['wins'] / data['matches']) * 100
                        avg_score = data['total_score'] / data['matches']
                        total_penalty_points = sum(data['ceza_puanlari'].values())
                        
                        table_data.append({
                            'Oyuncu': data['isim'],
                            'Maç': data['matches'],
                            'Kazanma': data['wins'],
                            'Win Rate %': win_rate,
                            'Ortalama': avg_score,
                            'Toplam Ceza Puanı': total_penalty_points,
                            'King Kazanma': data['king_wins']
                        })
                
                if table_data:
                    df_period = pd.DataFrame(table_data).sort_values('Win Rate %', ascending=False)
                    
                    if HAS_MATPLOTLIB:
                        styled_df = df_period.style.format({
                            'Win Rate %': '{:.1f}%',
                            'Ortalama': '{:.1f}',
                            'Toplam Ceza Puanı': '{:.0f}'
                        }).background_gradient(subset=['Win Rate %', 'Ortalama'], cmap='RdYlGn')
                    else:
                        styled_df = apply_simple_gradient(df_period, subset=['Win Rate %', 'Ortalama'])
                    
                    st.dataframe(
                        styled_df,
                        use_container_width=True
                    )
        
        # 4. GENEL
        with tabs[3]:
            st.subheader("🏆 Genel İstatistikler")
            
            # Özet metrikler
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Toplam Maç", total_matches_all)
            
            with col2:
                total_players = len(df_main)
                st.metric("Toplam Oyuncu", total_players)
            
            with col3:
                if total_matches_all > 0:
                    total_wins = df_main['pozitif_mac_sayisi'].sum()
                    # Her maçta 4 oyuncu var, her maçta 2 kazanan 2 kaybeden olabilir (KING hariç)
                    avg_wins = (total_wins / (total_matches_all * 2)) * 100  # Yaklaşık hesaplama
                    st.metric("Genel Win Rate", f"{avg_wins:.1f}%")
                else:
                    st.metric("Genel Win Rate", "0%")
            
            with col4:
                total_kings = df_main['king_sayisi'].sum()
                st.metric("Toplam King", total_kings)
            
            # En iyiler
            st.subheader("🎖️ Ödüller")
            
            awards_cols = st.columns(3)
            
            with awards_cols[0]:
                # En yüksek KKD
                top_kkd = df_main.nlargest(1, 'kkd')
                if not top_kkd.empty:
                    player = top_kkd.index[0]
                    kkd = top_kkd.iloc[0]['kkd']
                    st.markdown(f"""
                    <div class="custom-card">
                        <h4>🥇 En Yüksek KKD</h4>
                        <h2 style="color: #FFD700;">{player}</h2>
                        <p>KKD: {int(kkd)}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with awards_cols[1]:
                # En çok kazanan
                most_wins = df_main.nlargest(1, 'pozitif_mac_sayisi')
                if not most_wins.empty:
                    player = most_wins.index[0]
                    wins = most_wins.iloc[0]['pozitif_mac_sayisi']
                    total = most_wins.iloc[0]['mac_sayisi']
                    st.markdown(f"""
                    <div class="custom-card">
                        <h4>👑 En Çok Kazanan</h4>
                        <h2 style="color: #FFD700;">{player}</h2>
                        <p>{wins} kazanma / {total} maç</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with awards_cols[2]:
                # En iyi King
                king_players = df_main[df_main['king_sayisi'] > 0].copy()
                if not king_players.empty:
                    king_players['king_rate'] = king_players['king_kazanma'] / king_players['king_sayisi']
                    best_king = king_players.nlargest(1, 'king_rate')
                    if not best_king.empty:
                        player = best_king.index[0]
                        rate = best_king.iloc[0]['king_rate'] * 100
                        st.markdown(f"""
                        <div class="custom-card">
                            <h4>🤴 King Ustası</h4>
                            <h2 style="color: #FFD700;">{player}</h2>
                            <p>%{rate:.1f} King kazanma</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Detaylı tablo
            st.subheader("📈 Tüm İstatistikler")
            
            display_cols = ['mac_sayisi', 'pozitif_mac_sayisi', 'toplam_puan', 'kkd', 
                           'averaj', 'win_streak', 'king_kazanma', 'toplam_ceza_puani', 'toplam_koz_puani']
            
            display_df = df_main[display_cols].copy()
            display_df.columns = ['Maç', 'Kazanma', 'Toplam Puan', 'KKD', 
                                 'Ortalama', 'Aktif Seri', 'King Kazanma', 'Toplam Ceza', 'Toplam Koz']
            
            # Sıralama seçeneği
            sort_by = st.selectbox("Sıralama Ölçütü", 
                                  ['KKD', 'Ortalama', 'Maç', 'Kazanma', 'Aktif Seri'])
            
            sorted_df = display_df.sort_values(sort_by, ascending=False)
            
            if HAS_MATPLOTLIB:
                styled_df = sorted_df.style.format({
                    'KKD': '{:.0f}',
                    'Ortalama': '{:.1f}',
                    'Toplam Ceza': '{:.0f}',
                    'Toplam Koz': '{:.0f}'
                }).background_gradient(subset=['KKD', 'Ortalama'], cmap='RdYlGn')
            else:
                styled_df = apply_simple_gradient(sorted_df, subset=['KKD', 'Ortalama'])
            
            st.dataframe(
                styled_df,
                use_container_width=True
            )
        
        # 5. ARŞİV
        with tabs[4]:
            st.subheader("📜 Maç Arşivi")
            
            if not match_hist:
                st.info("Henüz maç kaydı bulunmuyor.")
                return
            
            # Maç seçimi
            match_titles = [m['baslik'].replace("--- MAÇ: ", "").replace(" ---", "") 
                           for m in match_hist[::-1]]
            
            selected_match = st.selectbox("Maç Seçin:", match_titles)
            
            # Seçilen maçı bul
            selected_full = f"--- MAÇ: {selected_match} ---"
            found_match = next((m for m in match_hist if m['baslik'] == selected_full), None)
            
            if found_match:
                # Maç bilgileri
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Tarih", found_match['tarih'].strftime("%d.%m.%Y"))
                
                with col2:
                    st.metric("Oyun Tipi", found_match.get('oyun_tipi', 'Normal'))
                
                with col3:
                    if found_match.get('oyun_tipi') == 'KING':
                        winner = found_match.get('king_winner')
                        if winner:
                            winner_name = id_map.get(winner, 'Bilinmeyen')
                            st.metric("King Kazanan", winner_name)
                
                # Skor tablosu
                st.subheader("📊 Maç Detayları")
                
                # Skorları DataFrame'e dönüştür
                score_rows = []
                for score_row in found_match.get('skorlar', []):
                    row_dict = {'OYUN': score_row[0]}
                    for i, player in enumerate(found_match.get('oyuncular', [])):
                        if i + 1 < len(score_row):
                            row_dict[player] = score_row[i + 1]
                    score_rows.append(row_dict)
                
                if score_rows:
                    scores_df = pd.DataFrame(score_rows)
                    
                    # Toplam satırını ekle
                    if 'toplamlar' in found_match:
                        total_row = {'OYUN': 'TOPLAM'}
                        for i, player in enumerate(found_match.get('oyuncular', [])):
                            if i + 1 < len(found_match['toplamlar']):
                                total_row[player] = found_match['toplamlar'][i + 1]
                        
                        scores_df = pd.concat([scores_df, pd.DataFrame([total_row])], ignore_index=True)
                    
                    # Renklendirme
                    def color_negative_red(val):
                        try:
                            num = float(val)
                            if num < 0:
                                color = '#ff6b6b'
                            elif num > 0:
                                color = '#06d6a0'
                            else:
                                color = 'white'
                            return f'color: {color}; font-weight: bold;'
                        except:
                            return ''
                    
                    st.dataframe(
                        scores_df.style.applymap(color_negative_red, subset=found_match.get('oyuncular', []))
                        .set_properties(**{'text-align': 'center'}),
                        use_container_width=True
                    )
                
                # Ceza detayları
                if found_match.get('ceza_puan_detaylari'):
                    st.subheader("🚫 Ceza Detayları (Puan)")
                    
                    penalty_data = []
                    for uid, penalties in found_match['ceza_puan_detaylari'].items():
                        player_name = id_map.get(uid, f"Bilinmeyen({uid})")
                        for ceza_type, puan in penalties.items():
                            if puan < 0:  # Sadece ceza puanları
                                penalty_data.append({
                                    'Oyuncu': player_name,
                                    'Ceza Türü': ceza_type,
                                    'Puan': puan
                                })
                    
                    if penalty_data:
                        penalty_df = pd.DataFrame(penalty_data)
                        st.dataframe(
                            penalty_df.sort_values('Puan').style.format({
                                'Puan': '{:.0f}'
                            }),
                            use_container_width=True
                        )
        
        # 6. CEZALAR
        with tabs[5]:
            st.subheader("🚫 Ceza İstatistikleri (Puan Bazında)")
            
            # Ceza verilerini hazırla (puan bazında)
            ceza_data = []
            
            for uid, s in stats.items():
                if s['mac_sayisi'] == 0:
                    continue
                    
                player_name = id_map.get(uid, f"Bilinmeyen({uid})")
                
                # Toplam ceza puanı
                total_penalty_points = sum(s['ceza_puanlari'].values())
                
                if total_penalty_points < 0 or True:  # Tüm oyuncuları göster
                    row = {'Oyuncu': player_name, 'Maç': s['mac_sayisi'], 'Toplam Ceza Puanı': total_penalty_points}
                    
                    # Her ceza türü için puan
                    for ceza_type in OYUN_KURALLARI:
                        puan = s['ceza_puanlari'].get(ceza_type, 0)
                        # Maç başına ortalama
                        avg_per_match = puan / s['mac_sayisi'] if s['mac_sayisi'] > 0 else 0
                        row[ceza_type] = f"{puan:.0f} ({avg_per_match:.1f})"
                    
                    ceza_data.append(row)
            
            if ceza_data:
                ceza_df = pd.DataFrame(ceza_data).set_index('Oyuncu')
                
                # En çok ceza puanı alanlar
                st.subheader("🏆 Ceza Puanı Liderleri")
                
                top_penalty = ceza_df.nsmallest(5, 'Toplam Ceza Puanı')[['Toplam Ceza Puanı', 'Maç']]
                
                if HAS_MATPLOTLIB:
                    styled_top_penalty = top_penalty.style.background_gradient(subset=['Toplam Ceza Puanı'], cmap='Reds')
                else:
                    styled_top_penalty = top_penalty.style
                
                st.dataframe(
                    styled_top_penalty,
                    use_container_width=True
                )
                
                # Ceza türlerine göre dağılım (puan)
                st.subheader("📊 Ceza Türü Dağılımı (Puan)")
                
                # Grafik için veri hazırla
                penalty_types = []
                penalty_points = []
                
                for uid, s in stats.items():
                    if s['mac_sayisi'] > 0:
                        for ceza_type, puan in s['ceza_puanlari'].items():
                            if puan < 0:  # Sadece negatif cezalar
                                penalty_types.append(ceza_type)
                                penalty_points.append(abs(puan))  # Mutlak değer
                
                if penalty_points and HAS_MATPLOTLIB:
                    try:
                        # Bar chart
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # Benzersiz türleri grupla ve toplam puanları hesapla
                        unique_types = {}
                        for i, ceza_type in enumerate(penalty_types):
                            if ceza_type not in unique_types:
                                unique_types[ceza_type] = 0
                            unique_types[ceza_type] += penalty_points[i]
                        
                        if unique_types:
                            labels = list(unique_types.keys())
                            values = list(unique_types.values())
                            
                            bars = ax.bar(labels, values, 
                                         color=[OYUN_KURALLARI.get(t, {}).get('renk', '#FF0000') for t in labels])
                            
                            # Değerleri üzerine yaz
                            for i, (t, p) in enumerate(zip(labels, values)):
                                ax.text(i, p + 0.5, f"{p:.0f}", ha='center', va='bottom', fontweight='bold')
                            
                            ax.set_xticks(range(len(labels)))
                            ax.set_xticklabels(labels, rotation=45, ha='right')
                            ax.set_ylabel('Toplam Ceza Puanı')
                            ax.set_title('Ceza Türlerine Göre Toplam Ceza Puanı Dağılımı')
                            ax.grid(True, alpha=0.3)
                            
                            st.pyplot(fig)
                            plt.close(fig)
                    except Exception as e:
                        st.warning(f"Grafik oluşturulamadı: {str(e)}")
                
                # Detaylı tablo
                st.subheader("📋 Detaylı Ceza Karnesi (Puan)")
                
                # Sadece sayısal değerleri göster
                display_cols = ['Maç', 'Toplam Ceza Puanı'] + list(OYUN_KURALLARI.keys())
                if set(display_cols).issubset(ceza_df.columns):
                    display_df = ceza_df[display_cols].sort_values('Toplam Ceza Puanı')
                    
                    if HAS_MATPLOTLIB:
                        styled_display_df = display_df.style.background_gradient(subset=['Toplam Ceza Puanı'], cmap='Reds')
                    else:
                        styled_display_df = display_df.style
                    
                    st.dataframe(
                        styled_display_df,
                        use_container_width=True,
                        height=min(600, 150 + len(display_df) * 35)
                    )
                else:
                    st.warning("Ceza verileri eksik veya hatalı.")
            else:
                st.info("Henüz ceza kaydı bulunmuyor.")
        
        # 7. KOMANDİT
        with tabs[6]:
            st.subheader("🤝 Partner Performans Analizi")
            
            current_user_id = st.session_state.get("user_id")
            
            if current_user_id:
                if current_user_id in stats:
                    user_stats = stats[current_user_id]
                    user_name = id_map.get(current_user_id, "Bilinmeyen")
                    
                    st.markdown(f"**{user_name}** için partner analizi:")
                    
                    # Partner verilerini oluştur (mevcut maçlardan)
                    partner_data = []
                    
                    # Tüm maçları tara ve partnerleri bul
                    for match in chrono_matches:
                        if current_user_id in match.get('ids', []):
                            # Bu maçtaki diğer oyuncuları bul
                            for partner_id in match['ids']:
                                if partner_id != current_user_id:
                                    partner_name = id_map.get(partner_id, f"Bilinmeyen({partner_id})")
                                    
                                    # Partnerin bu maçtaki durumunu kontrol et
                                    is_user_winner = current_user_id in match.get('kazananlar', [])
                                    is_partner_winner = partner_id in match.get('kazananlar', [])
                                    
                                    # Partneri bul veya oluştur
                                    found = False
                                    for pd in partner_data:
                                        if pd['Partner'] == partner_name:
                                            pd['Birlikte Maç'] += 1
                                            if is_user_winner and is_partner_winner:
                                                pd['Birlikte Kazanma'] += 1
                                            found = True
                                            break
                                    
                                    if not found:
                                        partner_data.append({
                                            'Partner': partner_name,
                                            'Birlikte Maç': 1,
                                            'Birlikte Kazanma': 1 if is_user_winner and is_partner_winner else 0,
                                            'Win Rate %': 0,
                                            'Başarı': 'Orta'
                                        })
                    
                    if partner_data:
                        # Win rate hesapla
                        for pd in partner_data:
                            if pd['Birlikte Maç'] > 0:
                                pd['Win Rate %'] = (pd['Birlikte Kazanma'] / pd['Birlikte Maç']) * 100
                                if pd['Win Rate %'] > 60:
                                    pd['Başarı'] = 'Yüksek'
                                elif pd['Win Rate %'] > 40:
                                    pd['Başarı'] = 'Orta'
                                else:
                                    pd['Başarı'] = 'Düşük'
                        
                        partner_df = pd.DataFrame(partner_data).sort_values('Win Rate %', ascending=False)
                        
                        # En iyi partner
                        if not partner_df.empty:
                            best_partner = partner_df.iloc[0]
                            st.success(f"""
                            **🤝 En İyi Partner: {best_partner['Partner']}**
                            {best_partner['Birlikte Kazanma']} kazanma / {best_partner['Birlikte Maç']} maç
                            (%{best_partner['Win Rate %']:.1f} başarı)
                            """)
                            
                            # Tablo
                            if HAS_MATPLOTLIB:
                                styled_partner_df = partner_df.style.format({
                                    'Win Rate %': '{:.1f}%'
                                }).background_gradient(subset=['Win Rate %'], cmap='RdYlGn')
                            else:
                                styled_partner_df = apply_simple_gradient(partner_df, subset=['Win Rate %'])
                            
                            st.dataframe(
                                styled_partner_df,
                                use_container_width=True
                            )
                            
                            # Partner grafiği
                            if HAS_MATPLOTLIB and not partner_df.empty:
                                try:
                                    fig, ax = plt.subplots(figsize=(10, 6))
                                    
                                    x_pos = range(len(partner_df))
                                    colors = ['#FFD700', '#C0C0C0', '#CD7F32'] + ['#28a745'] * (len(partner_df) - 3)
                                    
                                    bars = ax.bar(x_pos, partner_df['Win Rate %'], color=colors)
                                    
                                    for i, (idx, row) in enumerate(partner_df.iterrows()):
                                        ax.text(i, row['Win Rate %'] + 1, f"{row['Win Rate %']:.1f}%", 
                                               ha='center', va='bottom', fontweight='bold')
                                    
                                    ax.set_xticks(x_pos)
                                    ax.set_xticklabels(partner_df['Partner'], rotation=45, ha='right')
                                    ax.set_ylabel('Win Rate %')
                                    ax.set_title('Partnerlere Göre Win Rate')
                                    ax.grid(True, alpha=0.3)
                                    
                                    st.pyplot(fig)
                                    plt.close(fig)
                                except Exception as e:
                                    st.warning(f"Grafik oluşturulamadı: {str(e)}")
                        else:
                            st.info("Henüz partner verisi bulunmuyor.")
                    else:
                        st.info("Henüz partner verisi bulunmuyor. Daha fazla maç oynadıkça burada görünecektir.")
                else:
                    st.info("Henüz istatistiğiniz bulunmuyor. Maç oynadıkça burada görünecektir.")
            else:
                st.warning("Partner analizi için giriş yapmalısınız.")
    except Exception as e:
        st.error(f"İstatistikler yüklenirken hata oluştu: {str(e)}")
        st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    
    try:
        stats, match_history, _, id_map = istatistikleri_hesapla()
        uid = st.session_state.get("user_id")
        
        if uid in stats:
            s = stats[uid]
            player_name = id_map.get(uid, "Bilinmeyen")
            
            # Temel metrikler
            col1, col2, col3 = st.columns(3)
            
            with col1:
                win_rate = (s['pozitif_mac_sayisi'] / s['mac_sayisi'] * 100) if s['mac_sayisi'] > 0 else 0
                st.metric("Win Rate", f"%{win_rate:.1f}")
            
            with col2:
                st.metric("KKD", int(s['kkd']))
            
            with col3:
                st.metric("Aktif Seri", s['win_streak'])
            
            # Detaylı metrikler
            col4, col5, col6 = st.columns(3)
            
            with col4:
                avg_score = s['toplam_puan'] / s['mac_sayisi'] if s['mac_sayisi'] > 0 else 0
                st.metric("Ortalama Puan", f"{avg_score:.1f}")
            
            with col5:
                king_rate = (s.get('king_kazanma', 0) / max(s.get('king_sayisi', 1), 1)) * 100
                st.metric("King Başarı", f"%{king_rate:.1f}")
            
            with col6:
                penalty_avg = s['toplam_ceza_puani'] / s['mac_sayisi'] if s['mac_sayisi'] > 0 else 0
                st.metric("Ort. Ceza", f"{penalty_avg:.1f}")
            
            # Son 5 maç
            st.subheader("📈 Son 5 Maç")
            
            if s.get('son_5_mac'):
                recent_matches = []
                for match in s['son_5_mac'][-5:]:
                    recent_matches.append({
                        'Tarih': match['tarih'].strftime("%d.%m"),
                        'Puan': match['puan'],
                        'Sonuç': '✅' if match['kazandi'] else '❌',
                        'Tur': match['tur']
                    })
                
                recent_df = pd.DataFrame(recent_matches[::-1])
                st.dataframe(recent_df, use_container_width=True)
                
                # Form grafiği
                scores = [m['puan'] for m in s['son_5_mac'][-5:]]
                if scores and HAS_MATPLOTLIB:
                    try:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(range(1, len(scores) + 1), scores, 
                               marker='o', linewidth=3, color='#FFD700', markersize=10)
                        
                        # Noktaları renklendir
                        for i, score in enumerate(scores):
                            color = '#28a745' if score >= 0 else '#dc3545'
                            ax.plot(i + 1, score, 'o', color=color, markersize=12)
                        
                        ax.set_xlabel('Maç')
                        ax.set_ylabel('Puan')
                        ax.set_title('Son 5 Maç Form Grafiği')
                        ax.grid(True, alpha=0.3)
                        
                        st.pyplot(fig)
                        plt.close(fig)
                    except Exception as e:
                        st.warning(f"Grafik oluşturulamadı: {str(e)}")
            
            # Aylık performans - DÜZELTİLDİ
            st.subheader("📅 Aylık Performans")
            
            if s.get('aylik_performans'):
                monthly_data = []
                for month, data in s['aylik_performans'].items():
                    if data['mac'] > 0:
                        monthly_data.append({
                            'Ay': month,
                            'Maç': data['mac'],
                            'Ortalama': data['puan'] / data['mac'],
                            'Toplam': data['puan']
                        })
                
                if monthly_data:
                    monthly_df = pd.DataFrame(monthly_data).sort_values('Ay', ascending=False)
                    st.dataframe(
                        monthly_df.style.format({'Ortalama': '{:.1f}'}),
                        use_container_width=True
                    )
            
            # Akıllı koç
            st.divider()
            st.subheader("🎓 Akıllı Koç Önerileri")
            
            if s['mac_sayisi'] > 0:
                # En çok ceza alınan oyun (puan bazında)
                if s['ceza_puanlari']:
                    worst_ceza = min(s['ceza_puanlari'].items(), key=lambda x: x[1])
                    ceza_name = worst_ceza[0]
                    ceza_puan = worst_ceza[1]
                    
                    if ceza_name in VIDEO_MAP:
                        st.warning(f"""
                        **⚠️ Gelişim Alanı: {ceza_name}**
                        
                        Toplam {ceza_puan:.0f} puan ceza aldınız.
                        Bu konuda pratik yapmanız önerilir.
                        """)
                        
                        if st.button("📺 Ders Videosunu İzle", key="coach_video"):
                            st.markdown(f"[Ders videosu için tıklayın]({VIDEO_MAP[ceza_name]})")
                
                # Genel öneriler
                if win_rate < 40:
                    st.info("""
                    **💡 Öneri:** Oyun stratejinizi gözden geçirin. 
                    Daha agresif veya daha savunmacı oynamayı deneyebilirsiniz.
                    """)
                elif s['win_streak'] >= 3:
                    st.success(f"""
                    **🔥 Harika Gidiyorsunuz!** 
                    {s['win_streak']} maçlık kazanma seriniz var. 
                    Bu formu koruyun!
                    """)
        
        # Ayarlar
        st.divider()
        with st.expander("⚙️ Hesap Ayarları", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Yeni Kullanıcı Adı", st.session_state['username'])
            
            with col2:
                new_password = st.text_input("Yeni Şifre", type="password", 
                                           placeholder="Değiştirmek istemiyorsanız boş bırakın")
            
            if st.button("🔄 Profili Güncelle", type="secondary"):
                if not new_username.strip():
                    st.error("Kullanıcı adı boş olamaz!")
                    return
                    
                result = update_user_in_sheet(
                    st.session_state['username'],
                    new_username,
                    new_password if new_password else "1234",
                    st.session_state['role']
                )
                
                if result in ["updated", "added"]:
                    st.success("Profil güncellendi!")
                    st.session_state['username'] = new_username
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Güncelleme başarısız!")
    except Exception as e:
        st.error(f"Profil yüklenirken hata oluştu: {str(e)}")

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim Paneli</h2>", unsafe_allow_html=True)
    
    current_role = st.session_state.get("role", "user")
    
    if current_role not in ["admin", "patron"]:
        st.error("Bu sayfaya erişim yetkiniz yok!")
        return
    
    # Kullanıcı yönetimi
    st.subheader("👥 Kullanıcı Yönetimi")
    
    _, _, users_df = get_users_map()
    
    with st.form("user_management_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            username = st.text_input("Kullanıcı Adı")
        
        with col2:
            password = st.text_input("Şifre", type="password")
        
        with col3:
            if current_role == "patron":
                role = st.selectbox("Yetki", ["user", "admin", "patron"])
            else:
                role = "user"
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            add_btn = st.form_submit_button("➕ Kullanıcı Ekle/Güncelle", type="primary")
        
        with col_btn2:
            delete_btn = st.form_submit_button("🗑️ Seçili Kullanıcıyı Sil", type="secondary")
        
        if add_btn:
            if not username:
                st.error("Kullanıcı adı gereklidir!")
            else:
                result = update_user_in_sheet(username, username, password or "1234", role)
                if result in ["added", "updated"]:
                    st.success(f"Kullanıcı {username} başarıyla işlendi!")
                    st.rerun()
                else:
                    st.error("İşlem başarısız!")
        
        if delete_btn:
            if not username:
                st.error("Silinecek kullanıcı adını girin!")
            else:
                result = update_user_in_sheet(username, "", "", "", delete=True)
                if result == "deleted":
                    st.success(f"Kullanıcı {username} silindi!")
                    st.rerun()
                else:
                    st.error("Silme işlemi başarısız!")
    
    # Kullanıcı listesi
    st.subheader("📋 Mevcut Kullanıcılar")
    
    if not users_df.empty:
        for _, row in users_df.iterrows():
            user_col, role_col, action_col = st.columns([3, 2, 1])
            
            with user_col:
                st.write(f"**{row['Username']}** (ID: {row['UserID']})")
            
            with role_col:
                st.write(f"`{row['Role']}` - KKD: {row['KKD']}")
            
            with action_col:
                if row['Username'] != st.session_state['username'] and current_role == "patron":
                    if st.button("🗑️", key=f"del_{row['UserID']}", help="Kullanıcıyı sil"):
                        if update_user_in_sheet(row['Username'], "", "", "", delete=True) == "deleted":
                            st.success("Silindi!")
                            time.sleep(1)
                            st.rerun()
    else:
        st.info("Henüz kullanıcı kaydı bulunmuyor.")
    
    # Maç yönetimi
    st.divider()
    st.subheader("🎮 Maç Yönetimi")
    
    try:
        stats, match_hist, _, _ = istatistikleri_hesapla()
        
        if match_hist:
            match_titles = [m['baslik'] for m in match_hist[::-1]]
            
            selected_match = st.selectbox("Silinecek Maçı Seç:", match_titles)
            
            if st.button("🗑️ Seçili Maçı Sil", type="secondary"):
                if delete_match_from_sheet(selected_match):
                    st.rerun()
        else:
            st.info("Henüz maç kaydı bulunmuyor.")
    except Exception as e:
        st.error(f"Maç yönetimi yüklenirken hata oluştu: {str(e)}")
    
    # Sistem araçları
    st.divider()
    st.subheader("⚙️ Sistem Araçları")
    
    col_tool1, col_tool2 = st.columns(2)
    
    with col_tool1:
        if st.button("🔄 Önbelleği Temizle", help="Tüm önbellek verilerini temizler"):
            clear_cache()
            st.success("Önbellek temizlendi!")
            time.sleep(1)
            st.rerun()
    
    with col_tool2:
        if st.button("📊 Verileri Yeniden Hesapla", help="Tüm istatistikleri yeniden hesaplar"):
            st.info("İstatistikler yeniden hesaplanıyor...")
            clear_cache()
            time.sleep(2)
            st.success("Hesaplama tamamlandı!")
            st.rerun()

# =============================================================================
# 9. ANA UYGULAMA
# =============================================================================

def main():
    # Sayfa ayarları
    st.set_page_config(
        page_title="King İstatistik Kurumu",
        layout="wide",
        page_icon="👑",
        initial_sidebar_state="collapsed",
        menu_items=None
    )
    
    # CSS enjeksiyonu
    inject_custom_css()
    
    # Session state başlatma
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "role" not in st.session_state:
        st.session_state["role"] = "user"
    
    # Giriş kontrolü
    if not st.session_state["logged_in"]:
        login_screen()
        return
    
    # Ana arayüz
    # Başlık
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1>👑 King İstatistik Kurumu</h1>
        <p style="color: #aaa; font-size: 1.1em;">
            Hoş geldin, <span style="color: #FFD700; font-weight: bold;">{st.session_state['username']}</span>!
            <span style="margin-left: 10px; background: #444; padding: 3px 10px; border-radius: 10px;">
                {st.session_state['role'].upper()}
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menü
    menu_items = ["📊 İstatistikler", "🏆 KKD Liderlik", "👤 Profilim"]
    
    if st.session_state["role"] in ["admin", "patron"]:
        menu_items = ["🎮 Oyun Ekle", "🛠️ Yönetim Paneli"] + menu_items
    
    selected_page = st.radio(
        "Menü",
        menu_items,
        horizontal=True,
        label_visibility="collapsed",
        key="main_menu"
    )
    
    # Çıkış butonu
    col1, col2, col3 = st.columns([3, 2, 1])
    with col3:
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # Sayfa yönlendirme
    page_map = {
        "🎮 Oyun Ekle": game_interface,
        "📊 İstatistikler": stats_interface,
        "🏆 KKD Liderlik": kkd_leaderboard_interface,
        "👤 Profilim": profile_interface,
        "🛠️ Yönetim Paneli": admin_panel
    }
    
    if selected_page in page_map:
        try:
            page_map[selected_page]()
        except Exception as e:
            st.error(f"Sayfa yüklenirken hata oluştu: {str(e)}")
            st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")
    else:
        st.error("Sayfa bulunamadı!")

if __name__ == "__main__":
    main()
