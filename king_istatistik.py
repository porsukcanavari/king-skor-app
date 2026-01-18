import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# =============================================================================
# 0. GÖRSEL AYARLAR VE CSS (SENİN AYARLARIN)
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

# =============================================================================
# 1. GOOGLE SHEETS BAĞLANTISI (YENİ BEYİN)
# =============================================================================

@st.cache_resource
def get_google_sheet_client():
    # Streamlit Secrets'tan anahtarı alıyoruz
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def get_data_from_sheet(sheet_name):
    """Google Sheet'ten veriyi çeker"""
    try:
        client = get_google_sheet_client()
        sheet = client.open("King_Veritabani").worksheet(sheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

def update_user_in_sheet(username, password, role):
    """Kullanıcı güncelleme"""
    try:
        client = get_google_sheet_client()
        sheet = client.open("King_Veritabani").worksheet("Users")
        
        # Kullanıcıları çek
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Varsa güncelle
        if not df.empty and 'Username' in df.columns:
            cell = sheet.find(username)
            if cell:
                sheet.update_cell(cell.row, 2, password)
                sheet.update_cell(cell.row, 3, role)
                return True
        
        # Yoksa ekle
        sheet.append_row([username, password, role])
        return True
    except Exception as e:
        st.error(f"Hata: {e}")
        return False

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
# 2. İSTATİSTİK MOTORU (GOOGLE SHEETS UYUMLU)
# =============================================================================

def istatistikleri_hesapla():
    # Artık dosyadan değil, Google Sheet'ten çekiyoruz
    df = get_data_from_sheet("Maclar")
    if df.empty: return None

    # Sayısal çevirme
    numeric_cols = [col for col in df.columns if col not in ['Tarih', 'Mac_Ismi', 'Oyun_Turu']]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    player_stats = {} 
    ceza_turu_listesi = [k for k, v in OYUN_KURALLARI.items() if v['puan'] < 0]
    
    # Tüm oyuncuları bul (Kolonlardan)
    players = numeric_cols

    # İlk döngü: Oyuncu profillerini oluştur
    for p in players:
        player_stats[p] = {
            "mac_sayisi": 0, "toplam_puan": 0, "pozitif_mac_sayisi": 0,
            "cezalar": {ceza: 0 for ceza in ceza_turu_listesi}, "partnerler": {}
        }

    # Maç bazlı gruplama
    if 'Mac_Ismi' in df.columns:
        maclar = df.groupby('Mac_Ismi')
        
        for mac_adi, mac_df in maclar:
            mac_toplamlari = mac_df[players].sum()
            
            for p in players:
                # O maçta bu oyuncu var mı?
                if p in mac_df.columns:
                    stats = player_stats[p]
                    stats["mac_sayisi"] += 1
                    puan = mac_toplamlari[p]
                    stats["toplam_puan"] += puan
                    if puan > 0: stats["pozitif_mac_sayisi"] += 1

                    # Ceza Analizi
                    for _, row in mac_df.iterrows():
                        oyun_turu = row['Oyun_Turu']
                        base_name = oyun_turu.split(" #")[0]
                        if base_name in stats["cezalar"]:
                            satir_puani = row[p]
                            if satir_puani < 0:
                                birim = OYUN_KURALLARI[base_name]['puan']
                                adet = int(satir_puani / birim)
                                stats["cezalar"][base_name] += adet

                    # Komandit (Partner) Analizi
                    other_players = [op for op in players if op != p]
                    for op in other_players:
                        if op in mac_df.columns:
                            if op not in stats["partnerler"]:
                                stats["partnerler"][op] = {"birlikte_mac": 0, "beraber_kazanma": 0, "beraber_kaybetme": 0, "puan_toplami": 0}
                            
                            p_stat = stats["partnerler"][op]
                            p_stat["birlikte_mac"] += 1
                            p_stat["puan_toplami"] += puan
                            if puan > 0: p_stat["beraber_kazanma"] += 1
                            elif puan < 0: p_stat["beraber_kaybetme"] += 1

    return player_stats

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
                # Google Sheet'ten kullanıcıları çek
                users_df = get_data_from_sheet("Users")
                
                # İlk kurulum (Eğer Sheet boşsa)
                if users_df.empty:
                    update_user_in_sheet("aaykutb", "1234", "patron")
                    st.info("İlk kurulum yapıldı. aaykutb / 1234 ile girin.")
                    return

                # Giriş Kontrolü
                # Username kolonu olup olmadığını kontrol et
                if 'Username' in users_df.columns:
                    user_row = users_df[users_df['Username'] == username]
                    if not user_row.empty and str(user_row.iloc[0]['Password']) == str(password):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.session_state["role"] = user_row.iloc[0]['Role']
                        st.success("Giriş Başarılı!")
                        st.rerun()
                    else:
                        st.error("Hatalı kullanıcı adı veya şifre!")
                else:
                    st.error("Users tablosu hatalı (Username kolonu yok).")

def logout():
    st.session_state.clear()
    st.rerun()

# =============================================================================
# 4. OYUN YÖNETİM ARAYÜZÜ (OYUN EKLE)
# =============================================================================

def game_interface():
    st.markdown("<h2>🎮 Oyun Ekle</h2>", unsafe_allow_html=True)
    
    # Geçici hafıza (Oyun bitene kadar burada tutuyoruz)
    if "temp_df" not in st.session_state:
        st.session_state["temp_df"] = pd.DataFrame()

    # --- MASA KURMA ---
    if st.session_state["temp_df"].empty:
        st.info("Yeni masa kurun.")
        
        # Kullanıcıları Sheet'ten al
        users_df = get_data_from_sheet("Users")
        tum_oyuncular = users_df['Username'].tolist() if not users_df.empty and 'Username' in users_df.columns else []
        
        st.markdown("### 1. Maç Ayarları")
        match_name_input = st.text_input("Maç İsmi:", value="King_Maci_1")
        
        st.markdown("### 2. Kadro Seçimi")
        secilenler = st.multiselect(
            "4 oyuncu seçin:", 
            options=tum_oyuncular,
            default=tum_oyuncular[:4] if len(tum_oyuncular) >= 4 else None
        )
        
        if len(secilenler) == 4:
            if st.button("Masayı Kur ve Başlat", type="primary"):
                # Boş DataFrame
                st.session_state["temp_df"] = pd.DataFrame(columns=secilenler)
                st.session_state["current_match_name"] = match_name_input
                st.session_state["game_index"] = 0 
                st.session_state["players"] = secilenler # Oyuncuları sakla
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
        
        st.success(f"Maç: **{st.session_state['current_match_name']}**")
        st.dataframe(df.style.format("{:.0f}"), use_container_width=True)
        
        total_limit = sum([k['limit'] for k in OYUN_KURALLARI.values()])
        oynanan_satir_sayisi = len(df)
        
        # OYUN BİTİŞİ
        if oynanan_satir_sayisi >= total_limit:
            st.success("🏁 OYUN BİTTİ! Geçmiş olsun.")
            cols = st.columns(4)
            totals = df.sum()
            for i, p in enumerate(secili_oyuncular):
                cols[i].metric(p, f"{totals[p]}", delta_color="normal" if totals[p]>0 else "inverse")
                
            if st.button("💾 Maçı Google Drive'a Kaydet"):
                with st.spinner("Google Sheets'e yazılıyor..."):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    match_name = st.session_state["current_match_name"]
                    
                    # Google Sheet Client
                    client = get_google_sheet_client()
                    sheet = client.open("King_Veritabani").worksheet("Maclar")
                    
                    # Mevcut başlıkları çek
                    headers = sheet.row_values(1)
                    if not headers:
                        # Boşsa başlık oluştur
                        headers = ["Tarih", "Mac_Ismi", "Oyun_Turu"] + secili_oyuncular
                        sheet.append_row(headers)
                    else:
                        # Eksik oyuncu varsa başlığa ekle
                        for p in secili_oyuncular:
                            if p not in headers:
                                headers.append(p)
                                sheet.update_cell(1, len(headers), p)
                    
                    # Satırları Ekle
                    for index, row in df.iterrows():
                        # Satır taslağı
                        final_row = [""] * len(headers)
                        final_row[0] = timestamp
                        final_row[1] = match_name
                        final_row[2] = index # Oyun Türü
                        
                        # Puanları doğru kolona yerleştir
                        for p in secili_oyuncular:
                            if p in headers:
                                col_idx = headers.index(p)
                                final_row[col_idx] = int(row[p])
                        
                        sheet.append_row(final_row)
                        
                st.balloons()
                st.success("✅ Maç başarıyla kaydedildi!")
                # Masayı temizle
                st.session_state["temp_df"] = pd.DataFrame()
                del st.session_state["players"]
                st.rerun()
            return

        # VERİ GİRİŞİ
        if "game_index" not in st.session_state: st.session_state["game_index"] = 0
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
                    
                    # Geçici tabloya ekle
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
# 6. İSTATİSTİK ARAYÜZÜ
# =============================================================================

def stats_interface():
    st.markdown("<h2>📊 Detaylı İstatistik Merkezi</h2>", unsafe_allow_html=True)
    data = istatistikleri_hesapla()
    if not data:
        st.warning("Henüz tamamlanmış maç verisi yok.")
        return

    tab_list = ["🏆 Genel", "🔥 Win Rate"] + [k for k in OYUN_KURALLARI.keys() if OYUN_KURALLARI[k]['puan'] < 0]
    tabs = st.tabs(tab_list)
    df_stats = pd.DataFrame.from_dict(data, orient='index')

    with tabs[0]:
        st.dataframe(df_stats[['mac_sayisi', 'toplam_puan']].sort_values('toplam_puan', ascending=False), use_container_width=True)
    with tabs[1]:
        df_stats['win_rate'] = (df_stats['pozitif_mac_sayisi'] / df_stats['mac_sayisi']) * 100
        st.dataframe(df_stats[['mac_sayisi', 'win_rate']].sort_values('win_rate', ascending=False).style.format({'win_rate': "{:.1f}%"}), use_container_width=True)
    
    ceza_list = [k for k in OYUN_KURALLARI.keys() if OYUN_KURALLARI[k]['puan'] < 0]
    for i, ceza_adi in enumerate(ceza_list):
        with tabs[i+2]:
            temp = {p: data[p]['cezalar'].get(ceza_adi, 0)/data[p]['mac_sayisi'] if data[p]['mac_sayisi']>0 else 0 for p in data}
            st.bar_chart(pd.Series(temp))
            st.caption(f"Maç başına ortalama {ceza_adi}")

# =============================================================================
# 7. PROFİL EKRANI
# =============================================================================

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    
    with st.expander("🔑 Şifre Değiştir"):
        new_pass = st.text_input("Yeni Şifre", type="password")
        if st.button("Güncelle"):
            if update_user_in_sheet(st.session_state["username"], new_pass, st.session_state["role"]):
                st.success("Şifreniz güncellendi!")

    data = istatistikleri_hesapla()
    my_name = st.session_state['username']
    
    if not data or my_name not in data:
        st.info("Henüz istatistik veriniz oluşmadı.")
        return
        
    my_stats = data[my_name]
    
    # KARTLAR
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Maç", my_stats['mac_sayisi'])
    c2.metric("Toplam Puan", my_stats['toplam_puan'])
    win_rate = (my_stats['pozitif_mac_sayisi'] / my_stats['mac_sayisi']) * 100 if my_stats['mac_sayisi'] > 0 else 0
    c3.metric("Kazanma %", f"%{win_rate:.1f}")

    # --- KOMANDİT ANALİZİ ---
    st.divider()
    st.subheader("🤝 Komanditlik Durumu (Kim Sana Yarıyor?)")
    
    partners = my_stats['partnerler']
    if partners:
        p_list = []
        for p_name, p_dat in partners.items():
            total = p_dat['birlikte_mac']
            wins = p_dat['beraber_kazanma']
            p_win_rate = (wins / total * 100) if total > 0 else 0
            
            p_list.append({
                "Komandit": p_name,
                "Maç": total,
                "Kazanma %": p_win_rate,
                "Net Skor": p_dat['puan_toplami']
            })
            
        df_p = pd.DataFrame(p_list).sort_values(by="Kazanma %", ascending=False)
        
        if not df_p.empty:
            best = df_p.iloc[0]
            worst = df_p.iloc[-1]
            col_b, col_w = st.columns(2)
            if best['Kazanma %'] >= 50:
                col_b.success(f"🍀 En Uğurlu: **{best['Komandit']}**\n(Beraberken kazanma oranı: %{best['Kazanma %']:.1f})")
            else:
                col_b.info(f"🍀 En Uğurlu: **{best['Komandit']}**\n(Beraberken kazanma oranı: %{best['Kazanma %']:.1f})")
            col_w.error(f"💀 En Uğursuz: **{worst['Komandit']}**\n(Beraberken kazanma oranı: %{worst['Kazanma %']:.1f})")
        
        st.dataframe(df_p.style.format({"Kazanma %": "{:.1f}%"}), use_container_width=True)
    else:
        st.info("Henüz yeterli komanditlik verisi yok.")

# =============================================================================
# 8. YÖNETİM PANELİ
# =============================================================================

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim Paneli</h2>", unsafe_allow_html=True)
    users_df = get_data_from_sheet("Users")
    current_user_role = st.session_state["role"]
    
    # KULLANICI EKLEME
    with st.form("add_user_form"):
        st.subheader("Yeni Kullanıcı Ekle")
        c1, c2, c3 = st.columns(3)
        u_name = c1.text_input("Kullanıcı Adı")
        u_pass = c2.text_input("Şifre")
        if current_user_role == "patron":
            u_role = c3.selectbox("Yetki", ["user", "admin", "patron"])
        else:
            u_role = c3.selectbox("Yetki", ["user"], disabled=True)
        
        if st.form_submit_button("Kaydet"):
            if u_name and u_pass:
                # Yetki kontrolü (Sheet'ten okuyarak)
                if not users_df.empty and u_name in users_df['Username'].values and current_user_role != "patron":
                    st.error("Yetkisiz işlem.")
                else:
                    if update_user_in_sheet(u_name, u_pass, u_role):
                        st.success(f"✅ {u_name} Drive'a kaydedildi.")

    st.divider()
    
    # --- PATRON ÖZEL ---
    if current_user_role == "patron":
        st.subheader("🕵️ Patron Özel: Oyuncu Röntgeni")
        # Sheet'teki kullanıcı listesi
        user_list = users_df['Username'].tolist() if not users_df.empty else []
        target_user = st.selectbox("İncelenecek Oyuncu:", user_list)
        
        if target_user:
            data = istatistikleri_hesapla()
            if data and target_user in data:
                t_stats = data[target_user]
                c1, c2, c3 = st.columns(3)
                c1.metric("Toplam Maç", t_stats['mac_sayisi'])
                c2.metric("Toplam Puan", t_stats['toplam_puan'])
                t_wr = (t_stats['pozitif_mac_sayisi'] / t_stats['mac_sayisi']) * 100 if t_stats['mac_sayisi'] > 0 else 0
                c3.metric("Kazanma %", f"%{t_wr:.1f}")
                
                st.write(f"**{target_user} için Komandit Analizi:**")
                t_partners = t_stats['partnerler']
                if t_partners:
                    tp_list = []
                    for p_name, p_dat in t_partners.items():
                        total = p_dat['birlikte_mac']
                        wins = p_dat['beraber_kazanma']
                        tp_win_rate = (wins / total * 100) if total > 0 else 0
                        tp_list.append({"Komandit": p_name, "Maç": total, "Kazanma %": tp_win_rate, "Net Skor": p_dat['puan_toplami']})
                    
                    df_tp = pd.DataFrame(tp_list).sort_values(by="Kazanma %", ascending=False)
                    st.dataframe(df_tp.style.format({"Kazanma %": "{:.1f}%"}), use_container_width=True)
                else:
                    st.warning("Bu oyuncunun komandit verisi yok.")
            else:
                st.warning("Bu oyuncunun henüz maç kaydı yok.")
    else:
        st.subheader("📋 Kullanıcı Listesi")
        if not users_df.empty:
            st.dataframe(users_df[['Username', 'Role']])

# =============================================================================
# 9. ANA UYGULAMA ÇATISI (MAIN)
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
