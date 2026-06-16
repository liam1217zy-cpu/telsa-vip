import streamlit as st
import pandas as pd
import requests
import urllib.parse
import io
from typing import Optional, Dict, List

# ============================================================================
# CONFIGURATION
# ============================================================================
try:
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
    SHORTIO_API_KEY = st.secrets["SHORTIO_API_KEY"]
    SHORTIO_DOMAIN = st.secrets["SHORTIO_DOMAIN"]
except Exception:
    st.error("Missing Secrets in Streamlit Cloud!")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"

# ----------------------------------------------------------------------------
# 1. 客户点击链接后，手机里自动准备好的话 (简单直接)
# ----------------------------------------------------------------------------
FIXED_TEMPLATES = {
    "Option 1: New Registration": {
        "EN": "Hi {m_name}, I am {user}. Help me with my VIP status.",
        "JP": "こんにちは {m_name}、{user} です。VIP特典について詳しく教えてください。"
    },
    "Option 2: Retention": {
        "EN": "Hi {m_name}, I am {user}. I'm back! Please sync my VIP perks.",
        "JP": "{m_name}さん、お久しぶりです。{user}です。VIP特典を同期してください。"
    },
    "Option 3: Weekly Challenge": {
        "EN": "Hi {m_name}, I am {user}. I am interested in the Weekly Exclusive Challenge!",
        "JP": "こんにちは {m_name}、{user} です。ウィークリー限定チャレンジに興味があります！"
    }
}

# ----------------------------------------------------------------------------
# 2. 你发给客户的精美宣传文案 (每一项都配好，绝不删减)
# ----------------------------------------------------------------------------
OUTREACH_TEMPLATES = {
    "Option 1: New Registration": {
        "EN": "🌟 *Welcome to VIP Elite* 🌟\n\nHello {user}, your account is eligible for a VIP status upgrade! Get ready for exclusive perks and priority service.\n\n👇 *Claim your status here:* {short_link}",
        "JP": "🌟 *VIPエリートへようこそ* 🌟\n\n{user}様、あなたのアカウントはVIPステータスへのアップグレード対象です！特別な特典と優先サービスをご用意しております。\n\n👇 *こちらから申請してください:* {short_link}"
    },
    "Option 2: Retention": {
        "EN": "👋 *We Miss You, {user}!* 👋\n\nWelcome back! We've prepared a special reactivation bonus just for you. Let's get your VIP perks back on track.\n\n👇 *Sync your perks here:* {short_link}",
        "JP": "👋 *おかえりなさい、{user}様！* 👋\n\nお久しぶりです！{user}様のために特別なリアクティベーションボーナスをご用意しました。VIP特典を今すぐ再有効化しましょう。\n\n👇 *こちらから同期:* {short_link}"
    },
    "Option 3: Weekly Challenge": {
        "EN": (
            "🏆 *13 Apr - 20 May '26 | Weekly Exclusive Challenge*\n\n"
            "Hello {user}, here is your exclusive bonus acquisition:\n"
            "• Bet $51,000+ → **$70 Bonus**\n"
            "• Bet $101,000+ → **$150 Bonus**\n"
            "✨ Wager requirement: **x1 only**\n\n"
            "⚠️ *Terms and Conditions:*\n"
            "- No stacked promos.\n"
            "- Slots & Live Casino only.\n"
            "- Fast games/Originals excluded.\n\n"
            "👇 *Apply here:* {short_link}"
        ),
        "JP": (
            "🏆 *4月13日 - 5月20日 '26 | ウィークリー限定チャレンジ*\n\n"
            "{user}様、今週の限定特典のご案内です：\n"
            "・$51,000以上のベット → **$70ボーナス**\n"
            "・$101,000以上のベット → **$150ボーナス**\n"
            "✨ 賭け条件：**わずか1倍**\n\n"
            "⚠️ *利用規約:*\n"
            "- 他のプロモーションとの併用不可\n"
            "- スロット・ライブカジノのみ対象\n"
            "- ファストゲーム、オリジナルゲーム除外\n\n"
            "👇 *こちらから申請:* {short_link}"
        )
    }
}

