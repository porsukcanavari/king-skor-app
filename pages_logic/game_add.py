# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def inject_white_box_css():
    st.markdown("""
    <style>
        /* 1. KUTUYU BEMBEYAZ YAP */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important; /* BEMBEYAZ */
            border: 1px solid #ccc !important;
            padding: 20px !important;
            border-radius: 5px !important;
            
            /* İÇİNDEKİLERİ AYDINLIK MODA ZORLA */
            /* Bu sayede siyah tema olsa bile içindeki yazılar siyah olur */
            color-scheme: light !important;
            color: black !important;
        }

        /* 2. KUTU İÇİNDEKİ TÜM METİNLERİ SİYAH YAP */
        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: black !important;
            font-family: Arial, sans-serif !important; /* Düz yazı tipi */
        }

        /* 3. INPUT (SAYI GİRİŞ) KUTULARI */
        /* Standart, temiz görünüm */
        div[data-testid="stVerticalBlockBorderWrapper"] input {
            background-color: #f0f2f6 !important; /* Hafif gri kutu */
            color: black !important;
            border: 1px solid #ccc !important;
            border-radius: 4px !important;
            text-align: center !important;
        }

        /* 4. ARTI / EKSİ OKLARINI SİL */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* Başlıklar */
        .sheet-title {
            text-align: center;
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 20px;
            border-bottom: 2px solid black;
        }
        
        .col-header {
            font-weight: bold;
            text-align: center;
            border-bottom: 1px solid black;
            padding-bottom: 5px;
        }

        /* Hata Mesajı */
        .error-text {
            color: red !important;
            font-weight: bold;
            font-size: 0.9em;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_white_box_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State
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

    # --- İŞTE BU KUTU BEMBEYAZ OLACAK ---
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div class="sheet-title">{st.session_state['current_match_name']}</div>
        <div style="text-align:center; margin-bottom:20px;">📅 {st.session_state['match_date']}</div>
        """, unsafe_allow_html=True)

        # Başlıklar
        c = st.columns([1.5, 1, 1, 1, 1])
        with c[0]: st.markdown('<div class="col-header" style="text-align:left">OYUN TÜRÜ</div>', unsafe_allow_html=True)
        for i, p in enumerate(players):
            with c[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

        # Satır Yapısı
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
                st.markdown(f'<div style="text-align:center; margin:15px 0; border-top:1px dashed black; padding-top:5px; font-weight:bold;">{r_info["label"]}</div>', unsafe_allow_html=True)
                continue

            c = st.columns([1.5, 1, 1, 1, 1])
            with c[0]:
                st.markdown(f'<div style="padding-top:10px; font-weight:bold;">{r_info["label"]}</div>', unsafe_allow_html=True)
            
            curr_vals = []
            for idx, p in enumerate(players):
                key = f"{r_info['id']}_{p}"
                if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
                
                with c[idx+1]:
                    val = st.number_input("h", min_value=0, max_value=13, step=1, key=key, label_visibility="collapsed")
                    curr_vals.append(val)
            
            row_sum = sum(curr_vals)
            if row_sum > 0: has_data = True
            
            if row_sum != 0 and row_sum != r_info["limit"]:
                st.markdown(f'<div class="error-text">⚠️ HATA ({row_sum}/{r_info["limit"]})</div>', unsafe_allow_html=True)
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
