# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL CSS: ESKİ DEFTER / PARŞÖMEN GÖRÜNÜMÜ ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. ARTI / EKSİ BUTONLARINI GİZLE */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type=number] {
            -moz-appearance: textfield;
        }
        div[data-testid="stNumberInputStepDown"],
        div[data-testid="stNumberInputStepUp"] {
            display: none !important;
        }

        /* 2. ANA PARŞÖMEN KUTUSU - ESKİ DEFTER GÖRÜNÜMÜ */
        .antique-container {
            background: linear-gradient(to bottom, #f7f3e8 0%, #f2e9d8 100%);
            background-image: 
                linear-gradient(to bottom, rgba(247, 243, 232, 0.9) 0%, rgba(242, 233, 216, 0.9) 100%),
                url("https://www.transparenttextures.com/patterns/aged-paper.png");
            border: 15px solid;
            border-image: url("https://www.transparenttextures.com/patterns/wood-pattern.png") 30 stretch;
            padding: 25px 30px !important;
            border-radius: 5px;
            box-shadow: 
                0 0 30px rgba(0, 0, 0, 0.4),
                inset 0 0 30px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        /* Kağıt yıpranmış kenar efekti */
        .antique-container::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url("https://www.transparenttextures.com/patterns/paper-fibers.png");
            opacity: 0.15;
            pointer-events: none;
        }

        /* 3. TABLO BAŞLIĞI - ESKİ MÜREKKEP */
        .sheet-title {
            text-align: center;
            font-size: 2.5em;
            font-family: 'Georgia', 'Times New Roman', serif;
            color: #3e2723 !important;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            position: relative;
            padding-bottom: 15px;
        }
        
        .sheet-title::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 25%;
            right: 25%;
            height: 3px;
            background: linear-gradient(to right, transparent, #795548, transparent);
        }

        /* 4. TABLO BAŞLIKLARI - ESKİ TÜKENMEZ KALEM */
        .col-header {
            font-family: 'Courier New', Courier, monospace;
            font-weight: 900;
            text-align: center;
            font-size: 1.2em;
            color: #4e342e !important;
            padding: 10px 5px;
            border-bottom: 3px double #5d4037;
            background: linear-gradient(to bottom, rgba(121, 85, 72, 0.1), transparent);
            border-radius: 3px;
            margin-bottom: 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        /* 5. SATIR ETİKETLERİ - EL YAZISI HİSSİ */
        .row-label {
            font-family: 'Brush Script MT', cursive;
            font-weight: bold;
            font-size: 1.4em;
            color: #3e2723 !important;
            display: flex;
            align-items: center;
            height: 45px;
            padding-left: 10px;
            background: rgba(121, 85, 72, 0.05);
            border-radius: 3px;
            margin-right: 5px;
            border-left: 4px solid #795548;
        }

        /* 6. INPUT KUTULARI - ESKİ DEFTER ÇİZGİLERİ */
        .antique-input {
            background: transparent !important;
            border: none !important;
            border-bottom: 2px solid #8d6e63 !important;
            border-top: 1px dashed #bcaaa4 !important;
            text-align: center !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            font-size: 1.3em !important;
            color: #3e2723 !important;
            height: 45px !important;
            padding: 5px !important;
            background-image: 
                linear-gradient(to bottom, transparent 95%, #d7ccc8 95%),
                linear-gradient(to right, #d7ccc8 1px, transparent 1px);
            background-size: 100% 20px, 20px 100%;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }

        .antique-input:focus {
            background: rgba(255, 236, 179, 0.3) !important;
            border-bottom: 3px solid #5d4037 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            outline: none;
        }

        /* 7. AYIRICI ÇİZGİ - MÜREKKEP LEKESİ GÖRÜNÜMÜ */
        .koz-separator {
            text-align: center;
            font-family: 'Georgia', serif;
            font-style: italic;
            font-size: 1.1em;
            color: #5d4037 !important;
            margin: 20px 0;
            position: relative;
            padding: 10px 0;
        }
        
        .koz-separator::before,
        .koz-separator::after {
            content: "";
            position: absolute;
            top: 50%;
            width: 35%;
            height: 2px;
            background: linear-gradient(to right, transparent, #795548, transparent);
        }
        
        .koz-separator::before { left: 0; }
        .koz-separator::after { right: 0; }

        /* 8. HATA UYARILARI - KIRMIZI MÜREKKEP */
        .error-badge {
            font-family: 'Courier New', Courier, monospace;
            color: #c62828 !important;
            font-weight: bold;
            font-size: 0.9em;
            text-align: center;
            padding: 5px;
            margin-top: 5px;
            background: rgba(198, 40, 40, 0.1);
            border-radius: 3px;
            border: 1px dashed #c62828;
        }

        /* 9. TARİH BAŞLIĞI - MÜHÜR GÖRÜNÜMÜ */
        .date-seal {
            display: inline-block;
            padding: 8px 20px;
            background: #efebe9;
            border: 2px solid #a1887f;
            border-radius: 50px;
            font-family: 'Georgia', serif;
            font-style: italic;
            color: #5d4037;
            margin: 0 auto 25px auto;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2);
            position: relative;
            text-align: center;
        }
        
        .date-seal::before,
        .date-seal::after {
            content: "✧";
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            color: #795548;
        }
        
        .date-seal::before { left: 8px; }
        .date-seal::after { right: 8px; }

        /* 10. BUTONLAR - ESKİ DÜĞME GÖRÜNÜMÜ */
        .stButton > button {
            background: linear-gradient(to bottom, #8d6e63, #5d4037);
            color: white !important;
            font-family: 'Georgia', serif;
            font-weight: bold;
            border: 2px solid #3e2723 !important;
            border-radius: 5px;
            padding: 10px 24px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(to bottom, #a1887f, #795548);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
            transform: translateY(-2px);
        }

        /* 11. TABLO SATIR ARALIKLARI */
        .antique-container > div > div {
            margin-bottom: 8px;
            padding: 5px 0;
        }

        /* 12. İPTAL BUTONU ÖZEL STİLİ */
        .cancel-button > button {
            background: linear-gradient(to bottom, #bcaaa4, #8d6e63) !important;
            border: 2px solid #6d4c41 !important;
        }
        
        .cancel-button > button:hover {
            background: linear-gradient(to bottom, #d7ccc8, #a1887f) !important;
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
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.info("📜 Defteri hazırlamak için oyuncuları seçin.")
        c1, c2 = st.columns(2)
        with c1: m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
        with c2: 
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
        
        selected = st.multiselect("Masadaki Oyuncular (4 Kişi):", list(name_to_id.keys()), max_selections=4)
        
        if len(selected) == 4:
            if st.button("📝 Kağıdı Çıkar", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    
    # Özel konteyner div'i
    st.markdown('<div class="antique-container">', unsafe_allow_html=True)
    
    # Başlık
    st.markdown(f"""
    <div class="sheet-title">{st.session_state['current_match_name']}</div>
    <div class="date-seal">📅 {st.session_state['match_date']}</div>
    """, unsafe_allow_html=True)

    # Sütun Başlıkları
    cols = st.columns([1.5, 1, 1, 1, 1])
    with cols[0]: st.markdown('<div class="col-header" style="text-align:left;">OYUN TÜRÜ</div>', unsafe_allow_html=True)
    for i, p in enumerate(players):
        with cols[i+1]: st.markdown(f'<div class="col-header">{p}</div>', unsafe_allow_html=True)

    # --- SATIRLARI OLUŞTURMA ---
    rows_structure = []
    # 1. Cezalar
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue
        limit = kural['limit']
        for i in range(1, limit + 1):
            rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})

    # Araya Ayırıcı
    rows_structure.append({"type": "separator", "label": "KOZ OYUNLARI"})

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
        # Ayırıcı Satır
        if row_info.get("type") == "separator":
            st.markdown(f'<div class="koz-separator">{row_info["label"]}</div>', unsafe_allow_html=True)
            continue

        # Normal Satır
        c = st.columns([1.5, 1, 1, 1, 1])
        
        # Sol Sütun (Oyun Adı)
        with c[0]:
            st.markdown(f'<div class="row-label">{row_info["label"]}</div>', unsafe_allow_html=True)
        
        # Oyuncu Sütunları
        current_vals = []
        for idx, p in enumerate(players):
            key = f"{row_info['id']}_{p}"
            if key not in st.session_state["scores"]: st.session_state["scores"][key] = 0
            
            with c[idx + 1]:
                # Özel stil ekleyelim
                st.markdown(f'''
                <style>
                    input[data-testid*="{key}"] {{
                        font-family: 'Courier New', Courier, monospace !important;
                        font-size: 1.3em !important;
                        color: #3e2723 !important;
                    }}
                </style>
                ''', unsafe_allow_html=True)
                
                val = st.number_input(
                    "hidden", 
                    min_value=0, max_value=13, step=1, 
                    key=key, 
                    label_visibility="collapsed"
                )
                current_vals.append(val)

        # --- KONTROLLER ---
        row_sum = sum(current_vals)
        if row_sum > 0: has_data = True

        if row_sum != 0 and row_sum != row_info["limit"]:
            st.markdown(f"""
            <div class="error-badge">
                ⚠️ HATA: {row_sum} girildi (Olması gereken: {row_info['limit']})
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
            
            p_vals = [v * row_info["puan"] for v in current_vals]
            valid_data_rows.append([db_name] + p_vals)
    
    # Konteyner kapanışı
    st.markdown('</div>', unsafe_allow_html=True)

    # --- BUTONLAR ---
    st.write("") 
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        if st.button("💾 DEFTERİ ONAYLA VE KAYDET", type="primary", use_container_width=True):
            if errors:
                st.error("⚠️ Defterde düzeltilmesi gereken satırlar var (Kırmızı uyarıları kontrol edin).")
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
                    st.success("Maç başarıyla kaydedildi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {} 
                    st.rerun()

    with c_cancel:
        if st.button("❌ İptal", use_container_width=True, key="cancel_btn"):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {} 
            st.rerun()
