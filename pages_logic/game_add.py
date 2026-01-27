# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

# --- SADECE TABLOYU PARŞÖMEN YAPAN CSS ---
def inject_paper_css():
    st.markdown("""
    <style>
        /* 1. SADECE TABLOYU HEDEF ALAN FİLTRE */
        /* Mantık: Dark Mode (Siyah) -> Negatif (Beyaz) -> Sepia (Sarımtırak Kağıt) */
        [data-testid="stDataEditor"] {
            filter: invert(1) sepia(0.6) contrast(0.9);
            background-color: black !important; /* Terste krem rengi görünmesi için zemin siyah olmalı */
            border: 2px solid #555; /* Terste kahverengi çerçeve */
            border-radius: 5px;
        }

        /* 2. TABLO İÇİNDEKİ SAYILARI DÜZELTME */
        /* Tabloyu ters çevirince içindeki sayılar da ters renk olur (Siyah olur), bu istediğimiz bir şey.
           Ancak seçim rengi (mavi) ters dönünce turuncu olur, bu da parşömene uyar. */
        
        /* 3. BAŞLIK ALANI (NORMAL GÖRÜNÜM) */
        .info-box {
            background-color: rgba(255, 255, 255, 0.1);
            border-left: 5px solid #FFD700;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        /* 4. HATA MESAJLARI */
        .error-box {
            background-color: rgba(255, 0, 0, 0.2);
            border: 1px solid red;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            color: #ffcccc;
        }
    </style>
    """, unsafe_allow_html=True)

def create_paper_sheet(players):
    """
    Boş King Defteri Şablonu
    """
    data = []
    
    # 1. CEZALAR
    for oyun_adi, kural in OYUN_KURALLARI.items():
        if "Koz" in oyun_adi: continue 
        limit = kural['limit']
        for _ in range(limit):
            row = {"OYUN": oyun_adi}
            for p in players: row[p] = 0
            data.append(row)
            
    # 2. KOZLAR (8 Adet)
    for _ in range(8):
        row = {"OYUN": "KOZ"}
        for p in players: row[p] = 0
        data.append(row)
        
    return pd.DataFrame(data)

def game_interface():
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
    
    # Bilgi Alanı
    st.markdown(f"""
    <div class="info-box">
        <h3 style="margin:0; color:#FFD700;">{st.session_state['current_match_name']}</h3>
        <p style="margin:0;">📅 {st.session_state['match_date']} | 👥 4 Kişi</p>
        <small>Aşağıdaki tabloyu doldurun. Hatalı satırlar uyarılacaktır.</small>
    </div>
    """, unsafe_allow_html=True)

    # --- TABLO (PARŞÖMEN GÖRÜNÜMLÜ) ---
    # İlk sütunu (Oyun isimleri) kilitliyoruz
    column_config = {"OYUN": st.column_config.TextColumn("Oyun Türü", disabled=True, width="medium")}
    for p in players:
        column_config[p] = st.column_config.NumberColumn(p, min_value=0, step=1, required=True)

    # CSS burada devreye girip sadece bu tabloyu ters yüz edecek
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=800,
        hide_index=True,
        column_config=column_config
    )
    
    st.session_state["sheet_df"] = edited_df # Veriyi kaybetme

    # --- MÜFETTİŞ (KONTROL) ---
    errors = []
    valid_data_rows = []
    
    # Sayaçlar
    koz_count = 0 
    ceza_counts = {k: 0 for k in OYUN_KURALLARI}

    for i, row in edited_df.iterrows():
        game_name = row["OYUN"]
        row_sum = sum([row[p] for p in players])
        
        # Boş satırsa geç
        if row_sum == 0:
            continue
            
        # 1. KOZ KONTROLÜ (Toplam 13 olmalı)
        if game_name == "KOZ":
            koz_count += 1
            if row_sum != 13:
                errors.append(f"❌ **Satır {i+1} (KOZ)**: Toplam el sayısı 13 olmalı. (Şu an: {row_sum})")
            else:
                # Doğruysa veriyi hazırla
                db_name = f"Koz (Tümü) {koz_count}"
                r_data = [db_name] + [row[p] * 50 for p in players] # 50 ile çarp
                valid_data_rows.append(r_data)
        
        # 2. CEZA KONTROLÜ (Adet kontrolü)
        elif game_name in OYUN_KURALLARI:
            ceza_counts[game_name] += 1
            required = OYUN_KURALLARI[game_name]['adet']
            
            if row_sum != required:
                errors.append(f"❌ **Satır {i+1} ({game_name})**: Toplam {required} kart olmalı. (Şu an: {row_sum})")
            else:
                # Doğruysa veriyi hazırla
                db_name = f"{game_name} {ceza_counts[game_name]}"
                puan_carpani = OYUN_KURALLARI[game_name]['puan']
                r_data = [db_name] + [row[p] * puan_carpani for p in players]
                valid_data_rows.append(r_data)

    st.write("") # Boşluk

    # --- BUTONLAR ---
    c_save, c_cancel = st.columns([2, 1])
    
    if not errors and valid_data_rows:
        with c_save:
            if st.button("💾 KAĞIDI İMZALA VE KAYDET", type="primary", use_container_width=True):
                # Toplam satırı
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
                    st.success("Maç başarıyla deftere işlendi!")
                    st.session_state["sheet_active"] = False
                    st.session_state["sheet_df"] = pd.DataFrame()
                    st.rerun()
                    
    elif not valid_data_rows:
        with c_save:
            st.info("Defteri doldurmaya başlayın.")
            
    else:
        # Hata varsa kaydet butonu yerine hata raporu göster
        with c_save:
            st.warning("⚠️ Hatalı satırlar var, düzeltmeden kaydedilemez.")
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            for e in errors:
                st.markdown(f"- {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    with c_cancel:
        if st.button("Kağıdı Yırt At (İptal)", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.rerun()
