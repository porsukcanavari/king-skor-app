# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. PARŞÖMEN ARKAPLANI (Ana Taşıyıcı) */
        .stDataFrame {
            background-color: #fdfbf7 !important;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png") !important;
            border: 2px solid #5c4033 !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6) !important;
            border-radius: 4px !important;
            padding: 20px !important;
        }

        /* 2. TABLO HÜCRELERİ VE BAŞLIKLAR */
        /* Tüm tabloyu şeffaflaştırıp kağıt dokusunu gösterelim */
        div[data-testid="stDataFrameResizable"] {
            background-color: transparent !important;
        }
        
        /* Başlık Satırı */
        div[data-testid="stDataFrameResizable"] div[role="columnheader"] {
            background-color: rgba(62, 39, 35, 0.1) !important;
            color: #2c1e12 !important;
            font-family: 'Courier New', monospace !important;
            font-weight: 900 !important;
            font-size: 16px !important;
            border-bottom: 2px solid #5c4033 !important;
        }

        /* Hücreler (Satırlar) */
        div[data-testid="stDataFrameResizable"] div[role="gridcell"] {
            background-color: transparent !important; /* Şeffaf yap */
            color: #2c1e12 !important; /* Yazı rengi */
            font-family: 'Courier New', monospace !important;
            font-weight: bold !important;
            font-size: 15px !important;
            border-bottom: 1px solid #8b7d6b !important; /* Satır çizgisi */
        }

        /* Sol Baştaki İndeks Sütunu (Oyun Adları) */
        div[data-testid="stDataFrameResizable"] div[role="rowheader"] {
            background-color: rgba(0,0,0,0.02) !important;
            color: #2c1e12 !important;
            font-family: 'Courier New', monospace !important;
            font-weight: bold !important;
            font-size: 14px !important;
            text-align: left !important;
        }

        /* Hücreye Tıklayınca (Edit Modu) */
        div[data-testid="stDataFrameResizable"] input {
            color: #2c1e12 !important;
            background-color: #fff8dc !important; /* Yazarken hafif krem olsun */
            font-family: 'Courier New', monospace !important;
        }
        
        /* Başlık */
        .kagit-baslik {
            text-align: center; color: #8b0000; margin-top: 0; 
            border-bottom: 2px solid #8b0000; padding-bottom: 15px; font-weight: 900;
            font-family: 'Courier New', monospace; margin-bottom: 20px;
        }

    </style>
    """, unsafe_allow_html=True)

def game_interface():
    inject_custom_css()
    id_to_name, name_to_id, _ = get_users_map()
    
    if "show_paper" not in st.session_state: st.session_state["show_paper"] = False
    
    # --- 1. SEÇİM EKRANI ---
    if not st.session_state["show_paper"]:
        st.info("Oyuncuları seçin.")
        users = list(name_to_id.keys())
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("📜 Parşömeni Getir", type="primary", use_container_width=True):
                st.session_state["current_players"] = selected
                st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
                st.session_state["show_paper"] = True
                
                # --- TABLOYU İLK KEZ OLUŞTURUYORUZ ---
                rows = []
                # Cezalar
                for oyun_adi, kural in OYUN_KURALLARI.items():
                    if "Koz" in oyun_adi: continue
                    limit = kural['limit']
                    for i in range(1, limit + 1):
                        label = oyun_adi if limit == 1 else f"{oyun_adi} {i}"
                        # [Oyun Adı, Puan, 0, 0, 0, 0]
                        rows.append({"OYUN": label, "TÜR": "Ceza", "Puan": kural['puan'], **{p: 0 for p in selected}})
                
                # Kozlar
                for i in range(1, 9):
                    rows.append({"OYUN": f"KOZ {i}", "TÜR": "Koz", "Puan": 50, **{p: 0 for p in selected}})

                # DataFrame oluştur
                df = pd.DataFrame(rows)
                # OYUN sütununu index yap (Solda sabit kalsın diye)
                df.set_index("OYUN", inplace=True)
                st.session_state["editor_df"] = df
                st.rerun()
        return

    # --- 2. VERİ GİRİŞLİ PARŞÖMEN ---
    else:
        players = st.session_state["current_players"]
        
        # Parşömen Başlığı (HTML)
        st.markdown('<h1 class="kagit-baslik">KRALİYET DEFTERİ</h1>', unsafe_allow_html=True)
        
        # --- SİHİRLİ TABLO (DATA EDITOR) ---
        # Burada kullanıcı verileri girecek
        edited_df = st.data_editor(
            st.session_state["editor_df"],
            use_container_width=True,
            height=900, # Kağıt boyu kadar uzunluk
            column_config={
                "TÜR": None, # Tür sütununu gizle
                "Puan": None, # Puan sütununu gizle (arka planda kalsın)
                **{p: st.column_config.NumberColumn(
                    p,
                    min_value=0,
                    max_value=13,
                    step=1,
                    format="%d" 
                ) for p in players}
            },
            disabled=["OYUN"] # Oyun isimleri değiştirilemesin
        )

        st.write("")
        c1, c2 = st.columns([2, 1])

        with c1:
            if st.button("💾 DEFTERİ İMZALA (KAYDET)", type="primary", use_container_width=True):
                # --- KAYIT MANTIĞI ---
                # edited_df artık kullanıcının girdiği son verileri tutuyor!
                
                valid_data_rows = []
                total_row = ["TOPLAM", 0, 0, 0, 0] # Toplam satırı taslağı

                # DataFrame'i satır satır oku
                col_totals = {p: 0 for p in players}
                
                for index, row in edited_df.iterrows():
                    # Puan hesapla (Girilen Sayı * Oyunun Puan Değeri)
                    puan_degeri = row["Puan"]
                    row_vals = []
                    
                    row_sum = 0
                    for i, p in enumerate(players):
                        val = row[p] # Kullanıcının girdiği sayı
                        row_sum += val
                        hesaplanmis_puan = val * puan_degeri
                        
                        row_vals.append(hesaplanmis_puan)
                        col_totals[p] += hesaplanmis_puan # Toplama ekle

                    # Sadece veri girilmiş satırları al (hepsi 0 değilse)
                    if row_sum > 0:
                        # [Oyun Adı, Puan1, Puan2, Puan3, Puan4]
                        valid_data_rows.append([index] + row_vals)

                # Toplamları listeye çevir
                final_totals = ["TOPLAM"] + list(col_totals.values())

                # Başlık
                header = ["OYUN TÜRÜ"]
                for p in players:
                     uid = name_to_id.get(p, "?")
                     header.append(f"{p} (uid:{uid})")

                # Google Sheets'e Kaydet
                if not valid_data_rows:
                    st.warning("Defter boş, hiç sayı girmediniz.")
                else:
                    if save_match_to_sheet(header, valid_data_rows, final_totals):
                        st.balloons()
                        st.success("Tebrikler! Maç kaydedildi.")
                        st.session_state["show_paper"] = False
                        st.rerun()

        with c2:
            if st.button("İptal", use_container_width=True):
                st.session_state["show_paper"] = False
                st.rerun()
