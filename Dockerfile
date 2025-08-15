# UniMind AI Assistant - Production Dockerfile
# 基于多智能体架构的通用型AI助手
FROM python:3.12.3-slim

LABEL maintainer="UniMind Team"
LABEL description="UniMind - Universal AI Assistant with Multi-Agent Architecture"
LABEL version="1.0.0"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/unimind \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

# 设置工作目录
WORKDIR /unimind

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 安装Android ADB工具 (用于设备连接)
RUN wget -q https://dl.google.com/android/repository/platform-tools-latest-linux.zip \
    && unzip platform-tools-latest-linux.zip \
    && mv platform-tools /unimind/platform-tools \
    && rm platform-tools-latest-linux.zip

# 创建应用用户 (安全考虑)
RUN useradd --create-home --shell /bin/bash unimind \
    && chown -R unimind:unimind /unimind

# 复制依赖文件
COPY requirements.txt pyproject.toml ./

# 配置pip镜像 (可选)
ARG pip_mirror=false
RUN if [ "$pip_mirror" = "true" ]; then \
        pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple; \
    fi

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir streamlit

# 复制应用代码
COPY --chown=unimind:unimind . .

# 创建必要的目录
RUN mkdir -p /unimind/data/phone_auto_answer \
    && mkdir -p /unimind/data/voice_responses \
    && mkdir -p /unimind/logs \
    && mkdir -p /unimind/screenshots \
    && chown -R unimind:unimind /unimind/data /unimind/logs /unimind/screenshots

# 设置权限
RUN chmod +x /unimind/platform-tools/adb \
    && chown -R unimind:unimind /unimind

# 切换到应用用户
USER unimind

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 暴露端口
EXPOSE 8501

# 创建启动脚本
RUN echo '#!/bin/bash' > /unimind/start.sh && \
    echo 'set -e' >> /unimind/start.sh && \
    echo '' >> /unimind/start.sh && \
    echo 'echo "🚀 Starting UniMind AI Assistant..."' >> /unimind/start.sh && \
    echo 'echo "📱 Universal AI Assistant with Multi-Agent Architecture"' >> /unimind/start.sh && \
    echo 'echo "🏢 China Unicom Challenge Cup Competition"' >> /unimind/start.sh && \
    echo 'echo "=========================================================="' >> /unimind/start.sh && \
    echo '' >> /unimind/start.sh && \
    echo '# 检查环境' >> /unimind/start.sh && \
    echo 'echo "🔍 Checking environment..."' >> /unimind/start.sh && \
    echo 'python -c "import unimind; print(\"✅ UniMind module loaded successfully\")"' >> /unimind/start.sh && \
    echo '' >> /unimind/start.sh && \
    echo '# 检查ADB工具' >> /unimind/start.sh && \
    echo 'if [ -f "/unimind/platform-tools/adb" ]; then' >> /unimind/start.sh && \
    echo '    echo "✅ ADB tools available"' >> /unimind/start.sh && \
    echo 'else' >> /unimind/start.sh && \
    echo '    echo "⚠️  ADB tools not found, device features may be limited"' >> /unimind/start.sh && \
    echo 'fi' >> /unimind/start.sh && \
    echo '' >> /unimind/start.sh && \
    echo '# 启动Streamlit应用' >> /unimind/start.sh && \
    echo 'echo "🌐 Starting Streamlit server on port $STREAMLIT_SERVER_PORT..."' >> /unimind/start.sh && \
    echo 'exec streamlit run universal_ai_assistant_web.py \\' >> /unimind/start.sh && \
    echo '    --server.port=$STREAMLIT_SERVER_PORT \\' >> /unimind/start.sh && \
    echo '    --server.address=$STREAMLIT_SERVER_ADDRESS \\' >> /unimind/start.sh && \
    echo '    --server.headless=$STREAMLIT_SERVER_HEADLESS \\' >> /unimind/start.sh && \
    echo '    --browser.gatherUsageStats=$STREAMLIT_BROWSER_GATHER_USAGE_STATS \\' >> /unimind/start.sh && \
    echo '    --server.fileWatcherType=$STREAMLIT_SERVER_FILE_WATCHER_TYPE' >> /unimind/start.sh && \
    chmod +x /unimind/start.sh && \
    chown unimind:unimind /unimind/start.sh

# 入口点
ENTRYPOINT ["/unimind/start.sh"]

# 元数据
LABEL org.opencontainers.image.title="UniMind AI Assistant"
LABEL org.opencontainers.image.description="Universal AI Assistant with Multi-Agent Architecture for China Unicom"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
LABEL org.opencontainers.image.source="https://github.com/your-repo/unimind"
LABEL org.opencontainers.image.licenses="MIT"