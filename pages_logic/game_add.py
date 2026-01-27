# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL CSS: PARŞÖMEN VE TEMİZ INPUTLAR ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. ARTI / EKSİ BUTONLARINI YOK ET (Kesin Çözüm) */
        /* Chrome, Safari, Edge, Opera */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        /* Firefox */
        input[type=number] {
            -moz-appearance: textfield;
        }
        /* Streamlit'in kendi butonlarını gizle */
        div[data-testid="stNumberInputStepDown"],
        div[data-testid="stNumberInputStepUp"] {
            display: none !important;
        }

        /* 2. PARŞÖMEN KUTUSU (Sadece Tablo Alanı) */
        /* Streamlit'in border=True container'ını hedef alıyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #fdfbf7; /* Krem Rengi */
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            border: 1px solid #d3c6a0 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); /* Derin gölge */
            padding: 30px !important;
            border-radius: 2px !important;
        }

        /* 3. KUTU İÇİNDEKİ YAZILARI KOYULAŞTIR */
        /* Arka plan açık renk olduğu için yazılar koyu olmalı */
        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: #2c1e12 !important; /* Mürekkep rengi */
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* 4. INPUT TASARIMI (HAYALET KUTU) */
        /* Kutuyu şeffaf yap, sadece alt çizgi kalsın */
        div[data-testid="stVerticalBlockBorderWrapper"] input {
            background-color: transparent !important;
            border: none !important;
            border-bottom: 2px dashed #a89f91 !important; /* Kesik çizgi */
            text-align: center !important;
            font-weight: bold !important;
            font-size: 1.2em !important;
            padding: 0 !important;
            height: 40px !important;
        }

        /* Tıklayınca (Focus) */
        div[data-testid="stVerticalBlockBorderWrapper"] input:focus {
            background-color: rgba(255, 215, 0, 0.1) !important;
            border-bottom: 2px solid #8b0000 !important; /* Kırmızı çizgi */
            box-shadow: none !important;
        }

        /* 5. TABLO BAŞLIKLARI VE SATIR İSİMLERİ */
        .sheet-title {
            text-align: center;
            font-size: 2.2em;
            color: #8b0000 !important;
            font-weight: 900;
            text-transform: uppercase;
            border-bottom: 3px double #2c1e12;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .col-header {
            font-weight: 900;
            text-align: center;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .row-label {
            font-weight: bold;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            height: 40px; /* Input ile aynı hizada olsun */
        }

        /* Hata Uyarıları */
        .error-badge {
            color: #d93025 !important;
            font-weight: bold;
            font-size: 0.8em;
            display: block;
            text-align: center;
            border-top: 1px solid #d93025;
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

    # --- 1. KURULUM EKRANI (Normal Streamlit Teması) ---
    if not st.session_state["sheet_active"]:
        st.info("Defteri hazırlamak için oyuncuları seçin.")
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

    # --- 2. DEFTER EKRANI (Parşömen Kutusu) ---
    players = st.session_state["players"]
    
    # Kapsayıcı Kutu (Border=True dediğimiz için CSS bunu yakalayıp kağıda çevirecek)
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div class="sheet-title">{st.session_state['current_match_name']}</div>
        <div style="text-align:center; font-style:italic; margin-bottom:20px;">📅 {st.session_state['match_date']}</div>
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
                # İsimde sayı olmasın, sadece "Rıfkı" yazsın
                rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})

        # Araya Ayırıcı
        rows_structure.append({"type": "separator", "label": "--- KOZLAR ---"})

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
                st.markdown(f"<div style='text-align:center; margin:15px 0; border-top:2px dashed #2c1e12; padding-top:5px; font-weight:bold;'>{row_info['label']}</div>", unsafe_allow_html=True)
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
                    # NATIVE INPUT (Ama CSS ile makyajlı)
                    val = st.number_input(
                        "hidden", 
                        min_value=0, max_value=13, step=1, 
                        key=key, 
                        label_visibility="collapsed"
                    )
                    current_vals.append(val)

            # --- MÜFETTİŞ KONTROLÜ ---
            row_sum = sum(current_vals)
            if row_sum > 0: has_data = True

            # Hata varsa satırın altına yaz
            if row_sum != 0 and row_sum != row_info["limit"]:
                st.markdown(f"""
                <div class="error-badge">
                    ⚠️ HATA: {row_sum} girildi (Olması gereken: {row_info['limit']})
                </div>
                """, unsafe_allow_html=True)
                errors.append(f"{row_info['label']}: Hatalı toplam")
            
            # Veri Hazırlama (Sadece doğru satırlar)
            if row_sum == row_info["limit"]:
                if row_info["type"] == "koz":
                    koz_counter += 1
                    db_name = f"Koz (Tümü) {koz_counter}"
                else:
                    ceza_counters[row_info["label"]] += 1
                    db_name = f"{row_info['label']} {ceza_counters[row_info['label']]}"
                
                # Puan hesabı
                p_vals = [v * row_info["puan"] for v in current_vals]
                valid_data_rows.append([db_name] + p_vals)

    # --- KUTU DIŞI: BUTONLAR ---
    st.write("") 
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        # Hata varsa buton pasif (disabled) olmuyor ama uyarı veriyoruz
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
                    st.success("Maç kaydedildi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {} 
                    st.rerun()

    with c_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {} 
            st.rerun()