# ============================================================================
# UI & HELPERS
# ============================================================================
def inject_ui():
    st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 100%, #f8fafc 0%, #ffffff 100%) !important; }
    .main-title { font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #f97316 0%, #22c55e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .glass-card { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(20px); border-radius: 20px; padding: 2rem; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 2rem; }
    .stButton>button { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important; color: white !important; border-radius: 10px !important; width: 100%; height: 3rem; font-weight: 700; border: none; }
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
    st.set_page_config(page_title="RX-0 VIP PRO", layout="wide")
    inject_ui()
    if 'auth' not in st.session_state: st.session_state.auth = False
    st.markdown('<h1 class="main-title">VIP shortlink generator</h1>', unsafe_allow_html=True)

    if not st.session_state.auth:
        pwd = st.text_input("System Key", type="password")
        if st.button("ACTIVATE"):
            if pwd == ACCESS_PASSWORD: st.session_state.auth = True; st.rerun()
        return

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🚀 Mode A: Batch Outreach Generator")
    
    a_col1, a_col2, a_col3 = st.columns([1, 1, 2])
    with a_col1:
        a_mid = st.text_input("TG ID", value="max_bkio")
        a_mname = st.text_input("Manager Name", value="Max")
    with a_col2:
        # 在下拉菜单里加上 "Custom: Write Your Own" 选项
        scen_options = list(FIXED_TEMPLATES.keys()) + ["Custom: Write Your Own"]
        a_scen = st.selectbox("Scenario", scen_options)
    with a_col3:
        a_file = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'])

    # 🌟 如果选了自定义内容，动态显示输入框
    custom_outreach = {"EN": "", "JP": ""}
    custom_reply = {"EN": "", "JP": ""}
    
    if a_scen == "Custom: Write Your Own":
        st.markdown("---")
        st.markdown("### ✍️ Edit Custom Templates")
        st.caption("Available variables: `{user}` , `{m_name}` , `{short_link}` (Only for outreach)")
        
        c_tab1, c_tab2 = st.tabs(["🇺🇸 English Template", "🇯🇵 Japanese Template"])
        with c_tab1:
            custom_outreach["EN"] = st.text_area("Outreach Message (EN)", value="Hello {user}, this is your custom offer!\n\nApply here: {short_link}", height=120)
            custom_reply["EN"] = st.text_input("Client Auto-Reply (EN)", value="Hi {m_name}, I am {user}. I want to claim the custom offer.")
        with c_tab2:
            custom_outreach["JP"] = st.text_area("Outreach Message (JP)", value="{user}様、こちらはカスタム特典のご案内です！\n\n申請はこちら: {short_link}", height=120)
            custom_reply["JP"] = st.text_input("Client Auto-Reply (JP)", value="こんにちは {m_name}、{user} です。カスタム特典を申請します。")

    if a_file:
        df = pd.read_excel(a_file) if a_file.name.endswith('xlsx') else pd.read_csv(a_file)
        st.info("Confirm Column Mapping:")
        c1, c2 = st.columns(2)
        with c1: u_col = st.selectbox("Username Column", df.columns, index=0)
        with c2:
            def_idx = 0
            for i, col in enumerate(df.columns):
                if 'country' in col.lower(): def_idx = i; break
            c_col = st.selectbox("Country Column", df.columns, index=def_idx)

        if st.button("GENERATE CAMPAIGN"):
            results = []
            for _, row in df.iterrows():
                user = str(row.get(u_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                
                # 强化国家和语言逻辑
                country_val = str(row.get(c_col, "")).upper().strip()
                lang = "JP" if ("JP" in country_val or "JAPAN" in country_val) else "EN"
                
                # 判断并抓取对应的文案数据
                if a_scen == "Custom: Write Your Own":
                    raw_reply = custom_reply[lang]
                    raw_outreach = custom_outreach[lang]
                else:
                    raw_reply = FIXED_TEMPLATES[a_scen][lang]
                    raw_outreach = OUTREACH_TEMPLATES[a_scen][lang]

                # 1. 客户跳转后的回复
                cust_reply = raw_reply.format(m_name=a_mname, user=user)
                long_url = f"https://t.me/{a_mid}?text={urllib.parse.quote(cust_reply)}"
                short_link = shorten_url(long_url)
                
                # 2. 发给客户的精美宣传文案
                outreach_msg = raw_outreach.format(user=user, short_link=short_link)

                results.append({
                    "Username": user,
                    "Country": country_val,
                    "Language": lang,
                    "Message to Copy (To Client)": outreach_msg,
                    "Short Link": short_link
                })
            
            st.success(f"Success! Processed {len(results)} users.")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
