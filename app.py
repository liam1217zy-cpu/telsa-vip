import streamlit as st
import pandas as pd
import requests
import urllib.parse
import io
import time
from typing import Optional, Dict, List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================
try:
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
    SHORTIO_API_KEY = st.secrets["SHORTIO_API_KEY"]
    SHORTIO_DOMAIN = st.secrets["SHORTIO_DOMAIN"]
except Exception:
    st.error("Missing Secrets!")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"

# 第一个功能的固定模板
FIXED_TEMPLATES = {
    "Option 1: New Registration": {
        "EN": "Hi {m_name}, I am {user}. Help me with my VIP status.",
        "JP": "こんにちは {m_name}、{user} です。VIP特典について詳しく教えてください。"
    },
    "Option 2: Retention": {
        "EN": "Hi {m_name}, I am {user}. I'm back! Please sync my VIP perks.",
        "JP": "{m_name}さん、お久しぶりです。{user}です。VIP特典を同期してください。"
    }
}

# ============================================================================
# UI & LOGIC
# ============================================================================
def inject_ui():
    st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 100%, #f8fafc 0%, #ffffff 100%) !important; }
    .main-title { font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #f97316 0%, #22c55e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .glass-card { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(20px); border-radius: 25px; padding: 2rem; border: 2px solid; border-image: linear-gradient(135deg, #f97316, #22c55e) 1; box-shadow: 0 15px 35px rgba(0,0,0,0.05); margin-bottom: 2rem; }
    .stButton>button { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important; color: white !important; border-radius: 12px !important; width: 100%; height: 3rem; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

def shorten_url(long_url: str) -> str:
    headers = {"Authorization": SHORTIO_API_KEY, "Content-Type": "application/json"}
    payload = {"domain": SHORTIO_DOMAIN, "originalURL": long_url}
    try:
        res = requests.post(SHORTIO_API_URL, headers=headers, json=payload, timeout=10)
        return res.json().get("shortURL", "Error")
    except: return "Error"

def main():
    st.set_page_config(page_title="RX-0 VIP PRO", layout="centered")
    inject_ui()
    
    if 'auth' not in st.session_state: st.session_state.auth = False
    st.markdown('<h1 class="main-title">VIP RX-0 [DUAL-CORE]</h1>', unsafe_allow_html=True)

    if not st.session_state.auth:
        pwd = st.text_input("System Key", type="password")
        if st.button("ACTIVATE"):
            if pwd == ACCESS_PASSWORD: st.session_state.auth = True; st.rerun()
        return

    # ------------------------------------------------------------------------
    # 功能 1: 批量自动模板 (Fixed Template)
    # ------------------------------------------------------------------------
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🚀 Mode A: Batch Auto-Template")
    st.caption("使用预设的固定文案（New Reg / Retention）生成链接。")
    
    a_col1, a_col2 = st.columns(2)
    with a_col1:
        a_mid = st.text_input("TG ID", value="max_bkio", key="a_mid")
        a_mname = st.text_input("Manager Name", value="Max", key="a_mname")
    with a_col2:
        a_scen = st.selectbox("Scenario", list(FIXED_TEMPLATES.keys()), key="a_scen")
        a_file = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'], key="a_file")

    if st.button("EXECUTE MODE A"):
        if a_file:
            df = pd.read_excel(a_file) if a_file.name.endswith('xlsx') else pd.read_csv(a_file)
            user_col = next((c for c in df.columns if 'username' in c.lower()), None)
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            
            results = []
            for _, row in df.iterrows():
                user = str(row.get(user_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                country = str(row.get(country_col, "")).upper() if country_col else "EN"
                lang = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                
                # 调用固定模板
                raw_msg = FIXED_TEMPLATES[a_scen][lang].format(m_name=a_mname, user=user)
                long_url = f"https://t.me/{a_mid}?text={urllib.parse.quote(raw_msg)}"
                short_link = shorten_url(long_url)
                results.append({"Username": user, "Country": country, "Short Link": short_link})
            
            st.dataframe(pd.DataFrame(results))
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # 功能 2: 批量自定义内容 (Custom Content)
    # ------------------------------------------------------------------------
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("✍️ Mode B: Batch Custom Content")
    st.caption("自定义客人点击链接后会说的话。必须包含 {username}。")
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        b_mid = st.text_input("TG ID", value="max_bkio", key="b_mid")
        b_mname = st.text_input("Manager Name", value="Max", key="b_mname")
    with b_col2:
        b_file = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'], key="b_file")

    # 自定义文案输入区
    st.markdown("**Define what the CUSTOMER will say:**")
    custom_en = st.text_area("English Message (Global)", value="Hi {m_name}, my name is {username}. I am interested in...")
    custom_jp = st.text_area("Japanese Message (Japan)", value="こんにちは {m_name}、{username} です。興味があります...")

    if st.button("EXECUTE MODE B"):
        if b_file:
            df = pd.read_excel(b_file) if b_file.name.endswith('xlsx') else pd.read_csv(b_file)
            user_col = next((c for c in df.columns if 'username' in c.lower()), None)
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            
            results_b = []
            for _, row in df.iterrows():
                user = str(row.get(user_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                country = str(row.get(country_col, "")).upper() if country_col else "EN"
                lang = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                
                # 使用你在网页上输入的自定义内容
                raw_text = custom_jp if lang == "JP" else custom_en
                final_msg = raw_text.replace("{username}", user).replace("{m_name}", b_mname)
                
                long_url = f"https://t.me/{b_mid}?text={urllib.parse.quote(final_msg)}"
                short_link = shorten_url(long_url)
                results_b.append({"Username": user, "Country": country, "Short Link": short_link})
            
            st.success("Custom Batch Done!")
            st.dataframe(pd.DataFrame(results_b))
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
