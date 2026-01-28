# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- 1. SADE VE TEMİZ CSS ---
def inject_clean_css():
    st.markdown("""
    <style>
        .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        div[data-testid="stDataFrame"] {
            width: 100%;
            border: 1px solid #ccc;
        }
        /* Hata Kutusu */
        .error-box {
            background-color: #ffe6e6;
            color: #cc0000;
            padding: 10px;
            border-left: 5px solid #cc0000;
            margin-bottom: 5px;
            font-family: monospace;
            font-size: 14px;
        }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_clean_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "sheet_open" not in st.session_state: st.session_state["sheet_open"] = False
    
    # --- AŞAMA 1: OYUNCU SEÇİMİ ---
    if not st.session_state["sheet_open"]:
        st.header("📋 Yeni Maç")
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        selected_players = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected_players) == 4:
            if st.button("Tabloyu Aç", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["sheet_open"] = True
                
                # --- TABLO VERİSİNİ HAZIRLA ---
                data = []
                # Cezalar
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef_puan = kural['adet'] * kural['puan'] 
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        # HEDEF sütununu ekliyoruz ama ekranda gizleyeceğiz
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef_puan}
                        for p in selected_players: row[p] = 0
                        data.append(row)
                
                # Kozlar
                for i in range(1, 9):
                    row = {"OYUN TÜRÜ": f"KOZ {i}", "HEDEF": 650} # 13 el * 50
                    for p in selected_players: row[p] = 0
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.set_index("OYUN TÜRÜ", inplace=True)
                st.session_state["game_df"] = df
                st.rerun()
        return

    # --- AŞAMA 2: PUAN GİRİŞİ ---
    else:
        players = st.session_state["current_players"]
        st.subheader(f"{st.session_state['match_info']['name']}")
        
        st.info("ℹ️ Direkt PUAN giriniz. (Örn: Rıfkı yiyene 320 yazın).")
        
        # --- TABLO ---
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": None, # <--- İŞTE BURASI: Sütunu Gizledik!
                **{p: st.column_config.NumberColumn(
                    p,
                    min_value=0,
                    step=10, 
                    required=True
                ) for p in players}
            }
        )

        # --- HATA KONTROLÜ (Gizli HEDEF sütununa göre) ---
        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        for index, row in edited_df.iterrows():
            target = row["HEDEF"] # Gizli sütundan hedefi okuyoruz
            current_sum = sum([row[p] for p in players])
            
            if current_sum > 0:
                if current_sum != target:
                    errors.append(f"⚠️ **{index}** hatası: Toplam **{target}** olmalı, şu an **{current_sum}**.")
                else:
                    row_data = [index]
                    for p in players:
                        row_data.append(row[p])
                        col_totals[p] += row[p]
                    clean_rows.append(row_data)

        # --- UYARILAR VE KAYDET ---
        st.divider()
        
        if errors:
            for err in errors:
                st.markdown(f"<div class='error-box'>{err}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            # Hata varsa buton pasif
            if st.button("💾 Kaydet", type="primary", use_container_width=True, disabled=(len(errors) > 0)):
                if not clean_rows:
                    st.warning("Tablo boş.")
                else:
                    final_totals = ["TOPLAM"] + list(col_totals.values())
                    
                    header = ["OYUN TÜRÜ"]
                    for p in players:
                        uid = name_to_id.get(p, "?")
                        header.append(f"{p} (uid:{uid})")
                    
                    if save_match_to_sheet(header, clean_rows, final_totals):
                        st.success("✅ Kaydedildi!")
                        st.session_state["sheet_open"] = False
                        del st.session_state["game_df"]
                        st.rerun()

        with c2:
            if st.button("❌ İptal", use_container_width=True):
                st.session_state["sheet_open"] = False
                if "game_df" in st.session_state: del st.session_state["game_df"]
                st.rerun()
