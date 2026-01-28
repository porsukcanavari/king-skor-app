# pages_logic/game_add.py
import streamlit as st
from datetime import datetime
from utils.database import get_users_map

def game_interface():
    # Kullanıcıları çek
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State (Sayfa durumunu kontrol etmek için)
    if "show_paper" not in st.session_state:
        st.session_state["show_paper"] = False
    
    # --- DURUM 1: OYUNCU SEÇİM EKRANI ---
    if not st.session_state["show_paper"]:
        st.info("Oyuncuları seçin ve kağıdı isteyin.")
        
        col1, col2 = st.columns(2)
        with col1:
            match_name = st.text_input("Maç Adı", "King_Akşamı")
        with col2:
            match_date = st.date_input("Tarih", datetime.now())
            
        # Oyuncu Seçimi
        users_list = list(name_to_id.keys())
        selected_players = st.multiselect("Oyuncular (4 Kişi):", users_list, max_selections=4)
        
        # Buton
        if len(selected_players) == 4:
            if st.button("📜 Parşömeni Getir", type="primary", use_container_width=True):
                # Sadece durumu değiştiriyoruz, arka planda oyuncuları tutuyoruz
                st.session_state["current_players"] = selected_players
                st.session_state["show_paper"] = True
                st.rerun()
        return

    # --- DURUM 2: BOMBOŞ PARŞÖMEN KAĞIDI ---
    else:
        # Sadece Görsel CSS
        st.markdown("""
        <style>
            .bos-parsom-kagidi {
                /* Kağıt Dokusu ve Rengi */
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                
                /* Boyutlar */
                width: 100%;
                max-width: 750px;
                height: 900px; /* Uzun bir A4 kağıdı gibi */
                
                /* Konumlandırma */
                margin: 0 auto; /* Ortala */
                
                /* Süsleme */
                border: 1px solid #d3c6a0;
                box-shadow: 0 0 50px rgba(0,0,0,0.8); /* Siyah zeminde vurgu */
                border-radius: 3px;
            }
        </style>
        
        <div class="bos-parsom-kagidi"></div>
        
        """, unsafe_allow_html=True)

        # Geri Dön Butonu (İstersen basıp çıkmak için)
        st.write("")
        if st.button("Geri Dön (Seçimi Sıfırla)", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
