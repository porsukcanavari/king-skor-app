import streamlit as st
import pandas as pd
import os
import json
import glob

# =============================================================================
# 0. GÖRSEL AYARLAR VE CSS (ARAYÜZ DÜZELTMELERİ)
# =============================================================================

def inject_custom_css():
    st.markdown("""
    <style>
        /* GENEL SAYFA RENGİ */
        .stApp {
            background-color: #0e1117;
        }
        
        /* BAŞLIKLAR */
        h1 {
            color: #FFD700 !important;
            text-align: center;
            text-shadow: 2px 2px 4px #000000;
            font-family: 'Arial Black', sans-serif;
            margin-bottom: 10px;
        }
        h2, h3 {
            color: #ff4b4b !important;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        
        /* --- BUTON AYARLARI --- */
        .stButton > button {
            width: 100% !important;
            height: auto !important;
            background-color: #990000;
            color: white;
            border-radius: 8px;
            border: 1px solid #330000;
            font-weight: bold;
            font-size: 16px;
            padding: 12px 20px;
            white-space: nowrap !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .stButton > button:hover {
            background-color: #ff0000;
            border-color: white;
            transform: scale(1.01);
        }

        /* --- SAYI GİRİŞ KUTUSU --- */
        div[data-testid="stNumberInput"] button {
            background-color: #444 !important;
            color: white !important;
            border-color: #666 !important;
            min-height: 40px; 
            min-width: 40px;
        }
        
        /* --- MOBİL UYUMLULUK --- */
        @media only screen and (max-width: 600px) {
            h1 { font-size: 24px !important; }
            h2 { font-size: 20px !important; }
        }
        
        /* İSTATİSTİK KUTULARI */
        div[data-testid="stMetric"] {
            background-color: #262730;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #444;
            text-align: center;
        }

        /* TABLO GÖRÜNÜMÜ */
        div[data-testid="stDataFrame"] {
            border: 1px solid #444;
            border-radius: 5px;
        }
        
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}
        
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 1. VERİTABANI VE SABİT AYARLAR
# =============================================================================

USERS_FILE = "users.json"
GAME_DATA_FOLDER = "mac_gecmisi"
TEMP_GAME_FILE = "aktif_oyun.csv"

# Klasör yoksa oluştur
if not os.path.exists(GAME_DATA_FOLDER):
    os.makedirs(GAME_DATA_FOLDER)

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
# 2. VERİ YÖNETİM FONKSİYONLARI
# =============================================================================

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except UnicodeDecodeError:
            st.error(f"HATA: {filename} dosyası bozuk formatta. Sıfırlanıyor...")
            return default
        except json.JSONDecodeError:
            return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_system():
    users = load_json(USERS_FILE, {})
    if "aaykutb" not in users:
        users["aaykutb"] = {
            "password": "1234",
            "role": "patron"
        }
        save_json(USERS_FILE, users)

init_system()

# =============================================================================
# 3. GELİŞMİŞ İSTATİSTİK MOTORU (KİMYA GÜNCELLEMESİ)
# =============================================================================

def istatistikleri_hesapla():
    """Geçmiş tüm maçları tarar ve detaylı rapor oluşturur."""
    all_files = glob.glob(os.path.join(GAME_DATA_FOLDER, "*.csv"))
    if not all_files: return None

    player_stats = {} 
    ceza_turu_listesi = [k for k, v in OYUN_KURALLARI.items() if v['puan'] < 0]

    for file in all_files:
        try:
            df = pd.read_csv(file, index_col=0)
            players = df.columns.tolist()
            total_scores = df.sum()
            
            for p in players:
                if p not in player_stats:
                    player_stats[p] = {
                        "mac_sayisi": 0, "toplam_puan": 0, 
                        "pozitif_mac_sayisi": 0, 
                        "cezalar": {ceza: 0 for ceza in ceza_turu_listesi}, 
                        "partnerler": {} 
                    }
                
                stats = player_stats[p]
                stats["mac_sayisi"] += 1
                score = total_scores[p]
                stats["toplam_puan"] += score
                
                if score > 0: stats["pozitif_mac_sayisi"] += 1
                
                # --- DETAYLI CEZA ANALİZİ ---
                for oyun_adi in df.index:
                    base_name = oyun_adi.split(" #")[0]
                    if base_name in stats["cezalar"]:
                        puan = df.loc[oyun_adi, p]
                        if puan < 0:
                            birim_puan = OYUN_KURALLARI[base_name]['puan']
                            adet = int(puan / birim_puan)
                            stats["cezalar"][base_name] += adet
                
                # --- PARTNER (KİMYA) ANALİZİ ---
                other_players = [op for op in players if op != p]
                for op in other_players:
                    if op not in stats["partnerler"]:
                        stats["partnerler"][op] = {
                            "puan_toplami": 0, 
                            "birlikte_mac": 0,
                            "beraber_kazanma": 0, # Yeni: O varken kazandığın maç
                            "beraber_kaybetme": 0 # Yeni: O varken kaybettiğin maç
                        }
                    
                    stats["partnerler"][op]["birlikte_mac"] += 1
                    stats["partnerler"][op]["puan_toplami"] += score 
                    
                    if score > 0:
                        stats["partnerler"][op]["beraber_kazanma"] += 1
                    elif score < 0:
                         stats["partnerler"][op]["beraber_kaybetme"] += 1
                         
        except Exception as e:
            continue

    return player_stats

# =============================================================================
# 4. GİRİŞ VE KİMLİK DOĞRULAMA
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
                users = load_json(USERS_FILE, {})
                if username in users and users[username]["password"] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = users[username]["role"]
                    st.success("Giriş Başarılı!")
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")

def logout():
    st.session_state.clear()
    st.rerun()

# =============================================================================
# 5. OYUN YÖNETİM ARAYÜZÜ
# =============================================================================

def game_interface():
    st.markdown("<h2>🎮 Oyun Masası</h2>", unsafe_allow_html=True)
    
    # --- MASA KURMA ---
    if not os.path.exists(TEMP_GAME_FILE):
        st.info("Şu an aktif bir oyun yok. Yeni masa kurun.")
        
        users_db = load_json(USERS_FILE, {})
        tum_oyuncular = list(users_db.keys())
        
        st.markdown("### 1. Maç Ayarları")
        match_name_input = st.text_input("Maç İsmi:", value="King_Maci_1")
        
        st.markdown("### 2. Kadro Seçimi")
        secilenler = st.multiselect(
            "4 oyuncu seçiniz:", 
            options=tum_oyuncular,
            default=tum_oyuncular[:4] if len(tum_oyuncular) >= 4 else None
        )
        
        if len(secilenler) == 4:
            if st.button("Masayı Kur ve Başlat", type="primary"):
                df = pd.DataFrame(columns=secilenler)
                df.to_csv(TEMP_GAME_FILE)
                st.session_state["current_match_name"] = match_name_input
                st.session_state["game_index"] = 0 
                st.rerun()
        elif len(secilenler) < 4:
            st.warning(f"⚠️ {4 - len(secilenler)} kişi daha seçmelisin.")
        else:
            st.error("⛔ En fazla 4 kişi seçebilirsin!")
        return 

    # --- OYUN OYNAMA ---
    else:
        df = pd.read_csv(TEMP_GAME_FILE, index_col=0)
        secili_oyuncular = df.columns.tolist()
        
        if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "Devam_Eden_Mac"
        if "game_index" not in st.session_state: st.session_state["game_index"] = 0

        st.success(f"📁 Dosya: **{st.session_state['current_match_name']}**")
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
                
            if st.button("💾 Maçı Arşivle"):
                final_name = st.session_state["current_match_name"]
                # Sorter Logic
                df_sorted = df.copy()
                df_sorted['sort_helper'] = df_sorted.index.map(lambda x: OYUN_SIRALAMASI.index(x.split(" #")[0]))
                df_sorted['number_helper'] = df_sorted.index.map(lambda x: int(x.split(" #")[1]))
                df_sorted = df_sorted.sort_values(by=['sort_helper', 'number_helper']).drop(columns=['sort_helper', 'number_helper'])
                
                base_path = os.path.join(GAME_DATA_FOLDER, f"{final_name}.csv")
                counter = 1
                while os.path.exists(base_path):
                    base_path = os.path.join(GAME_DATA_FOLDER, f"{final_name}_{counter}.csv")
                    counter += 1
                
                df_sorted.to_csv(base_path)
                os.remove(TEMP_GAME_FILE)
                if "game_index" in st.session_state: del st.session_state["game_index"]
                st.balloons()
                st.rerun()
            return

        # VERİ GİRİŞİ
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
                    df = pd.concat([df, pd.DataFrame([row_data], index=[row_name])])
                    df.to_csv(TEMP_GAME_FILE)
                    
                    yeni_sayac = len([x for x in df.index if secilen_oyun in x])
                    if yeni_sayac >= rules['limit'] and st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
                        st.session_state["game_index"] += 1
                    st.rerun()
    
    st.divider()
    if st.button("⚠️ Son Satırı Sil (Geri Al)"):
        if not df.empty:
            last = df.index[-1].split(" #")[0]
            df = df[:-1]
            df.to_csv(TEMP_GAME_FILE)
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
# 7. PROFİL EKRANI (YENİ PARTNER ANALİZİ İLE)
# =============================================================================

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    
    with st.expander("🔑 Şifre Değiştir"):
        new_pass = st.text_input("Yeni Şifre", type="password")
        if st.button("Güncelle"):
            users = load_json(USERS_FILE, {})
            users[st.session_state["username"]]["password"] = new_pass
            save_json(USERS_FILE, users)
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

    # --- PARTNER ANALİZİ (YENİ ÖZELLİK) ---
    st.divider()
    st.subheader("🤝 Komanditlik Durumu (Kim Uğurlu?)")
    
    partners = my_stats['partnerler']
    if partners:
        # Tablo verisini hazırla
        p_list = []
        for p_name, p_dat in partners.items():
            total = p_dat['birlikte_mac']
            wins = p_dat['beraber_kazanma']
            loss = p_dat['beraber_kaybetme']
            # Beraber kazanma oranı
            p_win_rate = (wins / total * 100) if total > 0 else 0
            
            p_list.append({
                "Komandit": p_name,
                "Maç": total,
                "Kazanma %": p_win_rate,
                "Net Skor": p_dat['puan_toplami']
            })
            
        df_p = pd.DataFrame(p_list).sort_values(by="Kazanma %", ascending=False)
        
        # En iyi ve En Kötü Gösterimi
        if not df_p.empty:
            best = df_p.iloc[0]
            worst = df_p.iloc[-1]
            
            col_b, col_w = st.columns(2)
            # Eğer kazanma oranı %50'den büyükse yeşil, yoksa nötr
            if best['Kazanma %'] >= 50:
                col_b.success(f"🍀 En Uğurlu: **{best['Partner']}**\n(Beraberken kazanma oranı: %{best['Kazanma %']:.1f})")
            else:
                col_b.info(f"🍀 En Uğurlu: **{best['Partner']}**\n(Beraberken kazanma oranı: %{best['Kazanma %']:.1f})")
                
            col_w.error(f"💀 En Uğursuz: **{worst['Partner']}**\n(Beraberken kazanma oranı: %{worst['Kazanma %']:.1f})")
        
        st.dataframe(df_p.style.format({"Kazanma %": "{:.1f}%"}), use_container_width=True)
    else:
        st.info("Henüz yeterli komanditlik verisi yok.")

# =============================================================================
# 8. YÖNETİM PANELİ (PATRON ÖZEL ANALİZ EKLENDİ)
# =============================================================================

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim Paneli</h2>", unsafe_allow_html=True)
    users = load_json(USERS_FILE, {})
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
                if u_name in users and current_user_role != "patron":
                    st.error("Yetkisiz işlem.")
                else:
                    users[u_name] = {"password": u_pass, "role": u_role}
                    save_json(USERS_FILE, users)
                    st.success(f"✅ {u_name} eklendi.")

    st.divider()
    
    # --- PATRON ÖZEL: OYUNCU ANALİZİ (YENİ) ---
    if current_user_role == "patron":
        st.subheader("🕵️ Patron Özel: Oyuncu Röntgeni")
        st.info("İstediğin oyuncuyu seçip profilini ve komandit analizlerini görebilirsin.")
        
        target_user = st.selectbox("İncelenecek Oyuncu:", list(users.keys()))
        
        if target_user:
            data = istatistikleri_hesapla()
            if data and target_user in data:
                # Profil Sayfasındaki Mantığın Aynısını Burada Gösteriyoruz
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

        st.divider()
        st.subheader("📋 Kullanıcı Yönetimi")
        for u, data in users.items():
            with st.expander(f"Düzenle: {u} ({data['role']})"):
                new_p = st.text_input(f"Şifre ({u})", value=data['password'], key=f"pass_{u}")
                new_r = st.selectbox(f"Rol ({u})", ["user", "admin", "patron"], index=["user", "admin", "patron"].index(data['role']), key=f"role_{u}")
                if st.button("Güncelle", key=f"btn_{u}"):
                    users[u]["password"] = new_p
                    users[u]["role"] = new_r
                    save_json(USERS_FILE, users)
                    st.rerun()
    else:
        st.subheader("📋 Kullanıcı Listesi")
        display_data = {k: v['role'] for k, v in users.items()}
        st.table(pd.DataFrame(display_data.items(), columns=["Kullanıcı", "Yetki"]))

# =============================================================================
# 9. ANA UYGULAMA ÇATISI (MAIN)
# =============================================================================

st.set_page_config(page_title="King Pro Ultimate", layout="wide", page_icon="👑")
inject_custom_css()

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    with st.sidebar:
        st.markdown(f"### 👑 {st.session_state['username']}")
        st.caption(f"Yetki: {st.session_state['role'].upper()}")

        
        menu = ["📊 İstatistikler", "👤 Profilim"]
        if st.session_state["role"] in ["admin", "patron"]:
            menu = ["🎮 Oyun Masası", "🛠️ Yönetim Paneli"] + menu
            
        choice = st.radio("Navigasyon", menu)
        st.markdown("---")
        if st.button("Çıkış Yap"):
            logout()
    
    if choice == "🎮 Oyun Masası": game_interface()
    elif choice == "📊 İstatistikler": stats_interface()
    elif choice == "👤 Profilim": profile_interface()
    elif choice == "🛠️ Yönetim Paneli": admin_panel()
