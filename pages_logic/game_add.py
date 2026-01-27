# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- 1. CSS: PARŞÖMEN VE ÖZEL INPUTLAR ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* Ana Arka Plan: Sayfanın kendisini parşömen yapıyoruz */
        .stApp {
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            background-color: #fdfbf7;
            background-attachment: fixed;
        }

        /* 2. TABLO İSKELETİ */
        .paper-sheet {
            background-color: rgba(253, 251, 247, 0.9);
            padding: 30px;
            border: 1px solid #d3c6a0;
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
            margin: auto;
            max-width: 1000px;
            font-family: 'Courier New', Courier, monospace;
        }

        /* Başlıklar */
        .paper-header {
            text-align: center;
            border-bottom: 3px double #2c1e12;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }
        .paper-title {
            font-size: 2.5em;
            color: #8b0000;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
        }

        /* 3. INPUT KUTULARINI ÖZELLEŞTİRME */
        /* Streamlit'in standart kutularını "el yazısı alanı" gibi yapıyoruz */
        div[data-testid="stNumberInput"] {
            margin-bottom: -15px !important; /* Satırları sıkılaştır */
        }

        div[data-testid="stNumberInput"] input {
            background-color: transparent !important; /* Arkası şeffaf olsun */
            border: none !important;
            border-bottom: 1px dashed #2c1e12 !important; /* Sadece alt çizgi */
            color: #2c1e12 !important; /* Koyu Kahve Yazı */
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            font-size: 1.1em !important;
            text-align: center !important;
            padding: 0 !important;
            border-radius: 0 !important;
            height: 30px !important;
        }

        /* Inputa tıklayınca */
        div[data-testid="stNumberInput"] input:focus {
            background-color: rgba(230, 222, 195, 0.3) !important;
            border-bottom: 2px solid #8b0000 !important;
            box-shadow: none !important;
        }

        /* Arttır/Azalt (+/-) butonlarını gizle, temiz dursun */
        button[kind="secondaryFormSubmit"] { display: none; }
        div[data-testid="stNumberInputStepDown"] { display: none !important; }
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* Satır İsimleri */
        .row-label {
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            color: #2c1e12;
            padding-top: 5px;
            font-size: 1.1em;
        }
        
        /* Oyuncu İsimleri (Sütun Başlıkları) */
        .player-header {
            font-family: 'Courier New', Courier, monospace;
            font-weight: 900;
            color: #8b0000;
            text-align: center;
            font-size: 1.2em;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }

        /* Sadece bu sayfadaki butonlar */
        .stButton button {
            border: 2px solid #2c1e12 !important;
            color: #2c1e12 !important;
            background-color: #e6dec3 !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
        }
        .stButton button:hover {
            background-color: #2c1e12 !important;
            color: #e6dec3 !important;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_paper_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    # --- SESSION STATE ---
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []
    
    # Skorları tutacağımız sözlük (Session state içinde)
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.markdown("""
        <div class="paper-sheet" style="text-align:center;">
            <h1 class="paper-title">KRALİYET DEFTERİ</h1>
            <p>Maç açılışını yapınız.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
            users = list(name_to_id.keys())
        with c2:
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
            
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("🖋️ Defteri Önüme Getir", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                # Skorları sıfırla
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI (MANUEL TABLO YAPIMI) ---
    players = st.session_state["players"]
    
    # Ana Çerçeve Başlangıcı
    st.markdown('<div class="paper-sheet">', unsafe_allow_html=True)
    
    # Başlık
    st.markdown(f"""
    <div class="paper-header">
        <div class="paper-title">{st.session_state['current_match_name']}</div>
        <div>📅 {st.session_state['match_date']}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- TABLO BAŞLIKLARI (Manuel Grid) ---
    cols = st.columns([1.5, 1, 1, 1, 1])
    with cols[0]: st.markdown('<div class="player-header">OYUN</div>', unsafe_allow_html=True)
    with cols[1]: st.markdown(f'<div class="player-header">{players[0]}</div>', unsafe_allow_html=True)
    with cols[2]: st.markdown(f'<div class="player-header">{players[1]}</div>', unsafe_allow_html=True)
    with cols[3]: st.markdown(f'<div class="player-header">{players[2]}</div>', unsafe_allow_html=True)
    with cols[4]: st.markdown(f'<div class="player-header">{players[3]}</div>', unsafe_allow_html=True)

    # --- SATIRLARI OLUŞTURMA ---
    # Bu veriyi toplamak için geçici bir liste
    rows_structure = []

    # 1. CEZALAR
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue
        limit = kural['limit']
        for i in range(1, limit + 1):
            row_id = f"{oyun_adi}_{i}"
            rows_structure.append({"id": row_id, "label": oyun_adi, "type": "ceza", "limit": kural['adet'], "puan": kural['puan']})

    # 2. KOZLAR (8 Adet)
    for i in range(1, 9):
        row_id = f"KOZ_{i}"
        rows_structure.append({"id": row_id, "label": "KOZ", "type": "koz", "limit": 13, "puan": 50})

    # --- DÖNGÜ İLE INPUTLARI YERLEŞTİRME ---
    for row in rows_structure:
        c = st.columns([1.5, 1, 1, 1, 1])
        
        # 1. Sütun: Oyun İsmi
        with c[0]:
            st.markdown(f'<div class="row-label">{row["label"]}</div>', unsafe_allow_html=True)
        
        # 2-5. Sütunlar: Oyuncu Inputları
        for idx, p in enumerate(players):
            key = f"{row['id']}_{p}"
            # Varsayılan değer 0
            if key not in st.session_state["scores"]:
                st.session_state["scores"][key] = 0
            
            with c[idx + 1]:
                # Native number_input kullanıyoruz ama CSS ile şeklini değiştirdik
                val = st.number_input(
                    "gizli", # Label gizli
                    min_value=0, 
                    max_value=13, 
                    step=1, 
                    key=key, 
                    label_visibility="collapsed"
                )

    st.markdown("</div>", unsafe_allow_html=True) # Kağıt Bitişi
    st.write("") # Boşluk

    # --- KONTROL VE KAYIT ---
    col_save, col_cancel = st.columns([2, 1])
    
    errors = []
    valid_data_rows = []
    
    # Verileri Toplama ve Kontrol Etme
    # Ceza sayaçları (Rıfkı 1, Rıfkı 2 için)
    ceza_counters = {k: 0 for k in OYUN_KURALLARI}
    koz_counter = 0

    has_data = False # Hiç veri girilmiş mi?

    for row_info in rows_structure:
        # Bu satırdaki oyuncu puanlarını al
        current_row_scores = [st.session_state["scores"][f"{row_info['id']}_{p}"] for p in players]
        row_sum = sum(current_row_scores)
        
        if row_sum > 0: has_data = True

        # Boş satırsa (0) geç (henüz oynanmamış)
        if row_sum == 0:
            continue

        # Kontrol
        if row_sum != row_info["limit"]:
            errors.append(f"❌ **{row_info['label']}**: Toplam {row_info['limit']} olmalı (Şu an: {row_sum})")
        else:
            # Veri Hazırlama (Veritabanı için isimlendirme)
            db_name = ""
            if row_info["type"] == "koz":
                koz_counter += 1
                db_name = f"Koz (Tümü) {koz_counter}"
            else:
                ceza_counters[row_info["label"]] += 1
                db_name = f"{row_info['label']} {ceza_counters[row_info['label']]}"
            
            # Puan Çevirimi
            converted_scores = [score * row_info["puan"] for score in current_row_scores]
            
            # Satırı kaydet
            valid_data_rows.append([db_name] + converted_scores)

    if not errors and valid_data_rows:
        with col_save:
            if st.button("💾 DEFTERİ KAPAT VE KAYDET", use_container_width=True):
                # Toplamlar
                final_total = ["TOPLAM"]
                for i in range(4):
                    col_total = sum([r[i+1] for r in valid_data_rows])
                    final_total.append(col_total)
                
                header = ["OYUN TÜRÜ"]
                for p in players:
                    uid = name_to_id.get(p, "?")
                    header.append(f"{p} (uid:{uid})")

                if save_match_to_sheet(header, valid_data_rows, final_total):
                    st.balloons()
                    st.success("Kayıt Başarılı!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {}
                    st.rerun()
    elif errors:
        with col_save:
            st.warning("⚠️ Hatalar var, düzeltin:")
            for e in errors: st.write(e)
    elif not has_data:
        with col_save:
            st.info("Defter boş. Lütfen doldurun.")

    with col_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {}
            st.rerun()
