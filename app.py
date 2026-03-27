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
    st.error("Missing Secrets! Please configure ACCESS_PASSWORD, SHORTIO_API_KEY, and SHORTIO_DOMAIN.")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"

# 自动文案模板 (与之前一致)
CONTENT_TEMPLATES = {
    "Option 1: New Registration": {
        "EN": {
            "subject": "💎 {username}, You’ve been handpicked for VIP Onboarding.",
            "body": "Hi {username}, don't leave your rewards to chance. We’ve handpicked {m_name}, our VIP Guide, to help you navigate your account privileges and ensure you don't miss a single perk.\n\nConnect with {m_name} here: 👉 {short_link}\n\n{m_name} will personally walk you through how to fully utilize your new account status."
        },
        "JP": {
            "subject": "💎 {username}様、VIPオンボーディングの担当に選出されました。",
            "body": "{username}様、特典を逃さないでください。専属ガイドの{m_name}が、アカウントの特権を最大限に活用できるようサポートいたします。\n\nこちらから{m_name}に連絡してください：👉 {short_link}\n\n{m_name}が、新しいアカウントステータスの活用方法を個別にご案内いたします。"
        }
    },
    "Option 2: Retention": {
        "EN": {
            "subject": "💎 Welcome back {username}! Your VIP status is waiting.",
            "body": "Hi {username}, we missed you! {m_name} is ready to sync your account privileges and provide the latest standby links.\n\nReconnect with {m_name} here: 👉 {short_link}\n\n{m_name} will ensure your account is fully optimized for your return."
        },
        "JP": {
            "subject": "💎 {username}様、お帰りなさい！VIPステータスが待機中です。",
            "body": "{username}様、お久しぶりです！{m_name}がアカウント特典の同期と最新の予備リンクをご案内いたします。\n\nこちらから{m_name}に再接続してください：👉 {short_link}\n\n{m_name}が、お客様の復帰に合わせてアカウントを最適化いたします。"
        }
    }
}

# ============================================================================
# UI: UNICORN GUNDAM THEME
# ============================================================================
def inject_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
    .stApp { background: radial-gradient(circle at 50% 100%, #f8fafc 0%, #ffffff 100%) !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
    .main-title { font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #f97316 0%, #22c55e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; filter: drop-shadow(0 0 10px rgba(34, 197, 94, 0.2)); }
    .glass-card { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(25px); border-radius: 30px; padding: 2rem; border: 2px solid; border-image: linear-gradient(135deg, #f97316, #22c55e) 1; box-shadow: 0 20px 40px rgba(0,0,0,0.05); margin-top: 1rem; }
    .stButton>button { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important; color: white !important; font-weight: 700 !important; border-radius: 15px !important; border: none !important; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(34, 197, 94, 0.3) !important; }
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent !important; border-radius: 10px; font-weight: 700; color: #64748b; }
    .stTabs [aria-selected="true"] { color: #16a34a !important; border-bottom: 3px solid #16a34a !important; }
    </style>
    """, unsafe_allow_html=True)

def shorten_url(long_url: str) -> Tuple[Optional[str], Optional[str]]:
    headers = {"Authorization": SHORTIO_API_KEY, "Content-Type": "application/json"}
    payload = {"domain": SHORTIO_DOMAIN, "originalURL": long_url}
    try:
        response = requests.post(SHORTIO_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code in [200, 201]: return response.json().get("shortURL"), None
        return None, f"Error {response.status_code}"
    except Exception as e: return None, str(e)

# ============================================================================
# MAIN
# ============================================================================
def main():
    st.set_page_config(page_title="RX-0 VIP PRO", layout="centered")
    inject_ui()
    
    if 'auth' not in st.session_state: st.session_state.auth = False
    st.markdown('<h1 class="main-title">VIP RX-0 [PRO]</h1>', unsafe_allow_html=True)

    if not st.session_state.auth:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        pwd = st.text_input("Unlock System", type="password")
        if st.button("ACTIVATE"):
            if pwd == ACCESS_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Denied.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 使用 Tabs 分开两个功能
    tab1, tab2 = st.tabs(["🚀 Batch Generation (Auto)", "✍️ Manual Content (No Link)"])

    # --- TAB 1: 批量自动生成 ---
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            m_id = st.text_input("Telegram ID", value="max_bkio", key="auto_tid")
            m_name = st.text_input("Manager Name", value="Max", key="auto_mname")
        with c2:
            scenario = st.selectbox("Scenario", list(CONTENT_TEMPLATES.keys()))
            file = st.file_uploader("Upload File", type=['csv', 'xlsx'])

        if st.button("EXECUTE BATCH"):
            if not file: st.warning("Upload file first."); st.stop()
            df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            user_col = next((c for c in df.columns if 'username' in c.lower()), None)
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            
            results = []
            for _, row in df.iterrows():
                user = str(row.get(user_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                country = str(row.get(country_col, "")).upper() if country_col else "EN"
                lang = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                
                # Link Logic
                tg_msg = f"Hi {m_name}, I am {user}." if lang == "EN" else f"こんにちは {m_name}、{user} です。"
                long_url = f"https://t.me/{m_id}?text={urllib.parse.quote(tg_msg)}"
                short_link, _ = shorten_url(long_url)
                
                template = CONTENT_TEMPLATES[scenario][lang]
                results.append({
                    "Username": user,
                    "Short Link": short_link,
                    "Full Content": template["body"].format(username=user, m_name=m_name, short_link=short_link)
                })
            st.dataframe(pd.DataFrame(results))
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: 手动模式 (内容自定义, 无 Short.io) ---
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ✍️ Custom Content Generator")
        
        mc1, mc2 = st.columns(2)
        with mc1:
            u_name = st.text_input("Customer Username", placeholder="e.g. Jacky777")
            man_name = st.text_input("Manager Name", value="Max")
        with mc2:
            m_lang = st.radio("Language Mode", ["English 🌍", "Japanese 🇯🇵"], horizontal=True)
            custom_note = st.text_area("Custom Message / Note", placeholder="Enter your custom message here...")

        if st.button("GENERATE MANUAL CONTENT"):
            if not u_name:
                st.error("Please enter a Username.")
            else:
                lang_key = "JP" if "Japanese" in m_lang else "EN"
                # 手动生成的逻辑 (简单拼装)
                if lang_key == "EN":
                    final_msg = f"Subject: 💎 Important Update for {u_name}\n\nHi {u_name},\n\n{custom_note}\n\nBest regards,\n{man_name}"
                else:
                    final_msg = f"件名: 💎 {u_name}様への重要なお知らせ\n\n{u_name}様、\n\n{custom_note}\n\n宜しくお願いいたします。\n{man_name}"
                
                st.code(final_msg, language="text")
                st.info("Copy the content above for your manual reachout.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p style='text-align:center; color:#cbd5e1; margin-top:2rem;'>RX-0 PSYCHO-FRAME SYSTEM v4.0</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
