# pages_logic/game_add.py
import streamlit as st

def game_interface():
    st.header("🏎️ Deneme: Araba Görseli")
    
    # İnternetten rastgele havalı bir araba resmi
    st.image(
        "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=1000&auto=format&fit=crop",
        caption="İstediğin Araba Burada",
        use_container_width=True
    )
