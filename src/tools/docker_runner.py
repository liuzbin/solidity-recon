import subprocess
import os
from .file_utils import WORKSPACE_DIR


def run_forge_test(test_file_name: str = "Exploit.t.sol"):
    """
    调用 Docker 运行 Foundry 测试
    :param test_file_name: 要运行的测试脚本文件名
    :return: (success: bool, logs: str)
    """
    print(f"🐳 [Docker] 正在启动容器运行测试: {test_file_name}...")

    # 组装 Docker 命令
    cmd = [
        "docker", "run", "--rm",
        # 挂载 workspace 到容器内的 /app
        "-v", f"{WORKSPACE_DIR}:/app",
        "foundry-box",
        # 在容器内执行 forge test
        "forge", "test",
        "--match-path", f"/app/{test_file_name}",  # 只运行指定的测试文件
        "-vv"  # 显示详细日志 (verbosity level 2)
    ]

    try:
        # 运行命令 (Windows 下 encoding 处理很重要)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        stdout = result.stdout
        stderr = result.stderr

        # Foundry 的判定标准：如果输出中有 "PASS"，通常意味着测试通过（攻击成功）
        # 如果有 "FAIL"，意味着测试失败
        is_success = "PASS" in stdout

        # 组合日志返回
        full_logs = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        return is_success, full_logs

    except Exception as e:
        return False, f"Docker Execution Error: {str(e)}"