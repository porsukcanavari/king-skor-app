# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import json
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- API AYARLARI (BURAYA DİKKAT) ---
# Kendi API Key'ini buraya yazman lazım ya da st.secrets'a eklemelisin.
# Şimdilik boş bırakıyorum, çalışmazsa manuel moda düşer.
try:
    # Önce Streamlit secrets'tan okumayı dener
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Yoksa buraya manuel yazabilirsin: "AIzaSy..."
    API_KEY = None 

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- YAPAY ZEKA FONKSİYONU ---
def extract_scores_from_image(image, player_names):
    """
    Yüklenen fotoğrafı Gemini'ye gönderir ve JSON formatında skorları ister.
    """
    if not API_KEY:
        st.error("⚠️ API Key bulunamadı! Fotoğraf okuma pas geçiliyor.")
        return None

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Sen uzman bir 'King' kağıt oyunu skor tablosu okuyucususun.
    Bu fotoğraftaki el yazısı skor tablosunu okumanı istiyorum.
    
    Oyuncular (Sütunlar): {', '.join(player_names)}
    
    Lütfen şu formatta SADECE JSON verisi döndür (Markdown kullanma):
    {{
        "Rıfkı": {{ "{player_names[0]}": 320, "{player_names[1]}": 0, ... }},
        "Kız": {{ ... }},
        "Erkek": {{ ... }},
        "Kupa": {{ ... }},
        "Son İki": {{ ... }},
        "El Almaz": {{ ... }},
        "Koz 1": {{ "{player_names[0]}": 5, ... }},
        ...
        "Koz 8": {{ ... }}
    }}
    
    Kurallar:
    1. Cezalar için (Rıfkı, Kız vb.) tabloda yazan PUANI oku (Örn: 320, 100, 50). Pozitif sayı olarak döndür.
    2. Kozlar için sadece EL SAYISINI (Adet) oku (Örn: 5, 3, 8).
    3. Eğer bir hücre boşsa veya okunmuyorsa 0 kabul et.
    4. Satır isimlerini tam olarak verdiğim anahtarlar (Rıfkı, Kız, Koz 1 vb.) gibi kullan.
    """
    
    try:
        response = model.generate_content([prompt, image])
        # JSON temizliği (Bazen ```json diye başlar)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data
    except Exception as e:
        st.error(f"Fotoğraf okunurken hata oluştu: {e}")
        return None

# --- GÖRÜNÜM CSS ---
def inject_stylish_css():
    st.markdown("""
    <style>
        .stApp {
            font-family: 'Courier New', Courier, monospace !important;
            background-color: #fafafa !important;
        }
        h1, h2, h3 {
            color: #8b0000 !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            border-bottom: 2px solid #8b0000;
            padding-bottom: 10px;
        }
        div[data-testid="stDataFrame"] {
            border: 2px solid #2c3e50 !important;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.1) !important;
            border-radius: 5px;
            background-color: white;
        }
        .error-box {
            background-color: #fff5f5;
            color: #c0392b;
            padding: 15px;
            border-left: 6px solid #c0392b;
            margin-bottom: 10px;
            font-weight: bold;
        }
        div[data-testid="stButton"] button {
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            border: 2px solid #000 !important;
            border-radius: 0px !important;
        }
        .beta-warning {
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ffeeba;
            font-size: 13px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_stylish_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_open" not in st.session_state: st.session_state["sheet_open"] = False
    
    # --- AŞAMA 1: KURULUM VE FOTOĞRAF ---
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ: YENİ MAÇ")
        
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        st.write("---")
        users = list(name_to_id.keys())
        selected_players = st.multiselect("MASADAKİ 4 KİŞİYİ SEÇİN:", users, max_selections=4)
        
        # FOTOĞRAF YÜKLEME ALANI
        uploaded_image = None
        if len(selected_players) == 4:
            st.write("---")
            st.markdown("### 📸 FOTOĞRAFTAN DOLDUR (OPSİYONEL)")
            
            st.markdown("""
            <div class="beta-warning">
                ⚠️ <b>BETA ÖZELLİK:</b> Kağıdın fotoğrafını yükleyin, yapay zeka okusun. 
                %100 doğruluk garanti edilmez. Işık yansıması veya kötü el yazısı hatalara yol açabilir.
                Tablo açılınca lütfen kontrol edin.
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_image = st.file_uploader("Kağıdın Fotoğrafını Yükle", type=['png', 'jpg', 'jpeg'])
            
            btn_label = "FOTOĞRAFI TARA VE TABLOYU AÇ" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_label, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                
                # --- AI VERİSİNİ HAZIRLA ---
                ai_data = None
                if uploaded_image:
                    with st.spinner("🤖 Yapay zeka kağıdı okuyor... Lütfen bekleyin..."):
                        img = Image.open(uploaded_image)
                        ai_data = extract_scores_from_image(img, selected_players)
                        if ai_data:
                            st.success("Fotoğraf okundu! Tablo dolduruluyor...")
                        else:
                            st.warning("Fotoğraf okunamadı, boş tablo açılıyor.")

                st.session_state["sheet_open"] = True
                
                # --- TABLOYU OLUŞTUR ---
                data = []
                
                # Helper: AI verisinden güvenli okuma
                def get_val(game_key, player_key):
                    if ai_data and game_key in ai_data:
                        # Oyuncu ismi tam eşleşmezse diye fuzzy match veya direkt kontrol
                        # Basitçe:
                        return ai_data[game_key].get(player_key, 0)
                    return 0

                # 1. CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan'] 
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}" # Tablodaki İsim
                        # AI'daki anahtarı tahmin et (Genelde 'Rıfkı' döner, 'Rıfkı 1' dönmeyebilir)
                        # Basitlik için oyun adını kullanıyoruz.
                        ai_key = label 
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for p in selected_players:
                            # Fotoğraftan gelen veri varsa onu koy, yoksa 0
                            row[p] = int(get_val(ai_key, p))
                        data.append(row)
                
                # 2. KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    row = {"OYUN TÜRÜ": label, "HEDEF": 13, "TÜR": "KOZ"}
                    for p in selected_players:
                        row[p] = int(get_val(label, p))
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.set_index("OYUN TÜRÜ", inplace=True)
                st.session_state["game_df"] = df
                st.rerun()
        return

    # --- AŞAMA 2: TABLO EKRANI (AYNI) ---
    else:
        players = st.session_state["current_players"]
        st.markdown(f"## {st.session_state['match_info']['name']}")
        
        st.info("💡 **KONTROL ET:** Yapay zeka verileri yanlış okumuş olabilir. Lütfen kırmızı hataları düzeltin.")
        
        # --- EDİTÖR ---
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None,
                "TÜR": None,
                **{p: st.column_config.NumberColumn(
                    p,
                    min_value=0,
                    step=1, 
                    required=True,
                    format="%d"
                ) for p in players}
            }
        )

        # --- KONTROL ---
        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for index, row in edited_df.iterrows():
            target = row["HEDEF"]
            tur = row["TÜR"]
            current_sum = sum([row[p] for p in players])
            
            if current_sum > 0:
                if current_sum != target:
                    if tur == "KOZ":
                        errors.append(f"⚠️ **{index}**: Toplam **13** el olmalı, şu an **{current_sum}**.")
                    else:
                        errors.append(f"⚠️ **{index}**: Puan **{target}** olmalı, şu an **{current_sum}**.")
                else:
                    row_data = [index]
                    for p in players:
                        val = row[p]
                        final_puan = val * 50 if tur == "KOZ" else val * -1
                        row_data.append(final_puan)
                        col_totals[p] += final_puan
                    clean_rows.append(row_data)

        st.write("---")
        
        if errors:
            for err in errors:
                st.markdown(f"<div class='error-box'>{err}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            if st.button("💾 KAYDET VE BİTİR", type="primary", use_container_width=True, disabled=(len(errors) > 0)):
                if not clean_rows:
                    st.warning("Tablo boş.")
                else:
                    final_totals = ["TOPLAM"] + list(col_totals.values())
                    header = ["OYUN TÜRÜ"] + [f"{p} (uid:{name_to_id.get(p,'?')})" for p in players]
                    
                    if save_match_to_sheet(header, clean_rows, final_totals):
                        st.balloons()
                        st.success("✅ KAYDEDİLDİ!")
                        st.session_state["sheet_open"] = False
                        del st.session_state["game_df"]
                        st.rerun()

        with c2:
            if st.button("❌ İPTAL", use_container_width=True):
                st.session_state["sheet_open"] = False
                if "game_df" in st.session_state: del st.session_state["game_df"]
                st.rerun()
