# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- 1. SADE VE TEMİZ CSS (GÖZ YORMAZ, HATA YAPMAZ) ---
def inject_clean_css():
    st.markdown("""
    <style>
        /* Genel Sayfa Temizliği */
        .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        
        /* Tabloyu Excel Gibi Yap */
        div[data-testid="stDataFrame"] {
            width: 100%;
            border: 1px solid #ccc;
        }
        
        /* Başlıklar */
        h1, h2, h3 {
            color: #8b0000 !important;
            font-family: Arial, sans-serif;
        }
        
        /* Hata Mesajları */
        .error-box {
            background-color: #fdd;
            color: #900;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #900;
            margin-bottom: 5px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_clean_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    # Session State Başlatma
    if "sheet_open" not in st.session_state: st.session_state["sheet_open"] = False
    
    # --- AŞAMA 1: OYUNCU SEÇİMİ ---
    if not st.session_state["sheet_open"]:
        st.header("📋 Maç Kurulumu")
        c1, c2 = st.columns(2)
        with c1: match_name = st.text_input("Maç Adı", "King_Akşamı")
        with c2: match_date = st.date_input("Tarih", datetime.now())
        
        users = list(name_to_id.keys())
        selected_players = st.multiselect("Oyuncular (4 Kişi Seçin):", users, max_selections=4)
        
        if len(selected_players) == 4:
            if st.button("Tabloyu Oluştur", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected_players
                st.session_state["match_info"] = {"name": match_name, "date": match_date}
                st.session_state["sheet_open"] = True
                
                # --- TABLOYU HAZIRLA (PUAN GİRİŞİ İÇİN) ---
                data = []
                # 1. Cezalar
                for oyun, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun: continue
                    tekrar = kural['limit']
                    hedef_puan = kural['adet'] * kural['puan'] # Örn: Kız (4*100 = 400)
                    
                    for i in range(1, tekrar + 1):
                        label = oyun if tekrar == 1 else f"{oyun} {i}"
                        row = {"OYUN TÜRÜ": label, "HEDEF": hedef_puan}
                        for p in selected_players: row[p] = 0 # Başlangıç puanı 0
                        data.append(row)
                
                # 2. Kozlar
                for i in range(1, 9):
                    row = {"OYUN TÜRÜ": f"KOZ {i}", "HEDEF": 650} # 13 el * 50 puan
                    for p in selected_players: row[p] = 0
                    data.append(row)
                
                # DataFrame oluştur ve kaydet
                df = pd.DataFrame(data)
                df.set_index("OYUN TÜRÜ", inplace=True)
                st.session_state["game_df"] = df
                st.rerun()
        return

    # --- AŞAMA 2: PUAN GİRİŞ EKRANI (EXCEL TARZI) ---
    else:
        players = st.session_state["current_players"]
        st.subheader(f"{st.session_state['match_info']['name']} - Puan Tablosu")
        
        # Kullanıcıya Bilgi Ver
        st.info("ℹ️ Lütfen **PUAN** giriniz. (Örn: Rıfkı yiyen kişiye '1' değil '320' yazın).")
        
        # --- DATA EDITOR (GÜÇLÜ VE HATASIZ) ---
        # Kullanıcı burada değişiklik yapar
        edited_df = st.data_editor(
            st.session_state["game_df"],
            use_container_width=True,
            height=800,
            column_config={
                "HEDEF": st.column_config.NumberColumn(
                    "Olması Gereken",
                    help="Bu satırdaki puanların toplamı bu sayıya eşit olmalıdır.",
                    disabled=True # Değiştirilemez
                ),
                **{p: st.column_config.NumberColumn(
                    p,
                    min_value=0,
                    step=10, # 10'ar 10'ar artsın (King puanları genelde katlıdır)
                    required=True
                ) for p in players}
            }
        )

        # --- CANLI HATA KONTROLÜ (MÜFETTİŞ) ---
        errors = []
        clean_rows = []
        col_totals = {p: 0 for p in players}

        # Tabloyu satır satır tara
        for index, row in edited_df.iterrows():
            target = row["HEDEF"]
            
            # Oyuncuların girdiği puanları topla
            current_sum = sum([row[p] for p in players])
            
            # Satıra hiç veri girilmiş mi? (Hepsi 0 değilse işlem var demektir)
            if current_sum > 0:
                # KURAL KONTROLÜ
                if current_sum != target:
                    errors.append(f"⚠️ **{index}** hatası: Toplam **{target}** olmalı, şu an **{current_sum}**.")
                else:
                    # Satır doğruysa kayda hazırla
                    row_data = [index]
                    for p in players:
                        row_data.append(row[p])
                        col_totals[p] += row[p] # Toplam puana ekle
                    clean_rows.append(row_data)

        # --- ALT KISIM (BUTONLAR VE UYARILAR) ---
        st.divider()
        
        if errors:
            st.error("Lütfen aşağıdaki hataları düzeltmeden kaydetmeyin:")
            for err in errors:
                st.markdown(f"<div class='error-box'>{err}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            # Kaydet Butonu (Hata varsa pasif gibi davranır)
            if st.button("💾 Kaydet ve Bitir", type="primary", use_container_width=True, disabled=(len(errors) > 0)):
                if not clean_rows:
                    st.warning("Tablo boş, kaydedilecek veri yok.")
                else:
                    # Toplam Satırı
                    final_totals = ["TOPLAM"] + list(col_totals.values())
                    
                    # Başlık Satırı
                    header = ["OYUN TÜRÜ"]
                    for p in players:
                        uid = name_to_id.get(p, "?")
                        header.append(f"{p} (uid:{uid})")
                    
                    # Google Sheets'e Gönder
                    if save_match_to_sheet(header, clean_rows, final_totals):
                        st.success("✅ Maç başarıyla kaydedildi!")
                        # State'i temizle
                        st.session_state["sheet_open"] = False
                        del st.session_state["game_df"]
                        st.rerun()

        with c2:
            if st.button("❌ İptal Et", use_container_width=True):
                st.session_state["sheet_open"] = False
                if "game_df" in st.session_state: del st.session_state["game_df"]
                st.rerun()
