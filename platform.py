import os
import json
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="灵径智链 | Qwen x Plotly",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Demo data
# -----------------------------
RISK_DF = pd.DataFrame([
    ["巴西", 82, "紫色/宗教联想", "避免大面积紫色，突出礼赠与节庆"],
    ["墨西哥", 77, "黄色/节庆语境错配", "区分节庆场景与日常卖点表达"],
    ["智利", 56, "疗愈表述边界", "避免功效承诺，强调氛围和礼物属性"],
    ["阿根廷", 35, "数字/迷信表达", "减少玄学色彩，强调工艺与设计"],
], columns=["国家", "风险分", "主要风险", "建议"])

SKU_DF = pd.DataFrame([
    ["工艺扇", "低价引流", 11.0, 467, "拍照道具/节庆搭配/视觉冲击"],
    ["香囊", "文化体验", 7.5, 60, "礼赠/空间香氛/节气故事"],
    ["汉服", "品牌溢价", 31.83, 60, "东方美学/内容传播/社交展示"],
], columns=["商品", "角色", "均价USD", "月销量样本", "转译方向"])

PROFIT_SERIES = pd.DataFrame({
    "日期": pd.date_range("2026-03-01", periods=12, freq="D"),
    "利润": [-980, -820, -760, -690, -610, -580, -540, -500, -430, -380, -260, -190],
    "运费": [120, 118, 117, 114, 112, 110, 109, 108, 107, 106, 105, 104],
    "税费": [36, 37, 38, 39, 41, 42, 44, 45, 47, 49, 50, 52],
})

ORDER_STEPS = [
    ("资料预审", "已完成", "商品编码、申报名称、材质说明已校核"),
    ("税费模拟", "已完成", "完成关税与小额包裹政策冲击测算"),
    ("清关规则检查", "进行中", "检测到墨西哥节庆标签表述需修订"),
    ("履约路径建议", "待确认", "推荐深圳仓→墨西哥城经济线"),
]

SUGGESTIONS = [
    "请基于当前财务数据，生成一份完整的利润诊断与优化建议。",
    "把“中式香囊”转译为适合巴西 TikTok Shop 的商品标题和五条卖点。",
    "如果墨西哥小额包裹免税额度下调，请重算建议售价和利润边界。",
    "请做一份汉服在拉美市场的内容传播和本地化表达建议。",
]

