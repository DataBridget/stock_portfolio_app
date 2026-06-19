A股智能投资组合配置平台
智投组合 | Smart Portfolio
项目简介
基于现代投资组合理论(MPT)和大数据技术的A股智能投资组合配置平台。为不同资金账户和风险承受等级的投资者推荐最优投资组合，提供风险对冲分析和专业报告下载。

核心功能
智能组合配置：基于MPT、风险平价、Black-Litterman等模型
风险对冲分析：VaR、CVaR、最大回撤、Beta等风险指标
可视化图表：有效前沿、蒙特卡洛模拟、相关性热力图等
报告下载：支持Word和PDF格式一键下载
实时数据：基于BaoStock的A股全市场数据
技术栈
Python 3.8+
Streamlit (Web框架)
BaoStock (数据源)
Plotly (可视化)
SciPy (数值优化)
Pandas (数据处理)
python-docx (Word报告)
ReportLab (PDF报告)
安装与运行
安装依赖

Bash

pip install -r requirements.txt
本地运行

Bash

streamlit run app.py
部署到Streamlit Cloud
将代码推送到GitHub仓库
在Streamlit Cloud中连接仓库
设置主文件为 app.py
点击Deploy
项目结构

Plain Text

stock_portfolio_app/
├── app.py                    # 主应用入口
├── requirements.txt          # 依赖包
├── utils/
│   ├── __init__.py          # 包初始化
│   ├── data_fetcher.py      # 数据获取模块 (BaoStock)
│   ├── portfolio_optimizer.py # 组合优化模块
│   └── report_generator.py  # 报告生成模块
├── pages/                    # 多页面目录
├── assets/                   # 静态资源
└── reports/                  # 报告输出
数据来源
BaoStock (www.baostock.com) - 免费开源证券数据平台
覆盖全部A股上市公司
数据更新频率：每个交易日收盘后
免责声明
本平台提供的所有投资组合推荐和分析报告仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。
