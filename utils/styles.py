# utils/styles.py
import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1d2e 100%); background-attachment: fixed; }
        h1 { color: #FFD700 !important; text-align: center; padding: 15px; border: 2px solid #FFD700; border-radius: 15px; background: linear-gradient(90deg, rgba(153,0,0,0.3) 0%, rgba(255,75,75,0.3) 100%); font-family: 'Arial Black', sans-serif; }
        h2, h3 { color: #ff4b4b !important; border-bottom: 3px solid #333; padding: 10px; background: rgba(30, 30, 40, 0.7); border-radius: 10px; }
        .stButton > button { width: 100% !important; background: linear-gradient(90deg, #990000 0%, #cc0000 100%) !important; color: white !important; border: 2px solid #FFD700 !important; border-radius: 10px !important; font-weight: bold !important; transition: all 0.3s ease !important; }
        .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 5px 15px rgba(255, 0, 0, 0.4) !important; }
        div[data-testid="stMetric"] { background: linear-gradient(135deg, #262730 0%, #363740 100%); border: 2px solid #444; border-radius: 15px; box-shadow: 0 6px 10px rgba(0,0,0,0.4); padding: 15px !important; }
        div[data-testid="stMetricValue"] { color: #FFD700 !important; font-size: 28px !important; font-weight: bold !important; }
        div[data-testid="stMetricLabel"] { color: #ff4b4b !important; font-weight: bold !important; }
        .stDataFrame { border: 2px solid #444 !important; border-radius: 10px !important; }
        .custom-card { background: linear-gradient(135deg, rgba(40, 40, 60, 0.9) 0%, rgba(30, 30, 50, 0.9) 100%); border-radius: 15px; padding: 20px; border: 2px solid #444; margin: 10px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.3); }
        .stats-card { background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 5px solid #ff4b4b; }
        /* Scrollbar */
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #1a1a2e; }
        ::-webkit-scrollbar-thumb { background: linear-gradient(45deg, #990000, #ff4b4b); border-radius: 10px; }
        /* Gizleme */
        header {visibility: hidden !important; height: 0 !important;}
        footer {visibility: hidden !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

def apply_simple_gradient(df, subset=None):
    def color_negative_red(val):
        try:
            num = float(val)
            if num < 0: return 'color: #ff6b6b; font-weight: bold;'
            elif num > 0: return 'color: #06d6a0; font-weight: bold;'
            return 'color: white;'
        except: return ''
    
    styled_df = df.style
    if hasattr(df, 'columns'):
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'float']: styled_df = styled_df.format({col: '{:.1f}'})
            elif df[col].dtype in ['int64', 'int32', 'int']: styled_df = styled_df.format({col: '{:.0f}'})
            
    if subset: styled_df = styled_df.applymap(color_negative_red, subset=subset)
    return styled_df