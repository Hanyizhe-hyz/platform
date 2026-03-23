import math
from io import BytesIO
from datetime import datetime
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import requests


# =========================================================
# Page setup
# =========================================================
st.set_page_config(
    page_title="灵径智链 | LatAm Cross-border SaaS",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# Demo data
# =========================================================
CULTURAL_RISK_DATA = [
    {
        "code": "BR",
        "country": "巴西",
        "country_en": "Brazil",
        "risk_level": "高风险",
        "risk_tag": "HIGH",
        "colors": ["紫色", "绿色"],
        "color_hex": ["#7E3AF2", "#16A34A"],
        "religious_items": 3,
        "marketing_items": 3,
        "notes": "紫色与葬礼语境关联度较高；部分手势表达需避免误读。",
        "suggestion": "视觉设计避免大面积紫色，强调节庆、手作和礼赠场景。",
        "platforms": "Shopee BR / TikTok Shop BR",
        "risk_score": 82,
    },
    {
        "code": "MX",
        "country": "墨西哥",
        "country_en": "Mexico",
        "risk_level": "高风险",
        "risk_tag": "HIGH",
        "colors": ["黄色", "红色"],
        "color_hex": ["#FACC15", "#DC2626"],
        "religious_items": 3,
        "marketing_items": 3,
        "notes": "黄色在部分场景里与死亡意象相关；节庆语境与日常营销需区分。",
        "suggestion": "适合做节庆限定或文化说明强化型页面，避免直白冲突表达。",
        "platforms": "Amazon MX / TikTok Shop MX",
        "risk_score": 77,
    },
    {
        "code": "AR",
        "country": "阿根廷",
        "country_en": "Argentina",
        "risk_level": "低风险",
        "risk_tag": "LOW",
        "colors": ["黑色", "橙色"],
        "color_hex": ["#111827", "#F97316"],
        "religious_items": 3,
        "marketing_items": 3,
        "notes": "数字 13、部分占卜式表达会触发不吉利联想。",
        "suggestion": "用工艺、礼赠、节日审美做包装，避免玄学色彩过重。",
        "platforms": "Mercado Libre / Tiendanube",
        "risk_score": 35,
    },
    {
        "code": "CL",
        "country": "智利",
        "country_en": "Chile",
        "risk_level": "中风险",
        "risk_tag": "MEDIUM",
        "colors": ["金色", "紫色"],
        "color_hex": ["#EAB308", "#8B5CF6"],
        "religious_items": 2,
        "marketing_items": 3,
        "notes": "礼赠表达接受度高，但保健、疗愈等宣称需谨慎。",
        "suggestion": "更适合空间香氛、仪式感礼盒与轻疗愈叙事。",
        "platforms": "Falabella / Mercado Libre",
        "risk_score": 56,
    },
    {
        "code": "CO",
        "country": "哥伦比亚",
        "country_en": "Colombia",
        "risk_level": "高风险",
        "risk_tag": "HIGH",
        "colors": ["绿色", "蓝灰"],
        "color_hex": ["#22C55E", "#64748B"],
        "religious_items": 2,
        "marketing_items": 3,
        "notes": "宗教节日营销敏感；过度神秘化表达容易偏离消费语境。",
        "suggestion": "建议聚焦设计感、工艺感与社交展示，不突出神秘暗示。",
        "platforms": "Mercado Libre / Instagram Shop",
        "risk_score": 68,
    },
]

CATEGORY_POSITIONING = {
    "工艺扇": {
        "定位": "低价引流款",
        "建议": "强调东方符号、视觉冲击和节庆搭配，用 10 美元以下试错价快速转化。",
        "页面表达": "夏日、节庆、舞蹈配饰、拍照道具",
    },
    "香囊": {
        "定位": "文化体验款",
        "建议": "强调礼赠、空间香氛与疗愈氛围，避免医疗疗效式宣传。",
        "页面表达": "礼物、空间香氛、节日祝福、手作体验",
    },
    "汉服": {
        "定位": "品牌溢价款",
        "建议": "强调东方美学、社交展示与内容传播，适合高客单与长尾利润。",
        "页面表达": "节庆穿搭、Cosplay、东方审美、品牌故事",
    },
}

ORDER_DF = pd.DataFrame(
    [
        ["PUENTE-MEX-2024-00123", "墨西哥城", "已送达", "2024-01-15", "2024-01-30", "2024-01-29", 100, 89],
        ["PUENTE-MEX-2024-00124", "蒙特雷", "运输中", "2024-01-18", "2024-02-02", "—", 33, 45],
        ["PUENTE-CHL-2024-00089", "圣地亚哥", "清关中", "2024-01-20", "2024-02-05", "—", 60, 210],
        ["PUENTE-PER-2024-00045", "利马", "已发货", "2024-01-22", "2024-02-08", "—", 15, 32],
        ["PUENTE-MEX-2024-00125", "瓜达拉哈拉", "运输中", "2024-01-25", "2024-02-10", "—", 22, 120],
    ],
    columns=["订单号", "目的地", "状态", "发货日期", "预计送达", "实际送达", "进度", "货值(USD)"],
)

TRACKING_STEPS = [
    {"title": "揽收入库", "place": "深圳仓库", "time": "01-15 09:30", "desc": "包裹已接收并完成扫描"},
    {"title": "国际起飞", "place": "香港国际机场", "time": "01-16 14:20", "desc": "国际航班起飞"},
    {"title": "目的国抵达", "place": "墨西哥城 MEX 机场", "time": "01-18 08:45", "desc": "到达目的国并进入预审"},
    {"title": "清关审核", "place": "墨西哥海关", "time": "01-19 10:15", "desc": "文件完整性通过，进入人工复核"},
    {"title": "末端派送", "place": "墨西哥城配送站", "time": "01-21 18:10", "desc": "本地承运人接单"},
    {"title": "签收完成", "place": "墨西哥城", "time": "01-29 11:20", "desc": "客户签收完成"},
]

DESTINATION_POINTS = pd.DataFrame(
    {
        "国家": ["墨西哥", "智利", "秘鲁", "哥伦比亚", "巴西"],
        "城市": ["墨西哥城", "圣地亚哥", "利马", "波哥大", "圣保罗"],
        "lat": [19.4326, -33.4489, -12.0464, 4.7110, -23.5505],
        "lon": [-99.1332, -70.6693, -77.0428, -74.0721, -46.6333],
        "订单": [156, 89, 67, 45, 32],
    }
)

CUSTOMS_REQUIRED_DOCS = [
    ("商业发票", "已验证", "invoice"),
    ("装箱单", "已验证", "packing"),
    ("原产地证明", "建议补充", "origin"),
    ("运输保险单", "缺失", "insurance"),
    ("进口许可证", "已验证", "permit"),
]

DEFAULT_SKUS = [
    {"SKU": "SKU-A", "运费(USD)": 1.3, "汇率": 6.85, "采购成本": 45.0, "售价": 120.0, "固定成本": 5000.0},
    {"SKU": "SKU-B", "运费(USD)": 2.0, "汇率": 6.85, "采购成本": 38.0, "售价": 99.0, "固定成本": 4000.0},
]

PLATFORMS = ["Shopify", "Magento", "WooCommerce", "美客多 API", "亚马逊 SP-API", "TikTok Shop"]


# =========================================================
# Styling helpers
# =========================================================
def apply_base_css(dark: bool = False):
    if dark:
        css = """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #020817;
            color: #dbeafe;
        }
        [data-testid="stSidebar"] {
            background: #071226;
            border-right: 1px solid rgba(56, 189, 248, 0.15);
        }
        .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        h1, h2, h3, h4, p, label, div, span { color: #dbeafe; }
        .sidebar-title {font-size: 1.3rem; font-weight: 800; color:#22d3ee; margin-bottom:0.25rem;}
        .sidebar-subtitle {font-size: 0.82rem; color:#7dd3fc; opacity:0.85;}
        .hero-title {font-size: 2.0rem; font-weight: 800; color: #22d3ee; margin-bottom: 0.2rem;}
        .hero-subtitle {color: #93c5fd; margin-bottom: 0.9rem;}
        .kpi-ribbon {background: linear-gradient(135deg, #031126, #071d3a); border:1px solid rgba(34,211,238,.18); border-radius:18px; padding:12px 18px; margin-bottom:18px;}
        .kpi-card {background: linear-gradient(180deg, rgba(2,8,23,.9), rgba(2,20,39,.95)); border:1px solid rgba(34,211,238,.18); border-radius:18px; padding:16px 18px; min-height:118px;}
        .kpi-label {font-size:0.8rem; letter-spacing:.08em; text-transform:uppercase; color:#7dd3fc; opacity:0.8;}
        .kpi-value {font-size:2.0rem; font-weight:800; color:#00f5a0; margin-top:10px;}
        .kpi-help {font-size:0.92rem; color:#60a5fa;}
        .section-shell {background:#020c1d; border:1px solid rgba(34,211,238,.12); border-radius:18px; padding:16px 18px; margin-top: 10px;}
        .mini-chip {display:inline-block; padding:4px 10px; border-radius:999px; font-size:.82rem; border:1px solid rgba(34,211,238,.18); margin-right:8px; color:#93c5fd;}
        .insight-box {background:rgba(8,47,73,.5); border-left:4px solid #22d3ee; border-radius:12px; padding:14px 16px; margin:12px 0;}
        .scenario-card {background:#030d20; border-radius:18px; border:1px solid rgba(34,211,238,.18); padding:18px; min-height:120px;}
        .scenario-card.bear {border-left:4px solid #fb7185;}
        .scenario-card.base {border-left:4px solid #22d3ee;}
        .scenario-card.bull {border-left:4px solid #00f5a0;}
        .scenario-name {font-size:0.92rem; letter-spacing:.08em; color:#7dd3fc; opacity:.8;}
        .scenario-value {font-size:2.2rem; font-weight:800; color:#00f5a0; margin-top:10px;}
        .scenario-meta {color:#60a5fa; font-size:0.92rem;}
        .top-brand {display:flex; justify-content:space-between; align-items:flex-start; gap:16px;}
        .status-live {color:#10b981; font-weight:700;}
        .footer-ticker {background:#061122; border:1px solid rgba(34,211,238,.14); border-radius:14px; padding:10px 14px; color:#60a5fa; margin-top:18px;}
        .stTabs [data-baseweb="tab-list"] {gap: 12px;}
        .stTabs [data-baseweb="tab"] {
            background: #071226; border-radius: 12px 12px 0 0; color:#93c5fd; padding: 12px 16px;
        }
        .stTabs [aria-selected="true"] {background:#0b1f3d !important; color:#22d3ee !important;}
        .stButton>button {background:#0f3a6b; color:#ecfeff; border:1px solid rgba(34,211,238,.25); border-radius:12px;}
        .stTextInput>div>div>input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div {
            background: #071226 !important; color: #e0f2fe !important; border: 1px solid rgba(34,211,238,.18) !important; border-radius: 12px !important;
        }
        .stSlider [data-baseweb="slider"] {margin-top: 8px;}
        </style>
        """
    else:
        css = """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #f5f7fb;
            color: #0f172a;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
        .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        .sidebar-title {font-size: 1.4rem; font-weight: 800; color:#1e293b; margin-bottom:0.1rem;}
        .sidebar-subtitle {font-size: 0.82rem; color:#94a3b8;}
        .hero-title {font-size: 2.0rem; font-weight: 800; color: #0f172a; margin-bottom: 0.15rem;}
        .hero-subtitle {color: #94a3b8; margin-bottom: 0.9rem;}
        .soft-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:20px; padding:18px 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);}
        .metric-tile {background:#ffffff; border:1px solid #e5e7eb; border-radius:20px; padding:18px 20px; min-height:116px;}
        .metric-label {color:#94a3b8; font-size:0.92rem;}
        .metric-value {font-size:2.1rem; color:#111827; font-weight:700; margin-top:10px;}
        .metric-delta.good {display:inline-block; padding:4px 10px; border-radius:999px; background:#ecfdf5; color:#059669; font-weight:600; margin-top:10px;}
        .metric-delta.warn {display:inline-block; padding:4px 10px; border-radius:999px; background:#eff6ff; color:#2563eb; font-weight:600; margin-top:10px;}
        .section-title {font-size:1.2rem; font-weight:700; color:#111827; margin-bottom:10px;}
        .section-note {color:#94a3b8;}
        .status-pill {display:inline-block; padding:4px 12px; border-radius:999px; font-weight:600; font-size:0.88rem;}
        .delivered {background:#ecfdf5; color:#059669; border:1px solid #bbf7d0;}
        .transit {background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe;}
        .customs {background:#fff7ed; color:#d97706; border:1px solid #fed7aa;}
        .pending {background:#f1f5f9; color:#64748b; border:1px solid #cbd5e1;}
        .timeline-item {position:relative; padding-left:32px; padding-bottom:18px;}
        .timeline-item:before {content:""; position:absolute; left:11px; top:6px; width:10px; height:10px; background:#10b981; border-radius:999px;}
        .timeline-item:after {content:""; position:absolute; left:15px; top:18px; width:2px; height:100%; background:#e2e8f0;}
        .timeline-item:last-child:after {display:none;}
        .timeline-title {font-size:1.2rem; font-weight:700; color:#0f172a;}
        .timeline-place {font-size:1.0rem; color:#0f172a; font-weight:600;}
        .timeline-meta {color:#94a3b8;}
        .tool-link {display:block; padding:14px 16px; border-radius:14px; border:1px solid #bfdbfe; background:#eff6ff; color:#2563eb !important; font-weight:700; text-decoration:none; margin-bottom:10px;}
        .module-card {background:linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); border:1px solid #e2e8f0; border-radius:22px; padding:20px; height:100%; box-shadow: 0 10px 24px rgba(15,23,42,.05);}
        .module-title {font-size:1.28rem; font-weight:800; color:#0f172a; margin-bottom:8px;}
        .module-desc {color:#64748b; min-height:68px;}
        .module-chip {display:inline-block; padding:4px 10px; border-radius:999px; background:#eff6ff; color:#2563eb; margin-right:8px; margin-top:8px; font-size:0.82rem;}
        .info-callout {background:#f8fafc; border:1px solid #e2e8f0; border-radius:18px; padding:16px 18px;}
        .risk-high {background:#fef2f2; color:#dc2626; border:1px solid #fecaca; border-radius:999px; padding:4px 10px; font-weight:700;}
        .risk-medium {background:#fffbeb; color:#d97706; border:1px solid #fde68a; border-radius:999px; padding:4px 10px; font-weight:700;}
        .risk-low {background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; border-radius:999px; padding:4px 10px; font-weight:700;}
        .stTabs [data-baseweb="tab-list"] {gap: 12px;}
        .stTabs [data-baseweb="tab"] {background: #ffffff; border-radius: 12px 12px 0 0; padding: 12px 16px;}
        .stTabs [aria-selected="true"] {background:#eff6ff !important; color:#2563eb !important;}
        .stButton>button {border-radius:14px; border:1px solid #cbd5e1; background:#2563eb; color:#fff;}
        .stDownloadButton>button {border-radius:14px;}
        .footer-strip {padding:14px 16px; border-radius:14px; background:#ffffff; border:1px solid #e2e8f0; color:#64748b; margin-top:18px;}
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def render_sidebar(current_module: str):
    with st.sidebar:
        st.markdown('<div class="sidebar-title">灵径智链</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-subtitle">文化转译核心 · 动态利润 · 合规预审</div>', unsafe_allow_html=True)
        st.markdown("---")

        account = st.selectbox("账户", ["MEX-001-2024", "MEX-002-2024", "CHL-001-2024"], index=0)
        market = st.selectbox("主目标市场", ["墨西哥", "巴西", "智利", "阿根廷", "哥伦比亚"], index=0)
        global_query = st.text_input("全局搜索", placeholder="SKU / 订单号 / 国家 / 风险词")

        st.markdown("### 模块导航")
        module = st.radio(
            "选择平台模块",
            ["平台总览", "文化转译中枢", "AI 文案工坊", "ProfitLab 动态利润", "Puente 合规预审"],
            index=["平台总览", "文化转译中枢", "AI 文案工坊", "ProfitLab 动态利润", "Puente 合规预审"].index(current_module),
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("### 工具直达")
        st.markdown('<a class="tool-link" href="#">• 文化风控系统</a>', unsafe_allow_html=True)
        st.markdown('<a class="tool-link" href="#">• AI 文案工坊</a>', unsafe_allow_html=True)
        st.markdown('<a class="tool-link" href="#">• 利润量化分析工具</a>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 关键指标")
        st.metric("活跃订单", "156", "+12")
        st.metric("平均时效", "15.2 天", "↓ 1.3")
        st.metric("妥投率", "98.3%", "+0.5%")

        st.markdown("---")
        st.caption("平台定位：文化转译为核心 · 动态利润为支撑 · 合规预审兜底")
        st.caption(f"当前市场焦点：{market}")
        if global_query:
            st.info(f"已记录搜索关键词：{global_query}")
    return module, account, market, global_query


# =========================================================
# Calculations
# =========================================================
def calculate_profit_metrics(shipping_cost_usd: float, exchange_rate: float, product_cost_cny: float, selling_price_cny: float, fixed_cost_cny: float):
    shipping_cost_cny = shipping_cost_usd * exchange_rate
    variable_cost_per_item = shipping_cost_cny + product_cost_cny
    profit_per_item = selling_price_cny - variable_cost_per_item
    margin = (profit_per_item / selling_price_cny * 100) if selling_price_cny > 0 else 0
    roi = (profit_per_item / variable_cost_per_item * 100) if variable_cost_per_item > 0 else 0
    break_even = math.ceil(fixed_cost_cny / profit_per_item) if profit_per_item > 0 else None
    return {
        "shipping_cost_cny": shipping_cost_cny,
        "variable_cost_per_item": variable_cost_per_item,
        "profit_per_item": profit_per_item,
        "margin": margin,
        "roi": roi,
        "break_even": break_even,
    }


def build_curve_df(metrics, selling_price_cny: float, fixed_cost_cny: float, sales_range: int):
    xs = list(range(0, sales_range + 1))
    total_cost = [fixed_cost_cny + metrics["variable_cost_per_item"] * x for x in xs]
    total_revenue = [selling_price_cny * x for x in xs]
    profit = [r - c for r, c in zip(total_revenue, total_cost)]
    return pd.DataFrame({"销量": xs, "总成本": total_cost, "总收入": total_revenue, "利润": profit})


def scenario_metrics(base_inputs):
    shipping, rate, product_cost, selling, fixed_cost = base_inputs
    configs = {
        "BEAR": (shipping * 1.3, rate, product_cost, selling, fixed_cost),
        "BASE": (shipping, rate, product_cost, selling, fixed_cost),
        "BULL": (shipping * 0.8, rate, product_cost, selling, fixed_cost),
        "HIKE": (shipping, rate, product_cost, selling * 1.15, fixed_cost),
        "CUT": (shipping, rate, product_cost, selling * 0.9, fixed_cost),
        "LEAN": (shipping, rate, product_cost, selling, fixed_cost * 0.5),
    }
    rows = {}
    for name, values in configs.items():
        rows[name] = calculate_profit_metrics(*values)
    return rows


def build_sensitivity_matrix(base_inputs, sales_points):
    shipping, rate, product_cost, selling, fixed_cost = base_inputs
    price_changes = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]
    records = []
    for change in price_changes:
        row = {"售价变化": f"{change:+.0%} ¥{selling * (1 + change):.0f}"}
        current_price = selling * (1 + change)
        metrics = calculate_profit_metrics(shipping, rate, product_cost, current_price, fixed_cost)
        for units in sales_points:
            pnl = current_price * units - fixed_cost - metrics["variable_cost_per_item"] * units
            row[f"{units}件"] = pnl
        records.append(row)
    return pd.DataFrame(records)


def risk_badge(level: str):
    if level == "高风险":
        return '<span class="risk-high">HIGH</span>'
    if level == "中风险":
        return '<span class="risk-medium">MEDIUM</span>'
    return '<span class="risk-low">LOW</span>'


def status_pill(status: str):
    mapping = {
        "已送达": ("delivered", status),
        "运输中": ("transit", status),
        "清关中": ("customs", status),
        "已发货": ("pending", status),
    }
    cls, text = mapping.get(status, ("pending", status))
    return f'<span class="status-pill {cls}">{text}</span>'


def score_risk(country: str, colors, symbols, copy_text: str):
    base = next((x for x in CULTURAL_RISK_DATA if x["country"] == country), CULTURAL_RISK_DATA[1])
    score = base["risk_score"]
    findings = []

    high_risk_terms = {
        "巴西": {"紫色": "紫色在葬礼语境中敏感", "OK手势": "OK 手势可能引发冒犯理解"},
        "墨西哥": {"黄色": "黄色在部分场景中关联死亡意象", "骷髅": "骷髅适合节庆语境，不宜泛化用于常规礼赠页面"},
        "阿根廷": {"13": "数字 13 容易触发不吉利联想"},
        "智利": {"疗效": "需避免医疗疗效式表达"},
        "哥伦比亚": {"神秘力量": "神秘化文案容易偏离消费语境"},
    }

    country_terms = high_risk_terms.get(country, {})
    for c in colors:
        if c in country_terms:
            findings.append(country_terms[c])
            score += 8

    for s in symbols:
        if s in country_terms:
            findings.append(country_terms[s])
            score += 10

    for term, message in country_terms.items():
        if term in copy_text:
            findings.append(message)
            score += 12

    score = min(score, 95)
    if score >= 75:
        level = "高风险"
    elif score >= 50:
        level = "中风险"
    else:
        level = "低风险"

    return level, score, findings or ["未触发显著高危词，但建议保留本地化说明与视觉适配。"]


# =========================================================
# Module renderers
# =========================================================

def render_overview(account, market):
    apply_base_css(False)
    st.markdown('<div class="hero-title">灵径智链 · 跨平台文化转译工作台</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">不是另一个商城，而是依托 Shopee / TikTok Shop / Amazon 的第三方赋能平台</div>', unsafe_allow_html=True)

    top_left, top_right = st.columns([2.1, 1])
    with top_left:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">平台首页</div>', unsafe_allow_html=True)
        st.markdown("""
        当前首页改为 **服务器前端式工作台**，把核心能力拆成独立服务区，避免“全托管平台”式的叙事误区。
        你可以按 **文化转译 → AI 文案生成 → ProfitLab → Puente** 的顺序完成从表达生成、利润决策到发货前合规预审的整体验证。
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    with top_right:
        st.markdown(
            '<div class="metric-tile"><div class="metric-label">当前账户</div><div class="metric-value">%s</div><div class="metric-delta good">聚焦市场：%s</div></div>' % (account, market),
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title" style="margin-top:0.6rem;">三大功能分区</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="module-card"><div class="module-title">灵径文化转译中枢</div><div class="module-desc">先做国家文化语义预审、卖点重写与场景转译，把高文化属性商品翻译成当地市场能听懂的消费语言。</div><span class="module-chip">国家规则库</span><span class="module-chip">上架预审</span><span class="module-chip">文案替换建议</span></div>',
            unsafe_allow_html=True,
        )
        st.caption('适合先判断“卖什么话术、怎么表达更安全”。')
    with c2:
        st.markdown(
            '<div class="module-card"><div class="module-title">ProfitLab 动态利润</div><div class="module-desc">再做成本拆解、关税/汇率波动模拟和多 SKU 对比，确认在政策变化下的定价边界。</div><span class="module-chip">BEP 曲线</span><span class="module-chip">情景模拟</span><span class="module-chip">多 SKU 对比</span></div>',
            unsafe_allow_html=True,
        )
        st.caption('适合回答“卖多少钱、多少单回本、怎么比方案”。')
    with c3:
        st.markdown(
            '<div class="module-card"><div class="module-title">Puente 合规预审</div><div class="module-desc">最后做发货前材料校核、行政风险预警与履约路径建议，把前面的判断落到合规预审和协同执行。</div><span class="module-chip">订单追踪</span><span class="module-chip">清关预审</span><span class="module-chip">系统工具</span></div>',
            unsafe_allow_html=True,
        )
        st.caption('适合处理“发出去前是否合规、怎么规避清关风险”。')

    st.markdown('<div class="section-title" style="margin-top:1rem;">平台概况</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    with a:
        st.markdown('<div class="metric-tile"><div class="metric-label">试点市场</div><div class="metric-value">5</div><div class="metric-delta good">墨西哥 / 巴西 / 智利 / 阿根廷 / 哥伦比亚</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="metric-tile"><div class="metric-label">已接入功能</div><div class="metric-value">3 大模块</div><div class="metric-delta warn">统一工作台</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="metric-tile"><div class="metric-label">当前模式</div><div class="metric-value">Demo</div><div class="metric-delta good">支持比赛展示</div></div>', unsafe_allow_html=True)
    with d:
        st.markdown('<div class="metric-tile"><div class="metric-label">平台状态</div><div class="metric-value">正常</div><div class="metric-delta good">SaaS Demo Ready</div></div>', unsafe_allow_html=True)

    row1_left, row1_mid, row1_right = st.columns([1.2, 1.2, 1])
    with row1_left:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">文化转译区</div>', unsafe_allow_html=True)
        st.markdown("""
        - 国家风险规则库
        - 商品命名与颜色风险检查
        - AI 文案重写与本地化表达
        - 市场进入注意事项
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    with row1_mid:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">利润量化区</div>', unsafe_allow_html=True)
        st.markdown("""
        - 成本拆解与利润率计算
        - 盈亏平衡点分析
        - 情景模拟与价格敏感性
        - 多 SKU 横向对比
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    with row1_right:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">合规预审区</div>', unsafe_allow_html=True)
        st.markdown("""
        - 发货前文件预审
        - 清关行政风险提示
        - 报关生成
        - API / 平台对接
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    lower_left, lower_right = st.columns([1.35, 1])
    with lower_left:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">实施路径</div>', unsafe_allow_html=True)
        roadmap = pd.DataFrame(
            {
                "阶段": ["Phase 1 产品重构", "Phase 2 市场验证", "Phase 3 规模扩展"],
                "目标": ["完成 SKU 文化转译与定价模型", "开展巴西/墨西哥小规模试卖与 A/B 测试", "沉淀 SOP 与服务商生态"],
                "关键输出": ["规则表、AI 文案样板、利润模型", "数据看板、反馈报告、预审样例", "节气/IP 系列与服务商协同 SOP"],
            }
        )
        st.dataframe(roadmap, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with lower_right:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">收入结构草图</div>', unsafe_allow_html=True)
        st.markdown("""
        - 一次性诊断：文化风控报告 / 市场进入建议
        - SaaS 订阅：ProfitLab、风控库、数据看板
        - 项目服务：上架优化、详情页改造、A/B 测试
        - 项目服务：AI 文案、详情页改造、A/B 测试
        - 代理协同：合规预审、清关支持、服务商撮合
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-callout"><b>当前版本说明</b><br>首页仅做结构整理，其他页面与原先逻辑保持不变。</div>', unsafe_allow_html=True)

def render_cultural_risk(market):
    apply_base_css(False)
    st.markdown('<div class="hero-title">灵径 · 文化转译中枢</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">拉美核心市场文化语义、颜色禁忌、营销注意事项与 AI 转译前的风险预审</div>', unsafe_allow_html=True)

    high_count = sum(1 for x in CULTURAL_RISK_DATA if x["risk_level"] == "高风险")
    medium_count = sum(1 for x in CULTURAL_RISK_DATA if x["risk_level"] == "中风险")
    low_count = sum(1 for x in CULTURAL_RISK_DATA if x["risk_level"] == "低风险")

    m1, m2 = st.columns([3, 1])
    with m1:
        st.markdown(
            f'''<div class="metric-tile"><div class="metric-label">覆盖市场</div><div class="metric-value">{len(CULTURAL_RISK_DATA)}</div><div class="metric-delta warn">高风险 {high_count} / 中风险 {medium_count} / 低风险 {low_count}</div></div>''',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'''<div class="metric-tile"><div class="metric-label">当前聚焦</div><div class="metric-value">{market}</div><div class="metric-delta good">支持 SKU 级预审</div></div>''',
            unsafe_allow_html=True,
        )

    filters = st.columns([1, 1, 1.2])
    with filters[0]:
        risk_filter = st.selectbox("风险级别", ["全部", "高风险", "中风险", "低风险"], index=0)
    with filters[1]:
        category = st.selectbox("试点品类", list(CATEGORY_POSITIONING.keys()), index=0)
    with filters[2]:
        keyword = st.text_input("搜索国家 / 风险点", placeholder="如：墨西哥、紫色、疗效")

    rows = CULTURAL_RISK_DATA
    if risk_filter != "全部":
        rows = [x for x in rows if x["risk_level"] == risk_filter]
    if keyword:
        rows = [
            x for x in rows
            if keyword.lower() in x["country"].lower()
            or keyword.lower() in x["country_en"].lower()
            or keyword.lower() in x["notes"].lower()
            or keyword.lower() in x["suggestion"].lower()
        ]

    display_rows = []
    for row in rows:
        display_rows.append(
            {
                "市场": f"{row['code']}\n{row['country']}\n{row['country_en']}",
                "忌讳颜色": " / ".join(row["colors"]),
                "宗教禁忌": f"{row['religious_items']} 条",
                "营销注意": f"{row['marketing_items']} 条",
                "推荐平台": row["platforms"],
                "风险等级": row["risk_tag"],
                "备注": row["notes"],
            }
        )

    st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)

    detail_left, detail_right = st.columns([1.25, 1])
    with detail_left:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">国家风险详情</div>', unsafe_allow_html=True)
        selected_country = st.selectbox("选择市场", [x["country"] for x in CULTURAL_RISK_DATA], index=1)
        country_detail = next(x for x in CULTURAL_RISK_DATA if x["country"] == selected_country)

        c_html = "".join(
            [f'<span style="display:inline-block;width:18px;height:18px;border-radius:999px;background:{hexv};margin-right:10px;border:2px solid #fff;box-shadow:0 0 0 1px #e2e8f0;"></span>' for hexv in country_detail["color_hex"]]
        )
        st.markdown(f"**风险等级**：{country_detail['risk_level']}  {risk_badge(country_detail['risk_level'])}", unsafe_allow_html=True)
        st.markdown(f"**色彩关注**：{c_html} {' / '.join(country_detail['colors'])}", unsafe_allow_html=True)
        st.markdown(f"**风险说明**：{country_detail['notes']}")
        st.markdown(f"**推荐表达**：{country_detail['suggestion']}")
        positioning = CATEGORY_POSITIONING[category]
        st.info(f"**{category}** 当前更适合定位为：{positioning['定位']}\n\n页面表达建议：{positioning['页面表达']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with detail_right:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">SKU 上架预审</div>', unsafe_allow_html=True)
        product_name = st.text_input("商品名", value=f"{category}·拉美上新款")
        country = st.selectbox("目标国家", [x["country"] for x in CULTURAL_RISK_DATA], index=1, key="precheck_country")
        colors = st.multiselect("主色调", ["红色", "黄色", "紫色", "绿色", "黑色", "金色", "蓝灰"], default=["红色", "黄色"])
        symbols = st.multiselect("视觉符号", ["OK手势", "骷髅", "13", "花朵", "龙凤纹", "神秘力量"], default=[])
        copy_text = st.text_area("卖点文案", value="适合节庆、礼赠和空间装饰，突出东方设计与手作质感。")
        if st.button("运行文化预审", use_container_width=True):
            level, score, findings = score_risk(country, colors, symbols, copy_text)
            st.markdown(f"**综合风险评分**：{score}/100")
            st.progress(score / 100)
            st.markdown(f"**风险判断**：{level}")
            st.warning("\n".join([f"• {x}" for x in findings]))
            suggestion = CATEGORY_POSITIONING[category]["建议"]
            st.success(f"建议命名：{product_name.replace('上新', '礼赠') if level != '低风险' else product_name}\n\n表达建议：{suggestion}")
        st.markdown('</div>', unsafe_allow_html=True)




def build_ai_prompt(product_name: str, product_category: str, target_country: str, platform_name: str, brand_tone: str, selling_points: str, banned_words: str, compliance_notes: str):
    return f"""你是一名跨境电商拉美本地化运营顾问。
请为{target_country}市场、上架在{platform_name}的{product_category}生成中文后台参考文案。
商品名：{product_name}
品牌语气：{brand_tone}
核心卖点：{selling_points}
禁用或谨慎词：{banned_words or '无'}
合规与文化提醒：{compliance_notes or '避免医疗疗效、宗教冒犯和夸大承诺'}

输出要求：
1. 给出一个适合当地消费者理解的商品标题
2. 给出三条卖点 bullet
3. 给出一段详情页短文案
4. 给出两个适合社媒短视频封面的口号
5. 避免出现医疗疗效、绝对化承诺和文化冒犯
"""


def local_ai_fallback(product_name: str, product_category: str, target_country: str, brand_tone: str, selling_points: str):
    tone_map = {
        '东方礼赠': '强调礼物感、节庆氛围和东方手作感',
        '现代生活方式': '强调生活方式、美学搭配和轻仪式感',
        '品牌故事': '强调设计来源、工艺故事和文化灵感',
    }
    tone_desc = tone_map.get(brand_tone, brand_tone)
    title = f"{target_country}适配版｜{product_name} · 东方灵感礼赠系列"
    bullets = [
        f"以{product_category}为载体，突出东方审美与当代生活场景的结合。",
        f"文案语气以{tone_desc}为主，避免生硬直译与文化误读。",
        f"围绕{selling_points or '礼赠、装饰、社交展示'}展开，适合平台详情页与短视频种草同步使用。",
    ]
    body = (
        f"这款{product_category}并不只是传统元素的直接输出，而是面向{target_country}消费者重新整理后的生活方式表达。"
        f"我们弱化难以理解的抽象文化词，转而突出礼赠、空间氛围、穿搭展示等更容易被接受的消费语境，"
        f"帮助商品在保留东方气质的同时，更自然地进入当地平台页面和社媒传播场景。"
    )
    slogans = [
        "东方灵感，一眼看懂",
        "把文化变成愿意下单的表达",
    ]
    return {"title": title, "bullets": bullets, "body": body, "slogans": slogans}


def call_openai_compatible(api_base: str, api_key: str, model: str, prompt: str):
    endpoint = api_base.rstrip('/') + '/chat/completions'
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是跨境电商拉美市场文案与合规顾问。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.7,
    }
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    response = requests.post(endpoint, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    data = response.json()
    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    return content, payload


def render_ai_copy_lab(market):
    apply_base_css(False)
    st.markdown('<div class="hero-title">AI 文案工坊</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">像服务器前端一样配置模型、查看请求载荷，并生成适合拉美平台的标题、卖点与详情页文案</div>', unsafe_allow_html=True)

    left, right = st.columns([1.15, 1.55])
    with left:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">AI 接口设置</div>', unsafe_allow_html=True)
        provider = st.selectbox('推理方式', ['本地演示模式', 'OpenAI 兼容接口'])
        api_base = st.text_input('API Base URL', value='https://api.openai.com/v1')
        api_key = st.text_input('API Key', type='password', placeholder='输入兼容接口密钥')
        model = st.text_input('模型名', value='gpt-4o-mini')
        st.caption('演示模式下不会真的发请求；配置兼容接口后可直接调用。')
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="soft-card" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">文案生成输入</div>', unsafe_allow_html=True)
        product_category = st.selectbox('商品类型', list(CATEGORY_POSITIONING.keys()), index=1)
        product_name = st.text_input('商品名称', value=f'{product_category} · 拉美礼赠版')
        platform_name = st.selectbox('目标平台', ['TikTok Shop', 'Shopee', 'Amazon', 'Mercado Libre'])
        target_country = st.selectbox('目标国家', [x['country'] for x in CULTURAL_RISK_DATA], index=1)
        brand_tone = st.selectbox('品牌语气', ['东方礼赠', '现代生活方式', '品牌故事'])
        selling_points = st.text_area('核心卖点', value=CATEGORY_POSITIONING[product_category]['页面表达'])
        banned_words = st.text_input('禁用/谨慎词', value='疗效, 治愈, 神秘力量')
        compliance_notes = st.text_area('合规/文化提醒', value='避免医疗疗效、绝对化承诺和宗教冒犯；标题要利于平台审核。')
        generate = st.button('生成智能文案', use_container_width=True, type='primary')
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">请求预览</div>', unsafe_allow_html=True)
        prompt = build_ai_prompt(product_name, product_category, target_country, platform_name, brand_tone, selling_points, banned_words, compliance_notes)
        st.code(prompt, language='markdown')
        st.markdown('</div>', unsafe_allow_html=True)

        if generate:
            country_detail = next(x for x in CULTURAL_RISK_DATA if x['country'] == target_country)
            full_notes = compliance_notes + '；' + country_detail['notes']
            prompt = build_ai_prompt(product_name, product_category, target_country, platform_name, brand_tone, selling_points, banned_words, full_notes)
            with st.spinner('正在生成拉美本地化文案...'):
                try:
                    if provider == 'OpenAI 兼容接口' and api_key.strip():
                        content, payload = call_openai_compatible(api_base, api_key, model, prompt)
                        st.session_state['ai_payload'] = payload
                        st.session_state['ai_result'] = {'raw': content}
                    else:
                        st.session_state['ai_payload'] = {'mode': 'fallback', 'prompt': prompt}
                        st.session_state['ai_result'] = local_ai_fallback(product_name, product_category, target_country, brand_tone, selling_points)
                except Exception as exc:
                    st.error(f'接口调用失败，已保留演示模式建议：{exc}')
                    st.session_state['ai_payload'] = {'mode': 'fallback', 'prompt': prompt}
                    st.session_state['ai_result'] = local_ai_fallback(product_name, product_category, target_country, brand_tone, selling_points)

        st.markdown('<div class="soft-card" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">生成结果</div>', unsafe_allow_html=True)
        result = st.session_state.get('ai_result')
        if not result:
            st.info('点击“生成智能文案”后，这里会显示标题、卖点、详情页短文案和短视频口号。')
        elif 'raw' in result:
            st.text_area('模型原始返回', value=result['raw'], height=280)
        else:
            st.markdown(f"**建议标题**\n\n{result['title']}")
            st.markdown('**卖点 Bullet**')
            for item in result['bullets']:
                st.markdown(f'- {item}')
            st.markdown('**详情页短文案**')
            st.write(result['body'])
            st.markdown('**短视频封面口号**')
            for item in result['slogans']:
                st.markdown(f'- {item}')
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="soft-card" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">请求载荷 / 审计留痕</div>', unsafe_allow_html=True)
        payload_preview = st.session_state.get('ai_payload', {'mode': 'idle'})
        st.code(json.dumps(payload_preview, ensure_ascii=False, indent=2), language='json')
        st.caption('这里模拟“服务器前端”里的请求预览和审计留痕，方便比赛演示“AI 接口 + 风险留痕”的逻辑。')
        st.markdown('</div>', unsafe_allow_html=True)

def render_profitlab():
    apply_base_css(True)
    st.markdown('<div class="top-brand"><div><div class="hero-title">PROFITLAB</div><div class="hero-subtitle">Policy-aware Pricing Engine · v4 Demo</div></div><div class="status-live">● LIVE &nbsp;&nbsp; %s</div></div>' % datetime.now().strftime("%H:%M:%S"), unsafe_allow_html=True)

    if "sku_store" not in st.session_state:
        st.session_state.sku_store = [dict(x) for x in DEFAULT_SKUS]

    left, right = st.columns([0.9, 3.1])

    with left:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.markdown("### 参数配置")
        shipping = st.number_input("运输成本 USD/件", min_value=0.1, value=1.3, step=0.1)
        rate = st.number_input("汇率 USD/CNY", min_value=5.0, max_value=10.0, value=6.85, step=0.01)
        product_cost = st.number_input("采购成本 CNY/件", min_value=0.0, value=45.0, step=1.0)
        price = st.number_input("销售价格 CNY/件", min_value=1.0, value=120.0, step=1.0)
        fixed_cost = st.number_input("固定运营成本 CNY", min_value=0.0, value=5000.0, step=100.0)
        sales_range = st.select_slider("分析区间", options=[100, 200, 500, 1000], value=200)
        st.markdown("<div class='mini-chip'>BASE</div><div class='mini-chip'>BEP</div><div class='mini-chip'>ROI</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    metrics = calculate_profit_metrics(shipping, rate, product_cost, price, fixed_cost)

    with right:
        k1, k2, k3, k4, k5 = st.columns(5)
        stats = [
            ("毛利/件", f"¥{metrics['profit_per_item']:.2f}", "当前单件利润"),
            ("利润率", f"{metrics['margin']:.1f}%", "毛利率"),
            ("BEP", f"{metrics['break_even'] or '∞'}件", "盈亏平衡"),
            ("区间利润", f"¥{max(build_curve_df(metrics, price, fixed_cost, sales_range)['利润']):.0f}", f"{sales_range}件上限"),
            ("ROI", f"{metrics['roi']:.0f}%", "变动成本回报"),
        ]
        for col, stat in zip([k1, k2, k3, k4, k5], stats):
            with col:
                st.markdown(
                    f'''<div class="kpi-card"><div class="kpi-label">{stat[0]}</div><div class="kpi-value">{stat[1]}</div><div class="kpi-help">{stat[2]}</div></div>''',
                    unsafe_allow_html=True,
                )

        tabs = st.tabs(["盈亏分析", "情景模拟", "多 SKU 对比", "AI 顾问"])

        with tabs[0]:
            curve_df = build_curve_df(metrics, price, fixed_cost, sales_range)
            chart_col, info_col = st.columns([2.5, 1])
            with chart_col:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=curve_df["销量"], y=curve_df["总收入"], mode="lines", name="收入", line=dict(color="#00C2FF", width=4)))
                fig.add_trace(go.Scatter(x=curve_df["销量"], y=curve_df["总成本"], mode="lines", name="成本", line=dict(color="#FF477E", width=4)))
                if metrics["break_even"] and metrics["break_even"] <= sales_range:
                    be = metrics["break_even"]
                    be_y = fixed_cost + metrics["variable_cost_per_item"] * be
                    fig.add_vline(x=be, line_dash="dot", line_color="#00F5A0")
                    fig.add_annotation(x=be, y=be_y, text=f"BEP: {be}", showarrow=False, yshift=18, font=dict(color="#00F5A0", size=13))
                fig.update_layout(
                    height=540,
                    paper_bgcolor="#020817",
                    plot_bgcolor="#020817",
                    font=dict(color="#cbd5e1"),
                    xaxis_title="销售量（件）",
                    yaxis_title="金额（CNY）",
                    legend=dict(orientation="h", y=1.02, x=0.01),
                    margin=dict(l=20, r=20, t=30, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
            with info_col:
                st.markdown('<div class="section-shell">', unsafe_allow_html=True)
                st.markdown("### 盈亏平衡")
                st.metric("单件毛利", f"¥{metrics['profit_per_item']:.2f}")
                st.metric("达盈亏平衡", f"{metrics['break_even'] or '无法达成'} 件")
                st.metric("变动成本/件", f"¥{metrics['variable_cost_per_item']:.2f}")
                st.metric("运输成本/件", f"¥{metrics['shipping_cost_cny']:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="insight-box">当前原型保留了你现有利润计算逻辑，同时补上了视觉层级、顶部经营指标和 BEP 标记，尽量贴近你组员的 ProfitLab 演示风格。</div>', unsafe_allow_html=True)

        with tabs[1]:
            scenarios = scenario_metrics((shipping, rate, product_cost, price, fixed_cost))
            row1 = st.columns(3)
            row2 = st.columns(3)
            entries = [
                ("BEAR", "熊市（运费+30%）", scenarios["BEAR"]),
                ("BASE", "基准（当前）", scenarios["BASE"]),
                ("BULL", "牛市（运费-20%）", scenarios["BULL"]),
                ("HIKE", "提价15%", scenarios["HIKE"]),
                ("CUT", "降价10%", scenarios["CUT"]),
                ("LEAN", "固定成本减半", scenarios["LEAN"]),
            ]
            for col, (name, desc, item) in zip(row1 + row2, entries):
                with col:
                    style = "base" if name == "BASE" else ("bull" if name in ["BULL", "HIKE", "LEAN"] else "bear")
                    st.markdown(
                        f'''<div class="scenario-card {style}"><div class="scenario-name">{name} · {desc}</div><div class="scenario-value">¥{item['profit_per_item']:.2f}</div><div class="scenario-meta">单件毛利 · BEP: {item['break_even'] or '∞'}件</div></div>''',
                        unsafe_allow_html=True,
                    )
            st.markdown("<br>", unsafe_allow_html=True)
            matrix = build_sensitivity_matrix((shipping, rate, product_cost, price, fixed_cost), [50, 100, 150, 200])
            styled_matrix = matrix.copy()
            for col in [c for c in matrix.columns if c.endswith("件")]:
                styled_matrix[col] = styled_matrix[col].apply(lambda x: f"¥{x:,.0f}" if x >= 0 else f"¥{x:,.0f}")
            st.dataframe(styled_matrix, hide_index=True, use_container_width=True)

        with tabs[2]:
            st.markdown('<div class="section-shell">', unsafe_allow_html=True)
            st.markdown("### SKU 编辑")
            sku_count = st.slider("SKU 数量", 2, 4, len(st.session_state.sku_store))
            if sku_count > len(st.session_state.sku_store):
                for i in range(len(st.session_state.sku_store), sku_count):
                    st.session_state.sku_store.append({"SKU": f"SKU-{chr(65+i)}", "运费(USD)": 1.5, "汇率": 6.85, "采购成本": 40.0, "售价": 110.0, "固定成本": 4500.0})
            elif sku_count < len(st.session_state.sku_store):
                st.session_state.sku_store = st.session_state.sku_store[:sku_count]

            edit_cols = st.columns(sku_count)
            for i, col in enumerate(edit_cols):
                sku = st.session_state.sku_store[i]
                with col:
                    st.markdown(f"#### {sku['SKU']}")
                    sku["SKU"] = st.text_input(f"SKU 名称 {i+1}", value=sku["SKU"], key=f"sku_name_{i}")
                    sku["运费(USD)"] = st.number_input(f"运费 {i+1}", value=float(sku["运费(USD)"]), key=f"ship_{i}")
                    sku["汇率"] = st.number_input(f"汇率 {i+1}", value=float(sku["汇率"]), key=f"rate_{i}")
                    sku["采购成本"] = st.number_input(f"采购成本 {i+1}", value=float(sku["采购成本"]), key=f"cost_{i}")
                    sku["售价"] = st.number_input(f"售价 {i+1}", value=float(sku["售价"]), key=f"price_{i}")
                    sku["固定成本"] = st.number_input(f"固定成本 {i+1}", value=float(sku["固定成本"]), key=f"fixed_{i}")
            st.markdown('</div>', unsafe_allow_html=True)

            compare_rows = []
            for sku in st.session_state.sku_store:
                item = calculate_profit_metrics(sku["运费(USD)"], sku["汇率"], sku["采购成本"], sku["售价"], sku["固定成本"])
                compare_rows.append(
                    {
                        "SKU": sku["SKU"],
                        "售价": sku["售价"],
                        "变动成本": round(item["variable_cost_per_item"], 2),
                        "毛利/件": round(item["profit_per_item"], 2),
                        "利润率": round(item["margin"], 1),
                        "固定成本": sku["固定成本"],
                        "BEP": item["break_even"] or 999,
                    }
                )
            compare_df = pd.DataFrame(compare_rows)
            st.dataframe(compare_df, hide_index=True, use_container_width=True)

            fig = go.Figure()
            fig.add_bar(x=compare_df["SKU"], y=compare_df["BEP"], name="BEP", marker_color="#00C2FF")
            fig.add_bar(x=compare_df["SKU"], y=compare_df["毛利/件"], name="毛利/件", marker_color="#00F5A0")
            fig.update_layout(
                barmode="group",
                height=420,
                paper_bgcolor="#020817",
                plot_bgcolor="#020817",
                font=dict(color="#cbd5e1"),
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]:
            st.markdown('<div class="section-shell">', unsafe_allow_html=True)
            st.markdown("### AI 经营建议")
            bullets = [
                f"当前单件毛利为 ¥{metrics['profit_per_item']:.2f}，利润率 {metrics['margin']:.1f}%，建议把投放与折扣控制在不吃掉毛利的范围内。",
                f"如果 2026 年拉美关税或小额包裹额度调整，ProfitLab 可以基于当前参数快速重算；当前 BEP 为 {metrics['break_even'] or '无法达成'} 件。",
                "建议把文化转译页的文案结果同步到本页，形成“先转译、再定价、最后预审”的经营闭环。",
            ]
            st.markdown("\n".join([f"- {b}" for b in bullets]))
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="footer-ticker">✓ 当前模型已整合：BEP 曲线 / 情景模拟 / 多 SKU 对比。下一步建议接入真实运费、广告费和平台佣金字段。</div>', unsafe_allow_html=True)


def render_puente(account):
    apply_base_css(False)
    st.markdown('<div class="hero-title">Puente · 合规数字化预审</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">发货前材料校核 · 行政风险预警 · 履约路径协同 · 系统工具</div>', unsafe_allow_html=True)

    tabs = st.tabs(["履约追踪", "数据看板", "清关预审", "系统工具"])

    with tabs[0]:
        top1, top2, top3 = st.columns([3, 1, 1])
        with top1:
            query = st.text_input("搜索订单号或目的地", placeholder="例如：PUENTE-MEX-2024-00123 / 墨西哥城")
        with top2:
            st.markdown("<br>", unsafe_allow_html=True)
            export_clicked = st.button("导出")
        with top3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("新建运单", type="primary")

        order_view = ORDER_DF.copy()
        if query:
            order_view = order_view[
                order_view["订单号"].str.contains(query, case=False) | order_view["目的地"].str.contains(query, case=False)
            ]
        st.dataframe(
            order_view,
            hide_index=True,
            use_container_width=True,
            column_config={
                "进度": st.column_config.ProgressColumn("进度", min_value=0, max_value=100, format="%d%%"),
                "货值(USD)": st.column_config.NumberColumn("货值", format="$ %.2f"),
            },
        )

        if export_clicked:
            export_buf = BytesIO()
            order_view.to_csv(export_buf, index=False)
            st.download_button("下载订单 CSV", data=export_buf.getvalue(), file_name="puente_orders.csv", mime="text/csv")

        left, right = st.columns([1.2, 1.1])
        with left:
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">物流轨迹</div>', unsafe_allow_html=True)
            for step in TRACKING_STEPS:
                st.markdown(
                    f'''<div class="timeline-item"><div class="timeline-place">{step['title']}</div><div class="timeline-meta">{step['place']}</div><div class="timeline-meta">{step['time']} · {step['desc']}</div></div>''',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">目的地位置</div>', unsafe_allow_html=True)
            map_df = DESTINATION_POINTS.copy()
            fig = px.scatter_geo(
                map_df,
                lat="lat",
                lon="lon",
                hover_name="城市",
                size="订单",
                color="订单",
                scope="south america",
            )
            fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        a, b, c, d = st.columns(4)
        tiles = [
            ("平均运输时效", "15.2 天", "↓ 1.3 天", "good"),
            ("包裹妥投率", "98.3%", "↑ 0.5%", "good"),
            ("清关成功率", "96.7%", "↑ 1.2%", "warn"),
            ("客户满意度", "4.8", "/ 5.0", "warn"),
        ]
        for col, tile in zip([a, b, c, d], tiles):
            with col:
                st.markdown(f'''<div class="metric-tile"><div class="metric-label">{tile[0]}</div><div class="metric-value">{tile[1]}</div><div class="metric-delta {tile[3]}">{tile[2]}</div></div>''', unsafe_allow_html=True)

        left, right = st.columns([1.25, 1])
        with left:
            months = ["9月", "10月", "11月", "12月", "1月"]
            days = [19.8, 18.4, 16.9, 15.8, 15.2]
            fig = go.Figure(go.Scatter(x=months, y=days, mode="lines+markers", line=dict(color="#3b82f6", width=4), fill="tozeroy"))
            fig.update_layout(height=330, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="天")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.pie(values=[156, 89, 67, 45, 32], names=["墨西哥", "智利", "秘鲁", "哥伦比亚", "巴西"], hole=0.58)
            fig.update_layout(height=330, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        cost_df = pd.DataFrame(
            {
                "项目": ["国际运输", "本地派送", "运输保险", "清关费用", "仓储处理"],
                "占比": [45, 25, 2, 20, 8],
                "单票均价 USD": [4.5, 2.5, 0.2, 2.0, 0.8],
            }
        )
        st.dataframe(cost_df, hide_index=True, use_container_width=True)

    with tabs[2]:
        left, right = st.columns([1.1, 1])
        with left:
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">文件上传</div>', unsafe_allow_html=True)
            uploaded_files = st.file_uploader("拖拽文件到此，或点击选择", type=["pdf", "jpg", "png", "xlsx"], accept_multiple_files=True)
            existing_names = [f.name.lower() for f in uploaded_files] if uploaded_files else []
            st.markdown("#### 必要文件清单")
            checklist_rows = []
            for doc_name, status, keyword in CUSTOMS_REQUIRED_DOCS:
                computed = status
                if existing_names and any(keyword in name for name in existing_names):
                    computed = "已验证"
                checklist_rows.append({"文件": doc_name, "状态": computed})
            st.dataframe(pd.DataFrame(checklist_rows), hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">智能工具</div>', unsafe_allow_html=True)
            if st.button("自动检查文件完整性", use_container_width=True):
                complete = sum(1 for row in checklist_rows if row["状态"] == "已验证")
                st.success(f"已完成预审：{complete}/5 份文件通过。")
            if st.button("一键生成报关单", use_container_width=True):
                declaration = pd.DataFrame(
                    {
                        "字段": ["账户", "国家", "票数", "清关等级"],
                        "值": [account, "墨西哥", 24, "中"]
                    }
                )
                xlsx = BytesIO()
                with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
                    declaration.to_excel(writer, index=False, sheet_name="报关单")
                st.download_button("下载报关单", xlsx.getvalue(), file_name="customs_declaration.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.markdown("---")
            st.markdown("#### 清关风险预警")
            st.markdown("- 墨西哥：<span class='risk-low'>低</span> 无特殊管制", unsafe_allow_html=True)
            st.markdown("- 智利：<span class='risk-medium'>中</span> 需原产地证明", unsafe_allow_html=True)
            st.markdown("- 巴西：<span class='risk-high'>高</span> ANATEL 认证要求", unsafe_allow_html=True)
            st.markdown("---")
            st.info("联系清关专员\n\ncustoms@puente-logistics.com\n\n+52 55 1234 5678 · 工作日 09:00-18:00")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        left, right = st.columns(2)
        with left:
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">REST API</div>', unsafe_allow_html=True)
            st.code(
                '''import requests\n\nAPI_KEY = "pk_live_xxxxxx"\nBASE = "https://api.puente-logistics.com/v1"\n\ndef create_shipment(data):\n    r = requests.post(f"{BASE}/shipments", json=data, headers={"Authorization": f"Bearer {API_KEY}"})\n    return r.json()''',
                language="python",
            )
            api_df = pd.DataFrame(
                {
                    "方法": ["POST", "GET", "GET", "POST", "GET"],
                    "接口": ["/v1/shipments", "/v1/shipments/{id}", "/v1/tracking/{number}", "/v1/documents", "/v1/reports"],
                    "用途": ["创建运单", "查询运单", "包裹追踪", "上传文件", "获取报表"],
                }
            )
            st.dataframe(api_df, hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">平台对接与通知</div>', unsafe_allow_html=True)
            selected = st.multiselect("选择平台", PLATFORMS, default=["Shopify", "美客多 API"])
            if st.button("立即同步订单", use_container_width=True):
                prog = st.progress(0)
                for i in range(100):
                    prog.progress(i + 1)
                st.success(f"已完成 {len(selected)} 个平台的订单同步。")
            notify = st.multiselect("通知方式", ["邮件通知", "短信通知", "平台消息", "Webhook 回调"], default=["邮件通知", "平台消息"])
            email = st.text_input("收件邮箱", value="your-email@example.com")
            webhook = st.text_input("Webhook", value="https://example.com/callback")
            if st.button("保存设置", use_container_width=True):
                st.success(f"已保存 {', '.join(notify)}，发送至 {email}。")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="footer-strip">Puente 当前集成：订单追踪 / 清关预审 / API 工具 / 数据看板。后续建议接真实物流轨迹接口与报关模板。</div>', unsafe_allow_html=True)


# =========================================================
# Main app
# =========================================================
module, account, market, global_query = render_sidebar("平台总览")

if module == "平台总览":
    render_overview(account, market)
elif module == "文化转译中枢":
    render_cultural_risk(market)
elif module == "AI 文案工坊":
    render_ai_copy_lab(market)
elif module == "ProfitLab 动态利润":
    render_profitlab()
else:
    render_puente(account)
