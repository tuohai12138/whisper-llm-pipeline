import streamlit as st

import os

import tempfile

import httpx

from openai import OpenAI


# ==========================================

# 1. 页面基本配置 (Streamlit UI)

# ==========================================

st.set_page_config(page_title="🎙️ 语音录音转文字 (ASR)", page_icon="🎙️", layout="wide")

st.title("🎙️ 语音录音转文字 (ASR)")

st.markdown(
    "上传音频文件（MP3, WAV, M4A），使用 Whisper API（DeepSeek / Groq / OpenAI 兼容接口）将语音精准转化为文本。"
)


# ==========================================

# 2.5 初始化 session_state（自定义模板）

# ==========================================

DEFAULT_TEMPLATE = """# 📌 会议基本信息

- **会议主题**：（请根据内容总结）

- **参会人员**：（如未提及请标注"未提及"）

- **时间/背景**：（请根据上下文推断）



# 🎯 核心议题深挖

## 议题一：（请根据内容总结）

（每个议题用2-3句话概括讨论要点、关键观点和结论）



## 议题二：（请根据内容总结）



# 🚀 待办事项与执行计划

| 序号 | 待办事项 | 负责人 | 截止时间 | 优先级 |

|------|---------|--------|---------|--------|

| 1 | （待填充） | 待确认 | 待确认 | 🔴高 |

| 2 | （待填充） | 待确认 | 待确认 | 🟡中 |"""


if "custom_template" not in st.session_state:
    st.session_state.custom_template = DEFAULT_TEMPLATE


# ==========================================

# 2. 侧边栏 API 配置

# ==========================================

with st.sidebar:
    st.header("⚙️ API 配置")

    api_key = st.text_input(
        "API Key",
        type="password",
        value="",
        help="请到 https://console.groq.com 注册获取免费的 API Key",
    )

    base_url = st.text_input("API Base URL", value="https://api.groq.com/openai/v1")

    proxy_url = st.text_input(
        "网络代理(可选)",
        value="http://127.0.0.1:7897",
        placeholder="如 http://127.0.0.1:7890",
    )

    model_name = st.text_input("Model Name", value="whisper-large-v3")

    st.divider()

    st.header("🤖 摘要模型配置")

    summary_api_key = st.text_input(
        "摘要 API Key",
        type="password",
        value="",
        help="推荐使用 DeepSeek API Key（https://platform.deepseek.com）",
    )

    summary_base_url = st.text_input(
        "摘要 API Base URL", value="https://api.deepseek.com"
    )

    summary_model = st.text_input(
        "摘要模型名称",
        value="deepseek-chat",
        help="如 deepseek-chat (V3) 或 deepseek-reasoner (R1)",
    )

    st.divider()

    st.header("📝 自定义纪要模板")

    st.caption("编辑下方模板可实时调整会议纪要大模型的输出格式")

    template_value = st.text_area(
        "纪要模板（Markdown）",
        value=st.session_state.custom_template,
        height=400,
        label_visibility="collapsed",
        key="custom_template",
    )

    if st.button("🔄 重置为默认模板"):
        st.session_state.custom_template = DEFAULT_TEMPLATE

        st.rerun()


# ==========================================

# 3. 预留函数：pydub 音频切片（文件超过 25MB 时使用）

# ==========================================


def split_audio_if_needed(audio_path, max_size_mb=25):
    """

    预留接口：若音频文件超过 max_size_mb MB，使用 pydub 进行自动切片。



    后续实现示例（需安装 pydub + ffmpeg）：

        from pydub import AudioSegment

        audio = AudioSegment.from_file(audio_path)

        chunk_length_ms = 10 * 60 * 1000  # 10 分钟一片

        chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

        for idx, chunk in enumerate(chunks):

            chunk_path = f"{audio_path}_chunk_{idx}.mp3"

            chunk.export(chunk_path, format="mp3")

            yield chunk_path



    当前：文件小于 25MB 不切片，直接返回原路径。

    """

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    if file_size_mb > max_size_mb:
        st.warning(
            f"⚠️ 文件大小 {file_size_mb:.1f}MB 超过 {max_size_mb}MB 阈值。"
            "如需自动切片处理，请安装 pydub 并完善本函数。"
        )

    # 返回生成器，目前仅一个元素（原文件）

    yield audio_path


# ==========================================

# 4. 核心转录函数

# ==========================================


def transcribe_audio(audio_path, api_key, base_url, model="whisper-1", proxy_url=""):
    """

    调用 OpenAI 规范的 Whisper API 将语音转为文字。

    兼容 DeepSeek / Groq / OpenAI 等实现 /v1/audio/transcriptions 的端点。

    """

    # 构建自定义 HTTPX 客户端，注入浏览器 User-Agent 伪装头

    httpx_kwargs = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    if proxy_url:
        httpx_kwargs["proxy"] = proxy_url

    http_client = httpx.Client(**httpx_kwargs)

    client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)

    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=model, file=audio_file, response_format="text"
        )

    return transcript


