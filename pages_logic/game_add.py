# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- 1. CSS: SADECE ORTA ALAN PARŞÖMEN ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. KAĞIT KUTUSU (Paper Container) */
        /* Sadece bu sınıfı kullanan alan kağıt gibi görünecek */
        .paper-sheet {
            background-color: #fdfbf7;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            padding: 40px;
            border-radius: 2px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5); /* Siyah zemin üzerinde parlasın */
            margin: 20px auto;
            max-width: 950px;
            color: #2c1e12; /* Mürekkep rengi */
            font-family: 'Courier New', Courier, monospace;
            border: 1px solid #d3c6a0;
            position: relative;
        }

        /* 2. BAŞLIKLAR */
        .paper-header {
            text-align: center;
            border-bottom: 3px double #2c1e12;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }
        .paper-title {
            font-size: 2.2em;
            color: #8b0000;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 0;
        }

        /* 3. INPUT (SAYI GİRİŞ) KUTULARI */
        /* + ve - butonlarını yok etme operasyonu */
        div[data-testid="stNumberInput"] input {
            background-color: transparent !important;
            border: none !important;
            border-bottom: 1px dashed #aaa !important;
            color: #2c1e12 !important; /* Koyu yazı */
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            text-align: center !important;
            padding: 0 !important;
            height: 35px !important;
            font-size: 1.2em !important;
            -moz-appearance: textfield; /* Firefox okları gizle */
        }
        
        /* Chrome, Safari, Edge, Opera için okları gizle */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }

        /* Input focus (tıklayınca) */
        div[data-testid="stNumberInput"] input:focus {
            background-color: rgba(255, 215, 0, 0.1) !important;
            border-bottom: 2px solid #8b0000 !important;
            box-shadow: none !important;
        }

        /* Streamlit'in kendi +/- butonlarını gizle */
        button[kind="secondaryFormSubmit"] { display: none !important; }
        div[data-testid="stNumberInputStepDown"] { display: none !important; }
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* 4. TABLO BAŞLIKLARI VE SATIRLAR */
        .player-header {
            font-weight: bold;
            text-align: center;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            font-size: 1.1em;
            color: #8b0000;
        }
        
        .row-label {
            font-weight: bold;
            padding-top: 8px;
            font-size: 1em;
            color: #2c1e12;
        }

        /* Butonlar (Kağıt üzerinde uyumlu dursun) */
        .paper-btn button {
            background-color: #2c1e12 !important;
            color: #fdfbf7 !important;
            border: none !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            transition: all 0.3s ease;
        }
        .paper-btn button:hover {
            background-color: #8b0000 !important;
            transform: scale(1.02);
        }

        /* Hata Mesajı Stili */
        .error-msg {
            color: #d93025;
            font-weight: bold;
            font-size: 0.9em;
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
    
    # Skorları tutacağımız sözlük
    if "scores" not in st.session_state: st.session_state["scores"] = {}

    # --- 1. KURULUM EKRANI (Normal Streamlit Görünümü) ---
    if not st.session_state["sheet_active"]:
        st.info("Yeni bir defter sayfası açmak için oyuncuları seçin.")
        
        c1, c2 = st.columns(2)
        with c1:
            m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
            users = list(name_to_id.keys())
        with c2:
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
            
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("🖋️ Defteri Önüme Getir", type="primary", use_container_width=True):
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.session_state["scores"] = {} 
                st.rerun()
        return

    # --- 2. DEFTER EKRANI (Parşömen Kutusu İçinde) ---
    players = st.session_state["players"]
    
    # KAĞIT BAŞLANGICI
    st.markdown('<div class="paper-sheet">', unsafe_allow_html=True)
    
    # Başlık
    st.markdown(f"""
    <div class="paper-header">
        <h1 class="paper-title">{st.session_state['current_match_name']}</h1>
        <p>📅 {st.session_state['match_date']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Tablo Başlıkları
    cols = st.columns([1.5, 1, 1, 1, 1])
    with cols[0]: st.markdown('<div class="player-header">OYUN TÜRÜ</div>', unsafe_allow_html=True)
    with cols[1]: st.markdown(f'<div class="player-header">{players[0]}</div>', unsafe_allow_html=True)
    with cols[2]: st.markdown(f'<div class="player-header">{players[1]}</div>', unsafe_allow_html=True)
    with cols[3]: st.markdown(f'<div class="player-header">{players[2]}</div>', unsafe_allow_html=True)
    with cols[4]: st.markdown(f'<div class="player-header">{players[3]}</div>', unsafe_allow_html=True)

    # --- SATIRLARI OLUŞTURMA ---
    rows_structure = []

    # 1. CEZALAR
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue
        limit = kural['limit']
        for i in range(1, limit + 1):
            row_id = f"{oyun_adi}_{i}"
            rows_structure.append({"id": row_id, "label": oyun_adi, "type": "ceza", "limit": kural['adet'], "puan": kural['puan']})

    # 2. KOZLAR (8 Adet)
    for i in range(1, 9):
        row_id = f"KOZ_{i}"
        rows_structure.append({"id": row_id, "label": "KOZ", "type": "koz", "limit": 13, "puan": 50})

    # --- DÖNGÜ İLE INPUTLARI YERLEŞTİRME ---
    errors = []
    valid_data_rows = []
    
    # Sayaçlar
    ceza_counters = {k: 0 for k in OYUN_KURALLARI}
    koz_counter = 0
    has_data = False

    for row_info in rows_structure:
        c = st.columns([1.5, 1, 1, 1, 1])
        
        # Oyun İsmi
        with c[0]:
            st.markdown(f'<div class="row-label">{row_info["label"]}</div>', unsafe_allow_html=True)
        
        # Oyuncu Puanları
        current_row_scores = []
        for idx, p in enumerate(players):
            key = f"{row_info['id']}_{p}"
            if key not in st.session_state["scores"]:
                st.session_state["scores"][key] = 0
            
            with c[idx + 1]:
                val = st.number_input(
                    "hidden",
                    min_value=0, 
                    max_value=13, 
                    step=1, 
                    key=key, 
                    label_visibility="collapsed"
                )
                current_row_scores.append(val)

        # --- ANLIK KONTROL (MÜFETTİŞ) ---
        row_sum = sum(current_row_scores)
        
        if row_sum > 0: has_data = True

        # Hata varsa o satırın altına hemen uyarı yaz
        if row_sum != 0 and row_sum != row_info["limit"]:
            st.markdown(f"""
            <div class="error-msg" style="text-align:center; border-bottom:1px solid red; margin-bottom:10px;">
                ⚠️ HATA: Toplam {row_info['limit']} olmalı (Şu an: {row_sum})
            </div>
            """, unsafe_allow_html=True)
            # Genel hata listesine de ekle
            game_num = ceza_counters.get(row_info['label'], koz_counter) + 1 # Tahmini numara
            errors.append(f"{row_info['label']}: {row_sum} girildi, {row_info['limit']} olmalı.")
        
        # Veri hazırlama (Sadece geçerli ve dolu satırlar için)
        if row_sum == row_info["limit"]:
            db_name = ""
            if row_info["type"] == "koz":
                koz_counter += 1 # Buradaki sayaç sadece geçerli olanları sayar, düzeltilmesi gerekebilir
                # Doğru isimlendirme için döngü başındaki sırayı kullanmalıyız aslında
                # Ama basitlik adına:
                pass
            
    st.markdown('</div>', unsafe_allow_html=True) # KAĞIT BİTİŞİ
    
    # --- KAYIT İŞLEMİ (KAĞIDIN DIŞINDAKİ ALAN) ---
    st.write("")
    
    # Verileri tekrar temiz bir şekilde toplayalım (Kaydet tuşuna basınca)
    c_save, c_cancel = st.columns([2, 1])
    
    with c_save:
        st.markdown('<div class="paper-btn">', unsafe_allow_html=True)
        if st.button("💾 DEFTERİ KAPAT VE KAYDET", use_container_width=True):
            # Yeniden Kontrol
            final_errors = []
            final_rows = []
            
            # Sayaçları sıfırla
            c_counts = {k: 0 for k in OYUN_KURALLARI}
            k_count = 0
            
            for r_info in rows_structure:
                scores = [st.session_state["scores"][f"{r_info['id']}_{p}"] for p in players]
                r_sum = sum(scores)
                
                if r_sum == 0: continue # Boş satır
                
                if r_sum != r_info["limit"]:
                    final_errors.append(f"{r_info['label']}: Toplam {r_info['limit']} olmalı.")
                else:
                    # İsimlendirme
                    if r_info["type"] == "koz":
                        k_count += 1
                        db_name = f"Koz (Tümü) {k_count}"
                    else:
                        c_counts[r_info["label"]] += 1
                        db_name = f"{r_info['label']} {c_counts[r_info['label']]}"
                    
                    # Puanlama
                    conv_scores = [s * r_info["puan"] for s in scores]
                    final_rows.append([db_name] + conv_scores)
            
            if final_errors:
                st.error("⚠️ Aşağıdaki satırlarda hata var, kaydedilemedi:")
                for e in final_errors: st.write(f"- {e}")
            elif not final_rows:
                st.warning("Defter boş, kaydedilecek bir şey yok.")
            else:
                # Kayıt
                final_total = ["TOPLAM"]
                for i in range(4):
                    col_total = sum([r[i+1] for r in final_rows])
                    final_total.append(col_total)
                
                header = ["OYUN TÜRÜ"]
                for p in players:
                    uid = name_to_id.get(p, "?")
                    header.append(f"{p} (uid:{uid})")

                if save_match_to_sheet(header, final_rows, final_total):
                    st.balloons()
                    st.success("Kayıt Başarılı!")
                    st.session_state["sheet_active"] = False
                    st.session_state["scores"] = {}
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.session_state["scores"] = {}
            st.rerun()
