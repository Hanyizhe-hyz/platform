import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title='灵径智链 Lite', page_icon='🕊️', layout='wide', initial_sidebar_state='collapsed')

# -----------------------------
# Demo data
# -----------------------------
risk_df = pd.DataFrame([
    ["巴西", 82, "紫色宗教联想", "避免大面积紫色，突出礼赠与节庆"],
    ["墨西哥", 77, "黄色语境错配", "区分节庆表达与日常卖点"],
    ["智利", 56, "疗愈表述边界", "避免功效承诺，强调氛围和礼物属性"],
], columns=["国家", "风险分", "风险点", "建议"])

sku_df = pd.DataFrame([
    ["工艺扇", "低价引流", 11.0, 467],
    ["香囊", "文化体验", 7.5, 60],
    ["汉服", "品牌溢价", 31.8, 60],
], columns=["商品", "角色", "客单价USD", "月销量样本"])

profit_df = pd.DataFrame({
    "日期": pd.date_range("2026-03-01", periods=10, freq="D"),
    "利润": [-860, -730, -650, -590, -520, -430, -350, -260, -190, -120],
    "运费": [120, 118, 117, 114, 112, 110, 108, 106, 105, 104],
    "税费": [34, 36, 37, 38, 40, 42, 44, 46, 48, 50],
})

precheck_df = pd.DataFrame([
    ["申报名称", "通过", "建议补充材质说明"],
    ["标签用语", "预警", "避免功效性表达"],
    ["颜色元素", "预警", "不建议使用大面积紫色"],
    ["清关材料", "通过", "发票与装箱单齐全"],
], columns=["检查项", "状态", "系统提示"])

