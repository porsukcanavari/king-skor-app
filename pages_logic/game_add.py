# pages_logic/game_add.py
import streamlit as st
import streamlit.components.v1 as components
import json
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def game_interface():
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State Kontrolleri
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. SEÇİM EKRANI (Burası Aynı) ---
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

    # --- 2. HTML + JS İLE ÇALIŞAN PARŞÖMEN ---
    else:
        players = st.session_state["current_players"]
        
        # --- HTML İÇERİĞİ HAZIRLAMA ---
        # Burada hem CSS, hem HTML Tablo, hem de JavaScript var.
        
        # Oyuncu İsimlerini JS dizisi olarak hazırlayalım
        players_json = json.dumps(players)
        
        # HTML Başlangıcı
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            /* Senin Sevdiğin Parşömen CSS'i */
            body {{
                font-family: 'Courier New', monospace;
                background-color: transparent;
                margin: 0; padding: 10px;
            }}
            .kagit-konteyner {{
                background-color: #fdfbf7;
                background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
                padding: 30px;
                border: 2px solid #5c4033;
                box-shadow: 0 5px 20px rgba(0,0,0,0.5);
                border-radius: 4px;
                color: #2c1e12;
                max-width: 900px;
                margin: 0 auto;
            }}
            .kral-tablo {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            .kral-tablo th, .kral-tablo td {{
                border: 1px solid #4a3b2a;
                padding: 0;
                text-align: center;
                vertical-align: middle;
            }}
            .kral-tablo th {{
                padding: 10px;
                background-color: rgba(62, 39, 35, 0.1);
                border-bottom: 3px double #2c1e12;
                font-weight: 900;
                font-size: 14px;
            }}
            .hucre-input {{
                width: 90%;
                height: 35px;
                border: none;
                background-color: transparent;
                text-align: center;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #2c1e12;
                outline: none;
            }}
            .hucre-input:focus {{
                background-color: rgba(255, 215, 0, 0.1);
            }}
            .oyun-hucre {{
                text-align: left !important;
                padding-left: 10px !important;
                font-weight: bold;
                background-color: rgba(0,0,0,0.03);
                width: 25%;
                font-size: 14px;
            }}
            .ayrac-satir {{
                background-color: #2c1e12;
                color: #fdfbf7;
                font-weight: bold;
                letter-spacing: 3px;
                padding: 5px !important;
            }}
            .parsom-baslik {{
                text-align: center; color: #8b0000; margin-top: 0; 
                border-bottom: 2px solid #8b0000; padding-bottom: 10px; font-weight: 900;
            }}
            
            /* BUTON STİLİ */
            .kaydet-btn {{
                background-color: #2c1e12;
                color: #fdfbf7;
                border: none;
                padding: 15px 30px;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
                width: 100%;
                display: block;
                border-radius: 4px;
            }}
            .kaydet-btn:hover {{
                background-color: #8b0000;
            }}
        </style>
        </head>
        <body>
        
        <div class="kagit-konteyner">
            <h1 class="parsom-baslik">KRALİYET DEFTERİ</h1>
            <form id="kingForm">
            <table class="kral-tablo">
                <thead>
                    <tr>
                        <th>OYUN TÜRÜ</th>
                        <th>{players[0]}</th>
                        <th>{players[1]}</th>
                        <th>{players[2]}</th>
                        <th>{players[3]}</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # --- PYTHON İLE SATIRLARI EKLEME ---
        # Cezalar
        for oyun_adi, kural in OYUN_KURALLARI.items():
            if "Koz" in oyun_adi: continue
            limit = kural['limit']
            for i in range(1, limit + 1):
                label = oyun_adi if limit == 1 else f"{oyun_adi} {i}"
                # Her input'a özel name veriyoruz: "OyunAdi_OyuncuIndex"
                html_code += f"""
                <tr>
                    <td class="oyun-hucre">{label}</td>
                    <td><input type="number" class="hucre-input" name="{label}_0" min="0" max="13"></td>
                    <td><input type="number" class="hucre-input" name="{label}_1" min="0" max="13"></td>
                    <td><input type="number" class="hucre-input" name="{label}_2" min="0" max="13"></td>
                    <td><input type="number" class="hucre-input" name="{label}_3" min="0" max="13"></td>
                </tr>
                """

        # Koz Ayracı
        html_code += '<tr><td colspan="5" class="ayrac-satir">--- KOZLAR ---</td></tr>'

        # Kozlar
        for i in range(1, 9):
            label = f"KOZ {i}"
            html_code += f"""
            <tr>
                <td class="oyun-hucre">{label}</td>
                <td><input type="number" class="hucre-input" name="{label}_0" min="0" max="13"></td>
                <td><input type="number" class="hucre-input" name="{label}_1" min="0" max="13"></td>
                <td><input type="number" class="hucre-input" name="{label}_2" min="0" max="13"></td>
                <td><input type="number" class="hucre-input" name="{label}_3" min="0" max="13"></td>
            </tr>
            """

        # --- JAVASCRIPT ---
        # Butona basınca verileri toplayıp Streamlit'e gönderecek kısım
        html_code += """
                </tbody>
            </table>
            <button type="button" class="kaydet-btn" onclick="sendData()">💾 DEFTERİ İMZALA (KAYDET)</button>
            </form>
        </div>

        <script>
            function sendData() {
                const form = document.getElementById('kingForm');
                const formData = new FormData(form);
                const data = {};
                
                // Formdaki tüm verileri JSON objesine çevir
                for (let [key, value] of formData.entries()) {
                    if (value !== "") {
                        data[key] = value;
                    }
                }
                
                // Streamlit Component'ine veriyi gönder
                // Streamlit versiyonuna göre parent'a mesaj atıyoruz
                window.parent.postMessage({
                    type: "streamlit:componentValue",
                    data: data
                }, "*");
            }
        </script>
        </body>
        </html>
        """

        # --- BİLEŞENİ ÇALIŞTIR ---
        # height parametresi kağıdın boyunu belirler. Tablo uzun olduğu için yüksek verdim.
        # Bu fonksiyon bir "Dönüş Değeri" bekler. JS'den gelen veri buraya düşecek.
        received_data = components.html(html_code, height=1400, scrolling=True)

        # --- VERİ GELDİ Mİ KONTROLÜ ---
        # Streamlit'in standart component yapısı olmadığı için
        # Bu kısımda "Hack" yapmamız lazım.
        # Standart st.components.html geri değer döndürmez.
        # Geri değer döndürmesi için "Custom Component" yazmak gerekir ki bu çok karmaşık.
        
        st.warning("⚠️ Kanka, HTML formdan veri okumak için 'Custom Component' paketi gerekir. Ama senin için daha basit bir 'hülle' yapalım.")
        st.info("Bu ekran sadece GÖRÜNTÜ ve PDF çıktısı almak için mükemmeldir. Ama verileri kaydetmek için en baştaki 'Veri Girişli Parşömen' (Data Editor) yöntemi teknik olarak zorunludur.")
        
        # Geri Dön
        if st.button("Geri Dön"):
            st.session_state["show_paper"] = False
            st.rerun()
