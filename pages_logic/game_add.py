# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI

def create_empty_sheet(players):
    """Boş bir King defteri oluşturur"""
    rows = []
    
    # 1. Ceza Oyunları (Config'deki limitlere göre)
    for oyun_adi, kural in OYUN_KURALLARI.items():
        limit = kural['limit']
        for i in range(1, limit + 1):
            row_name = f"{oyun_adi} {i}"
            row_data = {"OYUN": row_name}
            for p in players:
                row_data[p] = 0
            rows.append(row_data)
            
    # 2. King Oyunları (Standart 20 el King varsayalım veya kullanıcı eklesin)
    # Genelde 4 kişi x 5 King = 20 King oynanır
    for i in range(1, 21):
        row_name = f"KING {i}"
        row_data = {"OYUN": row_name}
        for p in players:
            row_data[p] = 0
        rows.append(row_data)
        
    return pd.DataFrame(rows).set_index("OYUN")

def game_interface():
    st.markdown("<h2>📝 Tam Boy King Defteri</h2>", unsafe_allow_html=True)
    id_to_name, name_to_id, _ = get_users_map()
    
    # --- SESSION STATE ---
    if "sheet_active" not in st.session_state: st.session_state["sheet_active"] = False
    if "sheet_df" not in st.session_state: st.session_state["sheet_df"] = pd.DataFrame()
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []

    # --- 1. KURULUM EKRANI ---
    if not st.session_state["sheet_active"]:
        st.info("Yeni bir defter açmak için oyuncuları seçin.")
        
        c1, c2 = st.columns(2)
        with c1:
            m_name = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
            users = list(name_to_id.keys())
        with c2:
            is_past = st.checkbox("📅 Geçmiş Maç")
            d_val = st.date_input("Tarih", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
            
        selected = st.multiselect("Oyuncular (4 Kişi):", users, max_selections=4)
        
        if len(selected) == 4:
            if st.button("📖 Defteri Aç", type="primary", use_container_width=True):
                st.session_state["sheet_df"] = create_empty_sheet(selected)
                st.session_state["current_match_name"] = m_name
                st.session_state["match_date"] = d_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected
                st.session_state["sheet_active"] = True
                st.rerun()
        return

    # --- 2. DEFTER EKRANI ---
    players = st.session_state["players"]
    df = st.session_state["sheet_df"]
    
    # Başlık
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.05); padding:10px; border-radius:10px; margin-bottom:10px;">
        <div>
            <h3 style="margin:0; color:#FFD700;">{st.session_state['current_match_name']}</h3>
            <small>📅 {st.session_state['match_date']}</small>
        </div>
        <div>
            <span style="background:#444; padding:5px 10px; border-radius:5px;">4 Kişi</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("👇 **Aşağıdaki tabloyu doldurun. King satırlarında sadece King diyene 1 yazın.**")

    # --- DATA EDITOR (TABLO) ---
    # Kullanıcı burada verileri girecek
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=600,  # Uzun bir sayfa olsun
        column_config={
            p: st.column_config.NumberColumn(p, min_value=0, step=1, required=True) 
            for p in players
        }
    )
    
    # Session state güncelle (Veri kaybolmasın diye)
    st.session_state["sheet_df"] = edited_df

    st.markdown("---")
    
    # --- KONTROL VE KAYIT ---
    col_check, col_save, col_cancel = st.columns([1, 2, 1])
    
    # Hata listesi
    errors = []
    valid_data_rows = [] # Veritabanına gidecek temiz veri
    
    # Validasyon Mantığı
    for index, row in edited_df.iterrows():
        # Satır tamamen boşsa (0,0,0,0) ve King satırıysa atla (oynanmamış olabilir)
        row_sum = sum([row[p] for p in players])
        
        # Oyun tipini bul (örn: "Rıfkı 1" -> "Rıfkı")
        game_type = index.split(" ")[0]
        if game_type == "Kız" or game_type == "Erkek" or game_type == "Kupa" or game_type == "El" or game_type == "Son" or game_type == "Koz":
            # İsimlerdeki boşlukları düzeltmek için (Kız Almaz vs)
            for k in OYUN_KURALLARI.keys():
                if index.startswith(k):
                    game_type = k
                    break
        
        # 1. CEZA OYUNLARI KONTROLÜ
        if game_type in OYUN_KURALLARI:
            required = OYUN_KURALLARI[game_type]['adet']
            if row_sum != required:
                # Eğer hepsi 0 ise belki henüz oynanmamıştır, ama "Kaydet" dendiğinde eksik veri olmamalı
                # Kullanıcı kolaylığı: Hepsi 0 ise uyarı ver ama oynanmadı say.
                # Ama "Tüm Kağıt" mantığında genelde hepsi doldurulur.
                # Biz sıkı kontrol yapalım:
                errors.append(f"❌ **{index}**: Toplam {required} olmalı, şu an {row_sum}.")
            else:
                # Doğru veri, kaydetmek için hazırla (Puan Hesabı)
                puan_degeri = OYUN_KURALLARI[game_type]['puan']
                converted_row = [str(index)] # İsim
                for p in players:
                    converted_row.append(row[p] * puan_degeri)
                valid_data_rows.append(converted_row)
        
        # 2. KING KONTROLÜ
        elif index.startswith("KING"):
            if row_sum == 0:
                continue # Oynanmamış King satırı, sorun yok
            elif row_sum == 1:
                # Geçerli King
                converted_row = [f"👑 {index}"]
                # King puan hesabı stats.py içinde yapılıyor ama veritabanına
                # 1 (yapan) ve 0 (diğerleri) olarak gitmeli.
                for p in players:
                    converted_row.append(row[p]) 
                valid_data_rows.append(converted_row)
            else:
                errors.append(f"❌ **{index}**: King'i sadece 1 kişi söyleyebilir (Toplam 1 olmalı).")

    # Toplam Puan Önizlemesi (Opsiyonel, bilgilendirme amaçlı)
    if not errors:
        st.success("✅ Tablo hatasız görünüyor! Kaydetmeye hazır.")
        save_disabled = False
    else:
        with st.expander("⚠️ Hata Raporu (Düzeltmeniz Gerekiyor)", expanded=True):
            for e in errors:
                st.write(e)
        save_disabled = True

    # Butonlar
    with col_save:
        if st.button("💾 TÜM KAĞIDI KAYDET", type="primary", use_container_width=True, disabled=save_disabled):
            # Toplam hesaplama
            totals = {p: 0 for p in players}
            # valid_data_rows içinde ham puanlar var, onları toplayalım
            # Dikkat: King satırları burada 1/0, puan değil. Toplam satırı görsel amaçlı.
            # Veritabanına gönderirken total_row lazım.
            
            # Basit toplam (King puanları stats.py'da hesaplanıyor, burada veritabanına giden ham skor önemli)
            # Ancak "Users" sayfasındaki toplam için yaklaşık bir değer lazım.
            # Şimdilik toplam satırını sadece cezalardan oluşturalım (King sonra hesaplanır)
            
            final_total_row = ["TOPLAM"]
            for i, p in enumerate(players):
                # Sadece ceza puanlarını topla
                p_total = 0
                for v_row in valid_data_rows:
                    if not v_row[0].startswith("👑"): # King değilse
                         p_total += v_row[i+1] # i+1 çünkü index 0'da isim var
                final_total_row.append(p_total)

            # Başlık Satırı
            header = ["OYUN TÜRÜ"]
            for p in players:
                uid = name_to_id.get(p, "?")
                header.append(f"{p} (uid:{uid})")

            # Kaydet
            if save_match_to_sheet(header, valid_data_rows, final_total_row):
                st.balloons()
                st.success("Maç başarıyla veritabanına işlendi!")
                st.session_state["sheet_active"] = False
                st.session_state["sheet_df"] = pd.DataFrame()
                st.rerun()

    with col_cancel:
        if st.button("İptal", use_container_width=True):
            st.session_state["sheet_active"] = False
            st.rerun()
