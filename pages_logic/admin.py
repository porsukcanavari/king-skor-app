# pages_logic/admin.py
import streamlit as st
from utils.database import get_users_map, update_user_in_sheet, delete_match_from_sheet
from utils.stats import istatistikleri_hesapla

def admin_panel():
    if st.session_state.get("role") not in ["admin", "patron"]:
        st.error("Yetkisiz giriş!"); return

    st.subheader("👥 Kullanıcı Yönetimi")
    _, _, users = get_users_map()
    
    with st.form("add_user"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre")
        r = st.selectbox("Rol", ["user", "admin"])
        if st.form_submit_button("Ekle/Güncelle"):
            if update_user_in_sheet(u, u, p, r) in ["added", "updated"]: st.success("İşlem Tamam!")

    st.subheader("🗑️ Maç Sil")
    _, hist, _, _ = istatistikleri_hesapla()
    if hist:
        m = st.selectbox("Maç Seç", [x['baslik'] for x in hist[::-1]])
        if st.button("Sil"):
            if delete_match_from_sheet(m): st.success("Silindi!"); st.rerun()