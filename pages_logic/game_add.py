# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- GÜVENLİ IMPORT ---
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# --- API AYARLARI ---
API_KEY = None
if HAS_GENAI:
    try:
        API_KEY = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=API_KEY)
    except:
        pass

# --- YAPAY ZEKA FONKSİYONU (GELİŞTİRİLMİŞ) ---
def extract_scores_from_image(image, player_names):
    """
    Oyuncu isimlerini sırasıyla vererek sütun eşleştirmesi yapar.
    """
    if not HAS_GENAI or not API_KEY:
        return None

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # İsimleri numaralandırarak veriyoruz ki sütun sırası karışmasın
        players_str = ", ".join([f"Sütun {i+1}: {p}" for i, p in enumerate(player_names)])
        
        prompt = f"""
        Sen profesyonel bir King skor tablosu okuyucususun.
        Ekli fotoğrafta el yazısıyla yazılmış bir skor tablosu var.
        
        Tabloda 4 adet skor sütunu var. Soldan sağa doğru bu sütunlar şu oyunculara aittir:
        {players_str}
        
        Lütfen SADECE aşağıdaki JSON formatında veriyi döndür. Başka hiçbir açıklama yazma.
        
        Format:
        {{
          "Rıfkı": {{ "{player_names[0]}": 320, "{player_names[1]}": 0, ... }},
          "Kız": {{ "{player_names[0]}": 100, ... }},
          "Erkek": {{ ... }},
          "Kupa": {{ ... }},
          "Son İki": {{ ... }},
          "El Almaz": {{ ... }},
          "Koz 1": {{ "{player_names[0]}": 5, ... }},
          ...
          "Koz 8": {{ ... }}
        }}

        Kurallar:
        1. Fotoğraftaki isim ne olursa olsun, soldan 1. sütundaki sayıları "{player_names[0]}" anahtarına yaz. 2. sütunu "{player_names[1]}" anahtarına yaz. Eşleştirme KESİN bu sırayla olmalı.
        2. Cezalar (Rıfkı, Kız, Erkek, Kupa, Son İki, El Almaz) için tablodaki PUANI oku (Örn: 320, 50, 90). Pozitif tam sayı ver.
        3. Kozlar (Koz 1'den Koz 8'e kadar) için sadece EL SAYISINI (Adet) oku (Örn: 5, 3, 8).
        4. Okunamayan, boş veya çizgi çekilmiş yerleri 0 kabul et.
        5. "Rıfkı", "Kız", "Koz 1" gibi oyun isimlerini tam olarak benim verdiğim şekilde anahtar olarak kullan.
        """
        
        response = model.generate_content([prompt, image])
        # JSON Temizliği
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        return json.loads(text.strip())
        
    except Exception as e:
        st.error(f"AI Hatası: {str(e)}")
        return None

# --- CSS ---
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
        selected_players = st.multiselect("MASADAKİ 4 KİŞİ (Soldan Sağa Sırayla):", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            st.markdown("### 📸 FOTOĞRAFTAN DOLDUR")
            
            uploaded_image = None
            if HAS_GENAI and API_KEY:
                uploaded_image = st.file_uploader("Tablonun Fotoğrafını Yükle", type=['png', 'jpg', 'jpeg'])
            else:
                st.warning("⚠️ API Key eksik olduğu için fotoğraf okuma kapalı.")
            
            btn_text = "FOTOĞRAFI TARA VE AÇ" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_raw_data"] = None # Debug verisini sıfırla
                
                # --- AI İŞLEME ---
                ai_data = {}
                if uploaded_image:
                    with st.spinner("🤖 Fotoğraf taranıyor, sütunlar eşleştiriliyor..."):
                        img = Image.open(uploaded_image)
                        ai_result = extract_scores_from_image(img, selected_players)
                        
                        if ai_result:
                            ai_data = ai_result
                            st.session_state["ai_raw_data"] = ai_result # Debug için sakla
                            st.success("Fotoğraf başarıyla işlendi!")
                        else:
                            st.error("Fotoğraf okunamadı veya veri boş döndü.")

                st.session_state["sheet_open"] = True
                
                # --- TABLO OLUŞTURMA ---
                data = []
                
                # Veri Çekme Yardımcısı (Esnek Eşleşme)
                def get_val(game_keys_list, player):
                    # Oyun ismi "Rıfkı" olabilir ama tabloda "Rıfkı 1" yazıyor olabilir.
                    # AI'nin döndürdüğü anahtarlarda (Örn: Rıfkı) arama yapıyoruz.
                    for key in game_keys_list:
                        if key in ai_data:
                            val = ai_data[key].get(player, 0)
                            if val > 0: return int(val)
                    return 0

                # 1. CEZALAR
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef = kural['adet'] * kural['puan'] 
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        
                        # AI genelde "Rıfkı" diye tek bir anahtar döner, "Rıfkı 1" demez.
                        # Bu yüzden oyun adının kökünü (Rıfkı) arıyoruz.
                        search_keys = [label, oyun] 
                        
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for p in selected_players:
                            row[p] = get_val(search_keys, p)
                        data.append(row)
                
                # 2. KOZLAR
                for i in range(1, 9):
                    label = f"KOZ {i}"
                    row = {"OYUN TÜRÜ": label, "HEDEF": 13, "TÜR": "KOZ"}
                    for p in selected_players:
                        row[p] = get_val([label], p)
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
        
        # --- DEBUG ALANI (Sorunu çözmek için) ---
        if st.session_state.get("ai_raw_data"):
            with st.expander("🤖 Yapay Zeka Ham Verisini Gör (Debug)"):
                st.write("Eğer burası doluysa ama tablo boşsa, isim eşleşmesi sorunu vardır.")
                st.json(st.session_state["ai_raw_data"])
        
        st.info("💡 Lütfen kırmızı hataları kontrol edip düzeltin.")
        
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None,
                "TÜR": None,
                **{p: st.column_config.NumberColumn(p, min_value=0, step=1, required=True, format="%d") for p in players}
            }
        )

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
