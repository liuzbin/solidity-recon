import subprocess
import os
import json
from src.tools.file_utils import WORKSPACE_DIR


def create_foundry_config():
    """创建一个 foundry.toml 配置文件，告诉 Forge 在根目录查找文件"""
    config_content = """
[profile.default]
src = "."
test = "."
out = "out"
libs = ["/opt/foundry/lib"]  # 指向我们在 Dockerfile 里安装库的位置
"""
    config_path = os.path.join(WORKSPACE_DIR, "foundry.toml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)


def run_forge_test(test_file_name: str = "Exploit.t.sol"):
    """
    调用 Docker 运行 Foundry 测试 (JSON 解析版)
    """
    print(f"🐳 [Docker] 正在启动容器运行测试: {test_file_name}...")

    create_foundry_config()

    # 这里的命令保持不变
    forge_command = (
        f"forge test "
        f"--match-path /app/{test_file_name} "
        f"--json "
        f"--remappings forge-std/=/opt/foundry/lib/forge-std/src/"
    )

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{WORKSPACE_DIR}:/app",
        "foundry-box",
        forge_command
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        stdout = result.stdout
        stderr = result.stderr

        is_success = False
        logs_summary = ""

        # === 新增：优雅的 JSON 解析 ===
        try:
            # Foundry 的 JSON 输出有时会包含多行，最后一行通常是结果
            # 我们尝试找到包含 "test_results" 的那一行
            data = None
            for line in stdout.splitlines():
                if line.strip().startswith("{") and "test_results" in line:
                    data = json.loads(line)
                    break

            if data:
                # 遍历测试结果
                results = data.get("test_results", {})
                for test_name, res in results.items():
                    status = res.get("status")
                    reason = res.get("reason", "No reason provided")

                    logs_summary += f"Test: {test_name}\nStatus: {status}\nReason: {reason}\n"

                    if status == "Success":
                        is_success = True
            else:
                # 如果没找到 JSON，回退到原始日志
                logs_summary = stdout

        except json.JSONDecodeError:
            logs_summary = f"JSON Parse Error. Raw Stdout:\n{stdout}"

        # 最终返回
        full_logs = f"Parsed Results:\n{logs_summary}\n\nRaw STDERR:\n{stderr}"
        return is_success, full_logs

    except Exception as e:
        return False, f"Docker Execution Error: {str(e)}"