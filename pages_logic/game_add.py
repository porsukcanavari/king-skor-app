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
# Kanka senin verdiğin anahtarı buraya gömdüm.
MANUEL_API_KEY = "AIzaSyDp66e5Kxm3g9scKZxWKUdcuv6yeQcMgk0"

API_KEY = None
if HAS_GENAI:
    try:
        # Önce secrets dosyasına bakar, yoksa senin verdiğin manuel anahtarı kullanır
        if "GOOGLE_API_KEY" in st.secrets:
            API_KEY = st.secrets["GOOGLE_API_KEY"]
        elif MANUEL_API_KEY:
            API_KEY = MANUEL_API_KEY
            
        if API_KEY:
            genai.configure(api_key=API_KEY)
    except Exception as e:
        print(f"API Yapılandırma Hatası: {e}")

# --- YAPAY ZEKA FONKSİYONU ---
def extract_scores_from_image(image, player_names):
    """
    Fotoğrafı Gemini'ye gönderir, sütun sırasına göre verileri çeker.
    """
    if not HAS_GENAI or not API_KEY:
        return None

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Sütun sırasını belirtiyoruz (Soldan sağa)
        players_str = ", ".join([f"Sütun {i+1}: {p}" for i, p in enumerate(player_names)])
        
        prompt = f"""
        Sen uzman bir King kart oyunu skor tablosu okuyucususun.
        Fotoğrafta 4 sütunlu bir tablo var.
        
        SÜTUN SAHİPLERİ (Soldan Sağa): {players_str}
        
        GÖREV:
        Tablodaki sayıları oku ve aşağıdaki JSON formatında döndür.
        
        FORMAT:
        {{
          "Rıfkı": {{ "{player_names[0]}": 320, "{player_names[1]}": 0, "{player_names[2]}": 0, "{player_names[3]}": 0 }},
          "Kız": {{ ... }},
          "Erkek": {{ ... }},
          "Kupa": {{ ... }},
          "Son İki": {{ ... }},
          "El Almaz": {{ ... }},
          "Koz 1": {{ ... }},
          ...
          "Koz 8": {{ ... }}
        }}

        KURALLAR:
        1. İSİM EŞLEŞTİRME: Fotoğraftaki isimleri görmezden gel. Soldan 1. sütundaki sayıları "{player_names[0]}" anahtarına yaz. 2. sütunu "{player_names[1]}" anahtarına yaz. Sıralama KESİNLİKLE budur.
        2. SAYILAR: Cezalar (Rıfkı, Kız vb.) için PUAN oku (Örn: 320, 50). Kozlar için EL SAYISI oku (Örn: 5, 3).
        3. BOŞLUKLAR: Okunamayan, boş veya çizgi (-) olan yerleri 0 kabul et.
        4. Sadece saf JSON döndür, markdown kullanma.
        """
        
        response = model.generate_content([prompt, image])
        text = response.text
        # Temizlik
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        st.error(f"Yapay Zeka Okuma Hatası: {str(e)}")
        return None

