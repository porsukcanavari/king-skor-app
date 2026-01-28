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

    # --- 2. GÖRSEL PARŞÖMEN VE TABLO ---
    else:
        players = st.session_state["current_players"]
        
        # --- HTML İÇERİĞİNİ HAZIRLAMA ---
        # 1. Tablo Başlıkları
        table_rows = "<tr>"
        table_rows += '<th class="baslik-hucre sol-baslik">OYUN TÜRÜ</th>'
        for p in players:
            table_rows += f'<th class="baslik-hucre">{p}</th>'
        table_rows += "</tr>"

        # 2. Cezalar
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                label = f"{oyun_adi}" if limit == 1 else f"{oyun_adi} {i}"
                table_rows += f"""
                <tr>
                    <td class="oyun-adi">{label}</td>
                    <td></td><td></td><td></td><td></td>
                </tr>
                """

        # 3. Koz Ayracı
        table_rows += '<tr><td colspan="5" class="koz-ayrac">--- KOZLAR ---</td></tr>'

        # 4. Kozlar
        for i in range(1, 9):
            table_rows += f"""
            <tr>
                <td class="oyun-adi">KOZ {i}</td>
                <td></td><td></td><td></td><td></td>
            </tr>
            """

        # --- CSS STİLLERİ ---
        css_style = """
        <style>
            .parsom-kagidi {
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
            }
            .ozel-tablo {
                width: 100%;
                border-collapse: collapse; 
            }
            .ozel-tablo th, .ozel-tablo td {
                border: 1px solid #8b7d6b; 
                padding: 5px;
                text-align: center;
                height: 35px;
            }
            .baslik-hucre {
                border-bottom: 3px double #2c1e12 !important;
                font-weight: 900;
                font-size: 1.1em;
                text-transform: uppercase;
                background-color: rgba(44, 30, 18, 0.05);
            }
            .sol-baslik {
                text-align: left;
                padding-left: 10px;
                width: 30%;
            }
            .oyun-adi {
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
            }
            .koz-ayrac {
                background-color: #2c1e12;
                color: #fdfbf7;
                font-weight: bold;
                letter-spacing: 2px;
                height: 30px !important;
            }
        </style>
        """

        # --- HTML BİRLEŞTİRME VE BASMA ---
        full_html = f"""
        {css_style}
        <div class="parsom-kagidi">
            <h1 style="text-align:center; color:#8b0000; margin-top:0; border-bottom: 2px solid #8b0000; padding-bottom:10px;">KRALİYET DEFTERİ</h1>
            <table class="ozel-tablo">
                {table_rows}
            </table>
        </div>
        """

        # unsafe_allow_html=True ile HTML'i kod değil görüntü olarak işlemesini sağlıyoruz
        st.markdown(full_html, unsafe_allow_html=True)

        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