# ==========================================

# 4.5 核心摘要生成函数

# ==========================================


def generate_summary(
    transcript_text, api_key, base_url, model, proxy_url="", custom_template=""
):
    """

    调用 LLM（兼容 DeepSeek / OpenAI 等 Chat API）将转录文本提炼为结构化摘要。

    返回 Markdown 格式的会议纪要文本。

    支持 custom_template 参数，用户可自定义输出格式模板。

    """

    if custom_template:
        system_prompt = f"""你是一位专业的会议纪要秘书。请根据以下会议/对话的转录文本，生成一份结构化的会议纪要。



请严格按照以下用户提供的【格式模板】来重排和输出会议内容，不要随意更改标题层级，不要遗漏模板中的任何板块。即使原文信息不全，表格也需保留完整结构。



【格式模板】

{custom_template}



语言风格：专业、简洁、可执行。"""

    else:
        system_prompt = """你是一位专业的会议纪要秘书。请根据以下会议/对话的转录文本，生成一份结构化的会议纪要。



要求：

1. 【📌 会议基本信息】

   - 会议主题

   - 参会人员（如文本中未提及，标注"未提及"）

   - 时间/背景等关键上下文



2. 【🎯 核心议题深挖】

   逐条列出会议讨论的核心议题，每个议题用 2-3 句话概括讨论要点、关键观点和结论。



3. 【🚀 待办事项与执行计划】

   用 Markdown 表格列出所有 Action Items：



   | 序号 | 待办事项 | 负责人 | 截止时间 | 优先级 |



   - 负责人未提及则填"待确认"

   - 截止时间未提及则填"待确认"

   - 优先级根据上下文推断：🔴高 / 🟡中 / 🟢低



格式规范：

- 使用清晰的 Markdown 格式

- 语言风格：专业、简洁、可执行

- 即使原文信息不全，表格也需保留完整结构"""

    httpx_kwargs = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    if proxy_url:
        httpx_kwargs["proxy"] = proxy_url

    http_client = httpx.Client(**httpx_kwargs)

    client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"以下是会议转录文本：\n---\n{transcript_text}\n---",
            },
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    return response.choices[0].message.content


# ==========================================

# 5. 主区域布局：左列上传 + 右列展示结果

# ==========================================

col_left, col_right = st.columns([1, 2])


with col_left:
    st.subheader("📁 上传音频")

    uploaded_file = st.file_uploader(
        "选择音频文件（MP3, WAV, M4A）",
        type=["mp3", "wav", "m4a"],
        help="支持 MP3、WAV、M4A 格式，单文件最大 200MB",
    )

    transcribe_button = st.button(
        "🎤 开始转录", type="primary", disabled=not uploaded_file
    )

    summary_button = st.button(
        "🤖 一键生成智能摘要",
        type="secondary",
        disabled="transcript" not in st.session_state
        or not st.session_state.transcript,
    )

    if uploaded_file is not None:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

        st.info(f"📄 文件名：{uploaded_file.name}")

        st.info(f"📦 文件大小：{file_size_mb:.2f} MB")


with col_right:
    tab1, tab2, tab3 = st.tabs(["📝 原始转录文本", "📋 结构化会议纪要", "📋 运行日志"])

    with tab1:
        # 使用 st.empty() 容器，方便后续原位更新
        transcript_area = st.empty()
        if "transcript" in st.session_state and st.session_state.transcript:
            transcript_area.text_area(
                "转录结果",
                st.session_state.transcript,
                height=400,
                label_visibility="collapsed",
            )
            # 👇 新增：如果检测到成功标记，则在这里渲染成功提示
            if st.session_state.get("transcribe_success"):
                st.success("🎉 转录完成，结果已在右侧「原始转录文本」选项卡中展示！")
                st.session_state.transcribe_success = (
                    False  # 显示后立刻重置，避免之后误触发
                )
        else:
            transcript_area.info("👈 请先在左侧上传音频文件并点击「开始转录」")

    with tab2:
        summary_area = st.empty()

        if "summary" in st.session_state and st.session_state.summary:
            summary_area.markdown(st.session_state.summary)

        else:
            summary_area.info(
                "📄 尚未生成摘要，请先完成转录后点击「🤖 一键生成智能摘要」"
            )

    with tab3:
        log_area = st.empty()

        if "log_lines" not in st.session_state:
            st.session_state.log_lines = []

        log_area.code(
            "\n".join(st.session_state.log_lines)
            if st.session_state.log_lines
            else "暂无日志",
            language="text",
        )


# ==========================================

# 6. 转录逻辑（按钮触发后执行）

# ==========================================

