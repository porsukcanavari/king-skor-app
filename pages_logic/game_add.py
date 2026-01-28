# pages_logic/game_add.py
import streamlit as st
from utils.database import get_users_map
from utils.config import OYUN_KURALLARI

def game_interface():
    # Gerekli verileri al
    id_to_name, name_to_id, _ = get_users_map()
    
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. SEÇİM EKRANI ---
    if not st.session_state["show_paper"]:
        st.info("Oyuncuları seçin.")
        users = list(name_to_id.keys())
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("📜 Parşömeni Getir", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected
                st.session_state["show_paper"] = True
                st.rerun()
        return

    # --- 2. GÖRÜNTÜ (HTML OLUŞTURMA) ---
    else:
        players = st.session_state["current_players"]
        
        # --- HTML KODUNU PARÇA PARÇA OLUŞTURUYORUZ ---
        # Bu yöntemle "kod bloğu" hatası olmaz.
        
        # 1. CSS BAŞLANGICI
        html_code = """
        <style>
            .kagit-zemin {
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                padding: 40px;
                border: 2px solid #8b7d6b;
                box-shadow: 0 10px 30px rgba(0,0,0,0.8);
                color: #2c1e12;
                font-family: 'Courier New', Courier, monospace;
                max-width: 800px;
                margin: 0 auto;
            }
            .tablo-sus {
                width: 100%;
                border-collapse: collapse;
            }
            .tablo-sus th {
                border: 2px solid #5c4033;
                padding: 10px;
                background-color: rgba(92, 64, 51, 0.1);
                font-weight: 900;
            }
            .tablo-sus td {
                border: 1px solid #8b7d6b;
                height: 35px; /* Satır yüksekliği */
            }
            .oyun-ismi {
                font-weight: bold;
                padding-left: 10px;
                width: 30%;
            }
            .ayrac {
                background-color: #2c1e12;
                color: #fdfbf7;
                font-weight: bold;
                text-align: center;
                letter-spacing: 2px;
            }
        </style>
        """

        # 2. HTML GÖVDE BAŞLANGICI
        html_code += '<div class="kagit-zemin">'
        html_code += '<h1 style="text-align:center; color:#8b0000; margin-top:0; border-bottom:3px double #2c1e12;">KRALİYET DEFTERİ</h1>'
        
        # 3. TABLO BAŞLIĞI
        html_code += '<table class="tablo-sus">'
        html_code += '<tr><th>OYUN TÜRÜ</th>'
        for p in players:
            html_code += f'<th>{p}</th>'
        html_code += '</tr>'

        # 4. CEZALAR DÖNGÜSÜ (Satır Satır Ekliyoruz)
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue # Kozları sona sakla
            
            limit = kural['limit']
            for i in range(1, limit + 1):
                # İsimlendirme (Rıfkı 1, Rıfkı 2 gibi)
                if limit == 1:
                    ad = oyun_adi
                else:
                    ad = f"{oyun_adi} {i}"
                
                # Satırı ekle
                html_code += f"""
                <tr>
                    <td class="oyun-ismi">{ad}</td>
                    <td></td><td></td><td></td><td></td>
                </tr>
                """

        # 5. KOZ AYRACI
        html_code += '<tr><td colspan="5" class="ayrac">--- KOZLAR ---</td></tr>'

        # 6. KOZLAR DÖNGÜSÜ
        for i in range(1, 9):
            html_code += f"""
            <tr>
                <td class="oyun-ismi">KOZ {i}</td>
                <td></td><td></td><td></td><td></td>
            </tr>
            """

        # 7. KAPANIŞ
        html_code += '</table></div>'
        
        # --- EKRANA BAS ---
        st.markdown(html_code, unsafe_allow_html=True)

        # Geri butonu
        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
