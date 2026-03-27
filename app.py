import streamlit as st
import pandas as pd
import urllib.parse
import requests
import io
import os
from datetime import datetime

# ============================================================================
# 1. 安全配置与模板定义
# ============================================================================
ACCESS_PASSWORD = "BK8VIP2026"

# 从 Secrets 获取敏感信息
SHORTIO_API_KEY = st.secrets.get("SHORTIO_API_KEY")
SHORTIO_DOMAIN = st.secrets.get("SHORTIO_DOMAIN", "vincent17.short.gy")

# --- 英文模板 ---
TEMPLATE_EN_LVL1 = "Subject: 💎 {username}, You’ve been handpicked for VIP Onboarding.\n\nHi {username}, don't leave your rewards to chance. We’ve handpicked Max, our VIP Guide, to help you navigate your account privileges and ensure you don't miss a single perk.\n\nConnect with Max here: 👉 {short_link}\n\nMax will personally walk you through how to fully utilize your new account status."
TEMPLATE_EN_HIGH = "Subject: 🏆 {username}, Your Private VIP Consultant is ready.\n\nDear {username}, a high-tier player needs a high-tier consultant. We have handpicked Max to be your direct point of contact for all strategic account moves.\n\nMessage Max for 1-on-1 guidance: 👉 {short_link}\n\nMax’s role is to ensure your loyalty is reflected in your rewards. Get expert guidance starting now."

# --- 日文模板 ---
TEMPLATE_JP_LVL1 = "Subject: 💎 {username}様、VIPオンボーディングの担当者に选出されました。\n\n{username}様、特典を逃す手はありません。アカウントの优待を最大限に活用し、すべての特典を确実にお受け取りいただくため、VIPガイドのMaxが贵方をサポートいたします。\n\nMaxへの联络はこちらから： 👉 {short_link}\n\nMaxが、新しいアカウントステータスの活用方法を个别にご案内いたします。"
TEMPLATE_JP_HIGH = "Subject: 🏆 {username}様、専属VIPコンサルタントのご准备が整いました。\n\n{username}様、ハイティアプレイヤーには、それに相応しいコンサルタントが必要です。戦略的なアカウント运用を直接サポートするため、専属担当としてMaxを選出いたしました。\n\n1対1の个别ガイダンスはこちら： 👉 {short_link}\n\nMaxの役割は、お客様のロイヤリティを确実に報酬へと反映させることです。今すぐ専门的なサポートをご利用ください。"

# ============================================================================
# 2. 核心逻辑函数
# ============================================================================

def clean_id(raw_id):
    """自动清洗 Telegram ID，只保留用户名部分"""
    if not raw_id: return ""
    text = raw_id.strip().replace("@", "")
    if "t.me/" in text:
        text = text.split("t.me/")[-1].split("?")[0]
    return text

def get_short_url(long_url):
    """调用 Short.io API"""
    if not SHORTIO_API_KEY: return long_url
    url = "https://api.short.io/links"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": SHORTIO_API_KEY
    }
    payload = {"originalURL": long_url, "domain": SHORTIO_DOMAIN}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return res.json().get('shortURL')
    except:
        pass
    return long_url

def process_row(row, manager_id):
    """处理每一行数据，生成短链和文案"""
    # 模糊匹配列名
    cols = {str(c).lower().strip(): c for c in row.index}
    def find_col(key):
        for k in cols:
            if key in k: return cols[k]
        return None

    user_key = find_col("user") or row.index[0]
    country_key = find_col("country")
    vip_key = find_col("vip")

    username = str(row[user_key]).strip()
    country = str(row.get(country_key, "other")).strip().lower()
    vip_level = str(row.get(vip_key, "Level 1")).strip()

    # 1. 构造 Telegram 链接 (客户点开后自动发出的消息)
    msg = f"Hi Max I need your assistance, my username is {username}"
    encoded_msg = urllib.parse.quote(msg)
    long_link = f"https://t.me/{manager_id}?text={encoded_msg}"
    
    # 2. 缩短
    short_link = get_short_url(long_link)
    
    # 3. 匹配文案模板
    is_lvl1 = "level 1" in vip_level.lower()
    if "japan" in country:
        template = TEMPLATE_JP_LVL1 if is_lvl1 else TEMPLATE_JP_HIGH
    else:
        template = TEMPLATE_EN_LVL1 if is_lvl1 else TEMPLATE_EN_HIGH
        
    content = template.format(username=username, short_link=short_link)
    return short_link, content

# ============================================================================
# 3. Streamlit UI 界面
# ============================================================================

def main():
    st.set_page_config(page_title="VIP Manager Tool", page_icon="💎", layout="wide")
    
    # 注入 CSS 视觉样式
    st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { background: linear-gradient(90deg, #4edea3, #3bc48a); color: black; font-weight: bold; border-radius: 10px; border: none; }
    .glass-card { background: rgba(255, 255, 255, 0.03); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

    # 登录逻辑
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 System Access")
        pwd = st.text_input("Enter Vault Key", type="password")
        if st.button("Access System"):
            if pwd == ACCESS_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Access Denied.")
        return

    # 主界面
    st.title("💎 VIP Link & Content Generator")
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            raw_manager_id = st.text_input("Manager Telegram ID", value="max_bkio", help="系统会自动清洗网址前缀")
            manager_id = clean_id(raw_manager_id)
            if manager_id: st.caption(f"✅ 链接将导向: t.me/{manager_id}")
        with c2:
            st.markdown("**功能状态检查：**")
            if SHORTIO_API_KEY: st.success("🟢 Short.io API 已连接")
            else: st.warning("🟡 未检测到 API Key，将生成原始长链接")
        st.markdown('</div>', unsafe_allow_html=True)

    # 文件上传
    file = st.file_uploader("上传客户名单 (Excel 或 CSV)", type=["xlsx", "csv"])
    
    if file:
        df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
        st.write("📊 数据预览 (前 3 行):")
        st.dataframe(df.head(3), use_container_width=True)

        if st.button("🚀 开始批量生成文案和短链接"):
            results = []
            bar = st.progress(0)
            status = st.empty()
            
            for i, (idx, row) in enumerate(df.iterrows()):
                status.text(f"正在处理: {i+1}/{len(df)}")
                short_url, content = process_row(row, manager_id)
                
                new_row = row.to_dict()
                new_row['Short_Link'] = short_url
                new_row['Invitation_Content'] = content
                results.append(new_row)
                bar.progress((i + 1) / len(df))
            
            res_df = pd.DataFrame(results)
            st.success("✨ 处理完成！")
            st.dataframe(res_df[['Short_Link', 'Invitation_Content']].head(), use_container_width=True)

            # 导出按钮
            csv = res_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 下载结果表格 (Excel 可用)",
                data=csv,
                file_name=f"VIP_Outreach_{datetime.now().strftime('%m%d')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
