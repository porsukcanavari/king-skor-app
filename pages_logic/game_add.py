# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import re
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- GÜVENLİ IMPORT ---
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# --- API AYARLARI ---
# Senin anahtarın burada gömülü.
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
def normalize_str(text):
    """Metni küçültür ve Türkçe karakterleri temizler."""
    text = str(text).lower()
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', ' ': ''}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# --- YAPAY ZEKA FONKSİYONU ---
def extract_scores_from_image(image):
    if not HAS_GENAI or not API_KEY:
        return None, "Kütüphane veya Anahtar Eksik"

    try:
        # MODEL: FLASH (Hatasız çalışan model)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # GÜVENLİK AYARLARI (Sansürü Kapat)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        prompt = """
        Sen uzman bir OCR motorusun. King İskambil Oyunu skor tablosunu okuyacaksın.
        Tabloda 4 SÜTUN (4 OYUNCU) var.
        
        GÖREV:
        Tablodaki her satırı bul ve karşısındaki 4 sayıyı oku.
        
        AŞAĞIDAKİ FORMATTA SAF JSON DÖNDÜR:
        {
            "Rıfkı": [0, 320, 0, 0],
            "Kız": [100, 0, 100, 200],
            "Erkek": [50, 0, 0, 0],
            "Kupa": [0, 0, 0, 0],
            "Son İki": [0, 0, 180, 0],
            "El Almaz": [0, 50, 0, 0],
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
        1. "Rıfkı", "Kız", "Koz 1" gibi anahtarları KESİN kullan.
        2. Sadece sayıları oku. Boşlukları 0 yap.
        3. Asla yorum yapma, sadece JSON verisi ver.
        """
        
        response = model.generate_content([prompt, image], safety_settings=safety_settings)
        raw_text = response.text
        
        # Temizlik: Markdown bloklarını kaldır
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        # JSON Parse Denemesi
        try:
            return json.loads(clean_text), raw_text
        except json.JSONDecodeError:
            # Bazen JSON bozuk gelir, düzeltmeye çalışalım
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group()), raw_text
                except:
                    pass
            return None, raw_text
            
    except Exception as e:
        return None, str(e)

# --- STİL ---
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
    
    # --- AŞAMA 1 ---
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ")
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        st.warning("⚠️ OYUNCULARI FOTOĞRAFTAKİ SIRAYLA (SOLDAN SAĞA) SEÇİN!")
        selected_players = st.multiselect("OYUNCU SIRASI:", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            uploaded_image = None
            if API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR (FLASH MOD)")
                st.markdown('<div class="ai-info">🤖 <b>Sistem Hazır.</b> Fotoğrafı yükleyin, okumaya çalışacağım.</div>', unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı", type=['png', 'jpg', 'jpeg'])
            
            btn_text = "FOTOĞRAFI TARA" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_json"] = None
                st.session_state["ai_raw_text"] = None
                
                if uploaded_image and API_KEY:
                    with st.spinner("🤖 Analiz yapılıyor..."):
                        img = Image.open(uploaded_image)
                        json_data, raw_text = extract_scores_from_image(img)
                        st.session_state["ai_json"] = json_data
                        st.session_state["ai_raw_text"] = raw_text
                        
                        if json_data:
                            st.success("Veri Çözüldü!")
                        else:
                            st.warning("Veri tam çözülemedi, Debug penceresine bakın.")

                st.session_state["sheet_open"] = True
                
                # --- VERİ DOLDURMA (AKILLI EŞLEŞTİRME) ---
                data = []
                ai_data = st.session_state.get("ai_json", {}) or {}
                
                # Normalizasyonlu anahtarlar oluştur
                normalized_ai_data = {}
                for k, v in ai_data.items():
                    normalized_ai_data[normalize_str(k)] = v

                def find_best_match(target_label):
                    """Hedef oyun ismini AI verisinde arar (Akıllı Arama)"""
                    target_norm = normalize_str(target_label)
                    target_root = normalize_str(target_label.split(" ")[0]) # "Koz 1" -> "koz"
                    
                    # 1. Tam Eşleşme
                    if target_norm in normalized_ai_data:
                        return normalized_ai_data[target_norm]
                    
                    # 2. İçinde Geçiyor mu?
                    for ai_key, val in normalized_ai_data.items():
                        if target_norm in ai_key:
                            return val
                    
                    # 3. Kök Eşleşmesi (Kozlar hariç)
                    if "koz" not in target_norm: 
                        if target_root in normalized_ai_data:
                            return normalized_ai_data[target_root]
                            
                    return [0, 0, 0, 0]

                # CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        vals = find_best_match(label)
                        
                        # Liste güvenliği
                        vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                        while len(vals) < 4: vals.append(0)
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for idx, p in enumerate(selected_players): row[p] = vals[idx]
                        data.append(row)
                
                # KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    vals = find_best_match(label)
                    
                    vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                    while len(vals) < 4: vals.append(0)
                    
                    row = {"OYUN TÜRÜ": label, "HEDEF": 13, "TÜR": "KOZ"}
                    for idx, p in enumerate(selected_players): row[p] = vals[idx]
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.set_index("OYUN TÜRÜ", inplace=True)
                st.session_state["game_df"] = df
                st.rerun()
        return

    # --- AŞAMA 2 ---
    else:
        players = st.session_state["current_players"]
        st.markdown(f"## {st.session_state['match_info']['name']}")
        
        # --- DEBUG PENCERESİ (BURAYA BAKACAĞIZ) ---
        with st.expander("🤖 DEBUG PENCERESİ (Sorun varsa buraya tıkla)", expanded=True):
            st.write("**1. Yapay Zekanın Ham Cevabı (Raw Text):**")
            st.code(st.session_state.get("ai_raw_text", "Veri yok"))
            
            st.write("**2. Bizim Anladığımız JSON:**")
            st.json(st.session_state.get("ai_json", {}))
        
        # TABLO
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
