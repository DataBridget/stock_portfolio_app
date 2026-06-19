"""
A股智能投资组合配置平台 - 主应用
智投组合 | Smart Portfolio
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_fetcher import (
    get_all_stocks, get_stock_history, get_stock_latest_data,
    get_hs300_stocks, get_sz50_stocks, get_zz500_stocks,
    prepare_portfolio_data, get_stock_industry, get_index_data
)
from utils.portfolio_optimizer import (
    PortfolioOptimizer, recommend_portfolio, hedge_analysis
)
from utils.report_generator import (
    generate_report_data, generate_word_report, generate_pdf_report
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="智投组合 | A股智能投资组合配置",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 自定义CSS ====================
custom_css = """
<style>
    :root {
        --primary-color: #1E88E5;
        --secondary-color: #26A69A;
        --accent-color: #FF7043;
        --bg-color: #F8FAFC;
        --card-bg: #FFFFFF;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: var(--bg-color); }
    .card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 16px;
        border: 1px solid #E8ECF0;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(30,136,229,0.3);
    }
    .metric-card.green {
        background: linear-gradient(135deg, #26A69A 0%, #00897B 100%);
        box-shadow: 0 4px 12px rgba(38,166,154,0.3);
    }
    .metric-card.orange {
        background: linear-gradient(135deg, #FF7043 0%, #E64A19 100%);
        box-shadow: 0 4px 12px rgba(255,112,67,0.3);
    }
    .metric-card.purple {
        background: linear-gradient(135deg, #7E57C2 0%, #5E35B1 100%);
        box-shadow: 0 4px 12px rgba(126,87,194,0.3);
    }
    .metric-value { font-size: 28px; font-weight: bold; margin: 8px 0; }
    .metric-label { font-size: 13px; opacity: 0.9; }
    .main-title { font-size: 32px; font-weight: bold; color: #1A237E; margin-bottom: 8px; }
    .sub-title { font-size: 16px; color: #546E7A; margin-bottom: 24px; }
    .dataframe th { background-color: #1E88E5; color: white; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #1E88E5; }
    .stButton > button {
        background-color: #1E88E5; color: white; border-radius: 8px;
        font-weight: bold; transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #1565C0; transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30,136,229,0.4);
    }
    .info-box {
        background: #E3F2FD; border-left: 4px solid #2196F3;
        padding: 12px 16px; border-radius: 4px; margin: 12px 0;
    }
    .divider {
        height: 2px;
        background: linear-gradient(to right, #1E88E5, #26A69A, transparent);
        margin: 24px 0; border-radius: 1px;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.5s ease-in; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==================== 初始化Session State ====================
if 'stock_list' not in st.session_state:
    st.session_state.stock_list = []
if 'portfolio_result' not in st.session_state:
    st.session_state.portfolio_result = None
if 'hedge_result' not in st.session_state:
    st.session_state.hedge_result = None
if 'returns_df' not in st.session_state:
    st.session_state.returns_df = None
if 'price_df' not in st.session_state:
    st.session_state.price_df = None
if 'all_stocks_df' not in st.session_state:
    st.session_state.all_stocks_df = None

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:20px 0;">
        <h1 style="color:#1E88E5; margin:0;">📊 智投组合</h1>
        <p style="color:#546E7A; font-size:12px;">A股智能投资组合配置平台</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 导航
    st.subheader("📋 功能导航")
    nav_page = st.radio(
        "选择功能模块",
        ["🏠 首页概览", "📈 组合配置", "🔍 市场数据", "📉 风险分析", "📄 下载报告", "🏢 关于我们"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # 快速设置
    st.subheader("⚙️ 快速设置")
    risk_level = st.selectbox(
        "风险承受等级",
        ["conservative", "moderate", "balanced", "growth", "aggressive"],
        format_func=lambda x: {
            "conservative": "🛡️ 保守型",
            "moderate": "⚖️ 稳健型",
            "balanced": "📊 均衡型",
            "growth": "🚀 进取型",
            "aggressive": "🔥 激进型"
        }[x],
        key="risk_level"
    )

    capital = st.number_input(
        "投资金额 (元)",
        min_value=10000,
        max_value=100000000,
        value=100000,
        step=10000,
        format="%d"
    )

    st.markdown("---")

    # 数据信息
    st.subheader("📡 数据信息")
    st.markdown(f"""
    <div class="info-box">
        <strong>数据来源：</strong> BaoStock<br>
        <strong>更新频率：</strong> 每日收盘后<br>
        <strong>覆盖范围：</strong> 全部A股上市公司<br>
        <strong>当前日期：</strong> {datetime.now().strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("© 2024 智投组合 | Smart Portfolio")


# ==================== 页面渲染函数 ====================
def _render_home():
    """首页概览"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">📊 智投组合 - A股智能投资组合配置平台</h1>
        <p class="sub-title">基于现代投资组合理论，运用大数据技术，为您量身定制最优投资组合方案</p>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">覆盖A股数量</div>
            <div class="metric-value">5,000+</div>
            <div class="metric-label">全部上市公司</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card green">
            <div class="metric-label">优化策略</div>
            <div class="metric-value">5种</div>
            <div class="metric-label">MPT/BL/风险平价等</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card orange">
            <div class="metric-label">风险等级</div>
            <div class="metric-value">5级</div>
            <div class="metric-label">个性化适配</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card purple">
            <div class="metric-label">报告格式</div>
            <div class="metric-value">Word/PDF</div>
            <div class="metric-label">一键下载</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 功能介绍
    st.markdown("""
    <div class="card">
        <h2 style="color:#1A237E;">🎯 核心功能</h2>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="card" style="text-align:center;">
            <h3 style="color:#1E88E5;">📈 智能组合配置</h3>
            <p>基于现代投资组合理论(MPT)，运用均值-方差优化、风险平价、Black-Litterman等模型，
            为不同风险偏好的投资者推荐最优组合权重。</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card" style="text-align:center;">
            <h3 style="color:#26A69A;">🛡️ 风险对冲分析</h3>
            <p>通过行业分散、风格对冲、相关性分析等手段，评估组合的系统性风险和特异性风险，
            计算VaR、CVaR、最大回撤等关键风险指标。</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="card" style="text-align:center;">
            <h3 style="color:#FF7043;">📊 可视化分析</h3>
            <p>提供有效前沿、风险收益散点图、权重饼图、相关性热力图等多种可视化图表，
            直观展示组合特征和风险分布。</p>
        </div>
        """, unsafe_allow_html=True)

    # 市场概览
    st.markdown("""
    <div class="card">
        <h2 style="color:#1A237E;">🌐 市场概览</h2>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        with st.spinner("正在加载市场数据..."):
            index_codes = {
                '上证综指': 'sh.000001',
                '深证成指': 'sz.399001',
                '沪深300': 'sh.000300',
                '创业板指': 'sz.399006',
            }
            index_data = {}
            for name, code in index_codes.items():
                try:
                    df = get_index_data(code)
                    if not df.empty:
                        latest = df.iloc[-1]
                        index_data[name] = {
                            'close': latest['close'],
                            'pctChg': latest['pctChg'],
                            'date': latest['date'].strftime('%Y-%m-%d') if hasattr(latest['date'], 'strftime') else str(latest['date'])
                        }
                except Exception:
                    pass

            if index_data:
                idx_cols = st.columns(len(index_data))
                for i, (name, data) in enumerate(index_data.items()):
                    with idx_cols[i]:
                        color = "#E53935" if data['pctChg'] < 0 else "#43A047"
                        st.markdown(f"""
                        <div class="card" style="text-align:center;">
                            <h4 style="color:#37474F;">{name}</h4>
                            <h2 style="color:{color};">{data['close']:.2f}</h2>
                            <p style="color:{color}; font-size:14px;">
                                {'▲' if data['pctChg'] >= 0 else '▼'} {abs(data['pctChg']):.2f}%
                            </p>
                            <p style="color:#90A4AE; font-size:11px;">{data['date']}</p>
                        </div>
                        """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"市场数据加载中，请稍后再试: {str(e)}")

    # 使用指南
    st.markdown("""
    <div class="card">
        <h2 style="color:#1A237E;">📖 使用指南</h2>
        <div class="divider"></div>
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
            <div style="text-align:center; padding:16px;">
                <div style="font-size:32px;">1️⃣</div>
                <h4>选择风险等级</h4>
                <p style="font-size:13px; color:#546E7A;">在左侧选择您的风险承受等级和投资金额</p>
            </div>
            <div style="text-align:center; padding:16px;">
                <div style="font-size:32px;">2️⃣</div>
                <h4>配置组合</h4>
                <p style="font-size:13px; color:#546E7A;">系统自动推荐最优组合权重配置</p>
            </div>
            <div style="text-align:center; padding:16px;">
                <div style="font-size:32px;">3️⃣</div>
                <h4>分析风险</h4>
                <p style="font-size:13px; color:#546E7A;">查看详细的风险对冲分析报告</p>
            </div>
            <div style="text-align:center; padding:16px;">
                <div style="font-size:32px;">4️⃣</div>
                <h4>下载报告</h4>
                <p style="font-size:13px; color:#546E7A;">一键下载Word或PDF格式分析报告</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_portfolio():
    """组合配置页面"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">📈 智能组合配置</h1>
        <p class="sub-title">基于您的风险偏好和资金规模，为您推荐最优投资组合</p>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    risk_info = {
        'conservative': {'name': '🛡️ 保守型', 'desc': '以资本保值为目标，追求稳定收益', 'color': '#26A69A'},
        'moderate': {'name': '⚖️ 稳健型', 'desc': '控制风险前提下追求适度收益', 'color': '#1E88E5'},
        'balanced': {'name': '📊 均衡型', 'desc': '兼顾风险与收益的最优配置', 'color': '#7E57C2'},
        'growth': {'name': '🚀 进取型', 'desc': '追求较高收益，承受较大波动', 'color': '#FF7043'},
        'aggressive': {'name': '🔥 激进型', 'desc': '追求最大化收益，承受高风险', 'color': '#E53935'},
    }

    current_risk = risk_info.get(risk_level, risk_info['balanced'])
    st.markdown(f"""
    <div class="card" style="border-left: 4px solid {current_risk['color']};">
        <h3>{current_risk['name']} - {capital:,.0f}元</h3>
        <p>{current_risk['desc']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">🎯 选择股票池</h3>
    </div>
    """, unsafe_allow_html=True)

    pool_option = st.selectbox(
        "选择股票池来源",
        ["沪深300成分股", "上证50成分股", "中证500成分股", "自定义股票池"],
        key="pool_option"
    )

    if pool_option == "自定义股票池":
        st.info("请在下方输入自定义股票代码（每行一个，格式如 sh.600000）")
        custom_stocks = st.text_area("输入股票代码", height=100,
                                      placeholder="sh.600000\nsh.600036\nsz.000001\nsz.000858")
    else:
        custom_stocks = ""

    if st.button("🚀 开始智能配置", type="primary", use_container_width=True):
        with st.spinner("正在获取数据并优化组合，请稍候..."):
            try:
                if pool_option == "沪深300成分股":
                    stock_pool = get_hs300_stocks()
                elif pool_option == "上证50成分股":
                    stock_pool = get_sz50_stocks()
                elif pool_option == "中证500成分股":
                    stock_pool = get_zz500_stocks()
                else:
                    codes = [c.strip() for c in custom_stocks.strip().split('\n') if c.strip()]
                    if codes:
                        all_stocks = get_all_stocks()
                        stock_pool = all_stocks[all_stocks['code'].isin(codes)]
                    else:
                        st.error("请输入股票代码")
                        return

                if stock_pool.empty:
                    st.error("未找到股票池数据")
                    return

                stock_codes = stock_pool['code'].tolist()
                st.session_state.stock_list = stock_codes

                price_df, returns_df = prepare_portfolio_data(stock_codes[:50])

                if returns_df.empty:
                    st.error("数据获取失败，请稍后重试")
                    return

                st.session_state.returns_df = returns_df
                st.session_state.price_df = price_df

                result = recommend_portfolio(returns_df, risk_level, capital)
                st.session_state.portfolio_result = result

                if result:
                    weights = np.array([result['weights'].get(c, 0) for c in returns_df.columns])
                    hedge = hedge_analysis(returns_df, weights)
                    st.session_state.hedge_result = hedge

                st.success("✅ 组合配置完成！")

            except Exception as e:
                st.error(f"配置失败: {str(e)}")

    # 显示结果
    if st.session_state.portfolio_result:
        result = st.session_state.portfolio_result
        hedge = st.session_state.hedge_result

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <h3 style="color:#1A237E;">📊 推荐组合概览</h3>
            <div class="divider"></div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">预期年化收益率</div>
                <div class="metric-value">{result['expected_return']:.2%}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card green">
                <div class="metric-label">年化波动率</div>
                <div class="metric-value">{result['volatility']:.2%}</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card orange">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{result['sharpe_ratio']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="metric-card purple">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value">{result['max_drawdown']:.2%}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown("""
            <div class="card">
                <h3 style="color:#1A237E;">📋 持仓明细</h3>
            </div>
            """, unsafe_allow_html=True)

            holdings_data = []
            for code, weight in sorted(result['weights'].items(), key=lambda x: x[1], reverse=True):
                if weight > 0.001:
                    holdings_data.append({
                        '股票代码': code,
                        '配置权重': f"{weight:.2%}",
                        '配置金额': f"¥{weight * capital:,.0f}",
                        '风险贡献': f"{result['risk_contribution'].get(code, 0):.2%}"
                    })
            if holdings_data:
                st.dataframe(pd.DataFrame(holdings_data), use_container_width=True, hide_index=True)

        with col_right:
            st.markdown("""
            <div class="card">
                <h3 style="color:#1A237E;">📈 可视化图表</h3>
            </div>
            """, unsafe_allow_html=True)

            import plotly.express as px
            import plotly.graph_objects as go

            weights_filtered = {k: v for k, v in result['weights'].items() if v > 0.005}
            if weights_filtered:
                labels = list(weights_filtered.keys())
                values = list(weights_filtered.values())
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels, values=values, hole=0.4,
                    textinfo='label+percent', textposition='outside',
                    marker=dict(colors=px.colors.qualitative.Set3[:len(labels)])
                )])
                fig_pie.update_layout(
                    title="组合权重分布", height=400,
                    margin=dict(t=40, b=20, l=20, r=20), showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <h3 style="color:#1A237E;">📉 风险指标详情</h3>
            <div class="divider"></div>
        </div>
        """, unsafe_allow_html=True)

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("95% VaR", f"{result['var_95']:.2%}")
        with r2:
            st.metric("95% CVaR", f"{result['cvar_95']:.2%}")
        with r3:
            st.metric("市场Beta", f"{result['market_beta']:.4f}")
        with r4:
            if hedge:
                st.metric("对冲有效性", f"{hedge['hedge_effectiveness']:.2%}")

        if hedge:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="card">
                <h3 style="color:#1A237E;">🛡️ 对冲分析</h3>
                <div class="divider"></div>
            </div>
            """, unsafe_allow_html=True)
            h1, h2, h3 = st.columns(3)
            with h1:
                st.metric("市场相关性", f"{hedge['market_correlation']:.4f}")
            with h2:
                st.metric("分散化比率", f"{hedge['diversification_ratio']:.4f}")
            with h3:
                st.metric("平均股票相关性", f"{hedge['avg_stock_correlation']:.4f}")


def _render_market():
    """市场数据页面"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">🔍 市场数据</h1>
        <p class="sub-title">实时A股市场数据查询与分析</p>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 指数行情", "🔍 个股查询", "📊 行业分布"])

    with tab1:
        st.markdown("""
        <div class="card">
            <h3 style="color:#1A237E;">主要指数走势</h3>
        </div>
        """, unsafe_allow_html=True)

        import plotly.graph_objects as go

        index_codes = {
            '上证综指': 'sh.000001',
            '深证成指': 'sz.399001',
            '沪深300': 'sh.000300',
            '创业板指': 'sz.399006',
        }
        for name, code in index_codes.items():
            try:
                with st.spinner(f"加载{name}数据..."):
                    df = get_index_data(code)
                    if not df.empty:
                        fig = go.Figure(data=[go.Candlestick(
                            x=df['date'], open=df['open'], high=df['high'],
                            low=df['low'], close=df['close'], name=name
                        )])
                        fig.update_layout(
                            title=f"{name}近期走势", height=350,
                            xaxis_rangeslider_visible=False, template='plotly_white'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.warning(f"{name}数据加载失败")

    with tab2:
        st.markdown("""
        <div class="card">
            <h3 style="color:#1A237E;">个股行情查询</h3>
        </div>
        """, unsafe_allow_html=True)

        search_code = st.text_input("输入股票代码", placeholder="sh.600000 或 sz.000001")
        period = st.selectbox("查询周期", ["近3个月", "近6个月", "近1年", "近2年"])

        if search_code and st.button("🔍 查询"):
            try:
                days_map = {"近3个月": 90, "近6个月": 180, "近1年": 365, "近2年": 730}
                df = get_stock_history(search_code, period_days=days_map.get(period, 365))
                if not df.empty:
                    import plotly.graph_objects as go
                    fig = go.Figure(data=[go.Candlestick(
                        x=df['date'], open=df['open'], high=df['high'],
                        low=df['low'], close=df['close'], name=search_code
                    )])
                    fig.update_layout(
                        title=f"{search_code} K线图", height=400,
                        xaxis_rangeslider_visible=False, template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    latest = df.iloc[-1]
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("最新价", f"¥{latest['close']:.2f}")
                    with c2:
                        st.metric("涨跌幅", f"{latest['pctChg']:.2f}%")
                    with c3:
                        st.metric("市盈率(TTM)", f"{latest['peTTM']:.2f}")
                    with c4:
                        st.metric("市净率", f"{latest['pbMRQ']:.2f}")
                else:
                    st.warning("未找到数据")
            except Exception as e:
                st.error(f"查询失败: {str(e)}")

    with tab3:
        st.markdown("""
        <div class="card">
            <h3 style="color:#1A237E;">行业分布</h3>
        </div>
        """, unsafe_allow_html=True)
        try:
            with st.spinner("加载行业数据..."):
                industry_df = get_stock_industry()
                if not industry_df.empty:
                    industry_counts = industry_df['industry'].value_counts().head(20)
                    import plotly.express as px
                    fig = px.bar(
                        industry_counts, orientation='h',
                        title="A股行业分布（Top 20）",
                        color=industry_counts.values, color_continuous_scale='Blues'
                    )
                    fig.update_layout(height=500, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"行业数据加载失败: {str(e)}")


def _render_risk():
    """风险分析页面"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">📉 风险分析</h1>
        <p class="sub-title">深入分析投资组合的风险特征和对冲效果</p>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.returns_df is None:
        st.info("请先在「组合配置」页面生成投资组合，然后返回此处查看风险分析。")
        return

    returns_df = st.session_state.returns_df
    result = st.session_state.portfolio_result
    hedge = st.session_state.hedge_result

    import plotly.express as px
    import plotly.graph_objects as go

    # 相关性热力图
    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">🔥 股票相关性热力图</h3>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    significant_stocks = [c for c in returns_df.columns if result['weights'].get(c, 0) > 0.01]
    if significant_stocks:
        corr_df = returns_df[significant_stocks].corr()
        fig = px.imshow(corr_df, title="组合内股票相关性矩阵",
                        color_continuous_scale='RdBu_r', zmin=-1, zmax=1, height=600)
        st.plotly_chart(fig, use_container_width=True)

    # 蒙特卡洛模拟
    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">🎲 蒙特卡洛模拟</h3>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("开始蒙特卡洛模拟 (5000次)", type="primary"):
        with st.spinner("正在运行蒙特卡洛模拟..."):
            optimizer = PortfolioOptimizer(returns_df)
            mc_results = optimizer.monte_carlo_simulation(n_simulations=5000)
            fig = px.scatter(mc_results, x='volatility', y='return', color='sharpe',
                            title="蒙特卡洛模拟 - 风险收益分布",
                            color_continuous_scale='RdYlGn', height=500,
                            labels={'volatility': '年化波动率', 'return': '年化收益率', 'sharpe': '夏普比率'})
            if result:
                fig.add_scatter(x=[result['volatility']], y=[result['expected_return']],
                               mode='markers', marker=dict(size=15, color='red', symbol='star'),
                               name='推荐组合')
            fig.update_layout(template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)

    # 有效前沿
    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">📐 有效前沿</h3>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("计算有效前沿"):
        with st.spinner("正在计算有效前沿..."):
            optimizer = PortfolioOptimizer(returns_df)
            frontier = optimizer.efficient_frontier(n_points=30)
            if not frontier.empty:
                fig = go.Figure()
                fig.add_scatter(x=frontier['volatility'], y=frontier['return'],
                               mode='lines+markers', name='有效前沿',
                               line=dict(color='#1E88E5', width=2))
                if result:
                    fig.add_scatter(x=[result['volatility']], y=[result['expected_return']],
                                   mode='markers', marker=dict(size=15, color='red', symbol='star'),
                                   name='推荐组合')
                fig.update_layout(title="有效前沿", xaxis_title="年化波动率",
                                 yaxis_title="年化收益率", height=450, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)

    # VaR分布图
    if result:
        st.markdown("""
        <div class="card">
            <h3 style="color:#1A237E;">📊 收益分布与VaR</h3>
            <div class="divider"></div>
        </div>
        """, unsafe_allow_html=True)

        weights = np.array([result['weights'].get(c, 0) for c in returns_df.columns])
        portfolio_returns = returns_df @ weights

        fig = px.histogram(portfolio_returns, nbins=50, title="组合日收益率分布",
                          color_discrete_sequence=['#1E88E5'])
        var_line = np.percentile(portfolio_returns, 5)
        fig.add_vline(x=var_line, line_dash="dash", line_color="red",
                     annotation_text=f"95% VaR: {var_line:.4f}")
        fig.update_layout(template='plotly_white', height=400)
        st.plotly_chart(fig, use_container_width=True)


def _render_report():
    """报告下载页面"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">📄 下载分析报告</h1>
        <p class="sub-title">一键下载完整的投资组合分析报告</p>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.portfolio_result is None:
        st.info("请先在「组合配置」页面生成投资组合，然后返回此处下载报告。")
        return

    result = st.session_state.portfolio_result
    hedge = st.session_state.hedge_result

    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">📋 报告预览</h3>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card" style="border-left: 4px solid #1E88E5;">
        <h3>📊 {result['name']}</h3>
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>预期年化收益率</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{result['expected_return']:.2%}</td>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>年化波动率</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{result['volatility']:.2%}</td>
            </tr>
            <tr>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>夏普比率</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{result['sharpe_ratio']:.2f}</td>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>最大回撤</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{result['max_drawdown']:.2%}</td>
            </tr>
            <tr>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>95% VaR</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{result['var_95']:.2%}</td>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>投资金额</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee;">¥{result['capital']:,.0f}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">📋 持仓概览</h3>
    </div>
    """, unsafe_allow_html=True)

    holdings = []
    for code, weight in sorted(result['weights'].items(), key=lambda x: x[1], reverse=True):
        if weight > 0.001:
            holdings.append({
                '股票代码': code,
                '配置权重': f"{weight:.2%}",
                '配置金额': f"¥{weight * result['capital']:,.0f}",
            })
    if holdings:
        st.dataframe(pd.DataFrame(holdings), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">⬇️ 下载报告</h3>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        all_stocks = get_all_stocks()
        report_data = generate_report_data(result, hedge, all_stocks, st.session_state.returns_df)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="text-align:center; padding:20px;">
                <div style="font-size:48px;">📝</div>
                <h3 style="color:#1E88E5;">Word格式报告</h3>
                <p style="color:#546E7A;">包含完整的组合分析、持仓明细、对冲分析和风险提示</p>
            </div>
            """, unsafe_allow_html=True)
            try:
                word_buffer = generate_word_report(report_data)
                st.download_button(
                    label="⬇️ 下载Word报告",
                    data=word_buffer.getvalue(),
                    file_name=f"投资组合分析报告_{datetime.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True, type="primary"
                )
            except Exception as e:
                st.error(f"Word报告生成失败: {str(e)}")

        with col2:
            st.markdown("""
            <div style="text-align:center; padding:20px;">
                <div style="font-size:48px;">📄</div>
                <h3 style="color:#E53935;">PDF格式报告</h3>
                <p style="color:#546E7A;">适合打印和正式提交的专业格式报告</p>
            </div>
            """, unsafe_allow_html=True)
            try:
                pdf_buffer = generate_pdf_report(report_data)
                st.download_button(
                    label="⬇️ 下载PDF报告",
                    data=pdf_buffer.getvalue(),
                    file_name=f"投资组合分析报告_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True, type="primary"
                )
            except Exception as e:
                st.error(f"PDF报告生成失败: {str(e)}")

    except Exception as e:
        st.error(f"报告生成失败: {str(e)}")


def _render_about():
    """关于我们页面"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">🏢 关于我们</h1>
        <p class="sub-title">智投组合 - A股智能投资组合配置平台</p>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h2 style="color:#1A237E;">📊 智投组合 - 公司介绍</h2>
        <div class="divider"></div>

        <p style="font-size:16px; line-height:1.8;">
        <strong>智投组合</strong>是一家专注于A股市场智能投资组合配置的金融科技平台。我们致力于运用
        现代量化投资理论和大数据技术，为不同资金规模和风险偏好的投资者提供科学、专业的投资组合推荐服务。
        </p>

        <br>

        <h3 style="color:#1E88E5;">🎯 我们的使命</h3>
        <p style="font-size:15px; line-height:1.8;">
        让每一位投资者都能享受到机构级别的量化投资服务，通过科学的资产配置和风险管理，
        实现财富的稳健增长。我们相信，科学的投资方法可以帮助投资者在控制风险的同时，最大化投资回报。
        </p>

        <br>

        <h3 style="color:#1E88E5;">🔬 核心技术</h3>
        <ul style="font-size:15px; line-height:2;">
            <li><strong>现代投资组合理论 (MPT)</strong>：基于Markowitz均值-方差模型，优化风险收益比</li>
            <li><strong>风险平价模型</strong>：等风险贡献配置，降低组合对单一资产的依赖</li>
            <li><strong>Black-Litterman模型</strong>：融合市场均衡与投资者观点的贝叶斯方法</li>
            <li><strong>蒙特卡洛模拟</strong>：大规模随机模拟，评估组合在各种市场环境下的表现</li>
            <li><strong>大数据分析</strong>：覆盖全部A股上市公司，多维度财务和行情数据分析</li>
            <li><strong>风险对冲策略</strong>：通过行业分散、风格对冲降低系统性风险</li>
        </ul>

        <br>

        <h3 style="color:#1E88E5;">📊 数据来源</h3>
        <p style="font-size:15px; line-height:1.8;">
        本平台所有数据均来自 <strong>BaoStock</strong>（www.baostock.com），一个免费、开源的证券数据平台。
        数据覆盖1990年至今的全部A股历史行情数据、上市公司财务数据等，确保数据的准确性和完整性。
        </p>

        <br>

        <h3 style="color:#1E88E5;">⚠️ 风险提示</h3>
        <div style="background:#FFF3E0; padding:16px; border-radius:8px; border-left:4px solid #FF9800;">
            <p style="font-size:14px; line-height:1.8; color:#E65100;">
            <strong>重要声明：</strong>本平台提供的所有投资组合推荐和分析报告仅供参考，不构成任何投资建议。
            股票市场存在风险，投资需谨慎。过往业绩不代表未来表现。
            </p>
        </div>

        <br>

        <h3 style="color:#1E88E5;">📧 联系我们</h3>
        <ul style="font-size:15px; line-height:2;">
            <li>📧 Email: contact@zhitou-portfolio.com</li>
            <li>🌐 Website: https://zhitou-portfolio.com</li>
            <li>📱 GitHub: https://github.com/zhitou-portfolio</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="color:#1A237E;">🛠️ 技术栈</h3>
        <div class="divider"></div>
        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
            <div style="text-align:center; padding:16px; background:#F5F5F5; border-radius:8px;">
                <h4>Python</h4>
                <p style="font-size:12px; color:#546E7A;">核心开发语言</p>
            </div>
            <div style="text-align:center; padding:16px; background:#F5F5F5; border-radius:8px;">
                <h4>Streamlit</h4>
                <p style="font-size:12px; color:#546E7A;">Web应用框架</p>
            </div>
            <div style="text-align:center; padding:16px; background:#F5F5F5; border-radius:8px;">
                <h4>BaoStock</h4>
                <p style="font-size:12px; color:#546E7A;">数据源</p>
            </div>
            <div style="text-align:center; padding:16px; background:#F5F5F5; border-radius:8px;">
                <h4>Plotly</h4>
                <p style="font-size:12px; color:#546E7A;">交互式图表</p>
            </div>
            <div style="text-align:center; padding:16px; background:#F5F5F5; border-radius:8px;">
                <h4>SciPy</h4>
                <p style="font-size:12px; color:#546E7A;">数值优化</p>
            </div>
            <div style="text-align:center; padding:16px; background:#F5F5F5; border-radius:8px;">
                <h4>Pandas</h4>
                <p style="font-size:12px; color:#546E7A;">数据处理</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==================== 主页面路由 ====================
if nav_page == "🏠 首页概览":
    _render_home()
elif nav_page == "📈 组合配置":
    _render_portfolio()
elif nav_page == "🔍 市场数据":
    _render_market()
elif nav_page == "📉 风险分析":
    _render_risk()
elif nav_page == "📄 下载报告":
    _render_report()
elif nav_page == "🏢 关于我们":
    _render_about()
