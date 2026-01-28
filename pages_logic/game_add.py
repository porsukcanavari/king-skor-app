# pages_logic/game_add.py (güncellenmiş kısımlar)
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

# --- DİNAMİK MODEL SEÇİCİ (404 SAVAR) ---
def get_best_available_model():
    """
    Sunucuda ve API anahtarında kullanılabilir olan İLK VİZYON modelini bulur.
    """
    if not HAS_GENAI or not API_KEY:
        return None, "API Key yok."

    log = []
    found_model = None

    try:
        # Google'a sor: Hangi modellerim var?
        for m in genai.list_models():
            log.append(f"- {m.name}")
            # 'generateContent' destekleyen ve 'vision' yeteneği olanlara bak
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name or 'vision' in m.name or 'pro' in m.name:
                    found_model = m.name
                    # Flash varsa direkt onu al ve çık, yoksa diğerlerine bakmaya devam et
                    if 'flash' in m.name:
                        break
        
        if found_model:
            return found_model, f"Otomatik Seçilen Model: {found_model}"
        else:
            # Hiçbir şey bulamazsa klasik olanı dene
            return "gemini-1.5-flash", "Listede uygun model bulunamadı, varsayılan deneniyor.\nModeller: " + ", ".join(log)

    except Exception as e:
        return "gemini-1.5-flash", f"Model listesi alınamadı ({str(e)}), varsayılan deneniyor."

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

    # 1. Modeli Bul
    model_name, log_msg = get_best_available_model()
    
    try:
        model = genai.GenerativeModel(model_name)
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        prompt = """
        GÖREV: Bu el yazısı King skor tablosunu oku. 4 Sütun (Oyuncu) var.
        Tabloda CEZA bölümü 6 farklı oyun türü ve her tür 2 kez tekrar ediyor (toplam 12 satır),
        KOZ bölümü ise 8 satırdan oluşuyor.
        
        KRİTİK KURALLAR:
        1. Her ceza türü 2 ayrı satırda - farklı veriler içerebilir!
        2. Örneğin "Rıfkı" iki ayrı satırda olacak: İlk Rıfkı satırı ve ikinci Rıfkı satırı
        3. Koz bölümü soldan sağa, yukarıdan aşağıya doğru okunur:
           - İlk satır: Koz 1, Koz 2, Koz 3, Koz 4 (soldan sağa)
           - İkinci satır: Koz 5, Koz 6, Koz 7, Koz 8 (soldan sağa)
           NOT: Koz değerleri her kutu için ayrı okunacak!
        
        CEZA SATIRLARI SIRASI (12 satır):
        1. Rıfkı 1
        2. Rıfkı 2
        3. Kız 1
        4. Kız 2
        5. Erkek 1
        6. Erkek 2
        7. Kupa 1
        8. Kupa 2
        9. Son İki 1
        10. Son İki 2
        11. El Almaz 1
        12. El Almaz 2
        
        KOZ SATIRLARI (8 satır):
        13. Koz 1
        14. Koz 2
        15. Koz 3
        16. Koz 4
        17. Koz 5
        18. Koz 6
        19. Koz 7
        20. Koz 8
        
        FORMAT (SAF JSON):
        {
            "satirlar": [
                [0, 320, 0, 0],     # Rıfkı 1
                [0, 0, 320, 0],     # Rıfkı 2
                [100, 0, 100, 200], # Kız 1
                [0, 100, 0, 0],     # Kız 2
                [50, 0, 0, 0],      # Erkek 1
                [0, 50, 0, 0],      # Erkek 2
                [0, 0, 0, 0],       # Kupa 1
                [0, 0, 0, 0],       # Kupa 2
                [0, 0, 180, 0],     # Son İki 1
                [0, 0, 0, 180],     # Son İki 2
                [0, 50, 0, 0],      # El Almaz 1
                [0, 0, 50, 0],      # El Almaz 2
                [5, 3, 2, 3],       # Koz 1 (İLK SATIR, SOL)
                [0, 0, 0, 0],       # Koz 2 (İLK SATIR, SAĞ)
                [0, 0, 0, 0],       # Koz 3 (İLK SATIR, SAĞ)
                [0, 0, 0, 0],       # Koz 4 (İLK SATIR, SAĞ)
                [0, 0, 0, 0],       # Koz 5 (İKİNCİ SATIR, SOL)
                [0, 0, 0, 0],       # Koz 6
                [0, 0, 0, 0],       # Koz 7
                [0, 0, 0, 0]        # Koz 8
            ]
        }
        
        KURALLAR:
        1. Boşlukları 0 yap.
        2. Markdown kullanma.
        3. Her satırı ayrı ayrı oku.
        """
        
        response = model.generate_content([prompt, image], safety_settings=safety_settings)
        raw_text = response.text
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(clean_text)
            if isinstance(data, dict) and "satirlar" in data:
                return data, f"{log_msg}\n\nBaşarı (Yeni Format)!\n{raw_text}"
            elif isinstance(data, dict):
                # Eski formatı yeni formata dönüştür
                satirlar = []
                normalized_ai_data = {normalize_str(k): v for k, v in data.items()}
                
                # Ceza satırları için
                ceza_oyunlari = ["Rıfkı", "Kız", "Erkek", "Kupa", "Son İki", "El Almaz"]
                for oyun in ceza_oyunlari:
                    oyun_norm = normalize_str(oyun)
                    # İki ayrı satır için
                    for i in range(2):
                        found = False
                        # Önce tam eşleşme
                        for ai_key in normalized_ai_data.keys():
                            if oyun_norm in ai_key or (f"{oyun_norm}{i+1}" in ai_key):
                                satirlar.append(normalized_ai_data[ai_key])
                                found = True
                                break
                        if not found:
                            satirlar.append([0, 0, 0, 0])
                
                # Koz satırları için
                for i in range(1, 9):
                    koz_key = f"koz{i}"
                    found = False
                    for ai_key in normalized_ai_data.keys():
                        if koz_key in normalize_str(ai_key):
                            satirlar.append(normalized_ai_data[ai_key])
                            found = True
                            break
                    if not found:
                        satirlar.append([0, 0, 0, 0])
                
                new_data = {"satirlar": satirlar}
                return new_data, f"{log_msg}\n\nEski Format Dönüştürüldü!\n{raw_text}"
            
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                    if isinstance(data, dict) and "satirlar" in data:
                        return data, f"{log_msg}\n\nRegex Başarısı (Yeni Format).\n{raw_text}"
                except:
                    pass
            return None, f"{log_msg}\n\nJSON Bozuk:\n{raw_text}"

    except Exception as e:
        return None, f"HATA ({model_name}): {str(e)}\n\nLOG:\n{log_msg}"

