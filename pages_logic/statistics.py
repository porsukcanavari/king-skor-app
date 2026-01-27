# pages_logic/statistics.py
import streamlit as st
import pandas as pd
from utils.stats import istatistikleri_hesapla
from utils.styles import apply_simple_gradient

def stats_interface():
    st.markdown("<h2>📊 İstatistik Merkezi</h2>", unsafe_allow_html=True)
    stats, match_hist, _, id_map = istatistikleri_hesapla()
    
    if not stats:
        st.warning("Veri yok.")
        return

    tabs = st.tabs(["🔥 Seriler", "🏆 Genel", "📜 Arşiv"])
    
    rows = []
    for uid, s in stats.items():
        if s['mac_sayisi'] > 0:
            s['Oyuncu'] = id_map.get(uid, f"?{uid}")
            rows.append(s)
    df_main = pd.DataFrame(rows).set_index("Oyuncu")

    with tabs[0]:
        st.subheader("🔥 En İyi Seriler")
        st.dataframe(df_main[['max_win_streak', 'win_streak', 'max_loss_streak']].sort_values('max_win_streak', ascending=False), use_container_width=True)

    with tabs[1]:
        st.subheader("🏆 Genel Tablo")
        cols = ['mac_sayisi', 'pozitif_mac_sayisi', 'toplam_puan', 'toplam_ceza_puani', 'king_sayisi']
        st.dataframe(apply_simple_gradient(df_main[cols]), use_container_width=True)
        
    with tabs[2]:
        st.subheader("📜 Maç Geçmişi")
        if match_hist:
            sel_match = st.selectbox("Maç Seç:", [m['baslik'] for m in match_hist[::-1]])
            found = next((m for m in match_hist if m['baslik'] == sel_match), None)
            if found:
                scores = []
                for sc in found['skorlar']:
                    r = {'OYUN': sc[0]}
                    for i, p in enumerate(found['ids']):
                        if i+1 < len(sc): r[id_map.get(p)] = sc[i+1]
                    scores.append(r)
                st.dataframe(pd.DataFrame(scores), use_container_width=True)