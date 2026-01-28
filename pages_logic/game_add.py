# pages_logic/game_add.py
import streamlit as st
from datetime import datetime
from utils.database import get_users_map
from utils.config import OYUN_KURALLARI

def game_interface():
    id_to_name, name_to_id, _ = get_users_map()
    
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. SEÇİM EKRANI ---
    if not st.session_state["show_paper"]:
        st.info("Oyuncuları seçin.")
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

    # --- 2. IZGARA GÖRÜNÜMLÜ PARŞÖMEN ---
    else:
        players = st.session_state["current_players"]
        
        # --- TABLO SATIRLARINI HAZIRLAMA (HTML String Olarak) ---
        table_rows_html = ""
        
        # 1. Başlık Satırı (Oyun Adı + Oyuncular)
        table_rows_html += "<tr>"
        table_rows_html += '<th class="baslik-hucre sol-baslik">OYUN TÜRÜ</th>'
        for p in players:
            table_rows_html += f'<th class="baslik-hucre">{p}</th>'
        table_rows_html += "</tr>"

        # 2. Cezalar (Döngü ile ekle)
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            # Eğer oyun birden fazla kez oynanıyorsa (Örn: Rıfkı 1, Rıfkı 2 gibi göstermek istersen)
            # Ama genelde King tablosunda satır satır ayrılır.
            for i in range(1, limit + 1):
                label = f"{oyun_adi}" if limit == 1 else f"{oyun_adi} {i}"
                table_rows_html += f"""
                <tr>
                    <td class="oyun-adi">{label}</td>
                    <td></td> <td></td> <td></td> <td></td> </tr>
                """

        # Araya Koz Ayracı (Görsel Süs)
        table_rows_html += '<tr><td colspan="5" class="koz-ayrac">--- KOZLAR ---</td></tr>'

        # 3. Kozlar (8 Adet)
        for i in range(1, 9):
            table_rows_html += f"""
            <tr>
                <td class="oyun-adi">KOZ {i}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            """

        # --- CSS VE HTML ---
        st.markdown(f"""
        <style>
            /* ANA KAĞIT */
            .parsom-kagidi {{
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                border: 1px solid #d3c6a0;
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
                border-radius: 3px;
                padding: 40px;
                color: #2c1e12;
                font-family: 'Courier New', Courier, monospace;
            }}

            /* HTML TABLOSU (IZGARA YAPISI) */
            .ozel-tablo {{
                width: 100%;
                border-collapse: collapse; /* Çizgileri birleştir (Izgara görünümü) */
            }}

            /* HÜCRELER VE ÇİZGİLER */
            .ozel-tablo th, .ozel-tablo td {{
                border: 1px solid #8b7d6b; /* Izgara Çizgileri (Kahve) */
                padding: 8px;
                text-align: center;
                height: 40px; /* Satır yüksekliği */
            }}

            /* BAŞLIK HÜCRELERİ */
            .baslik-hucre {{
                border-bottom: 3px double #2c1e12 !important; /* Başlığın altını kalın çiz */
                font-weight: 900;
                font-size: 1.1em;
                text-transform: uppercase;
            }}

            /* SOL SÜTUN (OYUN İSİMLERİ) */
            .sol-baslik {{
                width: 25%; /* Sol taraf biraz geniş olsun */
                text-align: left;
                padding-left: 10px;
            }}
            
            .oyun-adi {{
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
                background-color: rgba(44, 30, 18, 0.03); /* Hafif koyuluk */
            }}

            /* KOZ AYRACI */
            .koz-ayrac {{
                background-color: #2c1e12;
                color: #fdfbf7;
                font-weight: bold;
                letter-spacing: 2px;
                border: none;
            }}

        </style>

        <div class="parsom-kagidi">
            <h1 style="text-align:center; color:#8b0000; margin-top:0;">KRALİYET DEFTERİ</h1>
            
            <table class="ozel-tablo">
                {table_rows_html}
            </table>
        </div>
        
        """, unsafe_allow_html=True)

        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
