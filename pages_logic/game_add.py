# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def inject_ghost_table_css():
    st.markdown("""
    <style>
        /* 1. PARŞÖMEN ZEMİNİ (Olayın Merkezi) */
        /* st.container(border=True) ile oluşturulan kutuyu yakalıyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            /* O sevdiğin doku ve renk */
            background-color: #fdfbf7 !important;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png") !important;
            
            /* Kutu Süslemeleri */
            border: 1px solid #d3c6a0 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important;
            padding: 30px !important;
            border-radius: 3px !important;
            
            /* İçindekileri Aydınlık Moda Zorla (Siyah tema olsa bile yazı siyah olsun) */
            color-scheme: light !important;
        }

        /* 2. INPUT KUTULARINI ŞEFFAF YAP (HAYALET MODU) */
        /* İşte aradığın kod burası: Arkaplanı yok ediyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] input {
            background-color: transparent !important; /* ŞEFFAF! Arkadaki kağıdı gör */
            color: #2c1e12 !important; /* Mürekkep rengi */
            
            /* Çerçeveyi kaldır, sadece alt çizgi koy (Defter satırı gibi) */
            border: none !important;
            border-bottom: 1px solid #8b7d6b !important; 
            border-radius: 0 !important;
            
            text-align: center !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            font-size: 1.3em !important;
            padding: 0 !important;
            height: 40px !important;
        }

        /* Tıklayınca da beyaz olmasın, şeffaf kalsın */
        div[data-testid="stVerticalBlockBorderWrapper"] input:focus {
            background-color: transparent !important;
            border-bottom: 2px solid #8b0000 !important; /* Tıklayınca çizgi kalınlaşsın */
            box-shadow: none !important;
        }

        /* 3. ARTI / EKSİ OKLARINI YOK ET */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* 4. TABLO ÇİZGİLERİ VE YAZILAR */
        /* Metinlerin Rengi */
        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: #2c1e12 !important;
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* Satır İsimleri (Sol Sütun) */
        .row-label {
            font-weight: bold;
            font-size: 1.1em;
            padding-top: 10px;
            border-right: 2px solid #2c1e12; /* İsimleri tablodan ayıran dikey çizgi */
            height: 100%;
            display: flex;
            align-items: center;
        }

        /* Sütun Başlıkları */
        .col-header {
            text-align: center;
            font-weight: 900;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 10px;
            margin-bottom: 10px;
            font-size: 1.2em;
        }

        /* Ayırıcı (Kozlar) */
        .separator {
            text-align: center;
            font-weight: 900;
            margin: 15px 0;
            border-top: 2px dashed #2c1e12;
            padding-top: 10px;
        }

        /* Hata */
        .error-msg {
            color: #d93025 !important;
            font-size: 0.8em;
            text-align: center;
            font-weight: bold;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_ghost_table_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI (Normal Siyah Tema) ---
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

    # --- 2. DEFTER EKRANI (PARŞÖMEN) ---
    players = st.session_state["players"]

    # === PARŞÖMEN ALANI ===
    # Bu 'with' bloğu CSS'teki kurallara göre PARŞÖMENE dönüşecek
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div style="text-align:center; border-bottom:3px double #2c1e12; padding-bottom:15px; margin-bottom:20px;">
            <h1 style="margin:0; font-size:2.5em; text-transform:uppercase; color:#8b0000 !important;">{st.session_state['current_match_name']}</h1>
            <div style="font-style:italic;">📅 {st.session_state['match_date']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Tablo Başlıkları
        c = st.columns([1.5, 1, 1, 1, 1])
        with c[0]: st.markdown('<div class="col-header" style="text-align:left;">OYUN</div>', unsafe_allow_html=True)
        for i, p in enumerate(players):
            with c[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

        # Veri Hazırlığı
        rows_structure = []
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})
        
        rows_structure.append({"type": "sep", "label": "KOZLAR"})
        
        for i in range(1, 9):
            rows_structure.append({"id": f"KOZ_{i}", "label": "KOZ", "limit": 13, "puan": 50, "type": "koz"})

        # --- DÖNGÜ (IZGARA ÇİZİMİ) ---
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
            
            # SOL SÜTUN (İSİM)
            with c[0]:
                st.markdown(f'<div class="row-label">{r_info["label"]}</div>', unsafe_allow_html=True)
            
            # SAĞ SÜTUNLAR (ŞEFFAF INPUTLAR)
            curr_vals = []
            for idx, p in enumerate(players):
                key = f"{r_info['id']}_{p}"
                if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
                
                with c[idx+1]:
                    # BU INPUT ŞEFFAF OLACAK
                    val = st.number_input(
                        "h", 
                        min_value=0, max_value=13, step=1, 
                        key=key, 
                        label_visibility="collapsed"
                    )
                    curr_vals.append(val)
            
            # Kontrol
            row_sum = sum(curr_vals)
            if row_sum > 0: has_data = True
            
            if row_sum != 0 and row_sum != r_info["limit"]:
                st.markdown(f'<div class="error-msg">⚠️ ({row_sum}/{r_info["limit"]})</div>', unsafe_allow_html=True)
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

    # === PARŞÖMEN BİTTİ ===
    
    st.write("")
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        if st.button("💾 DEFTERİ KAYDET", type="primary", use_container_width=True):
            if errors:
                st.error("Kırmızı hataları düzeltin.")
            elif not has_data:
                st.warning("Defter boş.")
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
