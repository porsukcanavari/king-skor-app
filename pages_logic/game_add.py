# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL CSS: ESKİ DEFTER GÖRÜNÜMÜ - DÜZELTİLMİŞ ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. NUMBER INPUT'UN ARTI/EKSİ BUTONLARINI GİZLE */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type=number] {
            -moz-appearance: textfield;
        }
        /* Streamlit'in step butonlarını gizle */
        div[data-testid="stNumberInputStepDown"],
        div[data-testid="stNumberInputStepUp"] {
            display: none !important;
        }

        /* 2. ANA KONTEYNER - PARŞÖMEN KAĞIT */
        .antique-container {
            background: linear-gradient(to bottom, #f7f3e8 0%, #f2e9d8 100%);
            background-image: 
                linear-gradient(to bottom, rgba(247, 243, 232, 0.9) 0%, rgba(242, 233, 216, 0.9) 100%),
                url("https://www.transparenttextures.com/patterns/cream-paper.png");
            border: 1px solid #d4c4a8;
            padding: 25px 30px !important;
            border-radius: 3px;
            box-shadow: 
                0 5px 20px rgba(0, 0, 0, 0.3),
                inset 0 0 50px rgba(0, 0, 0, 0.05);
            position: relative;
            overflow: hidden;
        }

        /* 3. NUMBER INPUT'LAR - GÖRÜNÜR VE OKUNAKLI */
        .antique-container input[type="number"] {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 2px solid #8d6e63 !important;
            border-radius: 4px !important;
            color: #3e2723 !important;
            font-family: 'Courier New', monospace !important;
            font-weight: bold !important;
            font-size: 1.2em !important;
            text-align: center !important;
            height: 45px !important;
            width: 100% !important;
            padding: 8px !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
            -moz-appearance: textfield !important;
            -webkit-appearance: none !important;
            appearance: none !important;
        }

        /* 4. INPUT FOCUS STATE */
        .antique-container input[type="number"]:focus {
            background-color: rgba(255, 253, 231, 0.95) !important;
            border-color: #5d4037 !important;
            box-shadow: 
                inset 0 2px 4px rgba(0,0,0,0.1),
                0 0 0 2px rgba(93, 64, 55, 0.2) !important;
            outline: none !important;
        }

        /* 5. INPUT HOVER STATE */
        .antique-container input[type="number"]:hover {
            background-color: rgba(255, 253, 231, 0.9) !important;
            border-color: #a1887f !important;
        }

        /* 6. INPUT PLACEHOLDER */
        .antique-container input[type="number"]::placeholder {
            color: #bcaaa4 !important;
            opacity: 0.7 !important;
        }

        /* 7. TABLO BAŞLIĞI */
        .sheet-title {
            text-align: center;
            font-size: 2.2em;
            font-family: 'Georgia', serif;
            color: #3e2723 !important;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            padding-bottom: 10px;
            border-bottom: 3px double #795548;
        }

        /* 8. TARİH ALANI */
        .date-display {
            text-align: center;
            font-family: 'Georgia', serif;
            font-style: italic;
            font-size: 1.1em;
            color: #5d4037 !important;
            margin-bottom: 25px;
            background: rgba(121, 85, 72, 0.1);
            padding: 8px 20px;
            border-radius: 20px;
            display: inline-block;
        }

        /* 9. SÜTUN BAŞLIKLARI */
        .col-header {
            font-family: 'Georgia', serif;
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
            color: #4e342e !important;
            padding: 12px 5px;
            border-bottom: 2px solid #795548;
            background: linear-gradient(to bottom, rgba(121, 85, 72, 0.05), transparent);
            margin-bottom: 10px;
        }

        /* 10. SATIR ETİKETLERİ */
        .row-label {
            font-family: 'Georgia', serif;
            font-weight: 600;
            font-size: 1.1em;
            color: #3e2723 !important;
            display: flex;
            align-items: center;
            height: 45px;
            padding-left: 10px;
            background: rgba(121, 85, 72, 0.05);
            border-radius: 3px;
            margin-right: 5px;
            border-left: 3px solid #795548;
        }

        /* 11. AYIRICI ÇİZGİ */
        .section-divider {
            text-align: center;
            font-family: 'Georgia', serif;
            font-weight: bold;
            font-size: 1.1em;
            color: #5d4037 !important;
            margin: 20px 0;
            padding: 10px;
            position: relative;
            background: rgba(121, 85, 72, 0.1);
            border-radius: 3px;
            border-top: 1px dashed #a1887f;
            border-bottom: 1px dashed #a1887f;
        }

        /* 12. HATA MESAJLARI */
        .error-badge {
            font-family: 'Courier New', monospace;
            color: #c62828 !important;
            font-weight: bold;
            font-size: 0.85em;
            text-align: center;
            padding: 5px;
            margin-top: 5px;
            background: rgba(198, 40, 40, 0.1);
            border-radius: 3px;
            border: 1px solid #c62828;
        }

        /* 13. TABLO SATIRLARI ARASI BOŞLUK */
        .antique-container > div {
            margin-bottom: 8px !important;
        }

        /* 14. BUTON STİLLERİ */
        .stButton > button {
            background: linear-gradient(to bottom, #795548, #5d4037);
            color: white !important;
            font-family: 'Georgia', serif;
            font-weight: bold;
            border: 2px solid #3e2723 !important;
            border-radius: 5px;
            padding: 10px 24px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(to bottom, #8d6e63, #6d4c41);
            box-shadow: 0 5px 10px rgba(0,0,0,0.3);
            transform: translateY(-1px);
        }

        /* 15. İPTAL BUTONU */
        .cancel-button > button {
            background: linear-gradient(to bottom, #bcaaa4, #a1887f) !important;
            border: 2px solid #8d6e63 !important;
        }
        
        .cancel-button > button:hover {
            background: linear-gradient(to bottom, #d7ccc8, #bcaaa4) !important;
        }

        /* 16. NUMBER INPUT CONTAINER */
        .stNumberInput > div {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        
        .stNumberInput input {
            min-height: 45px !important;
        }

        /* 17. TABLO HÜCRE HİZALAMASI */
        .antique-container [data-testid="column"] {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* 18. SATIR ARALARI - ÇİZGİLİ DEFTER ETKİSİ */
        .antique-container > div:nth-child(even) .row-label {
            background: rgba(121, 85, 72, 0.03);
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
        st.markdown("### 📜 Yeni Maç Defteri")
        c1, c2 = st.columns(2)
        with c1: m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
        with c2: 
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
        
        selected = st.multiselect("Masadaki Oyuncular (4 Kişi):", list(name_to_id.keys()), max_selections=4)
        
        if len(selected) == 4:
            if st.button("📝 Defteri Aç", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        elif len(selected) > 0:
            st.warning(f"4 oyuncu seçmelisiniz. Şu anda {len(selected)} oyuncu seçtiniz.")
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    
    # Özel konteyner
    st.markdown('<div class="antique-container">', unsafe_allow_html=True)
    
    # Başlık
    st.markdown(f"""
    <div class="sheet-title">{st.session_state['current_match_name']}</div>
    <div style="text-align:center;">
        <span class="date-display">📅 {st.session_state['match_date']}</span>
    </div>
    """, unsafe_allow_html=True)

    # Sütun Başlıkları
    cols = st.columns([1.5, 1, 1, 1, 1])
    with cols[0]: st.markdown('<div class="col-header" style="text-align:left;">OYUN</div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="section-divider">{row_info["label"]}</div>', unsafe_allow_html=True)
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
            if key not in st.session_state["scores"]: 
                st.session_state["scores"][key] = 0
            
            with c[idx + 1]:
                # Input değerinin görünmesi için özel stil
                val = st.number_input(
                    label="", 
                    min_value=0, 
                    max_value=13, 
                    step=1, 
                    value=st.session_state["scores"][key],
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
    st.write("")
    
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        save_disabled = len(errors) > 0 or not has_data
        if st.button("💾 DEFTERİ KAYDET", type="primary", use_container_width=True, disabled=save_disabled):
            if errors:
                st.error("⚠️ Hatalı satırları düzeltin!")
            elif not has_data:
                st.warning("Defter boş!")
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
                    st.success("✅ Maç başarıyla kaydedildi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {} 
                    st.rerun()

    with c_cancel:
        if st.button("❌ İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {} 
            st.rerun()
    
    # Hata veya uyarı mesajları
    if errors:
        st.error(f"**{len(errors)} hata** bulundu. Lütfen kırmızı ile işaretli satırları düzeltin.")
    elif has_data:
        st.success("✓ Tüm satırlar doğru!")
    else:
        st.info("📝 Defteri doldurmaya başlayın. Her satırın toplamı belirtilen limit değerine eşit olmalıdır.")
