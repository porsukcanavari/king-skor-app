# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def inject_paper_css():
    st.markdown("""
    <style>
        /* --- 1. GLOBAL DEĞİŞKENLERİ EZİYORUZ (STREAMLIT TEMASINI YOK ETME) --- */
        :root {
            --primary-color: #8b0000;
            --background-color: #fdfbf7;
            --secondary-background-color: #f0e6d2;
            --text-color: #2c1e12;
            --font: "Courier New", monospace;
        }

        /* --- 2. ANA GÖVDEYİ KAĞIT YAPMA --- */
        /* Uygulamanın ana konteynerini zorla kağıt rengine boyuyoruz */
        .stAppViewContainer {
            background-color: #fdfbf7 !important;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png") !important;
            color: #2c1e12 !important;
        }
        
        /* Yan menü (Sidebar) hariç ana blok */
        section[data-testid="stMain"] {
            background-color: transparent !important;
        }

        /* --- 3. INPUT (SAYI GİRİŞ) KUTULARI --- */
        /* Kutuları şeffaf yapıp sadece alt çizgi koyuyoruz */
        div[data-testid="stNumberInput"] {
            background-color: transparent !important;
            border: none !important;
        }

        div[data-testid="stNumberInput"] input {
            background-color: rgba(255, 255, 255, 0.3) !important; /* Hafif beyazlık */
            color: #000000 !important; /* KESİN SİYAH YAZI */
            border: none !important;
            border-bottom: 2px dashed #8b7d6b !important;
            text-align: center !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: 900 !important;
            font-size: 1.2rem !important;
            padding: 0 !important;
            border-radius: 0 !important;
            caret-color: black !important; /* İmleç rengi */
            box-shadow: none !important;
        }

        /* Tıklayınca */
        div[data-testid="stNumberInput"] input:focus {
            background-color: rgba(255, 215, 0, 0.2) !important;
            border-bottom: 2px solid #8b0000 !important;
            color: #000000 !important;
        }

        /* --- 4. ARTI / EKSİ OKLARINI YOK ETME --- */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; 
            margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { 
            display: none !important; 
        }

        /* --- 5. METİNLER VE BAŞLIKLAR --- */
        h1, h2, h3, p, label, span, div {
            color: #2c1e12 !important; /* Her şeyi koyu kahveye zorla */
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* Özel Sınıflar */
        .sheet-header {
            text-align: center;
            border: 3px double #2c1e12;
            padding: 20px;
            margin-bottom: 30px;
            background: rgba(0,0,0,0.02);
        }
        
        .game-title {
            font-size: 3em !important;
            color: #8b0000 !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin: 0 !important;
            text-shadow: 1px 1px 0px rgba(255,255,255,0.5);
        }

        .row-label {
            font-size: 1.1em;
            font-weight: bold;
            display: flex;
            align-items: center;
            height: 100%;
        }

        .error-text {
            color: #d93025 !important;
            font-weight: bold;
            font-size: 0.9em;
            border-top: 1px solid #d93025;
            margin-top: 2px;
        }

        /* Butonlar */
        button[kind="primary"] {
            background-color: #2c1e12 !important;
            color: #fdfbf7 !important;
            border: none !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        button[kind="primary"]:hover {
            background-color: #8b0000 !important;
        }
        
        /* Selectbox ve Checkbox Metinleri */
        div[data-baseweb="select"] span {
            color: #2c1e12 !important;
        }
        label[data-testid="stCheckbox"] span {
            color: #2c1e12 !important;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    # CSS'i enjekte et
    inject_paper_css()
    
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []
    
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.markdown("<div class='sheet-header'><h1 class='game-title'>DEFTER AÇILIŞI</h1></div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1: m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
        with c2: 
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
        
        selected = st.multiselect("Oyuncular (4 Kişi):", list(name_to_id.keys()), max_selections=4)
        
        if len(selected) == 4:
            if st.button("📝 DEFTERİ GETİR", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        else:
            if len(selected) > 0:
                st.warning("Lütfen tam 4 kişi seçiniz.")
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    
    # KAĞIT BAŞLIK
    st.markdown(f"""
    <div class="sheet-header">
        <h1 class="game-title">{st.session_state['current_match_name']}</h1>
        <p style="margin-top:10px;">📅 {st.session_state['match_date']} | 👥 MASADAKİLER</p>
    </div>
    """, unsafe_allow_html=True)

    # OYUNCU İSİMLERİ (Başlıklar)
    cols = st.columns([1.5, 1, 1, 1, 1])
    with cols[0]: st.markdown("<div style='font-weight:900; font-size:1.2em; border-bottom:2px solid black;'>OYUN</div>", unsafe_allow_html=True)
    for i, p in enumerate(players):
        with cols[i+1]: st.markdown(f"<div style='font-weight:900; text-align:center; font-size:1.2em; border-bottom:2px solid black;'>{p}</div>", unsafe_allow_html=True)

    # --- SATIRLARI OLUŞTURMA ---
    rows_structure = []
    # 1. Cezalar
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue
        limit = kural['limit']
        for i in range(1, limit + 1):
            rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})

    # Araya çizgi
    rows_structure.append({"type": "sep", "label": "--- KOZLAR ---"})

    # 2. Kozlar
    for i in range(1, 9):
        rows_structure.append({"id": f"KOZ_{i}", "label": "KOZ", "limit": 13, "puan": 50, "type": "koz"})

    # --- DÖNGÜ ---
    errors = []
    valid_data_rows = []
    ceza_counters = {k: 0 for k in OYUN_KURALLARI}
    koz_counter = 0
    has_data = False

    for row_info in rows_structure:
        # Ayırıcı
        if row_info.get("type") == "sep":
            st.markdown(f"<div style='text-align:center; margin:20px 0; border-top:2px dashed #2c1e12; padding-top:10px; font-weight:900;'>{row_info['label']}</div>", unsafe_allow_html=True)
            continue

        c = st.columns([1.5, 1, 1, 1, 1])
        
        # Satır Adı
        with c[0]:
            st.markdown(f"<div class='row-label'>{row_info['label']}</div>", unsafe_allow_html=True)
        
        # Inputlar
        current_vals = []
        for idx, p in enumerate(players):
            key = f"{row_info['id']}_{p}"
            if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
            
            with c[idx + 1]:
                # Streamlit Input (CSS ile tanınmaz halde)
                val = st.number_input(
                    "hidden", min_value=0, max_value=13, step=1, 
                    key=key, label_visibility="collapsed"
                )
                current_vals.append(val)

        # MÜFETTİŞ
        row_sum = sum(current_vals)
        if row_sum > 0: has_data = True

        if row_sum != 0 and row_sum != row_info["limit"]:
            st.markdown(f"<div class='error-text'>⚠️ HATA: {row_sum} (Olması gereken: {row_info['limit']})</div>", unsafe_allow_html=True)
            errors.append(f"{row_info['label']} hatası")
        
        # Veri Hazırlama
        if row_sum == row_info["limit"]:
            if row_info["type"] == "koz":
                koz_counter += 1
                db_name = f"Koz (Tümü) {koz_counter}"
            else:
                ceza_counters[row_info["label"]] += 1
                db_name = f"{row_info['label']} {ceza_counters[row_info['label']]}"
            
            vals = [v * row_info["puan"] for v in current_vals]
            valid_data_rows.append([db_name] + vals)

    st.write("")
    st.markdown("---")
    
    # --- BUTONLAR ---
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        if st.button("💾 DEFTERİ İMZALA VE KAYDET", type="primary", use_container_width=True):
            if errors:
                st.error("⚠️ Defterde hatalar var! Kırmızı uyarıları düzeltin.")
            elif not has_data:
                st.warning("Defter boş.")
            else:
                final_total = ["TOPLAM"]
                for i in range(4):
                    t = sum([r[i+1] for r in valid_data_rows])
                    final_total.append(t)
                
                header = ["OYUN TÜRÜ"]
                for p in players:
                    uid = name_to_id.get(p, "?")
                    header.append(f"{p} (uid:{uid})")

                if save_match_to_sheet(header, valid_data_rows, final_total):
                    st.balloons()
                    st.success("Maç kaydedildi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {} 
                    st.rerun()

    with c_cancel:
        if st.button("❌ İptal / Yırt At", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {} 
            st.rerun()
