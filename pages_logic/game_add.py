# pages_logic/game_add.py
import streamlit as st
from utils.database import get_users_map
from utils.config import OYUN_KURALLARI

def inject_interactive_css():
    st.markdown("""
    <style>
        /* 1. PARŞÖMEN ZEMİNİ (Ana Kutuyu Hedefle) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #fdfbf7 !important;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png") !important;
            border: 2px solid #5c4033 !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8) !important;
            padding: 20px !important;
            border-radius: 4px !important;
        }

        /* 2. INPUT KUTULARI (HAYALET MODU) */
        /* Kutunun arka planını yok et, sadece alt çizgi bırak */
        div[data-testid="stNumberInput"] input {
            background-color: transparent !important;
            color: #2c1e12 !important; /* Mürekkep Rengi */
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            border: none !important;
            border-bottom: 1px solid #8b7d6b !important; /* Satır çizgisi */
            border-radius: 0 !important;
            text-align: center !important;
            padding: 0 !important;
            height: 35px !important;
        }

        /* Tıklayınca çizgi kalınlaşsın */
        div[data-testid="stNumberInput"] input:focus {
            border-bottom: 2px solid #8b0000 !important;
            box-shadow: none !important;
        }

        /* 3. ARTI/EKSİ OKLARINI SİL (Temiz görüntü için) */
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        div[data-testid="stNumberInputStepDown"], 
        div[data-testid="stNumberInputStepUp"] { display: none !important; }

        /* 4. METİNLER */
        .oyun-etiketi {
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            color: #2c1e12;
            padding-top: 10px;
            font-size: 1em;
        }
        
        .sutun-baslik {
            font-family: 'Courier New', Courier, monospace;
            font-weight: 900;
            color: #2c1e12;
            text-align: center;
            text-transform: uppercase;
            border-bottom: 2px solid #2c1e12;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }

        /* Ayracı */
        .ayrac {
            text-align: center;
            font-weight: 900;
            margin: 15px 0;
            border-top: 2px dashed #2c1e12;
            border-bottom: 2px dashed #2c1e12;
            padding: 5px;
            background-color: rgba(44, 30, 18, 0.05);
            color: #2c1e12;
            font-family: 'Courier New', Courier, monospace;
        }

        /* Başlık */
        .kagit-baslik {
            text-align: center;
            color: #8b0000;
            font-family: 'Courier New', Courier, monospace;
            font-weight: 900;
            margin-bottom: 20px;
            border-bottom: 3px double #2c1e12;
        }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_interactive_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. SEÇİM EKRANI ---
    if not st.session_state["show_paper"]:
        st.info("Oyuncuları seçin.")
        users = list(name_to_id.keys())
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("📜 Parşömeni Aç", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected
                st.session_state["show_paper"] = True
                st.rerun()
        return

    # --- 2. İNTERAKTİF PARŞÖMEN ---
    else:
        players = st.session_state["current_players"]
        
        # Parşömen Alanı Başlangıcı
        with st.container(border=True):
            
            # Başlık
            st.markdown('<h1 class="kagit-baslik">KRALİYET DEFTERİ</h1>', unsafe_allow_html=True)
            
            # Sütun Başlıkları (Grid'in en tepesi)
            cols = st.columns([1.5, 1, 1, 1, 1])
            with cols[0]: st.markdown('<div class="sutun-baslik" style="text-align:left">OYUN TÜRÜ</div>', unsafe_allow_html=True)
            for i, p in enumerate(players):
                with cols[i+1]: st.markdown(f'<div class="sutun-baslik">{p}</div>', unsafe_allow_html=True)

            # --- DÖNGÜ İLE SATIRLARI OLUŞTURMA ---
            
            # 1. CEZALAR
            for oyun_adi, kural in OYUN_KURALLARI.items():
                if "Koz" in oyun_adi: continue
                limit = kural['limit']
                
                for i in range(1, limit + 1):
                    label = f"{oyun_adi}" if limit == 1 else f"{oyun_adi} {i}"
                    
                    # Yeni bir satır (grid row) açıyoruz
                    row_cols = st.columns([1.5, 1, 1, 1, 1])
                    
                    # Sol Sütun (İsim)
                    with row_cols[0]:
                        st.markdown(f'<div class="oyun-etiketi">{label}</div>', unsafe_allow_html=True)
                    
                    # Sağ Sütunlar (Input Kutuları)
                    for idx, p in enumerate(players):
                        with row_cols[idx + 1]:
                            # Benzersiz anahtar (key) çok önemli
                            unique_key = f"{label}_{p}_{idx}"
                            st.number_input(
                                "hidden", 
                                min_value=0, max_value=13, step=1, 
                                key=unique_key, 
                                label_visibility="collapsed"
                            )

            # 2. AYRAÇ
            st.markdown('<div class="ayrac">--- KOZLAR ---</div>', unsafe_allow_html=True)

            # 3. KOZLAR
            for i in range(1, 9):
                row_cols = st.columns([1.5, 1, 1, 1, 1])
                
                with row_cols[0]:
                    st.markdown(f'<div class="oyun-etiketi">KOZ {i}</div>', unsafe_allow_html=True)
                
                for idx, p in enumerate(players):
                    with row_cols[idx + 1]:
                        unique_key = f"KOZ_{i}_{p}_{idx}"
                        st.number_input(
                            "hidden", 
                            min_value=0, max_value=13, step=1, 
                            key=unique_key, 
                            label_visibility="collapsed"
                        )
        
        # Alt Buton
        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
