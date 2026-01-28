# pages_logic/game_add.py
import streamlit as st
from datetime import datetime
from utils.database import get_users_map
from utils.config import OYUN_KURALLARI

def game_interface():
    id_to_name, name_to_id, _ = get_users_map()
    
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. OYUNCU SEÇİMİ ---
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

    # --- 2. PARŞÖMEN VE TABLO ---
    else:
        players = st.session_state["current_players"]
        
        # --- HTML İÇERİĞİ HAZIRLAMA (DÜZ METİN OLARAK) ---
        
        # 1. CSS STİLLERİ
        style_block = """
        <style>
            .parsom-kutu {
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                width: 100%;
                max-width: 850px;
                margin: 0 auto;
                border: 2px solid #8b7d6b;
                box-shadow: 0 10px 40px rgba(0,0,0,0.7);
                border-radius: 4px;
                padding: 40px;
                font-family: 'Courier New', Courier, monospace;
                color: #2c1e12;
            }
            .kral-tablo {
                width: 100%;
                border-collapse: collapse; /* Çizgileri yapıştır */
                margin-top: 20px;
            }
            .kral-tablo th {
                border: 2px solid #5c4033;
                padding: 10px;
                text-align: center;
                background-color: rgba(92, 64, 51, 0.1);
                font-weight: 900;
                font-size: 1.1em;
                text-transform: uppercase;
            }
            .kral-tablo td {
                border: 1px solid #8b7d6b;
                padding: 8px;
                height: 35px;
                font-weight: bold;
                color: #2c1e12;
            }
            .oyun-adi {
                text-align: left;
                padding-left: 15px !important;
                background-color: rgba(0,0,0,0.03);
                width: 25%;
            }
            .bos-hucre {
                background-color: transparent;
            }
            .ayrac-satir td {
                background-color: #2c1e12;
                color: #fdfbf7 !important;
                text-align: center;
                font-weight: bold;
                letter-spacing: 3px;
                border: 1px solid #2c1e12;
            }
            .baslik {
                text-align: center;
                font-size: 2.5em;
                font-weight: 900;
                color: #8b0000;
                margin: 0;
                text-transform: uppercase;
                border-bottom: 3px double #2c1e12;
                padding-bottom: 15px;
            }
        </style>
        """

        # 2. TABLO HTML'İ OLUŞTURMA
        # Başlıklar
        table_html = '<table class="kral-tablo">'
        table_html += '<thead><tr><th>OYUN TÜRÜ</th>'
        for p in players:
            table_html += f'<th>{p}</th>'
        table_html += '</tr></thead><tbody>'

        # Cezalar Satırları
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                label = f"{oyun_adi}" if limit == 1 else f"{oyun_adi} {i}"
                table_html += f"""
                <tr>
                    <td class="oyun-adi">{label}</td>
                    <td class="bos-hucre"></td>
                    <td class="bos-hucre"></td>
                    <td class="bos-hucre"></td>
                    <td class="bos-hucre"></td>
                </tr>
                """

        # Koz Ayracı
        table_html += '<tr class="ayrac-satir"><td colspan="5">--- KOZLAR ---</td></tr>'

        # Kozlar Satırları
        for i in range(1, 9):
            table_html += f"""
            <tr>
                <td class="oyun-adi">KOZ {i}</td>
                <td class="bos-hucre"></td>
                <td class="bos-hucre"></td>
                <td class="bos-hucre"></td>
                <td class="bos-hucre"></td>
            </tr>
            """
        
        table_html += '</tbody></table>'

        # --- HEPSİNİ BİRLEŞTİR VE BAS ---
        final_html = f"""
        {style_block}
        <div class="parsom-kutu">
            <h1 class="baslik">KRALİYET DEFTERİ</h1>
            {table_html}
        </div>
        """

        st.markdown(final_html, unsafe_allow_html=True)

        # Geri Dön
        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
