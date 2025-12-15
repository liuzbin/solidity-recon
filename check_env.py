import docker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def check_system():
    print("=== 开始环境自检 (V2) ===")

    # 1. 检查 API Key
    key = os.getenv("DASHSCOPE_API_KEY")
    if key:
        print(f"✅ .env 读取成功 (Key 长度: {len(key)})")
    else:
        print("❌ 未找到 API Key，请检查 .env 文件")

    # 2. 检查 Docker 连接
    try:
        client = docker.from_env()
        print("✅ Docker Desktop 连接成功")

        # 3. 检查镜像是否存在
        images = client.images.list(name="foundry-box")
        if images:
            print("✅ 镜像 'foundry-box' 存在")
        else:
            print("❌ 未找到镜像 'foundry-box'，请运行 docker build")
            return

        # 4. 终极测试：运行一个最简单的 Linux 命令
        # 我们这里强制覆盖 entrypoint，确保只是运行一个 echo
        print("🚀 正在测试容器沙盒...")
        logs = client.containers.run(
            "foundry-box",
            "echo 'Hello form Docker Sandbox!'",
            entrypoint="/bin/sh -c",  # 显式指定 entrypoint 确保万无一失
            remove=True
        )

        output = logs.decode('utf-8').strip()
        print(f"✅ 容器响应成功: {output}")

        if "Hello" in output:
            print("\n🎉 恭喜！整个系统环境（Python + Docker）已打通！")
            print("我们可以开始编写红队 Agent 代码了。")

    except Exception as e:
        print(f"❌ Docker 检查失败: {e}")
        print("提示: 请确保 Docker Desktop 正在运行")


if __name__ == "__main__":
    check_system()