# pages_logic/admin.py
import streamlit as st
import time
from utils.database import get_users_map, update_user_in_sheet, delete_match_from_sheet
from utils.stats import istatistikleri_hesapla

def admin_panel():
    st.markdown("<h2>🛠️ Yönetim Paneli</h2>", unsafe_allow_html=True)
    
    current_role = st.session_state.get("role", "user")
    
    if current_role not in ["admin", "patron"]:
        st.error("Bu sayfaya erişim yetkiniz yok!")
        return
    
    # --- KULLANICI YÖNETİMİ ---
    st.subheader("👥 Kullanıcı Yönetimi")
    _, _, users_df = get_users_map()
    
    with st.form("user_management_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            username_input = st.text_input("Kullanıcı Adı")
        with col2:
            password_input = st.text_input("Şifre")
        with col3:
            role_options = ["user", "admin"]
            if current_role == "patron":
                role_options.append("patron")
            role_input = st.selectbox("Yetki", role_options)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            add_btn = st.form_submit_button("➕ Ekle / Güncelle", type="primary")
        with col_btn2:
            del_btn = st.form_submit_button("🗑️ Kullanıcıyı Sil", type="secondary")
            
        if add_btn:
            if not username_input:
                st.error("Kullanıcı adı gerekli!")
            else:
                res = update_user_in_sheet(username_input, username_input, password_input or "1234", role_input)
                if res in ["added", "updated"]:
                    st.success(f"İşlem başarılı: {res}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("İşlem başarısız.")

        if del_btn:
            if not username_input:
                st.error("Silinecek kullanıcı adını yazın!")
            else:
                res = update_user_in_sheet(username_input, "", "", "", delete=True)
                if res == "deleted":
                    st.warning("Kullanıcı silindi.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Silme başarısız (Kullanıcı bulunamadı mı?)")

    # --- KULLANICI LİSTESİ ---
    if not users_df.empty:
        with st.expander("📋 Mevcut Kullanıcı Listesi", expanded=True):
            st.dataframe(users_df[['UserID', 'Username', 'Role', 'KKD']], use_container_width=True)

    st.divider()

    # --- MAÇ YÖNETİMİ ---
    st.subheader("🎮 Maç Yönetimi")
    
    # İstatistikleri çekip maç listesini alıyoruz
    try:
        _, match_hist, _, _ = istatistikleri_hesapla()
        
        if match_hist:
            match_titles = [m['baslik'].replace("--- MAÇ: ", "").replace(" ---", "") for m in match_hist[::-1]]
            full_titles = [m['baslik'] for m in match_hist[::-1]]
            
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                selected_match_display = st.selectbox("Silinecek Maçı Seç:", match_titles)
            
            # Seçilenin tam başlığını bul
            selected_full_title = ""
            if selected_match_display:
                for ft in full_titles:
                    if selected_match_display in ft:
                        selected_full_title = ft
                        break
            
            with col_m2:
                st.write("") # Boşluk
                st.write("") 
                if st.button("🗑️ Maçı Sil", type="primary"):
                    if selected_full_title:
                        if delete_match_from_sheet(selected_full_title):
                            st.success("Maç başarıyla silindi ve istatistikler güncellendi.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Silme sırasında hata oluştu.")
        else:
            st.info("Henüz silinecek maç kaydı yok.")
            
    except Exception as e:
        st.error(f"Maç listesi yüklenemedi: {e}")
