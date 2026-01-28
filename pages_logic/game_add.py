# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- GÖRÜNÜM CSS (AYNI KALDI) ---
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
            font-size: 14px;
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
    
    # --- AŞAMA 1: OYUNCU SEÇİMİ ---
    if not st.session_state["sheet_open"]:
        st.header("📋 KRALİYET DEFTERİ: YENİ MAÇ")
        
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        st.write("---")
        users = list(name_to_id.keys())
        selected_players = st.multiselect("MASADAKİ 4 KİŞİYİ SEÇİN:", users, max_selections=4)
        
        if len(selected_players) == 4:
            st.write("")
            if st.button("DEFTERİ AÇ", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["sheet_open"] = True
                
                # --- VERİ HAZIRLIĞI ---
                data = []
                
                # 1. CEZALAR (Hedef = Toplam Puan)
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    # Cezalarda toplam puan kontrolü yapacağız (Örn: Rıfkı = 320)
                    hedef = kural['adet'] * kural['puan'] 
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef, "TÜR": "CEZA"}
                        for p in selected_players: row[p] = 0
                        data.append(row)
                
                # 2. KOZLAR (Hedef = 13 El)
                for i in range(1, 9):
                    # Kozlarda toplam 13 el olduğu için hedef 13
                    row = {"OYUN TÜRÜ": f"KOZ {i}", "HEDEF": 13, "TÜR": "KOZ"}
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
        
        st.markdown(f"## {st.session_state['match_info']['name']}")
        
        # Kullanıcıya net talimatlar
        st.info("""
        📝 **NASIL DOLDURULUR?**
        - **CEZALAR:** Puanı direkt yazın (Örn: Rıfkı yiyene **320**, Kız yiyene **100**). **Eksi koymanıza gerek yok.**
        - **KOZLAR:** Sadece alınan **EL SAYISINI** (Adet) yazın (Örn: **5** el aldı). Sistem 50 ile çarpacak.
        """)
        
        # --- EDİTÖR ---
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None, # Gizli sütun
                "TÜR": None,   # Gizli sütun
                **{p: st.column_config.NumberColumn(
                    p,
                    min_value=0,
                    step=1, 
                    required=True,
                    format="%d"
                ) for p in players}
            }
        )

        # --- KONTROL MEKANİZMASI ---
        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for index, row in edited_df.iterrows():
            target = row["HEDEF"]
            tur = row["TÜR"]
            
            # Oyuncuların girdiklerini topla
            current_sum = sum([row[p] for p in players])
            
            # Eğer satıra bir şeyler girilmişse (Hepsi 0 değilse)
            if current_sum > 0:
                # KURAL KONTROLÜ
                if current_sum != target:
                    if tur == "KOZ":
                        errors.append(f"⚠️ **{index}** HATASI: Toplam el sayısı **13** olmalı, şu an **{current_sum}** el girildi.")
                    else:
                        errors.append(f"⚠️ **{index}** HATASI: Dağıtılan toplam puan **{target}** olmalı, şu an **{current_sum}** girildi.")
                else:
                    # VERİ DOĞRU, KAYDA HAZIRLA
                    row_data = [index]
                    
                    for p in players:
                        girilen_deger = row[p]
                        final_puan = 0
                        
                        # --- PUAN DÖNÜŞTÜRME BÜYÜSÜ ---
                        if tur == "KOZ":
                            # Koza el sayısı girildi, 50 ile çarpıp PUAN yap
                            final_puan = girilen_deger * 50
                        else:
                            # Cezaya puan girildi, -1 ile çarpıp NEGATİF yap
                            final_puan = girilen_deger * -1
                        
                        row_data.append(final_puan)
                        col_totals[p] += final_puan
                        
                    clean_rows.append(row_data)

        st.write("---")
        
        # Hataları Göster
        if errors:
            st.markdown("### 🚫 DİKKAT")
            for err in errors:
                st.markdown(f"<div class='error-box'>{err}</div>", unsafe_allow_html=True)
        
        # Butonlar
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Hata varsa kaydetme
            if st.button("💾 KAYDET VE BİTİR", type="primary", use_container_width=True, disabled=(len(errors) > 0)):
                if not clean_rows:
                    st.warning("Defter boş.")
                else:
                    final_totals = ["TOPLAM"] + list(col_totals.values())
                    
                    header = ["OYUN TÜRÜ"]
                    for p in players:
                        uid = name_to_id.get(p, "?")
                        header.append(f"{p} (uid:{uid})")
                    
                    # Google Sheets'e Kaydet
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
