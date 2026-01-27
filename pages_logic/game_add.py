# pages_logic/game_add.py
import streamlit as st

def game_interface():
    st.markdown("""
    <style>
        /* 1. PARŞÖMEN KUTUSU */
        .parsom-kagidi {
            background-color: #fdfbf7;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            width: 100%;
            max-width: 700px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8); /* Gölge */
            border: 1px solid #d3c6a0;
            padding: 40px; /* Kağıdın kenar boşlukları */
            box-sizing: border-box;
            border-radius: 2px;
        }

        /* 2. GÖRSEL TABLO (İŞLEVSİZ) */
        .hayalet-tablo {
            width: 100%;
            border-collapse: collapse; /* Çizgileri yapıştır */
        }

        /* Hücreler (Kutucuklar) */
        .hayalet-tablo td {
            border: 2px solid #2c1e12; /* Koyu Kahve Çizgiler */
            height: 50px; /* Her satırın yüksekliği */
            width: 50%;   /* İki sütunlu yaptım ki tabloya benzesin */
        }

        /* Başlık gibi görünen ilk satır */
        .hayalet-tablo tr:first-child td {
            border-top: 4px double #2c1e12; /* Üstü kalın olsun */
            height: 60px;
        }

    </style>

    <div class="parsom-kagidi">
        <table class="hayalet-tablo">
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
            <tr><td></td><td></td></tr>
        </table>
    </div>

    """, unsafe_allow_html=True)
