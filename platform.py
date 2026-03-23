import math
from datetime import datetime
import hashlib
import json
import os
import random

import pandas as pd
import streamlit as st

# =========================================================
# Page setup
# =========================================================
st.set_page_config(
    page_title="灵径智链 | 文化转译工作台",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# Theme / CSS
# =========================================================
BASE_CSS = """
<style>
:root {
  --bg:#f6f8fc;
  --card:#ffffff;
  --line:#e5e7eb;
  --text:#0f172a;
  --muted:#64748b;
  --blue:#2563eb;
  --cyan:#0ea5e9;
  --green:#059669;
  --soft:#eef6ff;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {background:var(--bg);}
.main .block-container {padding-top:1.2rem; padding-bottom:2rem; max-width:1180px;}
[data-testid="stSidebar"] {background:#fff; border-right:1px solid var(--line);}
.hero {
  background:linear-gradient(135deg,#0f172a 0%, #1d4ed8 45%, #0ea5e9 100%);
  color:#fff; border-radius:26px; padding:28px 30px; margin-bottom:18px;
  box-shadow:0 12px 30px rgba(37,99,235,.18);
}
.hero h1 {font-size:2.1rem; margin:0 0 .35rem 0; color:#fff;}
.hero p {margin:0; color:rgba(255,255,255,.88); line-height:1.65;}
.hero-badge {
  display:inline-block; padding:6px 12px; border-radius:999px; background:rgba(255,255,255,.14);
  margin-right:8px; font-size:.83rem; font-weight:700; border:1px solid rgba(255,255,255,.18);
}
.soft-card {
  background:var(--card); border:1px solid var(--line); border-radius:22px; padding:18px 20px;
  box-shadow:0 10px 24px rgba(15,23,42,.05); margin-bottom:14px;
}
.metric-card {
  background:var(--card); border:1px solid var(--line); border-radius:20px; padding:18px 18px; min-height:120px;
  box-shadow:0 8px 20px rgba(15,23,42,.04);
}
.metric-label {color:var(--muted); font-size:.9rem;}
.metric-value {font-size:2rem; font-weight:800; color:var(--text); margin-top:8px;}
.metric-note {margin-top:10px; font-size:.85rem; color:var(--blue);}
.section-title {font-size:1.18rem; font-weight:800; color:var(--text); margin-bottom:8px;}
.section-note {color:var(--muted); line-height:1.7;}
.module-card {
  background:linear-gradient(180deg,#fff 0%,#f8fbff 100%); border:1px solid var(--line); border-radius:22px;
  padding:20px; height:100%; box-shadow:0 10px 24px rgba(15,23,42,.04);
}
.module-title {font-size:1.15rem; font-weight:800; color:var(--text); margin-bottom:8px;}
.module-desc {color:var(--muted); line-height:1.7; min-height:78px;}
.chip {display:inline-block; padding:4px 10px; border-radius:999px; background:#eff6ff; color:#2563eb; font-size:.8rem; font-weight:700; margin:6px 8px 0 0;}
.notice {background:#f8fafc; border-left:4px solid var(--blue); padding:12px 14px; border-radius:12px; color:#334155;}
.ai-shell {
  background:#0f172a; color:#e2e8f0; border-radius:24px; padding:18px; border:1px solid rgba(148,163,184,.18);
}
.ai-topbar {
  display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:14px;
}
.ai-dot {width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:6px;}
.ai-window {
  background:#020617; border:1px solid rgba(148,163,184,.14); border-radius:18px; padding:16px; min-height:320px;
}
.prompt-box {
  background:#0b1220; border:1px solid rgba(148,163,184,.18); border-radius:14px; padding:12px 14px; color:#cbd5e1;
}
.result-box {
  background:#fff; border:1px solid var(--line); border-radius:18px; padding:18px; min-height:320px;
}
.small-tag {
  display:inline-block; padding:4px 10px; border-radius:999px; background:#ecfeff; color:#0f766e; font-size:.78rem; font-weight:700; margin-right:8px;
}
hr {border:none; border-top:1px solid #e5e7eb; margin: 12px 0 16px 0;}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# =========================================================
# Data
# =========================================================
COUNTRY_RISKS = pd.DataFrame([
    ["巴西", "高", "紫色、宗教联想、手势误读", 82],
    ["墨西哥", "高", "节庆语境、黄色死亡联想", 77],
    ["智利", "中", "疗愈宣传需谨慎", 56],
    ["哥伦比亚", "高", "宗教节日营销敏感", 68],
    ["阿根廷", "低", "玄学表达不宜过重", 35],
], columns=["国家", "风险等级", "关键风险", "风险分值"])

POLICY_SCENARIOS = pd.DataFrame([
    ["基准情境", 0, 6.90, 0.92],
    ["关税上调", 8, 6.90, 0.85],
    ["汇率波动", 0, 7.25, 0.88],
    ["双重压力", 8, 7.25, 0.80],
], columns=["情境", "关税变动%", "汇率", "转化系数"])

PRECHECK_ITEMS = pd.DataFrame([
    ["商业发票", "通过", "已补足品名、材质与申报价值"],
    ["装箱单", "通过", "箱规与重量一致"],
    ["品牌与图样权利", "待补充", "需商家上传授权说明"],
    ["清关敏感词", "预警", "疗愈相关表述需弱化效果承诺"],
    ["目标国限制", "通过", "当前 SKU 不涉及禁限运材质"],
], columns=["审查项", "状态", "说明"])

SAMPLE_PRODUCTS = {
    "工艺扇": {
        "position": "低价引流",
        "scene": "节庆、拍照、舞蹈配饰",
        "base_title": "中国古风折扇",
        "tone": "活泼、节庆、社交分享",
    },
    "香囊": {
        "position": "体验转译",
        "scene": "礼赠、空间香氛、节日祝福",
        "base_title": "中式香囊挂饰",
        "tone": "温和、礼赠、仪式感",
    },
    "汉服": {
        "position": "品牌溢价",
        "scene": "东方审美、内容传播、社交穿搭",
        "base_title": "中国风汉服套装",
        "tone": "高级、审美、品牌感",
    },
}

# =========================================================
# Helpers
# =========================================================
def nav_card(title: str, desc: str, badges=None):
    badges = badges or []
    chip_html = "".join([f'<span class="chip">{b}</span>' for b in badges])
    return f"""
    <div class="module-card">
        <div class="module-title">{title}</div>
        <div class="module-desc">{desc}</div>
        <div>{chip_html}</div>
    </div>
    """


def calc_profit(cost_cny, ship_usd, rate, tariff_pct, price_usd):
    ship_cny = ship_usd * rate
    total = cost_cny + ship_cny
    taxed_total = total * (1 + tariff_pct / 100)
    gross_profit = price_usd * rate - taxed_total
    gross_margin = 0 if price_usd * rate == 0 else gross_profit / (price_usd * rate)
    return round(taxed_total, 2), round(gross_profit, 2), round(gross_margin * 100, 1)


def qwen_style_copy(product, country, audience, scene, highlights, tone):
    seed = int(hashlib.md5(f"{product}{country}{audience}{scene}{highlights}{tone}".encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(seed)
    hooks = [
        "把东方美学翻译成当地消费者愿意点开的表达",
        "让高文化属性商品进入当地生活场景，而不是停留在异域标签",
        "把手作细节、礼赠意义与社交展示价值重新组织为可购买语言",
    ]
    opener = rnd.choice(hooks)
    highlight_list = [h.strip() for h in highlights.replace("，", ",").split(",") if h.strip()]
    if not highlight_list:
        highlight_list = ["手作细节", "礼赠属性", "东方氛围"]
    title = f"{country}市场｜{product} {scene}向本地化文案"
    bullets = [
        f"围绕“{scene}”场景，避免直译和过度异域化表达。",
        f"突出{highlight_list[0]}，让{audience}更容易理解商品价值。",
        f"语言风格保持{tone}，强调可送礼、可展示、可分享。",
    ]
    short_copy = (
        f"这不是简单把中文商品名翻译成西语或葡语，而是把 {product} 转化为 {country} 消费者能够理解的"
        f"生活场景表达。文案以“{scene}”为核心，突出{'、'.join(highlight_list[:3])}，"
        f"既保留东方审美，又降低文化误读风险。"
    )
    hero = f"{product}，用更懂 {country} 消费者的方式被看见"
    cta = f"先用文化转译改文案，再决定上架和定价"
    return {
        "title": title,
        "hook": opener,
        "bullets": bullets,
        "short_copy": short_copy,
        "hero": hero,
        "cta": cta,
        "audit": {
            "mode": "千问风格免配置演示",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "country": country,
            "audience": audience,
            "tone": tone,
        },
    }


# Optional real Qwen via env var only (no user-side API input needed)
def try_real_qwen(prompt: str):
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import requests
        resp = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-plus",
                "messages": [
                    {"role": "system", "content": "你是跨境电商中文案改写助手，擅长国潮商品在拉美市场的本地化表达。输出中文。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
            },
            timeout=40,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


# =========================================================
# Sidebar
# =========================================================
st.sidebar.markdown("### 灵径智链")
st.sidebar.caption("文化转译为核心 · 利润测算与合规预审为支撑")
page = st.sidebar.radio(
    "导航",
    ["平台总览", "文化转译中枢", "千问文案工坊", "ProfitLab 动态利润", "Puente 合规预审"],
    label_visibility="collapsed",
)
with st.sidebar.expander("当前版本说明", expanded=False):
    st.write("- 去除了 plotly 依赖，避免部署报错")
    st.write("- 文案工坊默认使用免配置的“千问风格演示模式”")
    st.write("- 若部署环境已配置 DASHSCOPE_API_KEY，会自动优先尝试真实千问接口")

# =========================================================
# Pages
# =========================================================
if page == "平台总览":
    st.markdown(
        """
        <div class="hero">
            <div>
                <span class="hero-badge">核心卖点：文化转译</span>
                <span class="hero-badge">支撑能力：动态利润 + 合规预审</span>
            </div>
            <h1>灵径智链：依托现有平台生态的跨文化运营工作台</h1>
            <p>不是另造一个 Temu 或 TikTok Shop，而是服务高文化属性、高附加值国潮商品，
            帮助商家在 Shopee、TikTok Shop、Amazon 等平台中完成文化转译、政策波动下的利润判断，以及发货前的合规数字化预审。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="metric-card"><div class="metric-label">核心能力权重</div><div class="metric-value">文化转译</div><div class="metric-note">作为首页首屏与主展示位</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card"><div class="metric-label">利润支撑</div><div class="metric-value">动态测算</div><div class="metric-note">响应关税、汇率与政策波动</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card"><div class="metric-label">交付支撑</div><div class="metric-value">预审协同</div><div class="metric-note">发货前发现清关与合规风险</div></div>', unsafe_allow_html=True)

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>平台能力结构：一核两翼</div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(nav_card("文化转译中枢", "围绕高文化属性商品的命名、卖点、页面场景与语义风险展开，是整个平台最核心的差异化能力。", ["核心卖点", "语义风控", "本地化表达"]), unsafe_allow_html=True)
    with g2:
        st.markdown(nav_card("ProfitLab 动态利润", "面对关税、汇率和平台规则波动，快速重算成本、利润和建议售价。", ["政策响应", "动态测算", "定价建议"]), unsafe_allow_html=True)
    with g3:
        st.markdown(nav_card("Puente 合规预审", "聚焦发货前的文件校核、风险提示和履约路径建议，而不是重资产全托管。", ["发货前预审", "清关协同", "风险留痕"]), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>为何不是‘大平台’，而是‘优质第三方运营插件’</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='notice'>
            灵径智链不直接争夺消费者流量，也不以低价工业品铺货为核心逻辑。它服务的是需要被重新讲述和重新包装的国潮商品，
            尤其适用于文创、非遗和疗愈类高文化属性商品，帮助商家在现有平台生态中实现更清晰的表达、更稳健的利润判断与更低风险的发货决策。
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("**样板 SKU 结构**")
        sku_df = pd.DataFrame([
            [k, v["position"], v["scene"]] for k, v in SAMPLE_PRODUCTS.items()
        ], columns=["样板商品", "验证角色", "核心场景"])
        st.dataframe(sku_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>五国文化风险热力</div>", unsafe_allow_html=True)
        st.bar_chart(COUNTRY_RISKS.set_index("国家")["风险分值"], height=280)
        st.caption("文化语义风控不是附属功能，而是本项目的首要竞争力。")
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "文化转译中枢":
    st.markdown("<div class='section-title'>文化转译中枢</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-note'>先解决‘当地人为什么不买账’，再谈投放、利润和发货。这里展示的是文化转译作为核心卖点的工作方式。</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.05, 1])
    with c1:
        product = st.selectbox("选择样板商品", list(SAMPLE_PRODUCTS.keys()))
        country = st.selectbox("目标国家", COUNTRY_RISKS["国家"].tolist())
        tone = st.selectbox("页面语气", ["礼赠感", "节庆感", "审美感", "轻疗愈感"])
        origin_name = st.text_input("原始中文商品名", SAMPLE_PRODUCTS[product]["base_title"])
        origin_selling = st.text_area("原始卖点", "国风、手作、传统元素，适合出海售卖。", height=120)
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown("**文化风险提示**")
        risk_row = COUNTRY_RISKS[COUNTRY_RISKS["国家"] == country].iloc[0]
        st.write(f"- 风险等级：**{risk_row['风险等级']}**")
        st.write(f"- 重点提醒：{risk_row['关键风险']}")
        st.write("- 建议：避免直译和抽象文化自嗨，优先翻译成礼赠、氛围、社交展示和生活场景。")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        translated_title = f"{country}市场版｜{product} · {SAMPLE_PRODUCTS[product]['scene']}表达"
        translated_points = [
            f"弱化‘传统’和‘古风’直译，改写成更贴近日常消费的 {SAMPLE_PRODUCTS[product]['scene']} 场景。",
            f"围绕 {tone} 组织主视觉和卖点层级，保留东方审美但避免文化隔膜。",
            "优先突出礼赠/搭配/展示用途，而不是抽象文化符号本身。",
        ]
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown("**转译后建议**")
        st.write(f"**建议标题**：{translated_title}")
        for item in translated_points:
            st.write(f"- {item}")
        st.write("**详情页主张**：让商品先进入当地生活，再进入当地购物车。")
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "千问文案工坊":
    st.markdown("<div class='section-title'>千问文案工坊（免配置）</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-note'>不需要手动输入 API。默认使用免配置的“千问风格演示模式”；如果部署环境已配置千问密钥，会自动尝试真实接口。</div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("<div class='ai-shell'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='ai-topbar'>
              <div>
                <span class='ai-dot' style='background:#fb7185'></span>
                <span class='ai-dot' style='background:#f59e0b'></span>
                <span class='ai-dot' style='background:#10b981'></span>
              </div>
              <div style='color:#94a3b8;font-size:.85rem;'>Lingjing Server Frontend · Qwen Copy Studio</div>
            </div>
            <div class='ai-window'>
            """,
            unsafe_allow_html=True,
        )
        product = st.selectbox("商品类型", list(SAMPLE_PRODUCTS.keys()), key="ai_product")
        country = st.selectbox("目标市场", COUNTRY_RISKS["国家"].tolist(), key="ai_country")
        audience = st.text_input("目标用户", "18-30岁喜欢社交分享和礼赠体验的年轻用户")
        scene = st.text_input("核心场景", SAMPLE_PRODUCTS[product]["scene"])
        highlights = st.text_input("希望突出的卖点（逗号分隔）", "东方美学,礼赠属性,手作细节")
        tone = st.selectbox("语气风格", ["轻盈温暖", "节庆活泼", "高级克制", "社交种草"], key="ai_tone")
        extra = st.text_area("补充指令", "请避免过度异域化表达，不要出现医疗疗效暗示。", height=110)
        st.markdown("<div class='prompt-box'>", unsafe_allow_html=True)
        st.caption("当前请求预览")
        st.code(
            f"商品={product}\n市场={country}\n用户={audience}\n场景={scene}\n卖点={highlights}\n语气={tone}\n附加要求={extra}",
            language="text",
        )
        if st.button("生成文案", use_container_width=True, type="primary"):
            prompt = f"为{country}市场的{product}生成本地化文案，用户是{audience}，场景是{scene}，卖点是{highlights}，语气是{tone}。要求：{extra}。输出标题、3条卖点、100字详情简介、封面标语。"
            real = try_real_qwen(prompt)
            if real:
                st.session_state["ai_output"] = {
                    "mode": "真实千问接口",
                    "raw": real,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            else:
                st.session_state["ai_output"] = qwen_style_copy(product, country, audience, scene, highlights, tone)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown("**生成结果**")
        out = st.session_state.get("ai_output")
        if not out:
            st.info("输入商品与市场信息后，点击“生成文案”。")
        elif "raw" in out:
            st.markdown(f"<span class='small-tag'>{out['mode']}</span>", unsafe_allow_html=True)
            st.write(out["raw"])
            st.caption(f"生成时间：{out['generated_at']}")
        else:
            st.markdown(f"<span class='small-tag'>{out['audit']['mode']}</span>", unsafe_allow_html=True)
            st.write(f"**建议标题**：{out['title']}")
            st.write(f"**文案切入点**：{out['hook']}")
            st.write("**卖点三条**")
            for b in out["bullets"]:
                st.write(f"- {b}")
            st.write("**详情页短文案**")
            st.write(out["short_copy"])
            st.write("**封面口号**")
            st.write(out["hero"])
            st.write("**行动引导**")
            st.write(out["cta"])
            st.caption(json.dumps(out["audit"], ensure_ascii=False, indent=2))
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "ProfitLab 动态利润":
    st.markdown("<div class='section-title'>ProfitLab：动态利润测算与政策响应</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-note'>不是静态计算器，而是围绕关税、汇率和政策波动快速重算成本与建议售价的经营支撑工具。</div>", unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        cost_cny = st.number_input("采购成本（人民币）", min_value=1.0, value=45.0, step=1.0)
        ship_usd = st.number_input("国际运费（美元）", min_value=0.1, value=1.8, step=0.1)
        rate = st.number_input("汇率（USD/CNY）", min_value=5.0, value=6.95, step=0.01)
        tariff = st.slider("关税/税费加成（%）", 0, 20, 6)
        price_usd = st.number_input("建议售价（美元）", min_value=1.0, value=16.9, step=0.1)
        total, gp, gm = calc_profit(cost_cny, ship_usd, rate, tariff, price_usd)
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("税后总成本", f"¥{total}")
        b.metric("单件毛利", f"¥{gp}")
        c.metric("毛利率", f"{gm}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        scenario_rows = []
        for _, row in POLICY_SCENARIOS.iterrows():
            sc_total, sc_gp, sc_gm = calc_profit(cost_cny, ship_usd, row["汇率"], tariff + row["关税变动%"], price_usd)
            scenario_rows.append([row["情境"], row["关税变动%"], row["汇率"], sc_total, sc_gp, sc_gm])
        scenario_df = pd.DataFrame(scenario_rows, columns=["情境", "额外关税%", "汇率", "税后总成本", "单件毛利", "毛利率%"])
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown("**政策波动情境测算**")
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
        st.caption("可用于模拟 2026 年拉美小额包裹税费调整、汇率波动等情境。")
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Puente 合规预审":
    st.markdown("<div class='section-title'>Puente：合规数字化预审与履约协同</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-note'>首阶段不讲“全托管”，而是聚焦货物发出前的材料校核、风险预警与路径建议。</div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        target_country = st.selectbox("目标国家", COUNTRY_RISKS["国家"].tolist(), key="pcountry")
        sku_type = st.selectbox("商品类型", list(SAMPLE_PRODUCTS.keys()), key="psku")
        st.write("**预审结果**")
        st.dataframe(PRECHECK_ITEMS, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
        st.markdown("**系统建议**")
        st.write("- 发货前补齐品牌与图样授权说明，避免知识产权争议。")
        st.write("- 弱化‘疗愈效果’等敏感词，用氛围、礼赠、空间体验替代表述。")
        st.write(f"- 针对 {target_country} 市场，优先采用保守申报与稳定履约路径。")
        st.write(f"- {sku_type} 当前更适合先做小样板测试，再逐步扩大投放。")
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("**模块定位说明**")
        st.write("Puente 的价值不在于重资产全托管，而在于通过数字化预审，把清关和行政风险尽量前置到发货前处理。")
        st.markdown("</div>", unsafe_allow_html=True)
