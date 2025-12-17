import subprocess
import os
import json
from .file_utils import WORKSPACE_DIR


def create_foundry_config():
    """
    [配置] 创建 foundry.toml
    """
    config_content = """
[profile.default]
src = "."
test = "."
out = "out"
libs = ["/opt/foundry/lib"]
"""
    config_path = os.path.join(WORKSPACE_DIR, "foundry.toml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)


def extract_json_from_stdout(stdout: str):
    """
    [解析] 滑动窗口提取 JSON
    """
    decoder = json.JSONDecoder()
    pos = 0

    while True:
        pos = stdout.find('{', pos)
        if pos == -1:
            return None

        try:
            obj, _ = decoder.raw_decode(stdout[pos:])
            # 简单验证：只要转成字符串后包含 test_results 就认为是我们要的
            # (虽然递归查找更严谨，但这里先做初步筛选)
            if "test_results" in str(obj):
                return obj
        except json.JSONDecodeError:
            pass

        pos += 1


def find_test_results_recursive(data):
    """
    [递归查找] 深度优先搜索 'test_results' 字段
    不管它被包裹在 'Exploit.t.sol:ExploitTest' 还是其他什么 Key 下面，都能找到。
    """
    if isinstance(data, dict):
        # 1. 如果当前层级直接包含目标 Key，返回它
        if "test_results" in data:
            return data["test_results"]

        # 2. 否则遍历所有 Value 继续找
        for key, value in data.items():
            found = find_test_results_recursive(value)
            if found:
                return found

    # 3. 列表情况（虽然 Foundry 输出通常是字典，但也防御一下）
    elif isinstance(data, list):
        for item in data:
            found = find_test_results_recursive(item)
            if found:
                return found

    return None


def run_forge_test(test_file_name: str = "Exploit.t.sol"):
    """
    [执行] Docker + Foundry (递归解析版)
    """
    print(f"🐳 [Docker] 正在启动容器运行测试: {test_file_name}...")

    create_foundry_config()

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

        # 1. 尝试提取 JSON 对象
        data = extract_json_from_stdout(stdout)

        # 2. 逻辑分支判断
        if data:
            # === 关键修改：使用递归查找 ===
            test_results = find_test_results_recursive(data)

            if test_results:
                logs_summary = ""
                is_attack_success = False

                # 遍历所有测试用例的结果
                for test_name, res in test_results.items():
                    status = res.get("status")  # "Success" / "Failure"
                    reason = res.get("reason", "None")
                    logs_summary += f"Test: {test_name} | Status: {status} | Reason: {reason}\n"

                    if status == "Success":
                        is_attack_success = True

                if is_attack_success:
                    return "success", f"ATTACK SUCCESS!\n{logs_summary}"
                else:
                    return "failed", f"ATTACK FAILED (Logic).\n{logs_summary}"
            else:
                # 提取到了 JSON，但在里面没找到 test_results 字段
                # 可能是编译报错的 JSON 信息
                return "error", f"JSON Parsed but 'test_results' not found recursively.\nData: {data}"

        # 3. 如果没拿到 JSON，检查返回码
        if result.returncode != 0:
            return "error", f"CRITICAL: Execution Failed (Code {result.returncode}).\nSTDERR:\n{stderr}\nSTDOUT:\n{stdout}"

        return "error", f"Unknown Error (No JSON found).\nSTDOUT:\n{stdout}"

    except Exception as e:
        return "error", f"System Exception: {str(e)}"