# -----------------------------
# Styles
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%); color: #0f172a;}
    .block-container {max-width: 1180px; padding-top: 1.2rem; padding-bottom: 2rem;}
    .hero {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 24px;
        padding: 24px 28px;
        box-shadow: 0 10px 30px rgba(15,23,42,0.06);
        margin-bottom: 14px;
    }
    .hero h1 {font-size: 2rem; margin: 0 0 6px 0; color:#0f172a;}
    .hero p {margin: 0; color:#475569; font-size: 1rem;}
    .chip {display:inline-block; padding:6px 12px; border-radius:999px; background:#e0ecff; color:#1d4ed8; margin-right:8px; margin-top:10px; font-size:.86rem;}
    .card {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 20px;
        padding: 18px 18px 14px 18px;
        box-shadow: 0 8px 24px rgba(15,23,42,0.05);
    }
    .kpi-label {color:#64748b; font-size:.86rem;}
    .kpi-value {font-size:1.8rem; font-weight:800; color:#0f172a; margin-top:6px;}
    .mini {color:#64748b; font-size:.86rem;}
    .section-title {font-size:1.1rem; font-weight:700; color:#0f172a; margin-bottom:8px;}
    .subtle {color:#64748b;}
    .status-ok {color:#16a34a; font-weight:700;}
    .status-warn {color:#dc2626; font-weight:700;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {
        background:#ffffff; border-radius:12px 12px 0 0; padding:10px 18px; border:1px solid rgba(148,163,184,0.18);
    }
    .stTabs [aria-selected="true"] {background:#dbeafe !important; color:#1d4ed8 !important;}
    .stButton>button {
        border-radius: 12px; border: 0; background: linear-gradient(90deg, #3b82f6, #60a5fa); color: white; font-weight: 700;
    }
    div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
        background: #ffffff !important; border-radius:12px !important; border:1px solid rgba(148,163,184,0.24) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# AI
# -----------------------------
def qwen_generate(prompt: str) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("当前环境未配置 DASHSCOPE_API_KEY，无法真实调用千问。")

    response = requests.post(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "qwen-turbo",
            "messages": [
                {"role": "system", "content": "你是灵径智链的跨文化电商文案助手，请输出务实、简洁、适合拉美电商平台的中文结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# -----------------------------
# Charts
# -----------------------------
def fig_profit_trend():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=profit_df["日期"], y=profit_df["利润"], mode="lines+markers", name="利润",
        line=dict(color="#3b82f6", width=3), marker=dict(size=8, color="#3b82f6")
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=10, t=20, b=20), showlegend=False,
        font=dict(color="#334155")
    )
    return fig


def fig_risk():
    fig = px.bar(risk_df, x="国家", y="风险分", text="风险分", color="风险分",
                 color_continuous_scale=["#bfdbfe", "#60a5fa", "#2563eb"])
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=300,
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=10, t=10, b=20), font=dict(color="#334155")
    )
    return fig


def fig_sku():
    fig = px.scatter(
        sku_df, x="客单价USD", y="月销量样本", size="月销量样本", color="角色",
        hover_name="商品", size_max=42,
        color_discrete_sequence=["#60a5fa", "#818cf8", "#f59e0b"]
    )
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=10, t=10, b=20), font=dict(color="#334155")
    )
    return fig


# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <div class="hero">
        <h1>灵径智链 Lite</h1>
        <p>面向拉美平台生态的国潮出海前端原型：文化转译为核心，动态利润与合规预审为支撑。</p>
        <span class="chip">文化转译</span>
        <span class="chip">AI文案</span>
        <span class="chip">动态利润</span>
        <span class="chip">合规预审</span>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.radio(
    "",
    ["平台总览", "文化转译", "AI文案生成", "ProfitLab", "合规预审"],
    horizontal=True,
    label_visibility="collapsed",
)


if page == "平台总览":
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><div class="kpi-label">核心卖点</div><div class="kpi-value">文化转译</div><div class="mini">服务高文化属性、高附加值国潮商品</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="kpi-label">支撑一</div><div class="kpi-value">动态利润</div><div class="mini">关税、汇率、税费变化下快速测算</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card"><div class="kpi-label">支撑二</div><div class="kpi-value">合规预审</div><div class="mini">发货前检查表达、材料与清关风险</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown('<div class="card"><div class="section-title">代表性商品结构</div></div>', unsafe_allow_html=True)
        st.plotly_chart(fig_sku(), use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown('<div class="card"><div class="section-title">重点国家文化风险</div></div>', unsafe_allow_html=True)
        st.plotly_chart(fig_risk(), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="card"><div class="section-title">平台定位</div><div class="subtle">灵径智链不是交易平台，而是依托 Shopee、TikTok Shop、Amazon 等生态运行的第三方赋能工具。</div></div>', unsafe_allow_html=True)

elif page == "文化转译":
    col1, col2 = st.columns([1, 1])
    with col1:
        product = st.selectbox("商品", ["香囊", "工艺扇", "汉服"])
        country = st.selectbox("目标市场", ["巴西", "墨西哥", "智利"])
        original = st.text_area("原始表达", value="中式香囊，具有传统吉祥寓意，适合随身佩戴。", height=140)
    with col2:
        st.markdown('<div class="card"><div class="section-title">系统建议</div></div>', unsafe_allow_html=True)
        if product == "香囊":
            st.text_area("转译建议", value="建议转译为节庆赠礼与空间香氛小物，避免功效承诺，突出手作、礼赠和氛围感。", height=140)
        elif product == "工艺扇":
            st.text_area("转译建议", value="建议转译为拍照道具、节庆搭配与视觉造型单品，强调轻便与内容传播属性。", height=140)
        else:
            st.text_area("转译建议", value="建议强调东方美学、节庆造型与内容传播属性，避免过于生硬的传统服饰直译。", height=140)

        risk_row = risk_df[risk_df["国家"] == country].iloc[0]
        status_class = "status-warn" if risk_row["风险分"] >= 70 else "status-ok"
        st.markdown(f'<div class="card"><div class="section-title">风险提示</div><div class="{status_class}">{country} 风险分：{risk_row["风险分"]}</div><div class="subtle">{risk_row["风险点"]}｜{risk_row["建议"]}</div></div>', unsafe_allow_html=True)

elif page == "AI文案生成":
    st.markdown('<div class="card"><div class="section-title">千问文案工坊</div><div class="subtle">直接输入需求，调用真实千问生成文案。未配置环境变量时会报错提示。</div></div>', unsafe_allow_html=True)
    product = st.text_input("商品名称", value="香囊")
    platform = st.selectbox("平台", ["TikTok Shop", "Shopee", "Amazon"])
    market = st.selectbox("市场", ["巴西", "墨西哥", "智利"])
    scene = st.selectbox("场景", ["商品标题", "五条卖点", "详情页短文案", "短视频口播"])
    extra = st.text_area("补充要求", value="强调礼赠、空间氛围和手作感，避免功效性表述。", height=110)

    if st.button("生成文案", use_container_width=False):
        prompt = f"请为{market}{platform}上的{product}生成{scene}，补充要求：{extra}。输出中文，简洁可直接用于平台。"
        try:
            result = qwen_generate(prompt)
            st.success("生成成功")
            st.text_area("生成结果", value=result, height=260)
        except Exception as e:
            st.error(str(e))

elif page == "ProfitLab":
    top1, top2, top3 = st.columns(3)
    with top1:
        st.markdown('<div class="card"><div class="kpi-label">单件净利润</div><div class="kpi-value">-¥29.8</div></div>', unsafe_allow_html=True)
    with top2:
        st.markdown('<div class="card"><div class="kpi-label">净利率</div><div class="kpi-value">-24.8%</div></div>', unsafe_allow_html=True)
    with top3:
        st.markdown('<div class="card"><div class="kpi-label">动态建议</div><div class="kpi-value">调价 +8%</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="section-title">利润趋势</div></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_profit_trend(), use_container_width=True, config={"displayModeBar": False})

    c1, c2 = st.columns([1.1, 1])
    with c1:
        tariff = st.slider("政策波动冲击（税费上调 %）", 0, 30, 12)
        fx = st.slider("汇率波动（%）", -10, 10, 3)
        price = st.number_input("建议售价（USD）", value=18.0, step=0.5)
        st.markdown(f'<div class="card"><div class="section-title">测算结论</div><div class="subtle">当税费上调 <b>{tariff}%</b>、汇率波动 <b>{fx}%</b> 时，系统建议优先提升售价并优化低货值SKU投放。</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="section-title">核心提示</div><div class="subtle">ProfitLab 用于政策波动下的动态重算，不只是静态成本计算。</div></div>', unsafe_allow_html=True)

elif page == "合规预审":
    st.markdown('<div class="card"><div class="section-title">Puente 合规数字化预审</div><div class="subtle">发货前检查表达、材料与清关要点，降低行政风险。</div></div>', unsafe_allow_html=True)
    st.dataframe(precheck_df, use_container_width=True, hide_index=True)
    st.markdown('<div class="card"><div class="section-title">系统建议</div><div class="subtle">当前最优先处理项：<b>标签用语</b>。建议将描述改为礼赠、装饰、氛围用途，避免功效性表达后再发货。</div></div>', unsafe_allow_html=True)

st.caption(f"Lite Demo · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
