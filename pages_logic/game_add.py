# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- SADECE GÖRÜNÜMÜ GÜZELLEŞTİREN CSS ---
def inject_stylish_css():
    st.markdown("""
    <style>
        /* 1. GENEL YAZI TİPİ (DAKTİLO MODU) */
        .stApp {
            font-family: 'Courier New', Courier, monospace !important;
            background-color: #fafafa !important; /* Çok hafif kırık beyaz, göz yormaz */
        }

        /* 2. BAŞLIKLAR (King Ruhu) */
        h1, h2, h3 {
            color: #8b0000 !important; /* Koyu Bordo */
            font-weight: 900 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #8b0000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        /* 3. TABLO (DATA EDITOR) MAKYAJI */
        div[data-testid="stDataFrame"] {
            border: 2px solid #2c3e50 !important; /* Koyu Lacivert Çerçeve */
            box-shadow: 5px 5px 15px rgba(0,0,0,0.1) !important; /* Hafif Gölge */
            border-radius: 5px;
            background-color: white;
        }

        /* 4. HATA KUTULARI (Daha Şık) */
        .error-box {
            background-color: #fff5f5;
            color: #c0392b;
            padding: 15px;
            border-left: 6px solid #c0392b; /* Sol tarafa kalın kırmızı çizgi */
            margin-bottom: 10px;
            font-weight: bold;
            font-size: 14px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }

        /* 5. BUTONLAR */
        div[data-testid="stButton"] button {
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            border-radius: 0px !important; /* Köşeli butonlar */
            border: 2px solid #000 !important;
        }
        
        /* Bilgi Kutusu */
        .stAlert {
            font-family: 'Courier New', Courier, monospace !important;
        }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_stylish_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_open" not in st.session_state: st.session_state["sheet_open"] = False
    
    # --- AŞAMA 1: OYUNCU SEÇİMİ ---
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ: YENİ MAÇ")
        
        # Kutuları yan yana alalım
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        st.write("---") # Ayırıcı çizgi
        
        users = list(name_to_id.keys())
        selected_players = st.multiselect("MASADAKİ 4 KİŞİYİ SEÇİN:", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("") # Boşluk
            if st.button("DEFTERİ AÇ", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["sheet_open"] = True
                
                # --- VERİ HAZIRLIĞI (Mantık aynı) ---
                data = []
                # Cezalar
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef_puan = kural['adet'] * kural['puan'] 
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef_puan}
                        for p in selected_players: row[p] = 0
                        data.append(row)
                
                # Kozlar
                for i in range(1, 9):
                    row = {"OYUN TÜRÜ": f"KOZ {i}", "HEDEF": 650}
                    for p in selected_players: row[p] = 0
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.set_index("OYUN TÜRÜ", inplace=True)
                st.session_state["game_df"] = df
                st.rerun()
        return

    # --- AŞAMA 2: TABLO EKRANI ---
    else:
        players = st.session_state["current_players"]
        
        # Başlık ve Tarih
        st.markdown(f"## {st.session_state['match_info']['name']}")
        st.caption(f"📅 Tarih: {st.session_state['match_info']['date'].strftime('%d.%m.%Y')}")
        
        st.info("💡 DİKKAT: Direkt **PUAN** giriniz. (Örn: Rıfkı yiyene 320, El almazda el başına 50).")
        
        # --- EDİTÖR ---
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None, # Gizli sütun
                **{p: st.column_config.NumberColumn(
                    p,
                    min_value=0,
                    step=10, 
                    required=True,
                    format="%d" # Virgüllü göstermesin
                ) for p in players}
            }
        )

        # --- KONTROL MEKANİZMASI ---
        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for index, row in edited_df.iterrows():
            target = row["HEDEF"]
            current_sum = sum([row[p] for p in players])
            
            if current_sum > 0:
                if current_sum != target:
                    errors.append(f"⚠️ **{index}** HATASI: Masada **{target}** puan dönmeli, şu an **{current_sum}** yazıldı.")
                else:
                    row_data = [index]
                    for p in players:
                        row_data.append(row[p])
                        col_totals[p] += row[p]
                    clean_rows.append(row_data)

        st.write("---") # Alt çizgi
        
        # Hataları Göster
        if errors:
            st.markdown("### 🚫 HATA VAR")
            for err in errors:
                st.markdown(f"<div class='error-box'>{err}</div>", unsafe_allow_html=True)
        
        # Butonlar
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Hata varsa buton kilitli
            if st.button("💾 KAYDET VE BİTİR", type="primary", use_container_width=True, disabled=(len(errors) > 0)):
                if not clean_rows:
                    st.warning("Defter boş, henüz bir şey yazmadınız.")
                else:
                    final_totals = ["TOPLAM"] + list(col_totals.values())
                    
                    header = ["OYUN TÜRÜ"]
                    for p in players:
                        uid = name_to_id.get(p, "?")
                        header.append(f"{p} (uid:{uid})")
                    
                    if save_match_to_sheet(header, clean_rows, final_totals):
                        st.balloons()
                        st.success("✅ MAÇ BAŞARIYLA KAYDEDİLDİ!")
                        st.session_state["sheet_open"] = False
                        del st.session_state["game_df"]
                        st.rerun()

        with c2:
            if st.button("❌ İPTAL", use_container_width=True):
                st.session_state["sheet_open"] = False
                if "game_df" in st.session_state: del st.session_state["game_df"]
                st.rerun()
