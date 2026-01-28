# pages_logic/game_add.py
import streamlit as st
from datetime import datetime
from utils.database import get_users_map

def game_interface():
    id_to_name, name_to_id, _ = get_users_map()
    
    # State kontrolü
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. OYUNCU SEÇİM EKRANI ---
    if not st.session_state["show_paper"]:
        st.info("Oyuncuları seçip parşömeni isteyin.")
        c1, c2 = st.columns(2)
        with c1: st.text_input("Maç Adı", "King_Akşamı")
        with c2: st.date_input("Tarih", datetime.now())
            
        users = list(name_to_id.keys())
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("📜 Parşömeni Getir", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected
                st.session_state["show_paper"] = True
                st.rerun()
        return

    # --- 2. 5'E BÖLÜNMÜŞ PARŞÖMEN ---
    else:
        players = st.session_state["current_players"]
        
        # HTML Oluşturma: 5 Sütun
        # 1. Sütun: Boş
        # 2,3,4,5. Sütunlar: Oyuncu İsimleri
        
        cols_html = ""
        # 1. Sütun (Boş)
        cols_html += f'<div class="sutun bos-sutun"></div>'
        
        # Oyuncu Sütunları
        for p in players:
            cols_html += f'<div class="sutun"><div class="isim-baslik">{p}</div></div>'

        st.markdown(f"""
        <style>
            /* ANA KAĞIT */
            .parsom-kagidi {{
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                width: 100%;
                max-width: 800px;
                height: 900px;
                margin: 0 auto;
                border: 1px solid #d3c6a0;
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
                border-radius: 3px;
                
                /* DİKEY BÖLME İŞLEMİ (GRID) */
                display: grid;
                grid-template-columns: 1fr 1fr 1fr 1fr 1fr; /* 5 Eşit Parça */
                /* İçeriği yukarıdan başlat */
                align-items: start; 
            }}

            /* SÜTUN YAPISI */
            .sutun {{
                height: 100%; /* Kağıdın sonuna kadar in */
                border-right: 1px solid #8b7d6b; /* Dikey Çizgi Rengi */
                display: flex;
                justify-content: center; /* İsmi ortala */
                padding-top: 15px;
            }}

            /* Son sütunun sağ çizgisini kaldır */
            .sutun:last-child {{
                border-right: none;
            }}

            /* İSİM STİLİ */
            .isim-baslik {{
                font-family: 'Courier New', Courier, monospace;
                font-weight: 900;
                color: #2c1e12;
                font-size: 1.2em;
                text-transform: uppercase;
                border-bottom: 2px solid #2c1e12; /* İsmin altına çizgi */
                padding-bottom: 5px;
                margin-bottom: auto; /* İsmi tepede tut */
            }}

        </style>

        <div class="parsom-kagidi">
            {cols_html}
        </div>
        
        """, unsafe_allow_html=True)

        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
