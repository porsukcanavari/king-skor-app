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
    
    # Session state tanımları
    if "game_active" not in st.session_state: st.session_state["game_active"] = False
    if "temp_df" not in st.session_state: st.session_state["temp_df"] = pd.DataFrame()
    if "game_index" not in st.session_state: st.session_state["game_index"] = 0
    if "king_mode" not in st.session_state: st.session_state["king_mode"] = False
    if "show_king_dialog" not in st.session_state: st.session_state["show_king_dialog"] = False
    
    if not st.session_state["game_active"]:
        st.info("Yeni bir maç başlatmak için aşağıdaki bilgileri doldurun.")
        col1, col2 = st.columns(2)
        with col1:
            match_name = st.text_input("🏷️ Maç İsmi:", "King_Macı")
            user_names = list(name_to_id.keys())
        with col2:
            is_past = st.checkbox("📅 Geçmiş Maç?")
            date_val = st.date_input("Tarih Seç", datetime.now() - timedelta(days=1)) if is_past else datetime.now()
            
        selected_names = st.multiselect("Oyuncuları seçin (4 Kişi):", user_names, max_selections=4)
        
        if len(selected_names) == 4:
            if st.button("🎯 Masayı Kur ve Oyunu Başlat", type="primary", use_container_width=True):
                st.session_state["temp_df"] = pd.DataFrame(columns=selected_names)
                st.session_state["current_match_name"] = match_name
                st.session_state["match_date"] = date_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected_names
                st.session_state["game_active"] = True
                st.session_state["game_index"] = 0
                st.session_state["king_mode"] = False
                st.rerun()
        elif len(selected_names) > 0:
            st.warning(f"{len(selected_names)} oyuncu seçtiniz. Tam 4 kişi olmalı.")
        return

    # Aktif oyun
    df = st.session_state["temp_df"]
    players = st.session_state["players"]
    
    st.markdown(f"""<div class="custom-card"><h3 style="margin:0;color:#FFD700;">🎮 Aktif Maç: {st.session_state['current_match_name']}</h3><p>{st.session_state['match_date']}</p></div>""", unsafe_allow_html=True)
    
    if not df.empty:
        st.subheader("📊 Mevcut Skorlar")
        st.dataframe(apply_simple_gradient(df.copy()), use_container_width=True)
        
        totals = df.sum()
        st.subheader("🏁 Toplamlar")
        cols = st.columns(4)
        for i, p in enumerate(players):
            with cols[i]:
                st.metric(p, f"{totals[p]:.0f}")

    # Oyun bitiş kontrolü
    all_limits = True
    for g_name, r in OYUN_KURALLARI.items():
        if len([x for x in df.index if g_name in str(x)]) < r['limit']:
            all_limits = False; break
            
    if len(df) >= sum([k['limit'] for k in OYUN_KURALLARI.values()]) or st.session_state["king_mode"] or all_limits:
        st.success("🏁 OYUN BİTTİ!")
        if st.button("💾 Maçı Kaydet", type="primary", use_container_width=True):
            header = ["OYUN TÜRÜ"] + [f"{p} (uid:{name_to_id.get(p,'?')})" for p in players]
            rows = [[str(idx)] + [int(row[p]) for p in players] for idx, row in df.iterrows()]
            total_row = ["TOPLAM"] + [int(totals[p]) for p in players]
            if save_match_to_sheet(header, rows, total_row):
                st.session_state["game_active"] = False
                st.session_state["temp_df"] = pd.DataFrame()
                st.rerun()
        return

    st.markdown("---")
    st.subheader("🎯 Sıradaki Oyun")
    
    # King Butonu
    if st.button("👑 KING YAPILDI", use_container_width=True): st.session_state["show_king_dialog"] = True
    
    if st.session_state["show_king_dialog"]:
        with st.container():
            st.warning("👑 KING OYUNU")
            km = st.selectbox("Kim King Yaptı?", players)
            if st.button("✅ Onayla"):
                k_row = {p: 0 for p in players}
                k_row[km] = 1
                st.session_state["temp_df"] = pd.concat([df, pd.DataFrame([k_row], index=[f"👑 KING ({km})"])])
                st.session_state["king_mode"] = True
                st.session_state["show_king_dialog"] = False
                st.rerun()
                
    # Oyun Seçimi
    c_idx = st.session_state["game_index"]
    if c_idx >= len(OYUN_SIRALAMASI): c_idx = len(OYUN_SIRALAMASI) - 1
    
    sel_game = st.selectbox("Oyun Türü:", OYUN_SIRALAMASI, index=c_idx)
    rules = OYUN_KURALLARI[sel_game]
    played = len([x for x in df.index if sel_game in str(x)])
    rem = rules['limit'] - played
    
    if rem <= 0:
        st.error("Bu oyunun limiti doldu!")
        if st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
            st.session_state["game_index"] += 1
            st.rerun()
        return

    st.info(f"Puan: {rules['puan']} | Adet: {rules['adet']} | Kalan Hak: {rem}")
    
    cols = st.columns(4)
    inputs = {}
    total_ent = 0
    r_key = f"{sel_game}_{played}"
    
    for i, p in enumerate(players):
        with cols[i]:
            val = st.number_input(p, 0, rules['adet'], key=f"in_{r_key}_{p}")
            inputs[p] = val
            total_ent += val
            
    if total_ent != rules['adet']:
        st.error(f"Toplam kart sayısı {rules['adet']} olmalı! (Girilen: {total_ent})")
    else:
        if st.button("💾 Skoru Ekle", type="primary", use_container_width=True):
            row_d = {p: inputs[p] * rules['puan'] for p in players}
            st.session_state["temp_df"] = pd.concat([df, pd.DataFrame([row_d], index=[f"{sel_game} #{played+1}"])])
            if played + 1 >= rules['limit']: st.session_state["game_index"] += 1
            st.rerun()