# pages_logic/game_add.py
import streamlit as st

def game_interface():
    st.header("🧱 Astar Mantığı: Tam Kaplama")

    # URL'ler
    araba_url = "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=1000&auto=format&fit=crop"
    kagit_doku_url = "https://www.transparenttextures.com/patterns/cream-paper.png" 

    st.markdown(f"""
    <style>
        /* Kapsayıcı Kutu */
        .resim-cercevesi {{
            position: relative; /* İçindekileri üst üste bindirmek için */
            display: inline-block;
            width: 100%;
            max-width: 700px;
            border: 3px solid #2c1e12;
            box-shadow: 10px 10px 15px rgba(0,0,0,0.5);
            overflow: hidden; /* Dışarı taşanları kes */
        }}

        /* 1. KATMAN: ASTAR (ARABA) */
        /* Bu resim sadece kutunun boyutunu belirler, görünmeyecek */
        .astar-resim {{
            display: block;
            width: 100%;
            height: auto;
        }}

        /* 2. KATMAN: SIVA (PARŞÖMEN) */
        /* Bu katman alttaki resmin üzerini tamamen örter */
        .kaplama {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            
            /* Doku ve Renk */
            background-image: url('{kagit_doku_url}'); 
            background-color: #fdfbf7; /* KESİN ÇÖZÜM: Krem rengi boya */
            
            /* Görünürlük Ayarları */
            opacity: 1; /* %100 Görünür (Tamamen Mat) */
            z-index: 10; /* En üstte dur */
            
            /* İçine yazı yazalım ki kağıt olduğu belli olsun */
            display: flex;
            align-items: center;
            justify-content: center;
            color: #2c1e12;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            font-size: 2em;
            text-align: center;
            
            /* Geçiş efekti (Mouse ile gelince görmek istersen diye) */
            transition: opacity 0.5s ease;
        }}

        /* SÜRPRİZ: Mouse ile üzerine gelince astarı göster (İstemezsen sil) */
        .resim-cercevesi:hover .kaplama {{
            opacity: 0.1; /* %90 şeffaflaş */
            cursor: pointer;
        }}

    </style>

    <div class="resim-cercevesi">
        <img src="{araba_url}" class="astar-resim">
        
        <div class="kaplama">
            GİZLİ GÖREV<br>
            <span style="font-size:0.5em">(Üzerine Gel)</span>
        </div>
    </div>
    
    """, unsafe_allow_html=True)
    
    st.info("Bu kutunun boyutunu içindeki görünmez araba belirliyor. Üzeri tamamen parşömenle sıvandı.")
