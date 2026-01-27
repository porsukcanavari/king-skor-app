# pages_logic/leaderboard.py
import streamlit as st
import pandas as pd
from utils.stats import istatistikleri_hesapla
from utils.styles import apply_simple_gradient

def kkd_leaderboard_interface():
    st.markdown("<h2>🏆 KKD Liderlik Tablosu</h2>", unsafe_allow_html=True)
    stats, _, _, id_map = istatistikleri_hesapla()
    
    if not stats:
        st.warning("Veri yok.")
        return

    data = []
    for uid, s in stats.items():
        if s['mac_sayisi'] > 0:
            data.append({
                "Oyuncu": id_map.get(uid, f"?{uid}"),
                "KKD": int(s['kkd']),
                "Maç": s['mac_sayisi'],
                "Win Rate": (s['pozitif_mac_sayisi']/s['mac_sayisi']*100),
                "Ortalama": s['toplam_puan']/s['mac_sayisi']
            })
            
    if not data: return
    df = pd.DataFrame(data).sort_values("KKD", ascending=False)
    
    # Top 3 Görsel
    if len(df) >= 3:
        cols = st.columns(3)
        colors = [('🥇', '#FFD700'), ('🥈', '#C0C0C0'), ('🥉', '#CD7F32')]
        for i in range(3):
            with cols[i]:
                row = df.iloc[i]
                st.markdown(f"""
                <div style="text-align:center; background:{colors[i][1]}; padding:15px; border-radius:10px;">
                    <h1>{colors[i][0]}</h1>
                    <h3>{row['Oyuncu']}</h3>
                    <h2>{row['KKD']}</h2>
                </div>
                """, unsafe_allow_html=True)
                
    st.subheader("📊 Detaylı Sıralama")
    st.dataframe(apply_simple_gradient(df, subset=['KKD']), use_container_width=True)