# pages_logic/game_add.py
import streamlit as st
from utils.database import get_users_map
from utils.config import OYUN_KURALLARI

def game_interface():
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

    # --- 2. GARANTİ HTML TABLO ---
    else:
        players = st.session_state["current_players"]
        
        # HTML parçalarını bu listenin içine atacağız.
        # Bu yöntem sayesinde girinti hatası olması imkansız.
        html_parts = []
        
        # A. CSS STİLLERİ
        html_parts.append("""
        <style>
            .kagit-konteyner {
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                padding: 30px;
                border: 2px solid #8b7d6b;
                box-shadow: 0 10px 30px rgba(0,0,0,0.8);
                border-radius: 4px;
                margin: 0 auto;
                color: #2c1e12;
                font-family: 'Courier New', monospace;
            }
            .kral-tablo {
                width: 100%;
                border-collapse: collapse;
            }
            .kral-tablo th {
                border: 2px solid #3e2723;
                background-color: rgba(62, 39, 35, 0.1);
                padding: 10px;
                text-align: center;
                font-weight: 900;
                font-size: 1.1em;
            }
            .kral-tablo td {
                border: 1px solid #8b7d6b;
                height: 35px;
                padding: 5px;
            }
            .oyun-hucre {
                font-weight: bold;
                padding-left: 10px;
                width: 30%;
                background-color: rgba(0,0,0,0.02);
            }
            .ayrac-satir {
                background-color: #2c1e12;
                color: #fdfbf7;
                text-align: center;
                font-weight: bold;
                letter-spacing: 2px;
            }
        </style>
        """)

        # B. KUTU VE BAŞLIK
        html_parts.append('<div class="kagit-konteyner">')
        html_parts.append('<h2 style="text-align:center; color:#8b0000; border-bottom:3px double #2c1e12; margin-top:0;">KRALİYET DEFTERİ</h2>')
        
        # C. TABLO BAŞLANGICI VE BAŞLIKLAR
        html_parts.append('<table class="kral-tablo">')
        html_parts.append('<thead><tr><th>OYUN TÜRÜ</th>')
        for p in players:
            html_parts.append(f'<th>{p}</th>')
        html_parts.append('</tr></thead><tbody>')

        # D. CEZALAR DÖNGÜSÜ
        # Artık girinti sorunu yok çünkü string olarak listeye ekliyoruz.
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            
            limit = kural['limit']
            for i in range(1, limit + 1):
                label = oyun_adi if limit == 1 else f"{oyun_adi} {i}"
                html_parts.append('<tr>')
                html_parts.append(f'<td class="oyun-hucre">{label}</td>')
                html_parts.append('<td></td><td></td><td></td><td></td>') # 4 Boş Hücre
                html_parts.append('</tr>')

        # E. KOZ AYRACI
        html_parts.append('<tr><td colspan="5" class="ayrac-satir">--- KOZLAR ---</td></tr>')

        # F. KOZLAR DÖNGÜSÜ
        for i in range(1, 9):
            html_parts.append('<tr>')
            html_parts.append(f'<td class="oyun-hucre">KOZ {i}</td>')
            html_parts.append('<td></td><td></td><td></td><td></td>')
            html_parts.append('</tr>')

        # G. KAPANIŞ
        html_parts.append('</tbody></table></div>')

        # H. HEPSİNİ BİRLEŞTİR VE BAS
        # Listeyi tek bir metne çeviriyoruz ("\n" kullanmadan birleştirebiliriz ama okunaklı olsun diye kullandım)
        final_html = "".join(html_parts)
        
        st.markdown(final_html, unsafe_allow_html=True)

        # Geri Dön Butonu
        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
