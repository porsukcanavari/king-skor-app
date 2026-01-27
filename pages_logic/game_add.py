# pages_logic/game_add.py
import streamlit as st

def game_interface():
    # Sadece görsel, işlev sıfır.
    st.markdown("""
    <style>
        .parsom-kagidi {
            /* 1. DOKU VE RENK (Olay burada) */
            background-color: #fdfbf7; /* Krem Zemin */
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png"); /* Kağıt Dokusu */
            
            /* 2. BOYUTLANDIRMA */
            width: 100%;
            max-width: 700px; /* Genişlik */
            height: 900px;    /* Yükseklik */
            margin: 0 auto;   /* Ekrana Ortala */
            
            /* 3. SÜSLEMELER */
            border: 1px solid #d3c6a0; /* Hafif kenarlık */
            box-shadow: 0 10px 30px rgba(0,0,0,0.7); /* Siyah zemin üzerinde gölge */
            border-radius: 3px;
        }
    </style>

    <div class="parsom-kagidi"></div>

    """, unsafe_allow_html=True)
