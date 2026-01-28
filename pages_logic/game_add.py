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

# --- MODEL SEÇİCİ ---
def get_working_model():
    return ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]

# --- METİN NORMALİZASYONU ---
def normalize_str(text):
    text = str(text).lower()
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', ' ': ''}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# --- YAPAY ZEKA FONKSİYONU ---
def extract_scores_from_image(image):
    if not HAS_GENAI:
        return None, "Kütüphane Eksik."

    models = get_working_model()
    last_error = ""

    # Yapay Zekadan İstediğimiz Net Format
    prompt = """
    Sen bir OCR uzmanısın. King skor tablosunu okuyacaksın. 4 Sütun (4 Oyuncu) var.
    
    AŞAĞIDAKİ ANAHTARLARI KULLANARAK JSON DÖNDÜR:
    "Rıfkı 1", "Rıfkı 2", "Kız", "Erkek 1", "Erkek 2", "Kupa", "Son İki", "El Almaz",
    "Koz 1", "Koz 2", "Koz 3", "Koz 4", "Koz 5", "Koz 6", "Koz 7", "Koz 8"
    
    KURALLAR:
    1. Tabloda "Rıfkı" başlığı altında iki satır varsa sırasıyla "Rıfkı 1" ve "Rıfkı 2"ye yaz.
    2. Tek satır varsa sadece "Rıfkı 1"e yaz, "Rıfkı 2" [0,0,0,0] olsun.
    3. Erkek oyunu için de aynısını yap (Erkek 1, Erkek 2).
    4. Sadece sayıları al, boşlukları 0 yap.
    5. Cevap SADECE JSON olsun.
    
    ÖRNEK ÇIKTI FORMATI:
    {
      "Rıfkı 1": [0, 320, 0, 0],
      "Rıfkı 2": [0, 0, 320, 0],
      "Kız": [100, 0, 0, 0],
      "Koz 1": [5, 3, 2, 3]
      ...
    }
    """

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            
            # Sansür Yok
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = model.generate_content([prompt, image], safety_settings=safety_settings)
            raw_text = response.text
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # JSON Parse (Hata toleranslı)
            try:
                # Olası tırnak hatalarını vs temizle
                if not clean_text.endswith("}"): clean_text += "}"
                data = json.loads(clean_text)
                return data, f"Başarı ({model_name})"
            except json.JSONDecodeError:
                # Regex ile JSON bloğunu yakala
                match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if match:
                    return json.loads(match.group()), f"Regex Başarısı ({model_name})"
                
        except Exception as e:
            last_error = str(e)
            continue
            
    return None, f"Hata: {last_error}"

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
    
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ")
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        st.warning("⚠️ OYUNCULARI FOTOĞRAFTAKİ SIRAYLA SEÇİN!")
        selected_players = st.multiselect("OYUNCU SIRASI:", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            uploaded_image = None
            
            if HAS_GENAI and API_KEY:
                st.markdown("### 📸 FOTOĞRAF YÜKLE")
                st.markdown('<div class="ai-info">🤖 <b>Hazır:</b> Fotoğrafı yükleyin, Rıfkı 1 ve 2\'yi ayırarak okumaya çalışacağım.</div>', unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı", type=['png', 'jpg', 'jpeg'])
            elif not HAS_GENAI:
                 st.error("🚨 KÜTÜPHANE EKSİK! requirements.txt dosyasını kontrol edin.")
            
            btn_text = "TARA VE AÇ" if uploaded_image else "BOŞ AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_json"] = None
                st.session_state["ai_log"] = None
                
                if uploaded_image and HAS_GENAI and API_KEY:
                    with st.spinner("🤖 Okunuyor..."):
                        img = Image.open(uploaded_image)
                        json_data, log_msg = extract_scores_from_image(img)
                        st.session_state["ai_json"] = json_data
                        st.session_state["ai_log"] = log_msg
                        
                        if json_data:
                            st.success("Okundu!")
                        else:
                            st.warning("Okunamadı.")

                st.session_state["sheet_open"] = True
                
                # --- VERİ EŞLEŞTİRME ---
                data = []
                ai_data = st.session_state.get("ai_json", {}) or {}
                
                # Normalizasyon
                norm_ai = {normalize_str(k): v for k, v in ai_data.items()}

                def get_vals(target_label):
                    """
                    Önce tam isme bakar ("Rıfkı 1"), bulamazsa kök isme bakar ("Rıfkı").
                    """
                    t_norm = normalize_str(target_label)
                    t_root = normalize_str(target_label.split(" ")[0])
                    
                    # 1. Tam Eşleşme (Öncelikli)
                    if t_norm in norm_ai: return norm_ai[t_norm]
                    
                    # 2. İçinde Geçme Kontrolü
                    for k, v in norm_ai.items():
                        if t_norm in k: return v
                        
                    # 3. Kök Eşleşmesi (Son çare)
                    # Sadece Rıfkı ve Erkek gibi oyunlarda, eğer "Rıfkı 1" arıyorsak ve 
                    # AI sadece "Rıfkı" döndüyse, onu Rıfkı 1'e yazalım.
                    if "koz" not in t_norm:
                        if t_root in norm_ai:
                            # Ancak bunu sadece "X 1" ise yapalım, "X 2"ye aynı veriyi yazmayalım
                            if "1" in target_label:
                                return norm_ai[t_root]
                            
                    return [0, 0, 0, 0]

                # CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    limit = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    
                    for i in range(1, limit + 1):
                        label = oyun if limit == 1 else f"{oyun} {i}"
                        vals = get_vals(label)
                        
                        vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                        while len(vals) < 4: vals.append(0)
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for idx, p in enumerate(selected_players): row[p] = vals[idx]
                        data.append(row)
                
                # KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    vals = get_vals(label)
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
        
        # DEBUG
        if not st.session_state.get("ai_json"):
             with st.expander("🛑 HATA RAPORU (Veri Neden Gelmedi?)"):
                 st.write(st.session_state.get("ai_log", "Log yok"))

        edited_df = st.data_editor(st.session_state["game_df"], use_container_width=True, height=800, column_config={"HEDEF": None, "TÜR": None, **{p: st.column_config.NumberColumn(p, min_value=0, step=1, format="%d") for p in players}})

        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for idx, row in edited_df.iterrows():
            tgt = row["HEDEF"]; tur = row["TÜR"]; cur = sum([row[p] for p in players])
            if cur > 0:
                if cur != tgt: errors.append(f"⚠️ {idx}: Toplam {tgt} olmalı ({cur})")
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
                    if save_match_to_sheet(hd, clean_rows, ft): st.balloons(); st.session_state["sheet_open"] = False; del st.session_state["game_df"]; st.rerun()
        with c2:
            if st.button("İPTAL", use_container_width=True): st.session_state["sheet_open"] = False; st.rerun()