# --- ANA UYGULAMA FONKSİYONU ---
def game_interface():
    # CSS fonksiyonunu game_interface içine taşıyoruz
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
    
    inject_stylish_css()
    
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_open" not in st.session_state: 
        st.session_state["sheet_open"] = False
    
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ")
        c1, c2 = st.columns(2)
        with c1: 
            match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: 
            match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        st.warning("⚠️ OYUNCULARI FOTOĞRAFTAKİ SIRAYLA (SOLDAN SAĞA) SEÇİN!")
        selected_players = st.multiselect("OYUNCU SIRASI:", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            uploaded_image = None
            if HAS_GENAI and API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR (AUTO-DETECT)")
                st.markdown('<div class="ai-info">🤖 <b>Akıllı Model Seçimi:</b> Sistem açık olan modeli kendi bulacak.</div>', unsafe_allow_html=True)
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
                    with st.spinner("🤖 Model aranıyor ve analiz yapılıyor..."):
                        img = Image.open(uploaded_image)
                        json_data, raw_text = extract_scores_from_image(img)
                        st.session_state["ai_json"] = json_data
                        st.session_state["ai_raw_text"] = raw_text
                        
                        if json_data:
                            st.success("Başarılı!")
                        else:
                            st.warning("Hata oluştu, Debug'a bakın.")

                st.session_state["sheet_open"] = True
                
                # --- YENİ VERİ DOLDURMA MANTIĞI ---
                data = []
                ai_data = st.session_state.get("ai_json", {}) or {}
                
                # AI'dan gelen satır verilerini kullan
                satirlar = []
                if "satirlar" in ai_data and isinstance(ai_data["satirlar"], list):
                    satirlar = ai_data["satirlar"]
                    # 20 satır olmalı (12 ceza + 8 koz)
                    while len(satirlar) < 20:
                        satirlar.append([0, 0, 0, 0])
                    satirlar = satirlar[:20]  # Fazla varsa kes
                
                # Ceza satırlarını doldur
                satir_index = 0
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: 
                        continue
                    
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan']
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        
                        # AI'dan gelen veriyi al
                        if satirlar and satir_index < len(satirlar):
                            vals = satirlar[satir_index]
                            satir_index += 1
                        else:
                            vals = [0, 0, 0, 0]
                        
                        vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                        while len(vals) < 4: 
                            vals.append(0)
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for idx, p in enumerate(selected_players): 
                            row[p] = vals[idx]
                        data.append(row)
                
                # Koz satırlarını doldur
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    
                    # AI'dan gelen veriyi al
                    if satirlar and satir_index < len(satirlar):
                        vals = satirlar[satir_index]
                        satir_index += 1
                    else:
                        vals = [0, 0, 0, 0]
                    
                    vals = [int(x) if str(x).isdigit() else 0 for x in vals]
                    while len(vals) < 4: 
                        vals.append(0)
                    
                    row = {"OYUN TÜRÜ": label, "HEDEF": 13, "TÜR": "KOZ"}
                    for idx, p in enumerate(selected_players): 
                        row[p] = vals[idx]
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

        edited_df = st.data_editor(st.session_state["game_df"], use_container_width=True, height=800, column_config={
            "HEDEF": None, 
            "TÜR": None, 
            **{p: st.column_config.NumberColumn(p, min_value=0, step=1, format="%d") for p in players}
        })

        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for idx, row in edited_df.iterrows():
            tgt = row["HEDEF"]
            tur = row["TÜR"]
            cur = sum([row[p] for p in players])
            
            if cur > 0:
                if cur != tgt: 
                    errors.append(f"⚠️ {idx}: Toplam {tgt} olmalı ({cur})")
                else:
                    r_data = [idx]
                    for p in players:
                        val = row[p] * (50 if tur == "KOZ" else -1)
                        r_data.append(val)
                        col_totals[p] += val
                    clean_rows.append(r_data)

        if errors:
            for e in errors: 
                st.markdown(f"<div class='error-box'>{e}</div>", unsafe_allow_html=True)
            
        c1, c2 = st.columns([2, 1])
        with c1:
            if st.button("💾 KAYDET", type="primary", use_container_width=True, disabled=bool(errors)):
                if clean_rows:
                    ft = ["TOPLAM"] + list(col_totals.values())
                    hd = ["OYUN TÜRÜ"] + [f"{p} (uid:{name_to_id.get(p,'?')})" for p in players]
                    if save_match_to_sheet(hd, clean_rows, ft): 
                        st.balloons()
                        st.session_state["sheet_open"] = False
                        if "game_df" in st.session_state:
                            del st.session_state["game_df"]
                        st.rerun()
        
        with c2:
            if st.button("İPTAL", use_container_width=True): 
                st.session_state["sheet_open"] = False
                st.rerun()