# -----------------------------
# Helpers
# -----------------------------
def load_css():
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: linear-gradient(180deg, #020817 0%, #071122 100%);
            color: #e2e8f0;
        }
        [data-testid="stSidebar"] {
            background: #06101f;
            border-right: 1px solid rgba(56,189,248,.16);
        }
        .main .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1500px;}
        .brand-box {
            background: linear-gradient(135deg, rgba(17,24,39,.96), rgba(3,8,20,.96));
            border: 1px solid rgba(59,130,246,.18);
            border-radius: 18px; padding: 16px 18px; margin-bottom: 14px;
        }
        .brand-title {font-size: 1.35rem; font-weight: 800; color: #f8fafc;}
        .brand-sub {color: #60a5fa; font-size: .86rem; letter-spacing: .08em; text-transform: uppercase;}
        .hero-card {
            background: linear-gradient(135deg, rgba(2,6,23,.96), rgba(7,18,38,.96));
            border: 1px solid rgba(59,130,246,.16); border-radius: 22px; padding: 22px 24px; margin-bottom: 16px;
            box-shadow: 0 20px 50px rgba(2,6,23,.35);
        }
        .hero-title {font-size: 2rem; font-weight: 800; color: #f8fafc; line-height: 1.2; margin-bottom: .35rem;}
        .hero-sub {color: #93c5fd; font-size: 1rem;}
        .chip {display:inline-block; padding: 5px 12px; background: rgba(8,47,73,.55); border: 1px solid rgba(34,211,238,.22); border-radius: 999px; color:#67e8f9; font-size: .82rem; margin-right: 8px; margin-top: 6px;}
        .metric-card {
            background: linear-gradient(180deg, rgba(2,8,23,.96), rgba(3,12,26,.98));
            border: 1px solid rgba(59,130,246,.14); border-radius: 18px; padding: 16px 18px; min-height: 115px;
        }
        .metric-label {font-size: .82rem; color: #60a5fa; text-transform: uppercase; letter-spacing: .08em;}
        .metric-value {font-size: 2rem; font-weight: 800; color: #f8fafc; margin-top: 10px;}
        .metric-delta-up {color:#22c55e; font-size: .92rem;}
        .metric-delta-down {color:#fb7185; font-size: .92rem;}
        .section-card {
            background: rgba(2,8,23,.96); border:1px solid rgba(59,130,246,.14); border-radius: 18px; padding: 16px 18px; margin-top: 12px;
        }
        .section-title {font-size: 1.08rem; font-weight: 700; color: #f8fafc; margin-bottom: 10px;}
        .insight {
            background: rgba(8,47,73,.45); border-left: 4px solid #22d3ee; padding: 12px 14px; border-radius: 12px; color:#dbeafe; margin: 10px 0;
        }
        .small-note {color:#94a3b8; font-size: .88rem;}
        .stream-box {background:#020817; border:1px solid rgba(56,189,248,.15); border-radius: 18px; padding: 14px; min-height: 420px;}
        .prompt-chip {display:inline-block; padding:6px 10px; margin-right:8px; margin-bottom:8px; background:#0b1830; border:1px solid rgba(59,130,246,.18); border-radius:12px; color:#cbd5e1; font-size:.85rem;}
        .stTabs [data-baseweb="tab-list"] {gap: 8px;}
        .stTabs [data-baseweb="tab"] {background:#071122; border-radius:12px 12px 0 0; padding:10px 16px; color:#cbd5e1;}
        .stTabs [aria-selected="true"] {background:#0b1730 !important; color:#67e8f9 !important;}
        .stButton > button {
            background: linear-gradient(90deg, #2563eb, #7c3aed); color: white; border: 0; border-radius: 12px; padding: .5rem .9rem; font-weight: 700;
        }
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea, .stNumberInput input {
            background: #071122 !important; color:#e2e8f0 !important; border-radius: 12px !important; border: 1px solid rgba(59,130,246,.16) !important;
        }
        .footer-line {color:#64748b; font-size: .82rem; text-align:right; margin-top: 8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str = "", up: bool | None = None):
    delta_cls = "metric-delta-up" if up else "metric-delta-down"
    delta_html = f'<div class="{delta_cls}">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def qwen_call(prompt: str) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if api_key:
        try:
            resp = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "qwen-turbo",
                    "messages": [
                        {"role": "system", "content": "你是灵径智链平台的跨文化电商文案顾问，回答务实、可落地、适合拉美市场。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                },
                timeout=40,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            pass

    # demo fallback
    if "利润" in prompt or "定价" in prompt:
        return (
            "### ProfitLab 快速分析\n"
            "1. 当前毛利为负，核心压力来自运费与税费上升。\n"
            "2. 建议先把主推 SKU 售价上调 8%–12%，并拆分出礼盒版与基础版。\n"
            "3. 若 2026 年小额包裹免税额度下调，优先改走合规经济线，并降低单票低货值 SKU 的投放。\n"
            "4. 建议把文化转译后的高溢价卖点写进详情页，否则提价无法被消费者接受。"
        )
    return (
        "### 千问文案草案\n"
        "**标题：** 东方香氛礼袋｜适合节庆赠礼与空间氛围布置\n\n"
        "**卖点：**\n"
        "- 结合东方手作与节庆礼赠语境，更适合拉美平台内容传播\n"
        "- 强调空间香氛与仪式感，而非功效性表达\n"
        "- 适合短视频展示“开箱—悬挂—送礼”完整场景\n\n"
        "**详情页短文案：**\n"
        "这不是简单的中式挂件，而是一件适合节庆、赠礼与空间装饰的东方香氛小物。平台建议结合礼盒包装与本地节日节点投放，以提升溢价空间与内容传播效率。"
    )


# -----------------------------
# Visual builders
# -----------------------------
def profit_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=PROFIT_SERIES["日期"], y=PROFIT_SERIES["利润"],
        mode="lines+markers", name="区间利润",
        line=dict(color="#22d3ee", width=3),
        marker=dict(size=7, color="#22d3ee")
    ))
    fig.add_trace(go.Bar(
        x=PROFIT_SERIES["日期"], y=PROFIT_SERIES["税费"],
        name="税费", marker_color="rgba(124,58,237,.55)"
    ))
    fig.update_layout(
        height=360,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    return fig


def risk_bar():
    fig = px.bar(
        RISK_DF,
        x="国家",
        y="风险分",
        color="风险分",
        color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
        text="风险分",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=320,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
    )
    return fig


def sku_bubble():
    fig = px.scatter(
        SKU_DF,
        x="均价USD",
        y="月销量样本",
        size="月销量样本",
        color="角色",
        hover_name="商品",
        size_max=50,
        color_discrete_sequence=["#22d3ee", "#a855f7", "#f59e0b"],
    )
    fig.update_layout(
        height=340,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


# -----------------------------
# Pages
# -----------------------------
def page_overview():
    st.markdown('<div class="hero-card"><div class="hero-title">灵径智链 · 文化转译驱动的拉美跨境赋能平台</div><div class="hero-sub">不是另一个 Temu，而是服务高文化属性、高附加值国潮商品的第三方赋能系统</div><span class="chip">核心：文化转译</span><span class="chip">支撑：动态利润</span><span class="chip">支撑：合规预审</span></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("核心市场", "LatAm", "墨西哥 / 巴西 / 智利")
    with c2:
        kpi_card("样板SKU", "3 类", "工艺扇 / 香囊 / 汉服")
    with c3:
        kpi_card("文化风险库", "120+", "规则节点持续扩充", True)
    with c4:
        kpi_card("预审通过率", "91%", "发货前问题前置发现", True)

    left, right = st.columns((1.1, 1))
    with left:
        st.markdown('<div class="section-card"><div class="section-title">项目定位</div></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="insight">灵径智链并非面向终端消费者的综合电商平台，而是依托 Shopee、TikTok Shop、Amazon 等现有平台生态，为国潮文创、非遗及疗愈类商家提供文化转译、利润测算与合规预审的一体化 B2B 赋能服务。</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(sku_bubble(), use_container_width=True)
    with right:
        st.markdown('<div class="section-card"><div class="section-title">拉美文化风险热区</div></div>', unsafe_allow_html=True)
        st.plotly_chart(risk_bar(), use_container_width=True)
        st.markdown('<div class="small-note">系统将文化误读风险前置到上架与发货前，避免“当地人不买账”和清关表达偏差。</div>', unsafe_allow_html=True)


def page_culture():
    st.markdown('<div class="hero-card"><div class="hero-title">文化转译中枢</div><div class="hero-sub">项目的核心竞争力：把“能卖的中国商品”翻译成“当地愿意买的表达”</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns((1, 1))
    with col1:
        sku = st.selectbox("样板商品", ["香囊", "工艺扇", "汉服"])
        market = st.selectbox("目标市场", ["巴西", "墨西哥", "智利", "阿根廷"])
        raw_title = st.text_input("原始商品标题", f"中式{sku}")
        raw_desc = st.text_area("原始表达", "强调东方工艺、节气寓意、手作设计，适合礼赠与节庆搭配。", height=120)

        if st.button("生成转译建议"):
            translated = qwen_call(f"请将商品“{raw_title}”转译为适合{market}电商平台的标题、三条卖点和一句详情页短文案，避免文化误读。")
            st.session_state["culture_output"] = translated

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">文化风控结果</div></div>', unsafe_allow_html=True)
        risk_row = RISK_DF[RISK_DF["国家"] == market].iloc[0]
        st.metric("目标市场风险分", int(risk_row["风险分"]))
        st.write(f"**主要风险：** {risk_row['主要风险']}")
        st.write(f"**平台建议：** {risk_row['建议']}")
        st.markdown('<div class="section-card"><div class="section-title">AI 转译输出</div></div>', unsafe_allow_html=True)
        st.markdown(st.session_state.get("culture_output", "点击左侧按钮生成适配当地市场的标题、卖点与详情页文案。"))


def page_copylab():
    st.markdown('<div class="hero-card"><div class="hero-title">千问文案工坊</div><div class="hero-sub">不手填 API。默认直接可演示；若部署环境已配置 DASHSCOPE_API_KEY，则自动调用真实千问接口</div></div>', unsafe_allow_html=True)

    left, right = st.columns((2.2, 1))
    with left:
        st.markdown('<div class="stream-box">', unsafe_allow_html=True)
        st.write("### 输入指令")
        for s in SUGGESTIONS:
            st.markdown(f'<span class="prompt-chip">{s}</span>', unsafe_allow_html=True)
        prompt = st.text_area(
            "给千问的任务",
            "请为巴西 TikTok Shop 的“东方香囊礼袋”生成 1 个商品标题、4 条卖点、1 段详情页短文案和 3 条短视频封面口号，风格偏礼赠、空间香氛与节庆氛围，避免功效承诺。",
            height=170,
            label_visibility="collapsed",
        )
        if st.button("生成 AI 文案"):
            st.session_state["copy_output"] = qwen_call(prompt)
        st.markdown("### 生成结果")
        st.markdown(st.session_state.get("copy_output", "这里会显示千问生成的标题、卖点和详情页文案。"))
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card"><div class="section-title">使用说明</div></div>', unsafe_allow_html=True)
        st.markdown(
            "- 适合做比赛演示：不用手填 API\n"
            "- 有服务器环境变量时可自动切真实千问\n"
            "- 无 Key 时也能跑演示文案，不会空白\n"
            "- 生成内容会围绕“文化转译 + 平台适配”风格输出"
        )
        st.markdown('<div class="section-card"><div class="section-title">建议输出结构</div></div>', unsafe_allow_html=True)
        st.markdown("标题 / 卖点 / 详情页 / 封面口号 / 风险规避提示")


def page_profit():
    st.markdown('<div class="hero-card"><div class="hero-title">ProfitLab 动态利润测算</div><div class="hero-sub">不是静态计算器，而是政策波动下的动态经营决策支持工具</div></div>', unsafe_allow_html=True)

    top1, top2, top3, top4, top5 = st.columns(5)
    with top1:
        kpi_card("毛利/件", "-¥29.81", "低于变动成本", False)
    with top2:
        kpi_card("净利率", "-24.8%", "需重算建议售价", False)
    with top3:
        kpi_card("运费/件", "¥104.80", "经济线为当前主路径")
    with top4:
        kpi_card("区间利润", "-¥1.1w", "主因：税费抬升", False)
    with top5:
        kpi_card("ROI", "-219%", "当前投放不可持续", False)

    tabs = st.tabs(["盈亏分析", "情景模拟", "多SKU对比", "AI 顾问"])
    with tabs[0]:
        a, b = st.columns((2, 1))
        with a:
            st.plotly_chart(profit_chart(), use_container_width=True)
        with b:
            st.markdown('<div class="section-card"><div class="section-title">当前财务快照</div></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({
                "指标": ["运费(CNY)", "变动成本", "固定成本", "净利润率", "ROI"],
                "当前值": ["¥104.80", "¥149.81", "¥5,000", "-24.84%", "-219%"]
            }), use_container_width=True, hide_index=True)
    with tabs[1]:
        c1, c2 = st.columns((1, 2))
        with c1:
            tariff = st.slider("关税上浮", 0, 30, 12)
            fx = st.slider("汇率波动", -10, 10, 3)
            freight = st.slider("运费变动", -20, 30, 8)
            st.markdown('<div class="small-note">可用于模拟 2026 年小额包裹免税额度调整、关税波动、汇率变化等政策冲击。</div>', unsafe_allow_html=True)
        with c2:
            base_cost = 149.81
            adj_cost = base_cost * (1 + tariff/100) * (1 + freight/100) * (1 + fx/100)
            suggested = round(adj_cost * 1.35, 2)
            df = pd.DataFrame({"场景": ["当前", "政策波动后"], "单件成本": [base_cost, adj_cost], "建议售价": [190.0, suggested]})
            fig = px.bar(df, x="场景", y=["单件成本", "建议售价"], barmode="group", template="plotly_dark")
            fig.update_layout(height=330, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with tabs[2]:
        st.dataframe(SKU_DF[["商品", "角色", "均价USD", "月销量样本"]], use_container_width=True, hide_index=True)
    with tabs[3]:
        prompt = st.text_area("财务提问", "请根据当前财务数据，为我生成一份全面的盈利分析报告，包括：1.现状诊断 2.风险点识别 3.可操作的优化建议", height=120)
        if st.button("生成 ProfitLab AI 分析"):
            st.session_state["profit_ai"] = qwen_call(prompt)
        st.markdown(st.session_state.get("profit_ai", "点击按钮，让 AI 基于当前财务快照给出诊断与优化建议。"))


def page_puente():
    st.markdown('<div class="hero-card"><div class="hero-title">Puente 合规数字化预审</div><div class="hero-sub">不讲“全托管野心”，聚焦发货前预审、规则校核与履约协同建议</div></div>', unsafe_allow_html=True)

    left, right = st.columns((1.3, 1))
    with left:
        st.markdown('<div class="section-card"><div class="section-title">预审流程</div></div>', unsafe_allow_html=True)
        for i, (title, status, desc) in enumerate(ORDER_STEPS, 1):
            st.markdown(f"**{i}. {title}** · `{status}`  \\n{desc}")
            st.divider()
    with right:
        st.markdown('<div class="section-card"><div class="section-title">预审结论</div></div>', unsafe_allow_html=True)
        st.metric("当前风险等级", "中风险")
        st.write("- 申报名称需从“中式香囊”改为“东方香氛礼袋”")
        st.write("- 巴西/墨西哥文案中避免功效性用语")
        st.write("- 推荐补充材质说明与原产地标签")
        st.write("- 推荐路径：深圳仓 → 墨西哥城经济线")
        st.markdown('<div class="insight">系统目标不是替代全部后端执行，而是在货物发出前通过 AI 预审把高概率行政风险前置发现。</div>', unsafe_allow_html=True)


# -----------------------------
# Main
# -----------------------------
load_css()

with st.sidebar:
    st.markdown('<div class="brand-box"><div class="brand-title">灵径智链</div><div class="brand-sub">Qwen × Plotly Demo</div></div>', unsafe_allow_html=True)
    page = st.radio(
        "导航",
        ["平台总览", "文化转译中枢", "千问文案工坊", "ProfitLab 动态利润", "Puente 合规预审"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**当前模式**")
    st.markdown("- 核心卖点：文化转译\n- 支撑能力：动态利润\n- 风险兜底：合规预审")

if page == "平台总览":
    page_overview()
elif page == "文化转译中枢":
    page_culture()
elif page == "千问文案工坊":
    page_copylab()
elif page == "ProfitLab 动态利润":
    page_profit()
else:
    page_puente()

st.markdown(f'<div class="footer-line">LINGJING ZHILIAN · {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
