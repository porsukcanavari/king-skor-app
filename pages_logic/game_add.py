# pages_logic/game_add.py
import streamlit as st

def game_interface():
    # Sadece CSS ve HTML ile boş bir kutu çiziyoruz
    st.markdown("""
    <style>
        .beyaz-kagit {
            background-color: white;
            width: 100%;
            max-width: 700px; /* Kağıt genişliği */
            height: 900px;    /* Kağıt yüksekliği */
            margin: 0 auto;   /* Ortala */
            box-shadow: 0 0 30px rgba(0,0,0,0.7); /* Gölge */
            border-radius: 2px;
        }
    </style>

    <div class="beyaz-kagit"></div>

    """, unsafe_allow_html=True)
