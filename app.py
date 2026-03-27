import streamlit as st
import pandas as pd
import requests
import urllib.parse
import io
import time
from typing import Optional, Dict, List, Tuple

# ============================================================================
# 安全配置：从 Streamlit Secrets 读取 (不公开在代码中)
# ============================================================================
ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
SHORTIO_API_KEY = st.secrets["SHORTIO_API_KEY"]
SHORTIO_DOMAIN = st.secrets["SHORTIO_DOMAIN"]
SHORTIO_API_URL = "https://api.short.io/links"

DEFAULT_MANAGER_ID = "max_bkio"
DEFAULT_MANAGER_NAME = "Max"

# 场景话术模板
SCENARIO_TEMPLATES = {
    "Option 1: 刚注册未入金 (New Reg)": {
        "CN": "你好 {manager_name}，我是 {username}。我已经开户了，请帮我确认一下我的账号是否已经开启了 VIP 快速通道，以及目前最稳的入金方式。",
        "EN": "Hello {manager_name}, I am {username}. I've opened an account. Please help confirm if my account has VIP priority access enabled and the most stable deposit method currently.",
        "JP": "こんにちは {manager_name}、{username} です。口座を開設しました。私のカウントが VIP 優先アクセスに対応しているかと、現在最も安定した入金方法を確認してください。"
    },
    "Option 2: 唤回老客户 (Retention)": {
        "CN": "你好 {manager_name}，我是 {username}。好久没上线了，请帮我检查一下账号状态是否正常，顺便同步一下现在的最新备用网址。",
        "EN": "Hello {manager_name}, I am {username}. I haven't been online for a while. Please help check if my account status is normal and provide the latest alternative URLs.",
        "JP": "こんにちは {manager_name}、{username} です。久しぶりにログインしました。アカウントの状態が正常かどうかを確認し、最新の予備 URL を教えてください。"
    }
}

# ============================================================================
# UI & UTILS
# ============================================================================
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    :root { --surface: #0b1326; --primary: #4edea3; --on-surface: #dae2fd; }
    .stApp { background: var(--surface) !important; font-family: 'Inter', sans-serif !important; }
    .display-title { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, var(--primary) 0%, var(--on-surface) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1rem; }
    .glass-panel { background: rgba(19, 27, 46, 0.8); backdrop-filter: blur(10px); border-radius: 1rem; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

def shorten_url(long_url: str) -> Tuple[Optional[str], Optional[str]]:
    headers = {"Authorization": SHORTIO_API_KEY, "Content-Type": "application/json"}
    payload = {"domain": SHORTIO_DOMAIN, "originalURL": long_url}
    try:
        response = requests.post(SHORTIO_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code in [200, 201]:
            return response.json().get("shortURL"), None
        return None, f"Error {response.status_code}"
    except Exception as e:
        return None, str(e)

def main():
    st.set_page_config(page_title="VIP Link Gen", page_icon="💎")
    inject_custom_css()
    
    if 'auth' not in st.session_state: st.session_state.auth = False
    st.markdown('<div class="display-title">VIP Deep-Link Tool</div>', unsafe_allow_html=True)

    if not st.session_state.auth:
        pwd = st.text_input("Access Key", type="password")
        if st.button("Unlock"):
            if pwd == ACCESS_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Key Error")
        return

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        m_id = st.text_input("Telegram ID", value=DEFAULT_MANAGER_ID)
        m_name = st.text_input("Manager Name", value=DEFAULT_MANAGER_NAME)
    with c2:
        scenario = st.selectbox("Scenario", list(SCENARIO_TEMPLATES.keys()))
        lang = st.selectbox("Language", ["CN", "EN", "JP"])
    
    file = st.file_uploader("Upload File (CSV/XLSX)", type=['csv', 'xlsx'])
    
    if file and st.button("🚀 Run"):
        df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
        user_col = next((c for c in df.columns if 'username' in c.lower()), None)
        
        if user_col:
            results = []
            p_bar = st.progress(0)
            usernames = df[user_col].dropna().tolist()
            
            for idx, user in enumerate(usernames):
                msg = SCENARIO_TEMPLATES[scenario][lang].format(manager_name=m_name, username=str(user))
                long_url = f"https://t.me/{m_id}?text={urllib.parse.quote(msg)}"
                short_url, err = shorten_url(long_url)
                
                results.append({"Username": user, "Short Link": short_url or "Error", "Status": "OK" if short_url else err})
                p_bar.progress((idx + 1) / len(usernames))
                time.sleep(0.05)

            res_df = pd.DataFrame(results)
            st.dataframe(res_df)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res_df.to_excel(writer, index=False)
            st.download_button("📥 Download", output.getvalue(), "links.xlsx")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()