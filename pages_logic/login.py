# pages_logic/login.py
import streamlit as st
import time
from utils.database import get_users_map

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #FFD700; font-size: 3em; margin-bottom: 10px;">👑</h1>
            <h1 style="color: #FFD700;">King İstatistik Kurumu</h1>
            <p style="color: #aaa;">Resmi Oyun İstatistik ve Takip Sistemi</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center;'>Sisteme Giriş</h3>", unsafe_allow_html=True)
            username = st.text_input("👤 Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
            password = st.text_input("🔒 Şifre", type="password", placeholder="Şifrenizi girin")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit = st.form_submit_button("🔓 Giriş Yap", type="primary", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Lütfen kullanıcı adı ve şifre girin!")
                    return
                
                _, _, users_df = get_users_map()
                if users_df.empty:
                    st.error("⚠️ HATA: Kullanıcı veritabanına ulaşılamıyor!")
                    return
                
                user_match = users_df[
                    (users_df['Username'].astype(str).str.strip() == username.strip()) &
                    (users_df['Password'].astype(str).str.strip() == str(password).strip())
                ]
                
                if not user_match.empty:
                    user_data = user_match.iloc[0]
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = user_data['Role']
                    st.session_state["user_id"] = int(user_data['UserID'])
                    st.success(f"Hoş geldiniz, **{username}**! 🎉")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Hatalı kullanıcı adı veya şifre!")

def logout():
    st.session_state.clear()
    st.success("Çıkış yapıldı! 👋")
    time.sleep(1)
    st.rerun()