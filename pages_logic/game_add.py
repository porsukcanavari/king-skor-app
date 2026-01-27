# pages_logic/game_add.py
import streamlit as st

def game_interface():
    st.header("🏎️ Parşömen Kaplama Testi")

    # URL'ler
    araba_url = "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=1000&auto=format&fit=crop"
    kagit_doku_url = "https://www.transparenttextures.com/patterns/cream-paper.png" # Eski kağıt deseni

    # HTML ve CSS ile Katmanlı Yapı (Overlay)
    st.markdown(f"""
    <style>
        /* 1. Kapsayıcı Kutu */
        .resim-kutusu {{
            position: relative; /* İçindekileri üst üste bindirmek için şart */
            display: inline-block;
            width: 100%;
            max-width: 700px; /* Resim çok devasa olmasın */
            border: 5px solid #2c1e12; /* Çerçeve */
            box-shadow: 10px 10px 20px rgba(0,0,0,0.5);
        }}

        /* 2. Alttaki Araba Resmi */
        .araba-img {{
            display: block;
            width: 100%;
            height: auto;
            /* Arabayı biraz sarartalım ki kağıtla uyumlu olsun (Sepia) */
            filter: sepia(0.6) contrast(1.2) brightness(0.9);
        }}

        /* 3. Üstteki Parşömen Dokusu (Sihir Burada) */
        .doku-katmani {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            
            /* Doku Resmi */
            background-image: url('{kagit_doku_url}');
            
            /* SIKINTI ÇÖZÜCÜ AYAR: */
            mix-blend-mode: multiply; /* Resmi alttaki resimle "Çarp". Kağıt efekti verir. */
            opacity: 0.8; /* Dokunun gücü */
            pointer-events: none; /* Tıklamalar alttaki resme geçsin */
        }}
    </style>

    <div class="resim-kutusu">
        <img src="{araba_url}" class="araba-img">
        
        <div class="doku-katmani"></div>
    </div>
    
    """, unsafe_allow_html=True)
    
    st.info("👆 Yukarıdaki resim normalde modern bir araba ama CSS ile üzerine kağıt dokusu bindirdik.")