if transcribe_button and uploaded_file is not None:
    # ---- 前置校验 ----

    if not api_key:
        st.error("❌ 请在左侧边栏配置有效的 API Key！")

        st.stop()

    if not base_url:
        st.error("❌ 请在左侧边栏配置 API Base URL！")

        st.stop()

    # 初始化日志

    st.session_state.log_lines = []

    def log(msg):
        st.session_state.log_lines.append(msg)

        # 实时更新日志区域

        log_area.code("\n".join(st.session_state.log_lines), language="text")

    log("📂 正在保存上传的音频文件…")

    # 将上传的音频保存到临时路径

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
    ) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())

        temp_audio_path = tmp_file.name

    try:
        log(f"📂 音频已保存至临时路径：{temp_audio_path}")

        file_size_mb = os.path.getsize(temp_audio_path) / (1024 * 1024)

        log(f"🔍 文件大小：{file_size_mb:.2f} MB")

        # ---- 预留切片接口 ----

        chunks = list(split_audio_if_needed(temp_audio_path))

        full_transcript = ""

        for idx, chunk_path in enumerate(chunks):
            log(f"🎤 正在调用 Whisper API 转录（第 {idx + 1} 段）…")

            try:
                transcript = transcribe_audio(
                    chunk_path, api_key, base_url, model_name, proxy_url
                )

                full_transcript += transcript + "\n"

                log(f"✅ 第 {idx + 1} 段转录完成（{len(transcript)} 字符）")

            except Exception as e:
                error_msg = str(e).lower()

                # -------------------- 异常捕获分类弹窗 --------------------

                if any(
                    kw in error_msg
                    for kw in ("401", "unauthorized", "invalid key", "authentication")
                ):
                    st.error("❌ API Key 认证失败！请检查 API Key 是否正确。")

                    log("❌ API Key 认证失败")

                elif any(
                    kw in error_msg for kw in ("timeout", "timed out", "connection")
                ):
                    st.error("⏱️ 网络请求超时！请检查网络连接或稍后重试。")

                    log("❌ 网络请求超时")

                elif any(
                    kw in error_msg
                    for kw in ("invalid file", "unsupported", "not a valid")
                ):
                    st.error("📁 不支持的音频格式或文件已损坏！")

                    log("❌ 不支持的音频格式")

                else:
                    st.error(f"❌ API 调用失败：{str(e)}")

                    log(f"❌ API 调用失败：{str(e)}")

                st.stop()

        # ---- 持久化存储到 session_state ----
        st.session_state.transcript = full_transcript
        log(f"✅ 全部转录完成！共 {len(full_transcript)} 个字符。")

        st.session_state.transcribe_success = True  # 记录转录成功标记
        st.rerun()  # 💡 核心：强制刷新全页，让大模型摘要按钮重新计算 disabled 状态

    except Exception as e:
        st.error(f"❌ 系统错误：{str(e)}")

        st.session_state.log_lines.append(f"❌ 系统错误：{str(e)}")

        log_area.code("\n".join(st.session_state.log_lines), language="text")

    finally:
        # ---- 清理临时文件 ----

        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

            log("🧹 临时文件已清理。")


# ==========================================

# 7. 摘要生成逻辑（按钮触发后执行）

# ==========================================

if summary_button and "transcript" in st.session_state and st.session_state.transcript:
    # ---- 前置校验 ----

    if not summary_api_key:
        st.error("❌ 请在左侧边栏配置有效的摘要 API Key！")

        st.stop()

    if not summary_base_url:
        st.error("❌ 请在左侧边栏配置摘要 API Base URL！")

        st.stop()

    def log(msg):
        st.session_state.log_lines.append(msg)

        log_area.code("\n".join(st.session_state.log_lines), language="text")

    log("🤖 正在调用摘要模型生成结构化会议纪要…")

    try:
        summary = generate_summary(
            transcript_text=st.session_state.transcript,
            api_key=summary_api_key,
            base_url=summary_base_url,
            model=summary_model,
            proxy_url=proxy_url,
            custom_template=st.session_state.custom_template,
        )

        st.session_state.summary = summary

        log(f"✅ 摘要生成完成！共 {len(summary)} 个字符。")

        # ---- 原位更新摘要区 ----

        summary_area.markdown(st.session_state.summary)

        st.success(
            "📋 结构化会议纪要已生成，可在右侧「📋 结构化会议纪要」选项卡中查看！"
        )

    except Exception as e:
        error_msg = str(e).lower()

        if any(
            kw in error_msg
            for kw in ("401", "unauthorized", "invalid key", "authentication")
        ):
            st.error("❌ 摘要 API Key 认证失败！请检查摘要模型 API Key 是否正确。")

            log("❌ 摘要 API Key 认证失败")

        elif any(kw in error_msg for kw in ("timeout", "timed out", "connection")):
            st.error("⏱️ 摘要 API 网络请求超时！请检查网络连接或代理配置。")

            log("❌ 摘要 API 网络请求超时")

        else:
            st.error(f"❌ 摘要生成失败：{str(e)}")

            log(f"❌ 摘要生成失败：{str(e)}")

        st.stop()
