# king_istatistik.py
import streamlit as st
from utils.styles import inject_custom_css
from pages_logic.login import login_screen, logout
from pages_logic.game_add import game_interface
from pages_logic.leaderboard import kkd_leaderboard_interface
from pages_logic.statistics import stats_interface
from pages_logic.profile import profile_interface
from pages_logic.admin import admin_panel

# Sayfa Ayarları
st.set_page_config(
    page_title="King İstatistik Kurumu",
    layout="wide",
    page_icon="👑",
    initial_sidebar_state="collapsed"
)

# CSS'i yükle
inject_custom_css()

# Session State Başlatma
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = "user"
if "username" not in st.session_state:
    st.session_state["username"] = ""

def main():
    # 1. GİRİŞ EKRANI KONTROLÜ
    if not st.session_state["logged_in"]:
        login_screen()
        return

    # 2. GİRİŞ YAPILDIYSA ANA EKRAN
    # Üst Bilgi Çubuğu
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px;">
        <span style="font-size: 1.2em;">👑 <strong>{st.session_state['username']}</strong></span>
        <span style="background: #444; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; margin-left: 10px;">
            {st.session_state['role'].upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Menü Seçenekleri (Yetkiye Göre)
    menu_items = ["📊 İstatistikler", "🏆 KKD Liderlik", "👤 Profilim"]
    if st.session_state["role"] in ["admin", "patron"]:
        menu_items = ["🎮 Oyun Ekle", "🛠️ Yönetim Paneli"] + menu_items
    
    # Navigasyon Menüsü
    selected_page = st.radio(
        "Menü", 
        menu_items, 
        horizontal=True, 
        label_visibility="collapsed",
        key="main_nav"
    )

    st.markdown("---")

    # Sidebar (Çıkış Butonu)
    with st.sidebar:
        st.markdown("### ⚙️ İşlemler")
        if st.button("🚪 Çıkış Yap", type="secondary", use_container_width=True):
            logout()

    # 3. SAYFA YÖNLENDİRME (ROUTER)
    if selected_page == "🎮 Oyun Ekle":
        game_interface()
    elif selected_page == "📊 İstatistikler":
        stats_interface()
    elif selected_page == "🏆 KKD Liderlik":
        kkd_leaderboard_interface()
    elif selected_page == "👤 Profilim":
        profile_interface()
    elif selected_page == "🛠️ Yönetim Paneli":
        admin_panel()

if __name__ == "__main__":
    main()