# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL CSS: RESİMDEKİ GİBİ TABLO ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. SADECE TABLO ALANI (PARŞÖMEN KUTUSU) */
        .king-table-container {
            background-color: #fdfbf7; /* Krem Rengi */
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png"); /* Hafif Doku */
            padding: 20px;
            border: 2px solid #2c1e12;
            border-radius: 5px;
            box-shadow: 0 0 20px rgba(0,0,0,0.7); /* Siyah zemin üstünde parlama */
            max-width: 1000px;
            margin: 0 auto;
            color: #2c1e12;
            font-family: 'Courier New', Courier, monospace;
        }

        /* 2. BAŞLIK */
        .king-header {
            text-align: center;
            border-bottom: 3px double #2c1e12;
            margin-bottom: 15px;
            padding-bottom: 10px;
        }
        .king-title {
            font-size: 2.2em;
            color: #8b0000; /* Kiremit Kırmızısı */
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 0;
        }

        /* 3. TABLO YAPISI (Izgara Görünümü) */
        /* Satır İsimleri */
        .row-name {
            font-weight: bold;
            font-size: 1em;
            display: flex;
            align-items: center;
            height: 40px; /* Yükseklik sabitleme */
            border-bottom: 1px solid #ccc;
        }

        /* 4. INPUT KUTULARI (Hücreler) */
        /* Streamlit inputlarını tablo hücresine benzetme */
        div[data-testid="stNumberInput"] {
            margin: 0 !important;
        }

        div[data-testid="stNumberInput"] input {
            background-color: transparent !important;
            color: #2c1e12 !important;
            border: 1px solid #ccc !important; /* Hücre kenarlığı */
            border-radius: 0 !important;
            text-align: center !important;
            font-weight: bold !important;
            font-size: 1.1em !important;
            height: 40px !important;
            padding: 0 !important;
        }

        /* Inputa tıklayınca */
        div[data-testid="stNumberInput"] input:focus {
            background-color: rgba(255, 215, 0, 0.2) !important;
            border: 2px solid #8b0000 !important;
            box-shadow: none !important;
        }

        /* OKLARI GİZLE (Artı/Eksi Yok) */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
        div[data-testid="stNumberInputStepDown"], div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* Sütun Başlıkları */
        .col-header {
            text-align: center;
            font-weight: 900;
            font-size: 1.1em;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            margin-bottom: 5px;
            color: #2c1e12;
        }

        /* Hata Göstergesi */
        .row-error {
            background-color: rgba(255, 0, 0, 0.1);
            border: 1px solid red !important;
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
    
    # Skorlar
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.info("Oyuncuları seçip defteri açın.")
        c1, c2 = st.columns(2)
        with c1: m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
        with c2: 
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
        
        selected = st.multiselect("Oyuncular (4 Kişi):", list(name_to_id.keys()), max_selections=4)
        
        if len(selected) == 4:
            if st.button("📝 Defteri Aç", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    
    # KAĞIT KUTUSU BAŞLANGICI
    st.markdown('<div class="king-table-container">', unsafe_allow_html=True)
    
    # Başlık
    st.markdown(f"""
    <div class="king-header">
        <div class="king-title">{st.session_state['current_match_name']}</div>
        <small>📅 {st.session_state['match_date']}</small>
    </div>
    """, unsafe_allow_html=True)

    # --- SÜTUN BAŞLIKLARI ---
    # Layout: Oyun Adı (2 birim) + 4 Oyuncu (1'er birim)
    cols = st.columns([2, 1, 1, 1, 1])
    with cols[0]: st.markdown('<div class="col-header" style="text-align:left;">OYUN</div>', unsafe_allow_html=True)
    for i, p in enumerate(players):
        with cols[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

    # --- SATIRLARI OLUŞTURMA ---
    rows_structure = []
    
    # 1. CEZALAR
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue
        limit = kural['limit']
        for i in range(1, limit + 1):
            # İsimde sayı olmasın, sadece "Rıfkı" yazsın istedin
            rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})

    # Araya çizgi (Boşluk)
    rows_structure.append({"type": "separator", "label": "--- KOZLAR ---"})

    # 2. KOZLAR (8 Adet)
    for i in range(1, 9):
        rows_structure.append({"id": f"KOZ_{i}", "label": "KOZ", "limit": 13, "puan": 50, "type": "koz"})

    # --- DÖNGÜ İLE TABLO ÇİZİMİ ---
    errors = []
    valid_data_rows = []
    ceza_counters = {k: 0 for k in OYUN_KURALLARI}
    koz_counter = 0
    has_data = False

    for row_info in rows_structure:
        # Ayırıcı satır ise
        if row_info["type"] == "separator":
            st.markdown(f"<div style='text-align:center; font-weight:bold; margin:10px 0; border-top:2px dashed #2c1e12; padding-top:5px;'>{row_info['label']}</div>", unsafe_allow_html=True)
            continue

        # Normal Satır
        c = st.columns([2, 1, 1, 1, 1])
        
        # Oyun İsmi (Sol Sütun)
        with c[0]:
            st.markdown(f'<div class="row-name">{row_info["label"]}</div>', unsafe_allow_html=True)
        
        # Oyuncu Puanları
        current_row_vals = []
        for idx, p in enumerate(players):
            key = f"{row_info['id']}_{p}"
            if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
            
            with c[idx + 1]:
                val = st.number_input(
                    "hidden", min_value=0, max_value=13, step=1, key=key, label_visibility="collapsed"
                )
                current_row_vals.append(val)

        # --- ANLIK KONTROL ---
        row_sum = sum(current_row_vals)
        if row_sum > 0: has_data = True

        if row_sum != 0 and row_sum != row_info["limit"]:
            # Hata varsa ismin yanına ünlem koy ve listeye ekle
            errors.append(f"❌ {row_info['label']}: {row_sum} girildi (Olması gereken: {row_info['limit']})")
            # Burada görsel olarak kırmızı yapmak zor olduğu için alta uyarı basıyoruz
            
        # Veri Hazırlama
        if row_sum == row_info["limit"]:
            if row_info["type"] == "koz":
                koz_counter += 1
                db_name = f"Koz (Tümü) {koz_counter}"
            else:
                ceza_counters[row_info["label"]] += 1
                db_name = f"{row_info['label']} {ceza_counters[row_info['label']]}"
            
            converted_scores = [s * row_info["puan"] for s in current_row_vals]
            valid_data_rows.append([db_name] + converted_scores)

    st.markdown('</div>', unsafe_allow_html=True) # KAĞIT KUTUSU BİTİŞ
    
    st.write("") # Boşluk

    # --- HATA RAPORU VE BUTONLAR ---
    c_save, c_cancel = st.columns([2, 1])
    
    if errors:
        st.error("⚠️ KAĞITTA HATALAR VAR! Düzeltmeden kaydedilemez.")
        for e in errors: st.error(e)
    
    with c_save:
        # Kaydet butonu sadece hatasız ve veri varsa aktif gibi davranacak
        if st.button("💾 KAĞIDI İMZALA VE KAYDET", type="primary", use_container_width=True, disabled=(len(errors) > 0 or not has_data)):
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
                st.success("Maç kaydedildi!")
                st.session_state["sheet_active"] = False
                st.session_state["scores"] = {}
                st.rerun()

    with c_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {}
            st.rerun()
