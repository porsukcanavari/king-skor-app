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
    """Çalışan ilk modeli bulur (Flash öncelikli)."""
    return ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]

# --- DİNAMİK JSON ŞABLONU OLUŞTURUCU ---
def create_expected_json_structure():
    """
    OYUN_KURALLARI'na bakarak AI'dan tam olarak ne beklediğimizi
    dinamik bir JSON taslağı olarak hazırlar.
    Örn: {"Rıfkı 1": [...], "Rıfkı 2": [...]}
    """
    structure = {}
    
    # Cezalar
    for game, rules in OYUN_KURALLARI.items():
        if "Koz" in game: continue
        limit = rules['limit']
        
        for i in range(1, limit + 1):
            # Eğer limit 1 ise sadece "Kız", 2 ise "Rıfkı 1", "Rıfkı 2"
            key = game if limit == 1 else f"{game} {i}"
            structure[key] = [0, 0, 0, 0]
            
    # Kozlar
    for i in range(1, 9):
        structure[f"Koz {i}"] = [0, 0, 0, 0]
        
    return json.dumps(structure, indent=2, ensure_ascii=False)

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
        return None, "Kütüphane Eksik! requirements.txt güncelleyin."

    models = get_working_model()
    last_error = ""
    
    # Dinamik şablonu oluştur
    expected_json_str = create_expected_json_structure()

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            prompt = f"""
            GÖREV: Bu el yazısı King skor tablosunu oku. Tabloda 4 Sütun (4 Oyuncu) var.
            
            AŞAĞIDAKİ JSON ŞABLONUNU BİREBİR DOLDURARAK CEVAP VER:
            {expected_json_str}
            
            KURALLAR:
            1. Eğer bir oyun (Örn: Rıfkı) tabloda iki satırsa, bunları sırasıyla "Rıfkı 1" ve "Rıfkı 2" alanlarına yaz.
            2. Eğer "Erkek" oyunu tabloda "Erkek 1" ve "Erkek 2" diye ayrılmışsa, şablondaki yerlerine yaz.
            3. Eğer tabloda tek satır "Erkek" varsa, sadece "Erkek 1"i doldur, diğerini 0 bırak.
            4. Boşlukları 0 yap. Sadece JSON döndür.
            """
            
            response = model.generate_content([prompt, image], safety_settings=safety_settings)
            raw_text = response.text
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(clean_text)
                return data, f"Başarı! Model: {model_name}\n{raw_text}"
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if match:
                    return json.loads(match.group()), f"Regex ile kurtarıldı. Model: {model_name}"
                
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
            
            if HAS_GENAI and API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR")
                st.markdown('<div class="ai-info">🤖 <b>Rıfkı 1/2 Destekli Mod:</b> Yapay zeka artık Rıfkı 1 ve Rıfkı 2\'yi ayırt edebilir.</div>', unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı", type=['png', 'jpg', 'jpeg'])
            elif not HAS_GENAI:
                 st.error("🚨 KÜTÜPHANE EKSİK! requirements.txt dosyasını güncelleyin.")
            
            btn_text = "FOTOĞRAFI TARA" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_json"] = None
                
                if uploaded_image and HAS_GENAI and API_KEY:
                    with st.spinner("🤖 Analiz yapılıyor..."):
                        img = Image.open(uploaded_image)
                        json_data, raw_text = extract_scores_from_image(img)
                        st.session_state["ai_json"] = json_data
                        
                        if json_data:
                            st.success("Veri Başarıyla Okundu!")
                        else:
                            st.warning("Veri tam çözülemedi.")

                st.session_state["sheet_open"] = True
                
                # --- VERİ DOLDURMA (GÜÇLÜ EŞLEŞTİRME) ---
                data = []
                ai_data = st.session_state.get("ai_json", {}) or {}
                
                # Normalizasyon sözlüğü (Anahtarları küçült ve temizle)
                normalized_ai_data = {normalize_str(k): v for k, v in ai_data.items()}

                def find_values(target_label):
                    """
                    Hedef etiketi (Örn: 'Rıfkı 1') AI verisinde arar.
                    Tam eşleşme veya normalize edilmiş eşleşme bakar.
                    """
                    target_norm = normalize_str(target_label)
                    
                    # 1. Direkt Eşleşme (AI "Rıfkı 1" döndüyse)
                    if target_norm in normalized_ai_data:
                        return normalized_ai_data[target_norm]
                    
                    # 2. Eğer "limit 1" olan bir oyunsa (Örn: Kız) ve AI "Kız" döndüyse
                    # (Burada Rıfkı 1 için sadece "Rıfkı" aramamalıyız çünkü Rıfkı 2 de var)
                    return [0, 0, 0, 0]

                # CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    limit = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    
                    for i in range(1, limit + 1):
                        # Tablodaki etiketimiz: "Rıfkı 1" veya sadece "Kız"
                        label = oyun if limit == 1 else f"{oyun} {i}"
                        
                        vals = find_values(label)
                        
                        # Eğer değer bulunamadıysa ve oyun "Rıfkı" gibi çoklu ise
                        # AI bazen sadece "Rıfkı" diye tek bir array dönmüş olabilir mi?
                        # Bu durumda ilk satıra yazıp geçebiliriz.
                        if vals == [0,0,0,0] and limit > 1 and i == 1:
                            if normalize_str(oyun) in normalized_ai_data:
                                vals = normalized_ai_data[normalize_str(oyun)]

                        # Liste güvenliği
                        vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                        while len(vals) < 4: vals.append(0)
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for idx, p in enumerate(selected_players): row[p] = vals[idx]
                        data.append(row)
                
                # KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    vals = find_values(label)
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
