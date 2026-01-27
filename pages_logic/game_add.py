# pages_logic/game_add.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database import get_users_map, save_match_to_sheet
from utils.config import OYUN_KURALLARI, OYUN_SIRALAMASI
from utils.styles import apply_simple_gradient

def game_interface():
    st.markdown("<h2>📝 Maç Kağıdı (Skor Girişi)</h2>", unsafe_allow_html=True)
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

    # --- 1. OYUN KURULUM EKRANI (Aynı Kalıyor) ---
    if not st.session_state["game_active"]:
        st.info("Yeni bir çetele oluşturmak için ayarları yapın.")
        
        col1, col2 = st.columns(2)
        with col1:
            match_name_input = st.text_input("🏷️ Maç Adı:", "King_Akşamı")
            user_names = list(name_to_id.keys())
        with col2:
            is_past = st.checkbox("📅 Eski Tarihli Maç")
            if is_past:
                date_val = st.date_input("Tarih Seç", datetime.now() - timedelta(days=1))
            else:
                date_val = datetime.now()
            
        selected_names = st.multiselect(
            "Masadaki 4 Kişiyi Seç:", 
            user_names, 
            max_selections=4
        )
        
        if len(selected_names) == 4:
            if st.button("🃏 Kağıdı Aç ve Başla", type="primary", use_container_width=True):
                st.session_state["temp_df"] = pd.DataFrame(columns=selected_names)
                st.session_state["current_match_name"] = match_name_input
                st.session_state["match_date"] = date_val.strftime("%d.%m.%Y")
                st.session_state["players"] = selected_names
                st.session_state["game_active"] = True
                st.session_state["game_index"] = 0
                st.session_state["king_mode"] = False
                st.rerun()
        elif len(selected_names) > 0:
            st.warning(f"Masada {len(selected_names)} kişi var. King 4 kişiyle oynanır.")
        return

    # --- 2. AKTİF OYUN EKRANI (Burayı Güzelleştirdik) ---
    df = st.session_state["temp_df"]
    players = st.session_state["players"]
    
    # Üst Bilgi Çubuğu
    col_info1, col_info2, col_info3 = st.columns([2, 1, 1])
    with col_info1:
        st.markdown(f"### 🏟️ {st.session_state['current_match_name']}")
    with col_info2:
        st.markdown(f"📅 **{st.session_state['match_date']}**")
    with col_info3:
        if st.button("❌ Masayı İptal Et", type="secondary", use_container_width=True):
            st.session_state["game_active"] = False
            st.session_state["temp_df"] = pd.DataFrame()
            st.rerun()

    st.markdown("---")

    # --- SKOR TABLOSU (ÇETELE) ---
    col_table, col_input = st.columns([1.5, 1])
    
    with col_table:
        st.subheader("📋 Puan Durumu")
        if not df.empty:
            # Tabloyu göster
            st.dataframe(
                apply_simple_gradient(df.copy()), 
                use_container_width=True,
                height=400
            )
            
            # Toplamlar
            totals = df.sum()
            st.markdown("#### 🏁 Toplam Puanlar")
            total_cols = st.columns(4)
            for i, p in enumerate(players):
                with total_cols[i]:
                    val = int(totals[p])
                    color = "green" if val >= 0 else "red"
                    st.markdown(f"<div style='text-align:center; border:1px solid #444; border-radius:5px; padding:5px;'><strong style='color:{color}'>{val}</strong><br><small>{p}</small></div>", unsafe_allow_html=True)
        else:
            st.info("Henüz oyun girilmedi. Sağ taraftan ilk eli girin. 👉")

    # --- GİRİŞ ALANI (SAĞ TARAFA ALDIK) ---
    with col_input:
        st.subheader("✍️ El Girişi")
        
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
            st.success("Oyun Tamamlandı!")
            if st.button("💾 Kaydet ve Arşivle", type="primary", use_container_width=True):
                 # Kayıt İşlemleri
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
        
        else:
            # Sıradaki oyunu otomatik bul
            c_idx = st.session_state["game_index"]
            if c_idx >= len(OYUN_SIRALAMASI): c_idx = len(OYUN_SIRALAMASI) - 1
            
            # Oyun Seçimi
            sel_game = st.selectbox("Oyun Seç:", OYUN_SIRALAMASI, index=c_idx)
            rules = OYUN_KURALLARI[sel_game]
            
            played_count = len([x for x in df.index if sel_game in str(x)])
            remaining = rules['limit'] - played_count
            
            if remaining <= 0:
                st.warning(f"⚠️ {sel_game} bitti! Başka seç.")
            else:
                # OYUN BİLGİ KARTI
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; border-left: 5px solid {rules['renk']};">
                    <strong>{sel_game}</strong><br>
                    Adet: <strong>{rules['adet']}</strong> | Puan: <strong>{rules['puan']}</strong>
                </div>
                """, unsafe_allow_html=True)
                st.write("")

                # --- YENİ TABLOLU GİRİŞ SİSTEMİ ---
                st.markdown("👇 **Oyuncuların Aldığı Kartları Yazın:**")
                
                # Başlangıç verisi (hepsi 0)
                input_data = {p: [0] for p in players}
                
                # Data Editor (Excel gibi giriş)
                edited_df = st.data_editor(
                    pd.DataFrame(input_data),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        p: st.column_config.NumberColumn(
                            p,
                            min_value=0,
                            max_value=rules['adet'],
                            step=1,
                            required=True
                        ) for p in players
                    }
                )

                # Girilenleri kontrol et
                current_values = edited_df.iloc[0].to_dict()
                total_entered = sum(current_values.values())
                
                # Toplam Kontrolü Göstergesi
                if total_entered == rules['adet']:
                    st.success(f"✅ Toplam: {total_entered} / {rules['adet']}")
                    save_disabled = False
                else:
                    st.error(f"⚠️ Toplam: {total_entered} / {rules['adet']}")
                    save_disabled = True

                # Butonlar
                c_save, c_king = st.columns([2, 1])
                
                with c_save:
                    if st.button("💾 İşle", type="primary", use_container_width=True, disabled=save_disabled):
                        row_data = {p: current_values[p] * rules['puan'] for p in players}
                        new_idx = f"{sel_game} #{played_count+1}"
                        
                        new_row_df = pd.DataFrame([row_data], index=[new_idx])
                        st.session_state["temp_df"] = pd.concat([df, new_row_df])
                        
                        # Index ilerlet
                        if played_count + 1 >= rules['limit']:
                            if st.session_state["game_index"] < len(OYUN_SIRALAMASI) - 1:
                                st.session_state["game_index"] += 1
                        st.rerun()

                with c_king:
                    if st.button("👑 King", use_container_width=True):
                        st.session_state["show_king_dialog"] = True

                # Geri Al Butonu
                if st.button("↩️ Son Eli Sil", use_container_width=True):
                    if not df.empty:
                        st.session_state["temp_df"] = df.iloc[:-1]
                        st.rerun()

    # --- KING DIALOG ---
    if st.session_state["show_king_dialog"]:
        with st.form("king_form"):
            st.warning("👑 KING YAPILDI")
            km = st.selectbox("King'i kim söyledi?", players)
            if st.form_submit_button("✅ Kaydet"):
                k_row = {p: 0 for p in players}
                k_row[km] = 1 # King için işaret (Puan hesaplama stats.py'da yapılıyor zaten)
                
                new_idx = f"👑 KING ({km})"
                new_df = pd.DataFrame([k_row], index=[new_idx])
                st.session_state["temp_df"] = pd.concat([df, new_df])
                
                st.session_state["king_mode"] = True
                st.session_state["show_king_dialog"] = False
                st.rerun()
            
            if st.form_submit_button("İptal"):
                st.session_state["show_king_dialog"] = False
                st.rerun()
