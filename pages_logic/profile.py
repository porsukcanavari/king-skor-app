# pages_logic/profile.py
import streamlit as st
from utils.stats import istatistikleri_hesapla
from utils.database import update_user_in_sheet

def profile_interface():
    st.markdown(f"<h2>👤 Profil: {st.session_state['username']}</h2>", unsafe_allow_html=True)
    stats, _, _, id_map = istatistikleri_hesapla()
    uid = st.session_state.get("user_id")
    
    if uid in stats:
        s = stats[uid]
        c1, c2, c3 = st.columns(3)
        c1.metric("KKD", int(s['kkd']))
        c2.metric("Maç", s['mac_sayisi'])
        c3.metric("Kazanma", s['pozitif_mac_sayisi'])
        
    with st.expander("⚙️ Hesap Ayarları"):
        new_pass = st.text_input("Yeni Şifre", type="password")
        if st.button("Şifreyi Güncelle"):
            if update_user_in_sheet(st.session_state['username'], st.session_state['username'], new_pass, st.session_state['role']) == "updated":
                st.success("Güncellendi!")