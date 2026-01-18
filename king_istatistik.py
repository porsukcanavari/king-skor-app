import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

# =============================================================================
# 🚨 SABİT AYARLAR VE LİNKLER
# =============================================================================
# Kendi tablo linkini buraya yapıştır:
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wTEdK-MvfaYMvgHmUPAjD4sCE7maMDNOhs18tgLSzKg/edit"

# =============================================================================
# 0. GÖRSEL AYARLAR VE CSS
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        h1 { color: #FFD700 !important; text-align: center; text-shadow: 2px 2px 4px #000000; font-family: 'Arial Black', sans-serif; margin-bottom: 10px; }
        h2, h3 { color: #ff4b4b !important; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .stButton > button { width: 100% !important; height: auto !important; background-color: #990000; color: white; border-radius: 8px; border: 1px solid #330000; font-weight: bold; font-size: 16px; padding: 12px 20px; white-space: nowrap !important; display: flex; align-items: center; justify-content: center; }
        .stButton > button:hover { background-color: #ff0000; border-color: white; transform: scale(1.01); }
        div[data-testid="stNumberInput"] button { background-color: #444 !important; color: white !important; border-color: #666 !important; min-height: 40px; min-width: 40px; }
        @media only screen and (max-width: 600px) { h1 { font-size: 24px !important; } h2 { font-size: 20px !important; } }
        div[data-testid="stMetric"] { background-color: #262730; padding: 10px; border-radius: 10px; border: 1px solid #444; text-align: center; }
        div[data-testid="stDataFrame"] { border: 1px solid #444; border-radius: 5px; }
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}
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
# 1. GOOGLE SHEETS BAĞLANTISI (GARANTİ YÖNTEM)
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
    """Link ile doğru dosyayı bulur"""
    client = get_google_sheet_client()
    return client.open_by_url(SHEET_URL)

def get_users_from_sheet():
    try:
        sheet = get_sheet_by_url().worksheet("Users")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

def update_user_in_sheet(old_username, new_username, password, role, delete=False):
    """Kullanıcı Ekleme, Güncelleme ve Silme"""
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Users")
        
        # Eğer sayfa boşsa başlık ekle
        if not sheet.get_all_values():
            sheet.append_row(["Username", "Password", "Role"])
            
        try:
            cell = sheet.find(old_username)
            if cell:
                if delete:
                    sheet.delete_rows(cell.row)
                    return "deleted"
                else:
                    # Güncelleme (İsim değişmiş olabilir)
                    sheet.update_cell(cell.row, 1, new_username)
                    sheet.update_cell(cell.row, 2, password)
                    sheet.update_cell(cell.row, 3, role)
                    return "updated"
            else:
                if not delete:
                    sheet.append_row([new_username, password, role])
                    return "added"
        except:
            if not delete:
                sheet.append_row([new_username, password, role])
                return "added"
        return False
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")
        return False

# =============================================================================
# 2. İSTATİSTİK MOTORU (GÖRSEL TABLOYU OKUYAN YAPI)
# =============================================================================

def istatistikleri_hesapla():
    try:
        wb = get_sheet_by_url()
        sheet = wb.worksheet("Maclar")
        raw_data = sheet.get_all_values()
    except:
        return None, None

    if not raw_data: return None, None

    player_stats = {}
    match_history = [] # Geçmiş maç listesi
    
    current_players = []
    current_match_data = {} # Anlık maç verisi
    current_match_name = ""
    
    # Satır satır analiz
    for row in raw_data:
        if not row: continue
        first_cell = str(row[0])
        
        # 1. Yeni Maç Başlangıcı
        if first_cell.startswith("--- MAÇ:"):
            current_match_name = first_cell
            current_players = []
            current_match_data = {"baslik": first_cell, "skorlar": [], "oyuncular": []}
            continue
            
        # 2. Oyuncu İsimleri (Başlık Satırı)
        if first_cell == "OYUN TÜRÜ":
            # [OYUN TÜRÜ, Aykut, Tuna, ...]
            for col_idx in range(1, len(row)):
                p_name = row[col_idx].strip()
                if p_name:
                    current_players.append(p_name)
                    current_match_data["oyuncular"].append(p_name)
                    if p_name not in player_stats:
                        player_stats[p_name] = {
                            "mac_sayisi": 0, "toplam_puan": 0, "pozitif_mac_sayisi": 0,
                            "cezalar": {}, "partnerler": {}, "gecici_mac_puani": 0,
                            "rekor_max": -9999, "rekor_min": 9999 # Rekorlar için
                        }
            continue

        # 3. Skor Verisi
        base_name = first_cell.split(" #")[0]
        if base_name in OYUN_KURALLARI and current_players:
            # Maç detayına ekle (Satır verisi)
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
                            
                            if score < 0:
                                if base_name not in stats["cezalar"]: stats["cezalar"][base_name] = 0
                                birim = OYUN_KURALLARI[base_name]['puan']
                                stats["cezalar"][base_name] += int(score/birim)
                except: continue

        # 4. Maç Sonu
        if first_cell == "TOPLAM":
            # Maç listesine kaydet
            current_match_data["toplamlar"] = row
            match_history.append(current_match_data)
            
            for p_name in current_players:
                if p_name in player_stats:
                    stats = player_stats[p_name]
                    stats["mac_sayisi"] += 1
                    mac_puani = stats["gecici_mac_puani"]
                    
                    # Batma/Çıkma
                    if mac_puani > 0:
                        stats["pozitif_mac_sayisi"] += 1
                    
                    # Rekorlar (Batış / Çıkış)
                    if mac_puani > stats["rekor_max"]: stats["rekor_max"] = mac_puani
                    if mac_puani < stats["rekor_min"]: stats["rekor_min"] = mac_puani
                    
                    # Partner (Komandit) Analizi
                    others = [op for op in current_players if op != p_name]
                    for op in others:
                        if op not in stats["partnerler"]:
                            stats["partnerler"][op] = {"birlikte_mac": 0, "beraber_kazanma": 0, "beraber_kaybetme": 0, "puan_toplami": 0}
                        
                        p_stat = stats["partnerler"][op]
                        p_stat["birlikte_mac"] += 1
                        p_stat["puan_toplami"] += mac_puani
                        if mac_puani > 0: p_stat["beraber_kazanma"] += 1
                        elif mac_puani < 0: p_stat["beraber_kaybetme"] += 1

            # Sıfırla
            for p in player_stats: player_stats[p]["gecici_mac_puani"] = 0
            current_players = []

    return player_stats, match_history

# =============================================================================
# 3. GİRİŞ VE KİMLİK DOĞRULAMA
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
                     st.error("⚠️ HATA: 'Users' tablosuna ulaşılamadı.")
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
                        else:
                            st.error("Hatalı şifre!")
                    else:
                        st.error("Kullanıcı bulunamadı!")
                else:
                    st.error(f"Tablo formatı hatalı! Görünen kolonlar: {users_df.columns.tolist()}")

def logout():
    st.session_state.clear()
    st.rerun()

# =============================================================================
# 4. OYUN YÖNETİM ARAYÜZÜ (OYUN EKLE)
# =============================================================================

def game_interface():
    st.markdown("<h2>🎮 Oyun Ekle</h2>", unsafe_allow_html=True)
    
    if "game_active" not in st.session_state: st.session_state["game_active"] = False
    if "temp_df" not in st.session_state: st.session_state["temp_df"] = pd.DataFrame()

    # --- MASA KURMA ---
    if not st.session_state["game_active"]:
        st.info("Yeni maç başlatın veya geçmiş bir maçı sisteme girin.")
        
        users_df = get_users_from_sheet()
        tum_oyuncular = users_df['Username'].tolist() if not users_df.empty and 'Username' in users_df.columns else []
        
        c1, c2 = st.columns(2)
        match_name_input = c1.text_input("Maç İsmi:", value="King_Maci")
        
        # TARİH SEÇİMİ
        is_past = c2.checkbox("Geçmiş Tarihli Maç?")
        if is_past:
            # Tarih seçici ama formatı biz ayarlayacağız
            selected_date = c2.date_input("Maç Tarihi", value=datetime.now())
            mac_tarihi_str = selected_date.strftime("%d.%m.%Y")
        else:
            mac_tarihi_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        st.markdown("### Kadro Seçimi")
        secilenler = st.multiselect("4 oyuncu seçin:", options=tum_oyuncular, default=tum_oyuncular[:4] if len(tum_oyuncular) >= 4 else None)
        
        if len(secilenler) == 4:
            if st.button("Masayı Kur ve Başlat", type="primary"):
                st.session_state["temp_df"] = pd.DataFrame(columns=secilenler)
                st.session_state["current_match_name"] = match_name_input
                st.session_state["match_date"] = mac_tarihi_str # Tarihi sakla
                st.session_state["game_index"] = 0 
                st.session_state["players"] = secilenler
                st.session_state["game_active"] = True
                st.rerun()
        elif len(secilenler) < 4:
            st.warning(f"⚠️ {4 - len(secilenler)} kişi daha seçmelisin.")
        else:
            st.error("⛔ En fazla 4 kişi seçebilirsin!")
        return 

    # --- OYUN OYNAMA ---
    else:
        df = st.session_state["temp_df"]
        secili_oyuncular = st.session_state["players"]
        tarih_goster = st.session_state["match_date"]
        
        st.success(f"Maç: **{st.session_state['current_match_name']}** ({tarih_goster})")
        st.dataframe(df.style.format("{:.0f}"), use_container_width=True)
        
        total_limit = sum([k['limit'] for k in OYUN_KURALLARI.values()])
        oynanan_satir_sayisi = len(df)
        
        if oynanan_satir_sayisi >= total_limit:
            st.success("🏁 OYUN BİTTİ!")
            cols = st.columns(4)
            totals = df.sum()
            for i, p in enumerate(secili_oyuncular):
                cols[i].metric(p, f"{totals[p]}", delta_color="normal" if totals[p]>0 else "inverse")
                
            if st.button("💾 Maçı Arşivle (Drive'a Yaz)"):
                with st.spinner("Tablo işleniyor..."):
                    try:
                        wb = get_sheet_by_url()
                        sheet = wb.worksheet("Maclar")
                        
                        # GÖRSEL BLOK OLUŞTURMA
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
                        
                        st.balloons()
                        st.success("✅ Maç başarıyla kaydedildi!")
                        st.session_state["game_active"] = False
                        st.session_state["temp_df"] = pd.DataFrame()
                        del st.session_state["players"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Google Drive Hatası: {e}")
            return

        # Veri Girişi
        mevcut_oyun_index = st.session_state["game_index"]
        if mevcut_oyun_index >= len(OYUN_SIRALAMASI): mevcut_oyun_index = len(OYUN_SIRALAMASI) - 1

        secilen_oyun = st.selectbox("Sıradaki Oyun:", OYUN_SIRALAMASI, index=mevcut_oyun_index, disabled=True)
        rules = OYUN_KURALLARI[secilen_oyun]
        current_count = len([x for x in df.index if secilen_oyun in x])
        remaining = rules['limit'] - current_count
        
        st.info(f"Oynanan: **{secilen_oyun}** | Kalan Hak: **{remaining}**")
        
        with st.form("input_form"):
            col_in = st.columns(4)
            inputs = {}
            total_input = 0
            for i, p in enumerate(secili_oyuncular):
                val = col_in[i].number_input(f"{p}", min_value=0, max_value=rules['adet'], step=1, key=f"in_{p}_{oynanan_satir_sayisi}")
                inputs[p] = val
                total_input += val
            
            if st.form_submit_button("Kaydet ve İlerle"):
                if total_input != rules['adet']:
                    st.error(f"Hata: Toplam {rules['adet']} olmalı, sen {total_input} girdin.")
                else:
                    row_name = f"{secilen_oyun} #{current_count + 1}"
                    row_data = {p: inputs[p] * rules['puan'] for p in secili_oyuncular}
                    
                    new_row = pd.DataFrame([row_data], index=[row_name])
                    st.session_state["temp_df"] = pd.concat([st.session_state["temp_df"], new_row])
                    
                    yeni_sayac = len([x for x in st.session_state["temp_df"].index if secilen_oyun in x])
                    if yeni_sayac >= rules['limit'] and st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
                        st.session_state["game_index"] += 1
                    st.rerun()
    
    st.divider()
    if st.button("⚠️ Son Satırı Sil (Geri Al)"):
        if not st.session_state["temp_df"].empty:
            last = st.session_state["temp_df"].index[-1].split(" #")[0]
            st.session_state["temp_df"] = st.session_state["temp_df"][:-1]
            if last in OYUN_SIRALAMASI: st.session_state["game_index"] = OYUN_SIRALAMASI.index(last)
            st.rerun()

# =============================================================================
# 6. İSTATİSTİK ARAYÜZÜ (GELİŞMİŞ)
# =============================================================================

def stats_interface():
    st.markdown("<h2>📊 Detaylı İstatistik Merkezi</h2>", unsafe_allow_html=True)
    stats, match_history = istatistikleri_hesapla()
    
    if not stats:
        st.warning("Henüz tamamlanmış maç verisi yok.")
        return

    # Sekmeler
    tabs = st.tabs(["🔥 Batma/Çıkma & Rekorlar", "🏆 Genel Durum", "📜 Maç Geçmişi", "🚫 Ceza Analizi", "🤝 Komanditlik"])
    df_stats = pd.DataFrame.from_dict(stats, orient='index')

    # 1. SEKME: BATMA ÇIKMA ORANI (EN ÖNEMLİSİ)
    with tabs[0]:
        st.subheader("🔥 Batma / Çıkma Oranı (Win Rate)")
        if not df_stats.empty:
            # Oran hesabı
            df_stats['win_rate'] = (df_stats['pozitif_mac_sayisi'] / df_stats['mac_sayisi']) * 100
            
            # Tabloyu hazırla
            win_table = df_stats[['mac_sayisi', 'pozitif_mac_sayisi', 'win_rate']].sort_values('win_rate', ascending=False)
            win_table.columns = ['Toplam Maç', 'Çıkılan Maç (Win)', 'Başarı Oranı (%)']
            st.dataframe(win_table.style.format({'Başarı Oranı (%)': "{:.1f}%"}), use_container_width=True)
            
            st.divider()
            st.subheader("🏔️ Zirveler ve Dipler (Tek Maçlık Rekorlar)")
            
            col_rec1, col_rec2 = st.columns(2)
            # En yüksek puanı bulan
            max_puan = df_stats['rekor_max'].max()
            max_player = df_stats['rekor_max'].idxmax()
            col_rec1.success(f"🚀 **En Yüksek Çıkış:**\n# {max_player} ({max_puan})")

            # En düşük puanı bulan
            min_puan = df_stats['rekor_min'].min()
            min_player = df_stats['rekor_min'].idxmin()
            col_rec2.error(f"⚓ **En Büyük Batış:**\n# {min_player} ({min_puan})")

    # 2. SEKME: GENEL DURUM
    with tabs[1]:
        st.subheader("🏆 Genel Puan ve Maç Sayısı")
        if not df_stats.empty:
            # Toplam Puan Sıralaması
            st.write("**Genel Puan Sıralaması**")
            st.dataframe(df_stats[['mac_sayisi', 'toplam_puan']].sort_values('toplam_puan', ascending=False), use_container_width=True)
            
            st.divider()
            # En çok maç yapan
            most_matches = df_stats['mac_sayisi'].idxmax()
            count = df_stats['mac_sayisi'].max()
            st.info(f"🏅 **İstikrar Abidesi (En Çok Maç):** {most_matches} ({count} Maç)")

    # 3. SEKME: MAÇ GEÇMİŞİ (LİSTE)
    with tabs[2]:
        st.subheader("📜 Tüm Maçların Arşivi")
        if match_history:
            # Maç isimleri listesi (Tersine çevir ki en yeni en üstte olsun)
            match_names = [f"{m['baslik']}" for m in match_history][::-1]
            selected_match_name = st.selectbox("İncelemek istediğin maçı seç:", match_names)
            
            # Seçilen maçı bul
            selected_data = next((m for m in match_history if m['baslik'] == selected_match_name), None)
            
            if selected_data:
                # DataFrame oluşturup göster
                # Kolonlar: Oyun Türü + Oyuncular
                cols = ["OYUN TÜRÜ"] + selected_data["oyuncular"]
                rows = []
                
                # Skor satırları
                for s in selected_data["skorlar"]:
                    # Sadece ilgili kolonları al (ilk kolon oyun adı, sonra oyuncular)
                    # s listesi: [OyunAdı, Puan1, Puan2...]
                    # Bizim cols ile uyumlu mu? Evet.
                    rows.append(s[:len(cols)])
                
                # Toplam satırı
                rows.append(selected_data["toplamlar"][:len(cols)])
                
                df_history = pd.DataFrame(rows, columns=cols)
                st.dataframe(df_history, use_container_width=True)
        else:
            st.info("Henüz kayıtlı maç yok.")

    # 4. SEKME: CEZA ANALİZİ
    with tabs[3]:
        st.subheader("🚫 Kim Neyi Çok Yiyor?")
        ceza_list = [k for k in OYUN_KURALLARI.keys() if OYUN_KURALLARI[k]['puan'] < 0]
        
        selected_ceza = st.selectbox("Ceza Türü Seç:", ceza_list)
        
        # Veriyi hazırla: Oyuncu başına o cezadan kaç tane yemiş?
        # Daha adil olması için: (Yediği Ceza Sayısı / Oynadığı Maç Sayısı)
        ceza_data = {}
        for p in stats:
            yenen = stats[p]['cezalar'].get(selected_ceza, 0)
            mac = stats[p]['mac_sayisi']
            ortalama = yenen / mac if mac > 0 else 0
            ceza_data[p] = ortalama
        
        st.bar_chart(pd.Series(ceza_data))
        st.caption(f"*Grafik: Maç başına ortalama yenen {selected_ceza} sayısı.*")

    # 5. SEKME: KOMANDİT
    with tabs[4]:
        st.subheader("🤝 Komanditlik Durumu")
        me = st.session_state["username"]
        if me in stats and stats[me]['partnerler']:
            partners = stats[me]['partnerler']
            p_list = []
            for p_name, p_dat in partners.items():
                total = p_dat['birlikte_mac']
                wins = p_dat['beraber_kazanma']
                p_win_rate = (wins / total * 100) if total > 0 else 0
                p_list.append({"Komandit": p_name, "Maç": total, "Kazanma %": p_win_rate})
            
            df_p = pd.DataFrame(p_list).sort_values(by="Kazanma %", ascending=False)
            st.dataframe(df_p.style.format({"Kazanma %": "{:.1f}%"}), use_container_width=True)
        else:
            st.info("Komandit verisi için maç yapmalısın.")

# =============================================================================
# 7. PROFİL EKRANI
# =============================================================================

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    
    # KULLANICI ADI DEĞİŞTİRME
    with st.expander("✏️ Kullanıcı Adı / Şifre Değiştir"):
        st.warning("Dikkat: Kullanıcı adınızı değiştirirseniz, eski maçlardaki isminiz tabloda güncellenmez. İstatistikleriniz yeni isimle sıfırdan başlar.")
        new_username = st.text_input("Yeni Kullanıcı Adı (Opsiyonel)", value=st.session_state["username"])
        new_pass = st.text_input("Yeni Şifre (Opsiyonel)", type="password")
        
        if st.button("Bilgileri Güncelle"):
            # Mevcut şifreyi koru eğer boşsa
            final_pass = new_pass if new_pass else "...." # Aslında mevcut şifreyi çekmek lazım ama güvenlik için boşsa elleme diyelim, şimdilik basit tutalım.
            # Basit yöntem: Direkt güncelle
            
            result = update_user_in_sheet(st.session_state["username"], new_username, new_pass if new_pass else "xxxx", st.session_state["role"])
            if result == "updated":
                st.success("Profil güncellendi! Lütfen tekrar giriş yapın.")
                st.session_state["username"] = new_username
                # Çıkış yaptırıp tekrar girmesini sağlayalım
                st.session_state["logged_in"] = False
                st.rerun()

    stats, _ = istatistikleri_hesapla() # Match history'ye gerek yok burada
    if not stats: return

    my_name = st.session_state['username']
    if my_name in stats:
        my_stats = stats[my_name]
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Maç", my_stats['mac_sayisi'])
        c2.metric("Toplam Puan", my_stats['toplam_puan'])
        win_rate = (my_stats['pozitif_mac_sayisi'] / my_stats['mac_sayisi']) * 100 if my_stats['mac_sayisi'] > 0 else 0
        c3.metric("Başarı %", f"%{win_rate:.1f}")

# =============================================================================
# 8. YÖNETİM PANELİ
# =============================================================================

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim Paneli</h2>", unsafe_allow_html=True)
    users_df = get_users_from_sheet()
    current_user_role = st.session_state["role"]
    
    # KULLANICI EKLEME / SİLME
    with st.form("user_mgmt"):
        st.subheader("Kullanıcı İşlemleri")
        c1, c2, c3 = st.columns(3)
        u_name = c1.text_input("Kullanıcı Adı")
        u_pass = c2.text_input("Şifre")
        if current_user_role == "patron":
            u_role = c3.selectbox("Yetki", ["user", "admin", "patron"])
            is_delete = st.checkbox("Bu Kullanıcıyı Sil?")
        else:
            u_role = c3.selectbox("Yetki", ["user"], disabled=True)
            is_delete = False
        
        if st.form_submit_button("İşlemi Uygula"):
            if u_name:
                if current_user_role != "patron" and is_delete:
                    st.error("Silme yetkiniz yok.")
                else:
                    # Şifre boşsa varsayılan ata (silme için önemli değil)
                    pwd = u_pass if u_pass else "1234"
                    res = update_user_in_sheet(u_name, u_name, pwd, u_role, delete=is_delete)
                    if res == "deleted": st.success(f"{u_name} silindi.")
                    elif res == "added": st.success(f"{u_name} eklendi.")
                    elif res == "updated": st.success(f"{u_name} güncellendi.")

    st.divider()
    
    if current_user_role == "patron":
        st.subheader("🕵️ Oyuncu Röntgeni")
        user_list = users_df['Username'].tolist() if not users_df.empty and 'Username' in users_df.columns else []
        target_user = st.selectbox("İncelenecek Oyuncu:", user_list)
        
        if target_user:
            stats, _ = istatistikleri_hesapla()
            if stats and target_user in stats:
                t_stats = stats[target_user]
                c1, c2, c3 = st.columns(3)
                c1.metric("Puan", t_stats['toplam_puan'])
                t_wr = (t_stats['pozitif_mac_sayisi'] / t_stats['mac_sayisi']) * 100 if t_stats['mac_sayisi'] > 0 else 0
                c2.metric("Win Rate", f"%{t_wr:.1f}")
                c3.metric("Rekor", t_stats['rekor_max'])
            else:
                st.warning("Veri yok.")
    
    st.subheader("📋 Kullanıcı Listesi")
    if not users_df.empty and 'Username' in users_df.columns:
        st.dataframe(users_df[['Username', 'Role']], use_container_width=True)

# =============================================================================
# 9. ANA UYGULAMA ÇATISI
# =============================================================================

st.set_page_config(page_title="King İstatistik Kurumu", layout="wide", page_icon="👑")
inject_custom_css()

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    with st.sidebar:
        st.markdown(f"### 👑 {st.session_state['username']}")
        st.caption(f"Yetki: {st.session_state['role'].upper()}")
        st.caption("*(Telefondaysan sol üstten menüyü aç)*")
        
        menu = ["📊 İstatistikler", "👤 Profilim"]
        if st.session_state["role"] in ["admin", "patron"]:
            menu = ["🎮 Oyun Ekle", "🛠️ Yönetim Paneli"] + menu
            
        choice = st.radio("Navigasyon", menu)
        st.markdown("---")
        if st.button("Çıkış Yap"):
            logout()
    
    if choice == "🎮 Oyun Ekle": game_interface()
    elif choice == "📊 İstatistikler": stats_interface()
    elif choice == "👤 Profilim": profile_interface()
    elif choice == "🛠️ Yönetim Paneli": admin_panel()
