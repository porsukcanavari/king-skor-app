# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. PARŞÖMEN ZEMİN (Konteyner) */
        /* Streamlit'in border=True kutusunu yakalayıp kağıda çeviriyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #fcfbf4;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            border: 2px solid #2c1e12 !important;
            border-radius: 5px;
            padding: 20px !important;
            box-shadow: 0 0 15px rgba(0,0,0,0.5);
            /* Dark mode gelse bile burayı aydınlık yap */
            color-scheme: light !important; 
        }

        /* 2. YAZILAR VE BAŞLIKLAR */
        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: #2c1e12 !important; /* Mürekkep rengi */
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: 600 !important;
        }

        /* 3. INPUT KUTULARI (HAYALET MODU) */
        /* Kutunun kendisini yok et, sadece alt çizgi kalsın */
        div[data-testid="stVerticalBlockBorderWrapper"] input {
            background-color: rgba(255,255,255,0.3) !important;
            border: none !important;
            border-bottom: 2px solid #aaa !important; /* Satır çizgisi */
            border-radius: 0 !important;
            color: black !important;
            text-align: center !important;
            font-size: 1.2em !important;
            height: 40px !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Tıklayınca çizgi kalınlaşsın */
        div[data-testid="stVerticalBlockBorderWrapper"] input:focus {
            border-bottom: 3px solid #8b0000 !important;
            box-shadow: none !important;
            background-color: rgba(255,255,255,0.6) !important;
        }

        /* 4. ARTI / EKSİ OKLARINI SİL */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* Başlık Stili */
        .sheet-header {
            text-align: center;
            border-bottom: 3px double #2c1e12;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .sheet-title {
            font-size: 2.2em;
            color: #8b0000 !important;
            font-weight: 900;
            text-transform: uppercase;
            margin: 0;
        }

        /* Tablo Başlıkları */
        .col-header {
            font-weight: 900;
            text-align: center;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            margin-bottom: 5px;
            font-size: 1.1em;
        }

        .row-label {
            font-weight: bold;
            font-size: 1.1em;
            padding-top: 10px;
            display: block;
        }

        /* Ayırıcı */
        .separator {
            text-align: center;
            font-weight: 900;
            margin: 20px 0;
            border-top: 2px dashed #2c1e12;
            padding-top: 10px;
        }
        
        /* Hata Mesajı */
        .error-badge {
            color: #d93025 !important;
            font-size: 0.8em;
            font-weight: bold;
            border-top: 1px solid #d93025;
            text-align: center;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_paper_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. SEÇİM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.info("Defteri açmak için oyuncuları seçin.")
        c1, c2 = st.columns(2)
        with c1: m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
        with c2: 
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
        
        selected = st.multiselect("Oyuncular (4 Kişi):", list(name_to_id.keys()), max_selections=4)
        
        if len(selected) == 4:
            if st.button("📝 DEFTERİ AÇ", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]

    # BU KUTU PARŞÖMEN OLACAK (CSS SAYESİNDE)
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div class="sheet-header">
            <h1 class="sheet-title">{st.session_state['current_match_name']}</h1>
            <div style="font-style:italic; margin-top:5px;">📅 {st.session_state['match_date']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Tablo Başlıkları
        c = st.columns([1.5, 1, 1, 1, 1])
        with c[0]: st.markdown('<div class="col-header" style="text-align:left">OYUN TÜRÜ</div>', unsafe_allow_html=True)
        for i, p in enumerate(players):
            with c[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

        # Satırlar
        rows_structure = []
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})
        
        rows_structure.append({"type": "sep", "label": "--- KOZLAR ---"})
        
        for i in range(1, 9):
            rows_structure.append({"id": f"KOZ_{i}", "label": "KOZ", "limit": 13, "puan": 50, "type": "koz"})

        # Input Döngüsü
        errors = []
        valid_rows = []
        ceza_c = {k:0 for k in OYUN_KURALLARI}
        koz_c = 0
        has_data = False

        for r_info in rows_structure:
            if r_info.get("type") == "sep":
                st.markdown(f'<div class="separator">{r_info["label"]}</div>', unsafe_allow_html=True)
                continue

            c = st.columns([1.5, 1, 1, 1, 1])
            with c[0]:
                st.markdown(f'<div class="row-label">{r_info["label"]}</div>', unsafe_allow_html=True)
            
            curr_vals = []
            for idx, p in enumerate(players):
                key = f"{r_info['id']}_{p}"
                if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
                
                with c[idx+1]:
                    val = st.number_input("h", min_value=0, max_value=13, step=1, key=key, label_visibility="collapsed")
                    curr_vals.append(val)
            
            # Kontrol
            row_sum = sum(curr_vals)
            if row_sum > 0: has_data = True
            
            if row_sum != 0 and row_sum != r_info["limit"]:
                st.markdown(f'<div class="error-badge">⚠️ HATA ({row_sum}/{r_info["limit"]})</div>', unsafe_allow_html=True)
                errors.append(f"{r_info['label']} hatası")
            
            if row_sum == r_info["limit"]:
                if r_info["type"] == "koz":
                    koz_c += 1
                    db_name = f"Koz (Tümü) {koz_c}"
                else:
                    ceza_c[r_info["label"]] += 1
                    db_name = f"{r_info['label']} {ceza_c[r_info['label']]}"
                
                calcs = [v * r_info["puan"] for v in curr_vals]
                valid_rows.append([db_name] + calcs)

    # --- BUTONLAR ---
    st.write("")
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        if st.button("💾 DEFTERİ KAYDET", type="primary", use_container_width=True):
            if errors:
                st.error("⚠️ Hataları düzeltin.")
            elif not has_data:
                st.warning("Boş defter kaydedilemez.")
            else:
                total_row = ["TOPLAM"]
                for i in range(4):
                    total_row.append(sum([r[i+1] for r in valid_rows]))
                
                header = ["OYUN TÜRÜ"]
                for p in players:
                    header.append(f"{p} (uid:{name_to_id.get(p, '?')})")
                
                if save_match_to_sheet(header, valid_rows, total_row):
                    st.success("Kaydedildi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {}
                    st.rerun()
    
    with c_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.rerun()
