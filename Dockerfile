# 使用 Foundry 官方镜像
FROM ghcr.io/foundry-rs/foundry:latest

USER root

# 1. 安装基础工具
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv git && \
    rm -rf /var/lib/apt/lists/*

# 2. 安装 forge-std 标准库 (关键步骤！)
# 我们把它装在 /opt/foundry/lib 下，这样挂载 /app 时不会被覆盖
WORKDIR /opt/foundry/lib
RUN git clone https://github.com/foundry-rs/forge-std.git

# 3. 配置 Python 环境
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 4. 安装 Slither
RUN pip install slither-analyzer solc-select

# 5. 安装 Solidity
RUN solc-select install 0.8.20 && solc-select use 0.8.20

# 6. 设置工作目录
WORKDIR /app

# 7. 入口
ENTRYPOINT ["/bin/sh", "-c"]