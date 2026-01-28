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

# --- DİNAMİK MODEL SEÇİCİ (2.5 EKLENDİ) ---
def get_best_available_model():
    if not HAS_GENAI or not API_KEY:
        return None, "API Key yok."

    # Senin istediğin sıralama: Önce 2.5 Pro, sonra 2.5 Flash, sonra diğerleri
    priority_models = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro-vision"
    ]
    
    # Direkt string liste döndürüyoruz, aşağıdaki fonksiyon sırayla deneyecek
    return priority_models

# --- METİN NORMALİZASYONU ---
def normalize_str(text):
    text = str(text).lower()
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', ' ': ''}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# --- ANA FONKSİYON ---
def extract_scores_from_image(image):
    if not HAS_GENAI:
        return None, "Kütüphane Eksik! requirements.txt güncelleyin."

    # Model listesini al
    model_list = get_best_available_model()
    last_error = ""

    # SADECE PROMPT DEĞİŞTİ (AYRIŞTIRMA İÇİN)
    prompt = """
    GÖREV: King skor tablosunu oku. 4 Sütun (Oyuncu) var.
    
    ÖNEMLİ - SATIRLARI AYIR:
    1. CEZALAR: "Rıfkı" ve "Erkek" oyunları tabloda genellikle alt alta İKİ SATIRDIR.
       - Üstteki satırı "Rıfkı 1" (veya "Erkek 1") olarak al.
       - Alttaki satırı "Rıfkı 2" (veya "Erkek 2") olarak al.
       - ASLA bu iki satırı toplayıp tek satırda verme.
    
    2. KOZLAR: Kağıdın altındaki kare kutucukları (grid) oku.
       - Sıralama: Sol Üst -> Sağ Üst -> Sol Alt -> Sağ Alt (Koz 1'den Koz 8'e kadar).

    AŞAĞIDAKİ FORMATTA JSON DÖNDÜR:
    {
        "Rıfkı 1": [0, 0, 0, 0],
        "Rıfkı 2": [0, 0, 0, 0],
        "Kız": [0, 0, 0, 0],
        "Erkek 1": [0, 0, 0, 0],
        "Erkek 2": [0, 0, 0, 0],
        "Kupa": [0, 0, 0, 0],
        "Son İki": [0, 0, 0, 0],
        "El Almaz": [0, 0, 0, 0],
        "Koz 1": [0, 0, 0, 0],
        "Koz 2": [0, 0, 0, 0],
        "Koz 3": [0, 0, 0, 0],
        "Koz 4": [0, 0, 0, 0],
        "Koz 5": [0, 0, 0, 0],
        "Koz 6": [0, 0, 0, 0],
        "Koz 7": [0, 0, 0, 0],
        "Koz 8": [0, 0, 0, 0]
    }
    
    KURALLAR:
    - Boşlukları 0 yap.
    - Sadece JSON ver.
    """

    for model_name in model_list:
        try:
            model = genai.GenerativeModel(model_name)
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = model.generate_content([prompt, image], safety_settings=safety_settings)
            raw_text = response.text
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            try:
                # Başarılı olursa dön
                return json.loads(clean_text), f"Başarı! Model: {model_name}\n{raw_text}"
            except:
                match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if match:
                    return json.loads(match.group()), f"Regex Başarısı! Model: {model_name}\n{raw_text}"
        
        except Exception as e:
            last_error = str(e)
            continue # Bu model çalışmadıysa sıradakine geç

    return None, f"Hiçbir model çalışmadı. Son hata: {last_error}"

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
        st.warning("⚠️ OYUNCULARI FOTOĞRAFTAKİ SIRAYLA (SOLDAN SAĞA) SEÇİN!")
        selected_players = st.multiselect("OYUNCU SIRASI:", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            uploaded_image = None
            if HAS_GENAI and API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR (2.5 MODEL)")
                st.markdown('<div class="ai-info">🤖 <b>Ayrıştırıcı Mod:</b> Rıfkı 1/2 ayrımı yapmayı dener.</div>', unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı", type=['png', 'jpg', 'jpeg'])
            elif not HAS_GENAI:
                st.error("⚠️ 'requirements.txt' DOSYASINI GÜNCELLEMEDİNİZ! Kütüphane eksik.")
            
            btn_text = "FOTOĞRAFI TARA" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_json"] = None
                st.session_state["ai_raw_text"] = None
                
                if uploaded_image and HAS_GENAI and API_KEY:
                    with st.spinner("🤖 Analiz yapılıyor..."):
                        img = Image.open(uploaded_image)
                        json_data, raw_text = extract_scores_from_image(img)
                        st.session_state["ai_json"] = json_data
                        st.session_state["ai_raw_text"] = raw_text
                        
                        if json_data:
                            st.success("Başarılı!")
                        else:
                            st.warning("Hata oluştu, Debug'a bakın.")

                st.session_state["sheet_open"] = True
                
                # --- VERİ DOLDURMA ---
                data = []
                ai_data = st.session_state.get("ai_json", {}) or {}
                # Normalizasyon
                normalized_ai_data = {normalize_str(k): v for k, v in ai_data.items()}

                def find_best_match(target_label):
                    target_norm = normalize_str(target_label)
                    target_root = normalize_str(target_label.split(" ")[0])
                    
                    # 1. Tam Eşleşme (Rıfkı 1 -> rifki1)
                    if target_norm in normalized_ai_data: 
                        return normalized_ai_data[target_norm]
                    
                    # 2. İçinde Geçiyor mu?
                    for ai_key, val in normalized_ai_data.items():
                        if target_norm in ai_key: return val

                    # 3. Kök Eşleşme (SON ÇARE): Kozlar hariç.
                    # Eğer yapay zeka ayıramazsa ve sadece "Rıfkı" dönerse,
                    # bunu sadece "Rıfkı 1"e (i=1) yaz, Rıfkı 2'ye yazma.
                    if "koz" not in target_norm and target_root in normalized_ai_data:
                         if "1" in target_label: # Sadece 1. satırsa doldur
                             return normalized_ai_data[target_root]
                    
                    return [0, 0, 0, 0]

                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        vals = find_best_match(label)
                        vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                        while len(vals) < 4: vals.append(0)
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for idx, p in enumerate(selected_players): row[p] = vals[idx]
                        data.append(row)
                
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

    else:
        players = st.session_state["current_players"]
        st.markdown(f"## {st.session_state['match_info']['name']}")
        
        with st.expander("🤖 DEBUG PENCERESİ", expanded=True):
            st.text(st.session_state.get("ai_raw_text", "Veri yok."))

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
                        # Koz x 50, Ceza x -1 mantığı
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
