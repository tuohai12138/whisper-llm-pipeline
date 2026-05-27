# 🎙️ Multi-API Audio Transcriber & Intelligent Meeting Summary System
### 基于异构 API 的智能语音转录与自动化会议纪要系统

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![API Support](https://img.shields.io/badge/Backend-Groq%20%7C%20DeepSeek%20%7C%20OpenAI-green.svg)](https://platform.deepseek.com/)

本系统是一个轻量级、响应式的全栈 AI 语音处理工具。打通了 **“原始音频输入 -> 动态切片预留 -> 语音精准转录 -> 大模型语义提炼 -> 结构化纪要输出”** 的自动化工作流，专为解决企业日常会议高效转录与内容复盘痛点而设计。

---

## ✨ 核心特性 (Key Features)

- **🚀 响应式双栏交互**：基于 **Streamlit** 架构设计，利用 `st.session_state` 实现转录流、自定义模板、Markdown 纪要及实时运行日志的状态持久化与动态全页刷新。
- **🔌 异构 API 统一路由**：基于 OpenAI 规范统一封装，上游无缝对接 **Groq (Whisper-large-v3)** 高速语音识别端点与 **DeepSeek-V3 / R1** 深度思考大语言模型。
- **🌐 稳健的网络工程**：借助 **HTTPX** 深度定制底层通信 Client，注入浏览器伪装头并**内置正向代理（Forward Proxy）路由机制**，彻底解决国内环境直连海外 API 超时与隔离问题。
- **📝 动态提示词工程**：设计可实时编辑的 Markdown 纪要模板注入机制，通过高度约束的 System Prompt 与思维链（CoT）引导，实现待办事项（Action Items）的自动化结构化表格输出。
- **🛡️ 防御性编程架构**：全链路构建多层级异常捕获机制，精准分类 401 认证失败、Timeout 超时、文件损坏等高频错误；前瞻性设计基于生成器（Generator）的流式切片架构，内存友好。

---

## 🛠️ 技术栈 (Tech Stack)

- **Frontend / UI**: Streamlit
- **Runtime / Language**: Python 3.9+
- **SDK / Network**: OpenAI SDK, HTTPX Client (with proxy integration)
- **AI Models**: Groq Whisper-large-v3, DeepSeek-chat (V3) / DeepSeek-reasoner (R1)

---

## 🚀 快速启动 (Quick Start)

### 1. 克隆本项目到本地
```bash
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd 你的仓库名

```

### 2. 安装依赖环境

```bash
pip install streamlit httpx openai

```

### 3. 运行应用

```bash
streamlit run app.py

```

---

## ⚙️ 使用配置说明 (Configuration)

打开本地 Web 页面后，请在左侧边栏配置以下参数：

1. **API 配置**：填入你的 Groq 或符合 OpenAI 规范的 Whisper API Key 及 Base URL。
2. **网络代理（可选）**：若在国内环境直连海外 API，请填写本地代理端口（如 `http://127.0.0.1:7897`）。
3. **摘要大模型配置**：填入 DeepSeek API Key（支持官方平台或第三方托管平台）。
4. **自定义模板**：可在侧边栏直接修改 Markdown 结构，点击一键生成将严格按照此结构输出纪要。

---

## 📂 项目结构 (Repository Structure)

```text
├── app.py               # Streamlit 主程序（包含前端 UI 与核心业务逻辑）
├── .gitignore           # Git 忽略配置文件（已自动屏蔽本地 VS Code 缓存及敏感设置）
└── README.md            # 项目说明文档

```

---

## 📝 免责声明与安全提示

* 本项目开源代码中**不包含任何硬编码的 API Key**。请妥善保管您的私钥，切勿将带有密钥的代码二次上传。
* 本项目预留了 `pydub` 超长音频流式切片接口，如需处理 25MB 以上的音频，请自行安装 `pydub` 及 `ffmpeg` 依赖并完善相关生成器函数。

```