# --- GÖRÜNÜM (STİL) ---
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
            padding: 10px;
            border-left: 6px solid #c0392b;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 14px;
        }
        div[data-testid="stButton"] button {
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            border: 2px solid #000 !important;
            border-radius: 0px !important;
        }
        .ai-info {
            background-color: #e3f2fd;
            color: #0d47a1;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #90caf9;
            font-size: 13px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_stylish_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_open" not in st.session_state: st.session_state["sheet_open"] = False
    
    # --- AŞAMA 1: MAÇ KURULUMU ---
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ")
        
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        # Kullanıcıları seçtiriyoruz
        selected_players = st.multiselect("MASADAKİ 4 KİŞİ (Fotoğraftaki sırayla seçin!):", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("---")
            
            # FOTOĞRAF YÜKLEME KISMI
            uploaded_image = None
            if API_KEY:
                st.markdown("### 📸 FOTOĞRAFTAN DOLDUR")
                st.markdown("""
                <div class="ai-info">
                    🤖 <b>Yapay Zeka Hazır!</b> Kağıdın fotoğrafını yükleyin, tabloyu otomatik dolduralım.
                    Lütfen fotoğrafın net olduğundan emin olun.
                </div>
                """, unsafe_allow_html=True)
                uploaded_image = st.file_uploader("Tablo Fotoğrafı Yükle", type=['png', 'jpg', 'jpeg'])
            else:
                st.warning("⚠️ API Key sorunu var, sadece manuel giriş yapılabilir.")
            
            btn_text = "FOTOĞRAFI TARA VE TABLOYU AÇ" if uploaded_image else "BOŞ TABLO AÇ"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["ai_raw_data"] = None
                
                # AI İŞLEME MANTIĞI
                ai_data = {}
                if uploaded_image and API_KEY:
                    with st.spinner("🤖 Fotoğraf okunuyor, puanlar eşleştiriliyor..."):
                        img = Image.open(uploaded_image)
                        res = extract_scores_from_image(img, selected_players)
                        if res:
                            ai_data = res
                            st.session_state["ai_raw_data"] = res
                            st.success("Okuma Başarılı!")
                        else:
                            st.error("Fotoğraf okunamadı, boş tablo açılıyor.")

                st.session_state["sheet_open"] = True
                
                # --- TABLO VERİSİNİ OLUŞTURMA ---
                data = []
                
                # Veri bulma yardımcısı (Esnek arama)
                def get_val(search_keys, player):
                    for k in search_keys:
                        if k in ai_data and player in ai_data[k]:
                            try:
                                return int(ai_data[k][player])
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
                        # AI'da "Rıfkı" olarak ararız (1, 2 ayrımı olmayabilir)
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for p in selected_players:
                            row[p] = get_val([label, oyun], p)
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
        
        # Debug Alanı (İsteğe bağlı açılır)
        if st.session_state.get("ai_raw_data"):
            with st.expander("🤖 Yapay Zeka Ne Okudu? (Tıkla Gör)"):
                st.json(st.session_state["ai_raw_data"])
        
        st.info("💡 **KONTROL ET:** Kırmızı ile işaretli satırlarda hata vardır. Lütfen düzeltip kaydedin.")
        
        # TABLO (EDİTÖR)
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None, # Gizli
                "TÜR": None,   # Gizli
                **{p: st.column_config.NumberColumn(
                    p, min_value=0, step=1, required=True, format="%d"
                ) for p in players}
            }
        )

        # HATA KONTROLÜ
        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for index, row in edited_df.iterrows():
            target = row["HEDEF"]
            tur = row["TÜR"]
            current_sum = sum([row[p] for p in players])
            
            # Sadece dolu satırları kontrol et
            if current_sum > 0:
                if current_sum != target:
                    if tur == "KOZ":
                        errors.append(f"⚠️ **{index}**: Toplam **13** el olmalı (Şu an: {current_sum})")
                    else:
                        errors.append(f"⚠️ **{index}**: Puan **{target}** olmalı (Şu an: {current_sum})")
                else:
                    # Kayıt için hazırla
                    row_data = [index]
                    for p in players:
                        val = row[p]
                        # Koz ise 50 ile çarp, Ceza ise -1 ile
                        final_puan = val * 50 if tur == "KOZ" else val * -1
                        row_data.append(final_puan)
                        col_totals[p] += final_puan
                    clean_rows.append(row_data)

        st.write("---")
        
        # Hataları Bas
        if errors:
            for err in errors:
                st.markdown(f"<div class='error-box'>{err}</div>", unsafe_allow_html=True)
        
        # Butonlar
        c1, c2 = st.columns([2, 1])
        with c1:
            if st.button("💾 KAYDET VE BİTİR", type="primary", use_container_width=True, disabled=(len(errors) > 0)):
                if not clean_rows:
                    st.warning("Tablo boş, kaydedilecek veri yok.")
                else:
                    final_totals = ["TOPLAM"] + list(col_totals.values())
                    header = ["OYUN TÜRÜ"] + [f"{p} (uid:{name_to_id.get(p,'?')})" for p in players]
                    
                    if save_match_to_sheet(header, clean_rows, final_totals):
                        st.balloons()
                        st.success("✅ MAÇ KAYDEDİLDİ!")
                        st.session_state["sheet_open"] = False
                        del st.session_state["game_df"]
                        st.rerun()
        
        with c2:
            if st.button("❌ İPTAL", use_container_width=True):
                st.session_state["sheet_open"] = False
                if "game_df" in st.session_state: del st.session_state["game_df"]
                st.rerun()
