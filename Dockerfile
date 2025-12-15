# 使用 Foundry 官方镜像
FROM ghcr.io/foundry-rs/foundry:latest

# 切换到 root 用户以确保有权限安装软件
USER root

# 1. 使用 apt-get 安装 Python3, pip, venv 和 git
# (注意：Debian/Ubuntu 下 venv 需要单独安装)
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv git && \
    rm -rf /var/lib/apt/lists/*

# 2. 创建虚拟环境 (PEP 668 标准)
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. 安装 Slither 和 solc-select
RUN pip install slither-analyzer solc-select

# 4. 安装指定的 Solidity 版本
RUN solc-select install 0.8.20 && solc-select use 0.8.20

# 5. 设置工作目录
WORKDIR /app

# 6. 默认入口
ENTRYPOINT ["/bin/sh", "-c"]