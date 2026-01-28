# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import re
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- GÜVENLİ KÜTÜPHANE KONTROLÜ ---
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# --- API AYARLARI ---
# Senin verdiğin anahtar burada
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
    except:
        pass

# --- METİN NORMALİZASYONU ---
def normalize_key(text):
    """Türkçe karakterleri ve boşlukları temizler: 'Rıfkı' -> 'rifki'"""
    text = str(text).lower()
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', ' ': ''}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# --- YAPAY ZEKA FONKSİYONU (MODEL GÜNCELLENDİ: PRO) ---
def extract_scores_from_image(image):
    if not HAS_GENAI or not API_KEY:
        return None

    try:
        # BURASI DEĞİŞTİ: FLASH YERİNE PRO KULLANIYORUZ (DAHA AKILLI)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = """
        Sen çok yetenekli bir OCR uzmanısın. El yazısıyla yazılmış King İskambil Oyunu skor tablosunu okuyacaksın.
        Tabloda 4 SÜTUN (4 oyuncu) var. Satırlar ise oyun türleridir.
        
        GÖREV:
        Fotoğrafı analiz et. Her oyun satırını bul ve karşısındaki 4 oyuncunun puanını/el sayısını oku.
        
        İPUÇLARI:
        - "Rıfkı" satırında genelde 320, 0, 0, 0 gibi puanlar olur.
        - "Kız" satırında 100, 200 gibi puanlar olur.
        - "Koz" satırlarında 13'e tamamlanan küçük sayılar (5, 3, 2, 3 gibi) olur.
        - Eğer bir hücrede çizgi (-), nokta (.) veya boşluk varsa onu 0 kabul et.
        
        Lütfen cevabı SADECE şu JSON formatında ver:
        {
            "Rıfkı": [p1, p2, p3, p4],
            "Kız": [p1, p2, p3, p4],
            "Erkek 1": [p1, p2, p3, p4],
            "Erkek 2": [p1, p2, p3, p4],
            "Kupa": [p1, p2, p3, p4],
            "Son İki": [p1, p2, p3, p4],
            "El Almaz": [p1, p2, p3, p4],
            "Koz 1": [el1, el2, el3, el4],
            "Koz 2": [el1, el2, el3, el4],
            "Koz 3": [el1, el2, el3, el4],
            "Koz 4": [el1, el2, el3, el4],
            "Koz 5": [el1, el2, el3, el4],
            "Koz 6": [el1, el2, el3, el4],
            "Koz 7": [el1, el2, el3, el4],
            "Koz 8": [el1, el2, el3, el4]
        }
        
        ÖNEMLİ:
        - Sadece JSON döndür. Başka kelime etme.
        - Satır isimlerini tahmin etmeye çalış, el yazısı olduğu için "Rifki", "Rfk" gibi yazılmış olabilir, sen doğrusunu (yukarıdaki anahtarları) kullan.
        """
        
        response = model.generate_content([prompt, image])
        text = response.text
        
        # Temizlik
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Olası hatalı virgülleri temizle (Json parse hatasını önlemek için)
        text = re.sub(r",\s*}", "}", text) 
        
        return json.loads(text)
        
    except Exception as e:
        st.error(f"AI Okuma Hatası: {str(e)}")
        return None

# --- CSS STİLİ ---
def inject_stylish_css():
    st.markdown("""
    <style>
        .stApp { font-family: 'Courier New', Courier, monospace !important; background-color: #fafafa !important; }
        h1, h2, h3 { color: #8b0000 !important; border-bottom: 2px solid #8b0000; padding-bottom: 10px; }
        div[data-testid="stDataFrame"] { border: 2px solid #2c3e50 !important; }
        .error-box { background-color: #fff5f5; color: #c0392b; padding: 10px; border-left: 6px solid #c0392b; font-weight: bold; }
        .ai-info { background-color: #e8f5e9; color: #2e7d32; padding: 10px; border: 1px solid #c8e6c9; border-radius: 5px; margin-bottom: 10px; }
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
        st.warning("⚠️ Lütfen oyuncuları kâğıtta **SOLDAN SAĞA** hangi sıradaysa öyle seçin!")
        selected_players = st.multiselect("OYUNCU SIRASI (Soldan Sağa):", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            uploaded_image = None
            if API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR (PRO MOD)")
                st.markdown('<div class="ai-info">🤖 <b>Gemini 1.5 PRO Devrede!</b> Fotoğrafı yükle, el yazısını söksün.</div>', unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı", type=['png', 'jpg', 'jpeg'])
            
            btn_text = "FOTOĞRAFI TARA VE AÇ" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_raw_data"] = None
                
                ai_data_normalized = {} # Normalize edilmiş anahtarlarla saklayacağız
                
                if uploaded_image and API_KEY:
                    with st.spinner("🤖 PRO Model analiz ediyor (Biraz sürebilir)..."):
                        img = Image.open(uploaded_image)
                        res = extract_scores_from_image(img)
                        if res:
                            st.session_state["ai_raw_data"] = res
                            # Normalizasyon (AI "Rıfkı" der, biz "rifki" yaparız)
                            ai_data_normalized = {normalize_key(k): v for k, v in res.items()}
                            st.success("Okuma Başarılı!")
                        else:
                            st.error("Okuma Başarısız.")

                st.session_state["sheet_open"] = True
                
                # --- VERİ DOLDURMA (ESNEK EŞLEŞTİRME) ---
                data = []
                
                def get_vals_for_row(game_label):
                    # 1. Tam isimle dene ("Rıfkı", "Koz 1")
                    key = normalize_key(game_label)
                    if key in ai_data_normalized:
                        return ai_data_normalized[key]
                    
                    # 2. Oyunun kök adıyla dene ("Rıfkı 1" -> "rifki")
                    # (Çünkü AI genelde "Rıfkı 1" demez, direkt "Rıfkı" der)
                    root_name = normalize_key(game_label.split(" ")[0])
                    if root_name in ai_data_normalized:
                        return ai_data_normalized[root_name]
                        
                    return [0, 0, 0, 0]

                # 1. CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        
                        # Yapay zekadan gelen listeyi ([320, 0, 0, 0] gibi) al
                        vals = get_vals_for_row(label)
                        
                        # Listeyi 4 kişiye tamamla ve sayı olduğundan emin ol
                        vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                        while len(vals) < 4: vals.append(0)
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for idx, p in enumerate(selected_players):
                            row[p] = vals[idx] # Sırayla dağıt
                        data.append(row)
                
                # 2. KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    vals = get_vals_for_row(label)
                    
                    # Listeyi 4 kişiye tamamla
                    vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                    while len(vals) < 4: vals.append(0)
                    
                    row = {"OYUN TÜRÜ": label, "HEDEF": 13, "TÜR": "KOZ"}
                    for idx, p in enumerate(selected_players):
                        row[p] = vals[idx]
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
        
        # Debug Alanı
        if st.session_state.get("ai_raw_data"):
            with st.expander("🤖 Yapay Zeka Ne Okudu? (Tıkla Gör)"):
                st.json(st.session_state["ai_raw_data"])
        
        # Tablo
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
