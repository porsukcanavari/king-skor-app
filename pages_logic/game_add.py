# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL CSS: SADECE KUTU İÇİ PARŞÖMEN ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. KAPSAYICI KUTU (Container) HEDEFLEME */
        /* Streamlit'in border=True olan container'ını yakalıyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #fdfbf7;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            border: 1px solid #d3c6a0 !important;
            border-radius: 5px !important;
            padding: 20px !important;
            box-shadow: 0 0 15px rgba(0,0,0,0.5); /* Siyah zemin üzerinde gölge */
        }

        /* 2. KUTU İÇİNDEKİ YAZILAR */
        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: #2c1e12 !important; /* Koyu Kahve Mürekkep Rengi */
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* 3. INPUT KUTULARI (ARTIK SADECE ÇİZGİ) */
        div[data-testid="stVerticalBlockBorderWrapper"] input {
            background-color: rgba(255, 255, 255, 0.5) !important; /* Yarı saydam beyaz */
            color: #000000 !important;
            border: none !important;
            border-bottom: 2px dashed #8b7d6b !important; /* Altı çizgili defter satırı gibi */
            text-align: center !important;
            font-weight: bold !important;
            font-size: 1.1em !important;
            padding: 0 !important;
            border-radius: 0 !important;
        }

        /* Inputa tıklayınca */
        div[data-testid="stVerticalBlockBorderWrapper"] input:focus {
            background-color: rgba(255, 215, 0, 0.2) !important;
            border-bottom: 2px solid #8b0000 !important;
            box-shadow: none !important;
        }

        /* 4. ARTI / EKSİ BUTONLARINI YOK ETME */
        button[kind="secondaryFormSubmit"] { display: none !important; }
        div[data-testid="stNumberInputStepDown"] { display: none !important; }
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* Başlıklar */
        .sheet-title {
            text-align: center;
            font-size: 2em;
            color: #8b0000 !important;
            font-weight: 900;
            margin-bottom: 5px;
            border-bottom: 3px double #2c1e12;
            padding-bottom: 10px;
        }

        .player-header {
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
            border-bottom: 1px solid #2c1e12;
            margin-bottom: 10px;
        }

        .row-label {
            font-weight: bold;
            font-size: 1em;
            padding-top: 10px;
        }

        /* Hata Mesajı */
        .error-line {
            color: #d93025 !important;
            font-size: 0.8em;
            font-weight: bold;
            text-align: center;
            border-top: 1px solid #d93025;
            margin-top: 5px;
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
    
    # Skorlar (Input değerleri burada tutulur)
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI (BURASI NORMAL GÖRÜNÜR) ---
    if not st.session_state["sheet_active"]:
        st.info("Defteri hazırlamak için oyuncuları seçin.")
        
        c1, c2 = st.columns(2)
        with c1:
            m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
            users = list(name_to_id.keys())
        with c2:
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
            
        selected = st.multiselect("Masadaki Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("🖋️ Defteri Önüme Getir", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI (PARŞÖMEN KUTUSU) ---
    players = st.session_state["players"]
    
    # === İŞTE PARŞÖMEN BURADA BAŞLIYOR ===
    # st.container(border=True) kullandığımız için CSS bunu yakalayıp kağıda çevirecek
    with st.container(border=True):
        
        # Başlık
        st.markdown(f"""
        <div class="sheet-title">{st.session_state['current_match_name']}</div>
        <div style="text-align:center; font-style:italic;">📅 {st.session_state['match_date']}</div>
        """, unsafe_allow_html=True)
        st.write("") # Boşluk

        # Sütun Başlıkları (Oyuncular)
        cols = st.columns([1.5, 1, 1, 1, 1])
        with cols[0]: st.markdown('<div class="player-header">OYUN</div>', unsafe_allow_html=True)
        with cols[1]: st.markdown(f'<div class="player-header">{players[0]}</div>', unsafe_allow_html=True)
        with cols[2]: st.markdown(f'<div class="player-header">{players[1]}</div>', unsafe_allow_html=True)
        with cols[3]: st.markdown(f'<div class="player-header">{players[2]}</div>', unsafe_allow_html=True)
        with cols[4]: st.markdown(f'<div class="player-header">{players[3]}</div>', unsafe_allow_html=True)

        # --- SATIR YAPISI ---
        rows_structure = []
        # 1. Cezalar
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                rows_structure.append({"id": f"{oyun_adi}_{i}", "label": oyun_adi, "limit": kural['adet'], "puan": kural['puan'], "type": "ceza"})
        # 2. Kozlar
        for i in range(1, 9):
            rows_structure.append({"id": f"KOZ_{i}", "label": "KOZ", "limit": 13, "puan": 50, "type": "koz"})

        # --- GİRİŞ ALANLARI VE MÜFETTİŞ ---
        errors = []
        valid_data_rows = []
        
        # Sayaçlar (Veritabanı ismi için)
        ceza_counters = {k: 0 for k in OYUN_KURALLARI}
        koz_counter = 0
        has_data = False

        for row_info in rows_structure:
            c = st.columns([1.5, 1, 1, 1, 1])
            
            # Satır İsmi
            with c[0]:
                st.markdown(f'<div class="row-label">{row_info["label"]}</div>', unsafe_allow_html=True)
            
            # Oyuncu Puanları
            current_row_vals = []
            for idx, p in enumerate(players):
                key = f"{row_info['id']}_{p}"
                # Session State'i başlat
                if key not in st.session_state["scores"]:
                    st.session_state["scores"][key] = 0 # Varsayılan 0
                
                with c[idx + 1]:
                    # NATIVE INPUT (CSS ile şekillendirildi)
                    val = st.number_input(
                        "hidden",
                        min_value=0, max_value=13, step=1,
                        key=key,
                        label_visibility="collapsed"
                    )
                    current_row_vals.append(val)

            # --- ANLIK KONTROL (MÜFETTİŞ) ---
            row_sum = sum(current_row_vals)
            if row_sum > 0: has_data = True

            # Hata varsa hemen altına yaz
            if row_sum != 0 and row_sum != row_info["limit"]:
                st.markdown(f"""
                <div class="error-line">
                    ⚠️ HATA: Toplam {row_info['limit']} olmalı (Girilen: {row_sum})
                </div>
                """, unsafe_allow_html=True)
                errors.append(f"{row_info['label']}: {row_sum} girildi.")
            
            # Veri Hazırlama (Eğer hata yoksa ve satır doluysa)
            if row_sum == row_info["limit"]:
                if row_info["type"] == "koz":
                    koz_counter += 1
                    # Burada ufak bir mantık hatası olabilir: 
                    # Koz 1 boş geçilip Koz 2 doldurulursa sıra kayar.
                    # Ama basitlik adına sayaç kullanıyoruz.
                    db_name = f"Koz (Tümü) {koz_counter}"
                else:
                    ceza_counters[row_info["label"]] += 1
                    db_name = f"{row_info['label']} {ceza_counters[row_info['label']]}"
                
                # Puanı hesapla ve listeye ekle
                converted_scores = [s * row_info["puan"] for s in current_row_vals]
                valid_data_rows.append([db_name] + converted_scores)

    # === PARŞÖMEN BİTTİ ===
    
    st.write("") # Boşluk

    # --- ALT BUTONLAR (Normal Görünüm) ---
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        if st.button("💾 DEFTERİ KAPAT VE KAYDET", type="primary", use_container_width=True):
            if errors:
                st.error("⚠️ Defterde hatalı satırlar var! (Kırmızı uyarıları kontrol edin)")
            elif not has_data:
                st.warning("Defter boş, kaydedilecek bir şey yok.")
            else:
                # Toplamlar
                final_total = ["TOPLAM"]
                for i in range(4):
                    # valid_data_rows yapısı: [İsim, P1, P2, P3, P4]
                    col_total = sum([r[i+1] for r in valid_data_rows])
                    final_total.append(col_total)
                
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
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {}
            st.rerun()
