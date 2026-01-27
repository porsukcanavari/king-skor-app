# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI, OYUN_SIRALAMASI
from utils.styles import apply_simple_gradient

def game_interface():
    st.markdown("<h2>🎮 Yeni Maç Başlat</h2>", unsafe_allow_html=True)
    id_to_name, name_to_id, _ = get_users_map()
    
    # --- SESSION STATE BAŞLATMA ---
    if "game_active" not in st.session_state: st.session_state["game_active"] = False
    if "temp_df" not in st.session_state: st.session_state["temp_df"] = pd.DataFrame()
    if "game_index" not in st.session_state: st.session_state["game_index"] = 0
    if "king_mode" not in st.session_state: st.session_state["king_mode"] = False
    if "show_king_dialog" not in st.session_state: st.session_state["show_king_dialog"] = False
    if "current_match_name" not in st.session_state: st.session_state["current_match_name"] = "King_Maci"
    if "match_date" not in st.session_state: st.session_state["match_date"] = datetime.now().strftime("%d.%m.%Y")
    if "players" not in st.session_state: st.session_state["players"] = []

    # --- OYUN KURULUM EKRANI ---
    if not st.session_state["game_active"]:
        st.info("Yeni bir maç başlatmak için aşağıdaki bilgileri doldurun.")
        
        col1, col2 = st.columns(2)
        with col1:
            match_name_input = st.text_input("🏷️ Maç İsmi:", "King_Macı")
            user_names = list(name_to_id.keys())
        with col2:
            is_past = st.checkbox("📅 Geçmiş Maç?")
            if is_past:
                date_val = st.date_input("Tarih Seç", datetime.now() - timedelta(days=1))
            else:
                date_val = datetime.now()
            
        selected_names = st.multiselect(
            "Oyuncuları seçin (Tam 4 Kişi):", 
            user_names, 
            max_selections=4
        )
        
        if len(selected_names) == 4:
            if st.button("🎯 Masayı Kur ve Oyunu Başlat", type="primary", use_container_width=True):
                # Başlatma İşlemleri
                st.session_state["temp_df"] = pd.DataFrame(columns=selected_names)
                st.session_state["current_match_name"] = match_name_input
                st.session_state["match_date"] = date_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected_names
                st.session_state["game_active"] = True
                st.session_state["game_index"] = 0
                st.session_state["king_mode"] = False
                st.rerun()
        elif len(selected_names) > 0:
            st.warning(f"{len(selected_names)} oyuncu seçtiniz. Lütfen 4 oyuncu seçin.")
        return

    # --- AKTİF OYUN EKRANI ---
    df = st.session_state["temp_df"]
    players = st.session_state["players"]
    
    # Bilgi Kartı
    st.markdown(f"""
    <div class="custom-card">
        <h3 style="margin:0;color:#FFD700;">🎮 Aktif Maç: {st.session_state['current_match_name']}</h3>
        <p style="margin:0;color:#ccc;">Tarih: {st.session_state['match_date']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Skor Tablosu
    if not df.empty:
        st.subheader("📊 Mevcut Skorlar")
        # Basit gradient fonksiyonunu kullan
        st.dataframe(apply_simple_gradient(df.copy()), use_container_width=True)
        
        totals = df.sum()
        st.subheader("🏁 Toplamlar")
        cols = st.columns(4)
        for i, p in enumerate(players):
            with cols[i]:
                st.metric(p, f"{totals[p]:.0f}")

    # Bitiş Kontrolü
    all_limits_reached = True
    for g_name, r in OYUN_KURALLARI.items():
        if len([x for x in df.index if g_name in str(x)]) < r['limit']:
            all_limits_reached = False
            break
            
    game_is_finished = (
        len(df) >= sum([k['limit'] for k in OYUN_KURALLARI.values()]) or 
        st.session_state["king_mode"] or 
        all_limits_reached
    )
            
    if game_is_finished:
        st.success("🏁 OYUN BİTTİ!")
        col_save, col_new = st.columns(2)
        with col_save:
            if st.button("💾 Maçı Kaydet ve Bitir", type="primary", use_container_width=True):
                # Veriyi hazırlama
                header = ["OYUN TÜRÜ"]
                for p in players:
                    uid = name_to_id.get(p, "?")
                    header.append(f"{p} (uid:{uid})")
                
                rows_to_save = []
                for idx, row in df.iterrows():
                    r_list = [str(idx)]
                    for p in players:
                        r_list.append(int(row[p]))
                    rows_to_save.append(r_list)
                
                total_row = ["TOPLAM"] + [int(totals[p]) for p in players]
                
                if save_match_to_sheet(header, rows_to_save, total_row):
                    st.success("Kaydedildi!")
                    st.session_state["game_active"] = False
                    st.session_state["temp_df"] = pd.DataFrame()
                    st.rerun()
        
        with col_new:
            if st.button("İptal / Yeni Maç", type="secondary", use_container_width=True):
                st.session_state["game_active"] = False
                st.session_state["temp_df"] = pd.DataFrame()
                st.rerun()
        return

    st.markdown("---")
    
    # King Dialog Kontrolü
    col_king, col_undo = st.columns([3, 1])
    with col_king:
        if st.button("👑 KING YAPILDI", use_container_width=True): 
            st.session_state["show_king_dialog"] = True
    
    with col_undo:
        if st.button("↩️ Geri Al", use_container_width=True):
            if not df.empty:
                st.session_state["temp_df"] = df.iloc[:-1]
                st.rerun()
    
    if st.session_state["show_king_dialog"]:
        with st.container():
            st.info("👑 KING OYUNU KAYDI")
            km = st.selectbox("Kim King Yaptı?", players)
            
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("✅ Onayla"):
                    k_row = {p: 0 for p in players}
                    k_row[km] = 1 # İşaret
                    
                    new_idx = f"👑 KING ({km})"
                    new_df = pd.DataFrame([k_row], index=[new_idx])
                    st.session_state["temp_df"] = pd.concat([df, new_df])
                    
                    st.session_state["king_mode"] = True
                    st.session_state["show_king_dialog"] = False
                    st.rerun()
            with c_no:
                if st.button("❌ İptal"):
                    st.session_state["show_king_dialog"] = False
                    st.rerun()
            st.markdown("---")

    # Normal Oyun Girişi
    st.subheader("🎯 Skor Girişi")
    
    # Sıradaki oyunu otomatik bul
    c_idx = st.session_state["game_index"]
    if c_idx >= len(OYUN_SIRALAMASI): c_idx = len(OYUN_SIRALAMASI) - 1
    
    sel_game = st.selectbox("Oyun Türü:", OYUN_SIRALAMASI, index=c_idx)
    rules = OYUN_KURALLARI[sel_game]
    
    played_count = len([x for x in df.index if sel_game in str(x)])
    remaining = rules['limit'] - played_count
    
    if remaining <= 0:
        st.warning(f"⚠️ {sel_game} limiti dolmuş! Lütfen başka oyun seçin.")
    else:
        st.write(f"**{sel_game}** (Puan: {rules['puan']} | Adet: {rules['adet']} | Kalan: {remaining})")
        
        cols = st.columns(4)
        inputs = {}
        total_entered = 0
        unique_key = f"{sel_game}_{played_count}_{len(df)}" # Benzersiz key
        
        for i, p in enumerate(players):
            with cols[i]:
                val = st.number_input(p, min_value=0, max_value=rules['adet'], key=f"in_{unique_key}_{p}")
                inputs[p] = val
                total_entered += val
        
        if total_entered != rules['adet']:
            st.error(f"Toplam {rules['adet']} olmalı! Şu an: {total_entered}")
        else:
            if st.button("💾 Skoru Ekle", type="primary", use_container_width=True):
                # Puanları hesapla
                row_data = {p: inputs[p] * rules['puan'] for p in players}
                new_idx = f"{sel_game} #{played_count+1}"
                
                new_row_df = pd.DataFrame([row_data], index=[new_idx])
                st.session_state["temp_df"] = pd.concat([df, new_row_df])
                
                # Eğer bu oyunun limiti dolduysa indexi ilerlet
                if played_count + 1 >= rules['limit']:
                    if st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
                        st.session_state["game_index"] += 1
                
                st.rerun()
