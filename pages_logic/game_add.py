# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- GÜVENLİ KÜTÜPHANE KONTROLÜ ---
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# --- API AYARLARI ---
MANUEL_API_KEY = "AIzaSyDp66e5Kxm3g9scKZxWKUdcuv6yeQcMgk0"

API_KEY = None
if HAS_GENAI:
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            API_KEY = st.secrets["GOOGLE_API_KEY"]
        elif MANUEL_API_KEY:
            API_KEY = MANUEL_API_KEY
        if API_KEY:
            genai.configure(api_key=API_KEY)
    except Exception as e:
        print(f"API Hatası: {e}")

# --- YAPAY ZEKA FONKSİYONU (YENİ SÜTUN MANTIĞI) ---
def extract_scores_from_image(image):
    """
    İsimlere bakmaksızın, her oyun türü için [p1, p2, p3, p4] şeklinde liste döndürür.
    """
    if not HAS_GENAI or not API_KEY:
        return None

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Sen uzman bir King kart oyunu skor tablosu okuyucususun.
        Fotoğrafta 4 oyuncuya ait 4 sütunlu bir tablo var.
        
        GÖREV:
        Satır satır oyunları oku ve her satır için soldan sağa 4 sütundaki değerleri bir LİSTE olarak ver.
        İsimleri okumana gerek yok, sadece sayıların sırasını koru.
        
        İSTENEN JSON FORMATI:
        {
          "Rıfkı": [320, 0, 0, 0],
          "Kız": [0, 100, 0, 100],
          "Erkek": [0, 0, 0, 0],
          "Kupa": [0, 0, 0, 0],
          "Son İki": [0, 0, 0, 0],
          "El Almaz": [0, 0, 0, 0],
          "Koz 1": [5, 3, 2, 3],
          "Koz 2": [0, 0, 0, 0],
          "Koz 3": [0, 0, 0, 0],
          "Koz 4": [0, 0, 0, 0],
          "Koz 5": [0, 0, 0, 0],
          "Koz 6": [0, 0, 0, 0],
          "Koz 7": [0, 0, 0, 0],
          "Koz 8": [0, 0, 0, 0]
        }

        KURALLAR:
        1. SADECE JSON döndür. Markdown yok.
        2. Cezalar (Rıfkı, Kız vb.) için tabloda yazan PUANI al (Örn: 320, 50).
        3. Kozlar (Koz 1..8) için tabloda yazan EL SAYISINI al (Örn: 5, 3).
        4. Boş, okunamayan veya çizgi (-) olan yerlere 0 yaz.
        5. Eğer bir oyun için satır bulamazsan [0, 0, 0, 0] döndür.
        """
        
        response = model.generate_content([prompt, image])
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        st.error(f"AI Okuma Hatası: {str(e)}")
        return None

# --- STİL ---
def inject_stylish_css():
    st.markdown("""
    <style>
        .stApp { font-family: 'Courier New', Courier, monospace !important; background-color: #fafafa !important; }
        h1, h2, h3 { color: #8b0000 !important; border-bottom: 2px solid #8b0000; padding-bottom: 10px; }
        div[data-testid="stDataFrame"] { border: 2px solid #2c3e50 !important; }
        .error-box { background-color: #fff5f5; color: #c0392b; padding: 10px; border-left: 6px solid #c0392b; font-weight: bold; }
        .ai-info { background-color: #e8f5e9; color: #2e7d32; padding: 10px; border: 1px solid #c8e6c9; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_stylish_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_open" not in st.session_state: st.session_state["sheet_open"] = False
    
    # --- AŞAMA 1: KURULUM ---
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ")
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        
        st.warning("⚠️ ÖNEMLİ: Oyuncuları fotoğraftaki kâğıtta SOLDAN SAĞA hangi sıradaysa öyle seçin!")
        selected_players = st.multiselect("OYUNCU SIRASI (Soldan Sağa):", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            uploaded_image = None
            if API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR")
                st.markdown('<div class="ai-info">🤖 <b>Sistem Hazır:</b> Fotoğrafı yükleyin, sütunları sırasıyla okuyup dolduracağım.</div>', unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı", type=['png', 'jpg', 'jpeg'])
            
            btn_text = "FOTOĞRAFI TARA VE AÇ" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_raw_data"] = None
                
                ai_data = {}
                if uploaded_image and API_KEY:
                    with st.spinner("🤖 Fotoğraf taranıyor..."):
                        img = Image.open(uploaded_image)
                        res = extract_scores_from_image(img) # Artık oyuncu ismi göndermiyoruz
                        if res:
                            ai_data = res
                            st.session_state["ai_raw_data"] = res
                            st.success("Okuma Başarılı!")
                        else:
                            st.error("Fotoğraf okunamadı.")

                st.session_state["sheet_open"] = True
                
                # --- VERİ DOLDURMA (SÜTUN BAZLI) ---
                data = []
                
                # Yardımcı fonksiyon: Listeden indexe göre puan çek
                def get_score_by_index(game_keys, player_index):
                    for key in game_keys:
                        if key in ai_data and isinstance(ai_data[key], list):
                            try:
                                # Listede yeterli eleman varsa al, yoksa 0
                                if len(ai_data[key]) > player_index:
                                    return int(ai_data[key][player_index])
                            except:
                                return 0
                    return 0

                # 1. CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        # AI genelde "Rıfkı" olarak döner, "Rıfkı 1" demez. Kök ismi de ara.
                        keys_to_search = [label, oyun]
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        
                        # Her oyuncu için (index 0, 1, 2, 3) sırayla puanı çek
                        for idx, p in enumerate(selected_players):
                            row[p] = get_score_by_index(keys_to_search, idx)
                            
                        data.append(row)
                
                # 2. KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    row = {"OYUN TÜRÜ": label, "HEDEF": 13, "TÜR": "KOZ"}
                    
                    # Kozları genelde "Koz 1", "Koz 2" diye düzgün okur
                    # Ama bazen "Koz" diye tek liste dönebilir (dikkatli olmak lazım)
                    for idx, p in enumerate(selected_players):
                         row[p] = get_score_by_index([label], idx)
                         
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.set_index("OYUN TÜRÜ", inplace=True)
                st.session_state["game_df"] = df
                st.rerun()
        return

    # --- AŞAMA 2: EDİTÖR ---
    else:
        players = st.session_state["current_players"]
        st.markdown(f"## {st.session_state['match_info']['name']}")
        
        if st.session_state.get("ai_raw_data"):
            with st.expander("🤖 Yapay Zeka Ne Okudu? (Debug)"):
                st.json(st.session_state["ai_raw_data"])
        
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None, "TÜR": None,
                **{p: st.column_config.NumberColumn(p, min_value=0, step=1, format="%d") for p in players}
            }
        )

        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for idx, row in edited_df.iterrows():
            tgt = row["HEDEF"]; tur = row["TÜR"]; cur = sum([row[p] for p in players])
            
            if cur > 0:
                if cur != tgt:
                    msg = f"⚠️ {idx}: Toplam {tgt} olmalı ({cur})"
                    errors.append(msg)
                else:
                    r_data = [idx]
                    for p in players:
                        val = row[p] * (50 if tur == "KOZ" else -1)
                        r_data.append(val); col_totals[p] += val
                    clean_rows.append(r_data)

        if errors:
            for e in errors: st.markdown(f"<div class='error-box'>{e}</div>", unsafe_allow_html=True)
            
        c1, c2 = st.columns([2, 1])
        with c1:
            if st.button("💾 KAYDET", type="primary", use_container_width=True, disabled=bool(errors)):
                if clean_rows:
                    ft = ["TOPLAM"] + list(col_totals.values())
                    hd = ["OYUN TÜRÜ"] + [f"{p} (uid:{name_to_id.get(p,'?')})" for p in players]
                    if save_match_to_sheet(hd, clean_rows, ft):
                        st.balloons(); st.session_state["sheet_open"] = False; del st.session_state["game_df"]; st.rerun()
        with c2:
            if st.button("İPTAL", use_container_width=True):
                st.session_state["sheet_open"] = False; st.rerun()
