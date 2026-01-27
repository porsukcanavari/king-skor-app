# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- KESİN ÇÖZÜM CSS ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. KUTU HEDEFLEME VE IŞIK AYARI */
        /* Streamlit'in border=True kutusunu yakalıyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            /* BU SATIR ÇOK ÖNEMLİ: Kutu içini Aydınlık Mod'a zorluyoruz */
            color-scheme: light !important; 
            
            /* Parşömen Arka Planı */
            background-color: #fdfbf7;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            
            /* Çerçeve ve Gölge */
            border: 2px solid #8b7d6b !important;
            box-shadow: 0 0 20px rgba(0,0,0,0.8) !important; /* Siyah zemin üstünde parlama */
            padding: 30px !important;
            border-radius: 3px !important;
        }

        /* 2. KUTU İÇİNDEKİ TÜM YAZILAR */
        /* Aydınlık mod olduğu için koyu renk yazı zorunlu */
        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: #2c1e12 !important; /* Koyu Kahve Mürekkep */
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: 600 !important;
        }

        /* 3. INPUT (SAYI GİRİŞ) KUTULARI - HAYALET MODU */
        div[data-testid="stVerticalBlockBorderWrapper"] input {
            background-color: transparent !important; /* Şeffaf */
            color: #000000 !important; /* Simsiyah Yazı */
            border: none !important;
            border-bottom: 2px dashed #a89f91 !important; /* Kesik Çizgi */
            text-align: center !important;
            font-size: 1.3em !important;
            padding: 0 !important;
            border-radius: 0 !important;
            caret-color: black !important; /* İmleç rengi SİYAH olsun */
        }

        /* Inputa tıklayınca */
        div[data-testid="stVerticalBlockBorderWrapper"] input:focus {
            background-color: rgba(230, 222, 195, 0.4) !important;
            border-bottom: 2px solid #8b0000 !important;
            box-shadow: none !important;
        }

        /* 4. ARTI / EKSİ OKLARINI YOK ETME (KESİN) */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; 
            margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { 
            display: none !important; 
        }

        /* 5. BAŞLIK VE SATIR STİLLERİ */
        .sheet-title {
            text-align: center;
            font-size: 2.5em;
            color: #8b0000 !important;
            text-transform: uppercase;
            border-bottom: 3px double #2c1e12;
            padding-bottom: 15px;
            margin-bottom: 20px;
            letter-spacing: 2px;
        }

        .col-header {
            text-align: center;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            font-size: 1.1em;
            font-weight: 900;
        }

        .row-label {
            font-size: 1.1em;
            padding-top: 12px;
            font-weight: bold;
        }

        /* Hata Mesajı */
        .error-msg {
            color: #d93025 !important;
            font-size: 0.9em;
            font-weight: bold;
            text-align: center;
            border-top: 1px solid #d93025;
            margin-top: 5px;
            padding-top: 2px;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_paper_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []
    
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI (Burası Karanlık Modda Kalır) ---
    if not st.session_state["sheet_active"]:
        st.info("Defteri hazırlamak için oyuncuları seçin.")
        c1, c2 = st.columns(2)
        with c1: m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
        with c2: 
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
        
        selected = st.multiselect("Oyuncular (4 Kişi):", list(name_to_id.keys()), max_selections=4)
        
        if len(selected) == 4:
            if st.button("🖋️ Defteri Önüme Getir", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    
    # === PARŞÖMEN KUTUSU BAŞLANGICI ===
    # st.container(border=True) kullandığımız için CSS burayı hedef alıp kağıda çevirecek
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div class="sheet-title">{st.session_state['current_match_name']}</div>
        <div style="text-align:center; font-style:italic; margin-bottom:20px;">
            📅 {st.session_state['match_date']}
        </div>
        """, unsafe_allow_html=True)

        # Sütun Başlıkları
        cols = st.columns([1.5, 1, 1, 1, 1])
        with cols[0]: st.markdown('<div class="col-header" style="text-align:left;">OYUN</div>', unsafe_allow_html=True)
        for i, p in enumerate(players):
            with cols[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

        # --- SATIR YAPISI ---
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

        # --- DÖNGÜ VE INPUTLAR ---
        errors = []
        valid_data_rows = []
        
        ceza_counters = {k: 0 for k in OYUN_KURALLARI}
        koz_counter = 0
        has_data = False

        for row_info in rows_structure:
            if row_info.get("type") == "sep":
                st.markdown(f"<div style='text-align:center; margin:15px 0; border-top:2px dashed #2c1e12; padding-top:5px; font-weight:bold;'>{row_info['label']}</div>", unsafe_allow_html=True)
                continue

            c = st.columns([1.5, 1, 1, 1, 1])
            
            # Satır İsmi
            with c[0]:
                st.markdown(f'<div class="row-label">{row_info["label"]}</div>', unsafe_allow_html=True)
            
            # Inputlar
            current_vals = []
            for idx, p in enumerate(players):
                key = f"{row_info['id']}_{p}"
                if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
                
                with c[idx + 1]:
                    # Input (Tamamen temizlenmiş)
                    val = st.number_input(
                        "hidden", 
                        min_value=0, max_value=13, step=1, 
                        key=key, 
                        label_visibility="collapsed"
                    )
                    current_vals.append(val)

            # --- MÜFETTİŞ ---
            row_sum = sum(current_vals)
            if row_sum > 0: has_data = True

            # Hata varsa uyar
            if row_sum != 0 and row_sum != row_info["limit"]:
                st.markdown(f"""
                <div class="error-msg">
                    ⚠️ Toplam {row_info['limit']} olmalı ({row_sum})
                </div>
                """, unsafe_allow_html=True)
                errors.append(f"{row_info['label']}: Hatalı toplam")
            
            # Veri Hazırlama
            if row_sum == row_info["limit"]:
                if row_info["type"] == "koz":
                    koz_counter += 1
                    db_name = f"Koz (Tümü) {koz_counter}"
                else:
                    ceza_counters[row_info["label"]] += 1
                    db_name = f"{row_info['label']} {ceza_counters[row_info['label']]}"
                
                converted = [v * row_info["puan"] for v in current_vals]
                valid_data_rows.append([db_name] + converted)

    # === PARŞÖMEN BİTTİ ===
    
    st.write("") 

    # --- BUTONLAR ---
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        # Hata varsa buton pasif gibi davranır
        if st.button("💾 DEFTERİ İMZALA VE KAPAT", type="primary", use_container_width=True):
            if errors:
                st.error("⚠️ Defterde hatalı satırlar var. Lütfen kırmızı uyarıları düzeltin.")
            elif not has_data:
                st.warning("Defter boş.")
            else:
                # Toplamlar
                final_total = ["TOPLAM"]
                for i in range(4):
                    col_tot = sum([r[i+1] for r in valid_data_rows])
                    final_total.append(col_tot)
                
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
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {} 
            st.rerun()
