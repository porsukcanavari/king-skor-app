# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL KAĞIT TASARIMI CSS (GÜÇLENDİRİLMİŞ) ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. Ana Parşömen Kutusu (Başlık ve Bilgi kısmı için) */
        .paper-header-box {
            background-color: #fdfbf7;
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            color: #2c1e12;
            padding: 20px;
            border: 1px solid #d3c6a0;
            border-radius: 5px 5px 0 0; /* Alt köşe düz, tablo ile birleşsin */
            font-family: 'Courier New', Courier, monospace;
            text-align: center;
            border-bottom: 2px dashed #2c1e12;
        }

        /* 2. TABLO İÇİN ZORLA KAĞIT GÖRÜNÜMÜ */
        /* Streamlit'in kendi tablosunu hedef alıyoruz */
        [data-testid="stDataEditor"] {
            background-color: #fdfbf7 !important; /* Arka plan krem */
            border: 1px solid #d3c6a0 !important;
            border-top: none !important; /* Başlıkla birleşsin */
            border-radius: 0 0 5px 5px;
        }

        /* Tablo Başlıkları (Header) */
        [data-testid="stDataEditor"] div[role="columnheader"] {
            background-color: #e6dec3 !important; /* Biraz daha koyu krem */
            color: #4a3b2a !important; /* Koyu kahve yazı */
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            border-bottom: 2px solid #2c1e12 !important;
        }

        /* Tablo Hücreleri (Cells) */
        [data-testid="stDataEditor"] div[role="gridcell"] {
            background-color: #fdfbf7 !important;
            color: #2c1e12 !important; /* Siyah/Kahve yazı */
            font-family: 'Courier New', Courier, monospace;
            border-bottom: 1px solid #e0dacc !important;
        }

        /* Satır Numaraları (Index) - Gizli olsa bile ayarını yapalım */
        [data-testid="stDataEditor"] div[role="rowheader"] {
            background-color: #fdfbf7 !important;
            color: #8b7d6b !important;
        }
        
        /* Tablo içindeki input alanları (Tıklayınca açılan yer) */
        [data-testid="stDataEditor"] input {
            color: #000000 !important;
            background-color: #ffffff !important;
            font-family: 'Courier New', Courier, monospace;
        }

        /* Başlık Stili */
        .paper-title {
            font-size: 2em;
            color: #8b0000 !important; /* Kan kırmızısı başlık */
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 5px;
            font-weight: bold;
            text-shadow: 1px 1px 0px rgba(0,0,0,0.1);
        }
        
        .paper-info {
            font-size: 0.9em;
            font-style: italic;
            opacity: 0.8;
        }
    </style>
    """, unsafe_allow_html=True)

def create_paper_sheet(players):
    """
    Sadece Cezalar ve Kozlar.
    """
    data = []
    
    # 1. Ceza Oyunları
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue # Koz'u ayır
            
        limit = kural['limit']
        for _ in range(limit):
            row = {"OYUN": oyun_adi}
            for p in players:
                row[p] = 0
            data.append(row)
            
    # 2. KOZ Oyunları (8 Adet)
    for _ in range(8):
        row = {"OYUN": "KOZ"}
        for p in players:
            row[p] = 0
        data.append(row)
        
    return pd.DataFrame(data)

def game_interface():
    # CSS'i enjekte et
    inject_paper_css()
    
    id_to_name, name_to_id, _ = get_users_map()
    
    # --- SESSION STATE ---
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "sheet_df" not in st.session_state: st.session_state["sheet_df"] = pd.DataFrame()
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []

    # --- 1. KURULUM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.markdown("<h2>📒 Defter Açılışı</h2>", unsafe_allow_html=True)
        st.info("Defteri hazırlamak için oyuncuları seçin.")
        
        c1, c2 = st.columns(2)
        with c1:
            m_name = st.text_input("🏷️ Maç Başlığı:", "King_Akşamı")
            users = list(name_to_id.keys())
        with c2:
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
            
        selected = st.multiselect("Masadaki Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("🖋️ Defteri Önüme Getir", type="primary", use_container_width=True):
                st.session_state["sheet_df"] = create_paper_sheet(selected)
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.rerun()
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    df = st.session_state["sheet_df"]
    
    # --- PARŞÖMEN BAŞLIK ALANI ---
    st.markdown(f"""
    <div class="paper-header-box">
        <div class="paper-title">{st.session_state['current_match_name']}</div>
        <div class="paper-info">📅 {st.session_state['match_date']} | 👥 4 Kişi</div>
        <div style="margin-top:10px; font-size:0.8em; border-top:1px dashed #2c1e12; padding-top:5px;">
            Cezaları ve Koz ellerini giriniz. Sistem otomatik hesaplar.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- TABLO (CSS İLE RENGİ DEĞİŞTİRİLDİ) ---
    column_config = {
        "OYUN": st.column_config.TextColumn("Oyun Türü", disabled=True, width="medium"),
    }
    for p in players:
        column_config[p] = st.column_config.NumberColumn(p, min_value=0, step=1, required=True)

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=800,
        hide_index=True,
        column_config=column_config
    )
    
    st.session_state["sheet_df"] = edited_df
    
    st.write("") # Boşluk

    # --- DOĞRULAMA VE KAYIT ---
    col_save, col_cancel = st.columns([2, 1])
    
    errors = []
    valid_data_rows = []
    
    koz_count = 0 
    ceza_counts = {k: 0 for k in OYUN_KURALLARI}

    for i, row in edited_df.iterrows():
        game_name = row["OYUN"]
        row_sum = sum([row[p] for p in players])
        
        # Boş satır kontrolü
        if row_sum == 0:
            pass 
            
        # 1. KOZ KONTROLÜ
        if game_name == "KOZ":
            koz_count += 1
            if row_sum != 13 and row_sum != 0:
                errors.append(f"❌ **Satır {i+1} (KOZ)**: Toplam el sayısı 13 olmalı (Şu an: {row_sum}).")
            elif row_sum == 13:
                db_name = f"Koz (Tümü) {koz_count}"
                r_data = [db_name]
                for p in players:
                    r_data.append(row[p] * 50) 
                valid_data_rows.append(r_data)
        
        # 2. CEZA KONTROLÜ
        elif game_name in OYUN_KURALLARI:
            ceza_counts[game_name] += 1
            required = OYUN_KURALLARI[game_name]['adet']
            
            if row_sum != required and row_sum != 0:
                errors.append(f"❌ **Satır {i+1} ({game_name})**: Toplam {required} kart olmalı (Şu an: {row_sum}).")
            elif row_sum == required:
                db_name = f"{game_name} {ceza_counts[game_name]}"
                puan_carpani = OYUN_KURALLARI[game_name]['puan']
                r_data = [db_name]
                for p in players:
                    r_data.append(row[p] * puan_carpani)
                valid_data_rows.append(r_data)

    if not errors and valid_data_rows:
        with col_save:
            if st.button("💾 KAĞIDI İMZALA VE KAYDET", type="primary", use_container_width=True):
                # Toplam
                final_total = ["TOPLAM"]
                for p_idx, p in enumerate(players):
                    p_score = 0
                    for v_row in valid_data_rows:
                        p_score += v_row[p_idx + 1]
                    final_total.append(p_score)
                
                header = ["OYUN TÜRÜ"]
                for p in players:
                    uid = name_to_id.get(p, "?")
                    header.append(f"{p} (uid:{uid})")

                if save_match_to_sheet(header, valid_data_rows, final_total):
                    st.balloons()
                    st.success("Maç deftere işlendi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["sheet_df"] = pd.DataFrame()
                    st.rerun()
    elif not valid_data_rows:
        with col_save:
            st.info("Tabloyu doldurunuz.")
    else:
        with col_save:
            st.warning("⚠️ Hatalar var.")
        with st.expander("Hata Müfettişi", expanded=True):
            for e in errors:
                st.write(e)

    with col_cancel:
        if st.button("Kağıdı Yırt At (İptal)", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.rerun()
