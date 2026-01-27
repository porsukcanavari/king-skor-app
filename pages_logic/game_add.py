# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- ÖZEL KAĞIT TASARIMI CSS ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* Kağıt Dokusu ve Konteyner */
        .paper-container {
            background-color: #fdfbf7; /* Krem/Eski Kağıt Rengi */
            background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
            padding: 40px;
            border: 1px solid #d3c6a0;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
            border-radius: 2px;
            color: #2c1e12; /* Mürekkep Rengi */
            font-family: 'Courier New', Courier, monospace; /* Daktilo Fontu */
            margin-bottom: 20px;
        }
        
        /* Tablo Başlıkları */
        .paper-header {
            text-align: center;
            border-bottom: 2px solid #2c1e12;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }
        
        .paper-header h2 {
            color: #8b0000 !important; /* Kırmızı Başlık */
            font-family: 'Courier New', Courier, monospace;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 0;
            text-shadow: none;
            border: none;
            background: none;
        }

        /* Streamlit Data Editor Özelleştirme */
        div[data-testid="stDataEditor"] {
            border: 1px solid #2c1e12;
            border-radius: 0;
            background-color: transparent;
        }
        
        /* Tablo içi renkler - Dark mode'u ezmek için */
        div[data-testid="stDataEditor"] table {
            color: #2c1e12 !important;
            background-color: #fdfbf7 !important;
        }
        
        div[data-testid="stDataEditor"] th {
            background-color: #e6dec3 !important;
            color: #2c1e12 !important;
            border-bottom: 1px solid #2c1e12 !important;
            font-family: 'Courier New', Courier, monospace;
        }
        
        /* Bilgi Kutucuğu */
        .info-box {
            border: 1px dashed #2c1e12;
            padding: 10px;
            margin-top: 10px;
            background: rgba(0,0,0,0.02);
            font-size: 0.9em;
        }
    </style>
    """, unsafe_allow_html=True)

def create_paper_sheet(players):
    """
    Sadece Cezalar ve Kozlar içeren boş defter.
    King satırları yok.
    """
    data = []
    
    # 1. Ceza Oyunları (Config'den)
    for oyun_adi, kural in OYUN_KURALLARI.items():
        # "Koz" config içinde varsa onu burada değil, aşağıda özel ekleyeceğiz.
        if "Koz" in oyun_adi: 
            continue
            
        limit = kural['limit']
        for _ in range(limit):
            row = {"OYUN": oyun_adi}
            for p in players:
                row[p] = 0
            data.append(row)
            
    # 2. KOZ Oyunları 
    # Standart King'de 4 kişi x 2 Koz hakkı = 8 Koz oyunu vardır.
    for _ in range(8):
        row = {"OYUN": "KOZ"}
        for p in players:
            row[p] = 0
        data.append(row)
        
    return pd.DataFrame(data)

def game_interface():
    # CSS'i yükle
    inject_paper_css()
    
    id_to_name, name_to_id, _ = get_users_map()
    
    # --- SESSION STATE ---
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "sheet_df" not in st.session_state: st.session_state["sheet_df"] = pd.DataFrame()
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []

    # --- 1. DEVE GİRİŞ EKRANI ---
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

    # --- 2. DEFTER GÖRÜNÜMÜ ---
    players = st.session_state["players"]
    df = st.session_state["sheet_df"]
    
    # Kağıt Konteyner Başlangıcı
    st.markdown('<div class="paper-container">', unsafe_allow_html=True)
    
    # Kağıt Başlığı
    st.markdown(f"""
    <div class="paper-header">
        <h2>{st.session_state['current_match_name']}</h2>
        <p>Tarih: {st.session_state['match_date']} | Masa: 4 Kişi</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    ℹ️ <b>Nasıl Doldurulur?</b><br>
    - Cezalarda oyuncuların aldığı <b>ceza kartı sayısını</b> girin.<br>
    - KOZ oyunlarında oyuncuların aldığı <b>el sayısını</b> girin.<br>
    - Puanlar otomatik hesaplanıp kaydedilecektir.
    </div>
    <br>
    """, unsafe_allow_html=True)

    # --- TABLO ---
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
    
    # Kağıt Konteyner Bitişi
    st.markdown('</div>', unsafe_allow_html=True) 

    # --- DOĞRULAMA VE KAYIT ---
    col_save, col_cancel = st.columns([2, 1])
    
    errors = []
    valid_data_rows = []
    
    koz_count = 0 
    ceza_counts = {k: 0 for k in OYUN_KURALLARI}

    for i, row in edited_df.iterrows():
        game_name = row["OYUN"]
        row_sum = sum([row[p] for p in players])
        
        # Boş satır kontrolü (Oynanmamışsa)
        if row_sum == 0:
            # Kullanıcıya sadece bilgi verelim ama hataya düşürmeyelim (Belki yarıda bırakıldı)
            # Ancak KOZ'da toplam 0 olamaz (13 el var).
            pass 
            
        # 1. KOZ KONTROLÜ
        if game_name == "KOZ":
            koz_count += 1
            if row_sum != 13 and row_sum != 0: # 0 ise oynanmamış sayılır
                errors.append(f"❌ **Satır {i+1} (KOZ)**: Toplam el sayısı 13 olmalı (Şu an: {row_sum}).")
            elif row_sum == 13:
                # Geçerli Koz
                db_name = f"Koz (Tümü) {koz_count}" # Veritabanında Koz (Tümü) olarak geçiyor
                # Puan hesabı: Her el +50 puan
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
                # Geçerli Ceza
                db_name = f"{game_name} {ceza_counts[game_name]}"
                puan_carpani = OYUN_KURALLARI[game_name]['puan']
                
                r_data = [db_name]
                for p in players:
                    r_data.append(row[p] * puan_carpani)
                valid_data_rows.append(r_data)

    if not errors and valid_data_rows:
        with col_save:
            if st.button("💾 KAĞIDI İMZALA VE KAYDET", type="primary", use_container_width=True):
                # Toplam Hesaplama
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
            st.info("Kaydedilecek veri yok. Tabloyu doldurun.")
    else:
        with col_save:
            st.warning("⚠️ Kağıtta hatalar var, düzeltmeden imzalanamaz.")
        
        with st.expander("Hata Müfettişi", expanded=True):
            for e in errors:
                st.write(e)

    with col_cancel:
        if st.button("Kağıdı Yırt At (İptal)", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.rerun()
