# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def inject_parchment_css():
    st.markdown("""
    <style>
        /* 1. PARŞÖMEN ZEMİNİ (KONTEYNER) */
        /* Streamlit'in border=True kutusunu yakalayıp kağıda çeviriyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #fdfbf7 !important; /* Krem Rengi */
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png") !important;
            border: 2px solid #8b7d6b !important; /* Kahve Çerçeve */
            box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important; /* Gölge */
            padding: 25px !important;
            border-radius: 3px !important;
            
            /* İÇERİĞİ AYDINLIK MODA ZORLA (Siyah tema olsa bile) */
            color-scheme: light !important;
            color: #2c1e12 !important;
        }

        /* 2. TABLO ÇİZGİLERİ VE YAPISI */
        /* Her sütunu ve satırı çizgiyle ayıracağız */
        
        /* Satır İsimleri (Oyun Adları) */
        .row-label {
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            font-size: 1.1em;
            color: #2c1e12;
            padding: 12px 5px;
            border-bottom: 1px solid #8b7d6b; /* Satır Çizgisi */
            border-right: 2px solid #2c1e12;  /* İsim sütunu ayracı (Dikey) */
        }

        /* 3. ŞEFFAF INPUT KUTULARI (HAYALET TABLO) */
        div[data-testid="stNumberInput"] {
            border-bottom: 1px solid #8b7d6b !important; /* Satır Çizgisi */
            margin: 0 !important;
        }

        div[data-testid="stNumberInput"] input {
            background-color: transparent !important; /* ŞEFFAF! Arkadaki kağıdı gör */
            border: none !important; /* Kutu çerçevesi yok */
            border-left: 1px dashed #d3c6a0 !important; /* Sütunlar arası hafif çizgi */
            border-radius: 0 !important;
            color: #2c1e12 !important; /* Mürekkep rengi */
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            font-size: 1.2em !important;
            text-align: center !important;
            padding: 10px 0 !important;
            height: 45px !important;
        }

        /* Tıklayınca (Focus) */
        div[data-testid="stNumberInput"] input:focus {
            background-color: rgba(255, 215, 0, 0.1) !important; /* Hafif sarı */
            box-shadow: inset 0 0 0 2px #8b0000 !important; /* İç çerçeve */
        }

        /* 4. ARTI / EKSİ OKLARINI YOK ET */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* Başlıklar */
        .sheet-header {
            text-align: center;
            border-bottom: 3px double #2c1e12;
            padding-bottom: 15px;
            margin-bottom: 10px;
        }
        .sheet-title {
            font-family: 'Courier New', Courier, monospace;
            font-size: 2.2em;
            color: #8b0000 !important;
            font-weight: 900;
            text-transform: uppercase;
            margin: 0;
            text-shadow: 1px 1px 0 rgba(255,255,255,0.5);
        }

        /* Sütun Başlıkları (Oyuncular) */
        .col-header {
            font-family: 'Courier New', Courier, monospace;
            font-weight: 900;
            text-align: center;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            font-size: 1.2em;
            color: #2c1e12;
        }

        /* Ayırıcı (Kozlar Bölümü) */
        .separator {
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
            font-weight: 900;
            margin: 0;
            background-color: rgba(44, 30, 18, 0.1); /* Hafif koyu şerit */
            padding: 5px;
            border-top: 2px solid #2c1e12;
            border-bottom: 2px solid #2c1e12;
        }

        /* Hata Mesajı */
        .error-msg {
            color: #d93025 !important;
            font-weight: bold;
            font-size: 0.8em;
            text-align: center;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_parchment_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI (Normal Görünüm) ---
    if not st.session_state["sheet_active"]:
        st.info("Defteri hazırlamak için oyuncuları seçin.")
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
    # border=True kullanarak CSS'teki "Kağıt" efektini tetikliyoruz
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div class="sheet-header">
            <h1 class="sheet-title">{st.session_state['current_match_name']}</h1>
            <div style="font-style:italic;">📅 {st.session_state['match_date']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Tablo Başlıkları (Sütunlar)
        # Oranları ayarladık: İsim sütunu biraz geniş, diğerleri eşit
        cols = st.columns([1.5, 1, 1, 1, 1])
        with cols[0]: st.markdown('<div class="col-header" style="text-align:left;">OYUN</div>', unsafe_allow_html=True)
        for i, p in enumerate(players):
            with cols[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

        # --- SATIRLARI OLUŞTURMA ---
        rows_structure = []
        # Cezalar
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})
        
        # Ayırıcı
        rows_structure.append({"type": "sep", "label": "KOZLAR"})
        
        # Kozlar
        for i in range(1, 9):
            rows_structure.append({"id": f"KOZ_{i}", "label": "KOZ", "limit": 13, "puan": 50, "type": "koz"})

        # --- DÖNGÜ VE ŞEFFAF INPUTLAR ---
        errors = []
        valid_rows = []
        ceza_c = {k:0 for k in OYUN_KURALLARI}
        koz_c = 0
        has_data = False

        for r_info in rows_structure:
            # Ayırıcı Satır
            if r_info.get("type") == "sep":
                st.markdown(f'<div class="separator">{r_info["label"]}</div>', unsafe_allow_html=True)
                continue

            c = st.columns([1.5, 1, 1, 1, 1])
            
            # Satır İsmi
            with c[0]:
                st.markdown(f'<div class="row-label">{r_info["label"]}</div>', unsafe_allow_html=True)
            
            # Oyuncu Puanları (Inputlar)
            curr_vals = []
            for idx, p in enumerate(players):
                key = f"{r_info['id']}_{p}"
                if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
                
                with c[idx+1]:
                    # NATIVE INPUT (Ama CSS ile şeffaflaştırıldı)
                    val = st.number_input(
                        "hidden", 
                        min_value=0, max_value=13, step=1, 
                        key=key, 
                        label_visibility="collapsed"
                    )
                    curr_vals.append(val)
            
            # Kontrol
            row_sum = sum(curr_vals)
            if row_sum > 0: has_data = True
            
            # Hata varsa (Kırmızı küçük not)
            if row_sum != 0 and row_sum != r_info["limit"]:
                st.markdown(f'<div class="error-msg">⚠️ ({row_sum}/{r_info["limit"]})</div>', unsafe_allow_html=True)
                errors.append(f"{r_info['label']} hatası")
            
            # Veri Hazırlama
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

    # --- BUTONLAR (Kağıdın Altında, Siyah Zeminde) ---
    st.write("")
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        if st.button("💾 DEFTERİ KAYDET", type="primary", use_container_width=True):
            if errors:
                st.error("⚠️ Defterde tutarsızlıklar var (kırmızı uyarılar). Düzeltin.")
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
                    st.balloons()
                    st.success("Maç kaydedildi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {}
                    st.rerun()
    
    with c_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.rerun()
