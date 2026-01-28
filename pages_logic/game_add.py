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

    # --- 2. TAM IZGARA PARŞÖMEN ---
    else:
        players = st.session_state["current_players"]
        
        html_parts = []
        
        # A. CSS (ÇİZGİLER BURADA AYARLANIYOR)
        html_parts.append("""
        <style>
            .kagit-konteyner {
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                padding: 30px;
                border: 2px solid #5c4033;
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
                border-radius: 4px;
                margin: 0 auto;
                color: #2c1e12;
                font-family: 'Courier New', monospace;
            }
            .kral-tablo {
                width: 100%;
                border-collapse: collapse; /* Hücre çizgilerini birleştirir (Tek çizgi yapar) */
                margin-top: 20px;
            }
            
            /* TÜM HÜCRELER İÇİN KESİN ÇİZGİ */
            .kral-tablo th, .kral-tablo td {
                border: 1px solid #4a3b2a; /* KOYU KAHVE ÇİZGİ (Net görünür) */
                padding: 8px;
                text-align: center;
            }

            /* BAŞLIK HÜCRELERİ */
            .kral-tablo th {
                border-bottom: 3px double #2c1e12; /* Başlığın altı daha kalın */
                background-color: rgba(62, 39, 35, 0.1);
                font-weight: 900;
                font-size: 1.1em;
                text-transform: uppercase;
            }

            /* SOL SÜTUN (OYUN İSİMLERİ) */
            .oyun-hucre {
                text-align: left !important;
                padding-left: 15px !important;
                font-weight: bold;
                background-color: rgba(0,0,0,0.03); /* Hafif koyu zemin */
                width: 25%;
            }

            /* KOZ AYRACI */
            .ayrac-satir {
                background-color: #2c1e12;
                color: #fdfbf7;
                font-weight: bold;
                letter-spacing: 3px;
                border: 1px solid #2c1e12;
            }
            
            /* BAŞLIK */
            .parsom-baslik {
                text-align: center; 
                color: #8b0000; 
                margin-top: 0; 
                border-bottom: 2px solid #8b0000; 
                padding-bottom: 10px;
                font-weight: 900;
            }
        </style>
        """)

        # B. HTML GÖVDE
        html_parts.append('<div class="kagit-konteyner">')
        html_parts.append('<h1 class="parsom-baslik">KRALİYET DEFTERİ</h1>')
        
        # C. TABLO VE BAŞLIKLAR
        html_parts.append('<table class="kral-tablo">')
        html_parts.append('<thead><tr><th>OYUN TÜRÜ</th>')
        for p in players:
            html_parts.append(f'<th>{p}</th>')
        html_parts.append('</tr></thead><tbody>')

        # D. CEZALAR
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            
            limit = kural['limit']
            for i in range(1, limit + 1):
                label = oyun_adi if limit == 1 else f"{oyun_adi} {i}"
                html_parts.append('<tr>')
                html_parts.append(f'<td class="oyun-hucre">{label}</td>')
                html_parts.append('<td></td><td></td><td></td><td></td>') # 4 Boş Hücre (Çizgili)
                html_parts.append('</tr>')

        # E. KOZ AYRACI
        html_parts.append('<tr><td colspan="5" class="ayrac-satir">--- KOZLAR ---</td></tr>')

        # F. KOZLAR
        for i in range(1, 9):
            html_parts.append('<tr>')
            html_parts.append(f'<td class="oyun-hucre">KOZ {i}</td>')
            html_parts.append('<td></td><td></td><td></td><td></td>') # 4 Boş Hücre (Çizgili)
            html_parts.append('</tr>')

        # G. BİTİRİŞ
        html_parts.append('</tbody></table></div>')

        # H. EKRANA BAS
        st.markdown("".join(html_parts), unsafe_allow_html=True)

        # Geri Dön
        st.write("")
        if st.button("Geri Dön", use_container_width=True):
            st.session_state["show_paper"] = False
            st.rerun()
