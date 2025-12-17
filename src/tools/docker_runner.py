import subprocess
import os
import json
from src.tools.file_utils import WORKSPACE_DIR


def create_foundry_config():
    """
    [配置] 创建 foundry.toml
    告诉 Foundry 将当前目录 (.) 既作为源码目录也作为测试目录。
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
    解决 stdout 中混杂非 JSON 日志的问题
    """
    decoder = json.JSONDecoder()
    pos = 0

    while True:
        pos = stdout.find('{', pos)
        if pos == -1:
            return None

        try:
            obj, _ = decoder.raw_decode(stdout[pos:])
            return obj
        except json.JSONDecodeError:
            pass

        pos += 1


def find_recursive(data, target_key):
    """
    [递归查找] 在任意深度的字典中查找指定的 Key
    """
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for _, value in data.items():
            found = find_recursive(value, target_key)
            if found: return found
    elif isinstance(data, list):
        for item in data:
            found = find_recursive(item, target_key)
            if found: return found
    return None


def check_compilation(filename: str):
    """
    [Checker] 专门负责检查代码是否可编译 (Syntax Check)
    逻辑：执行全量编译 -> 解析 JSON 错误 -> 过滤出与 filename 相关的错误
    """
    print(f"🔍 [Checker] 正在通过编译器检查语法: {filename}...")
    create_foundry_config()

    # 1. 运行编译命令 (去掉不支持的 --files，使用 --json 获取结构化错误)
    # --skip test/script 没什么用，因为我们的目录结构很扁平，直接全量编译
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{WORKSPACE_DIR}:/app",
        "foundry-box",
        "forge build --json --remappings forge-std/=/opt/foundry/lib/forge-std/src/"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    # 2. 解析编译结果
    data = extract_json_from_stdout(result.stdout)

    # 如果没拿到 JSON，且返回码非0，说明是严重的环境错误（如 Docker 挂了）
    if not data and result.returncode != 0:
        return False, f"COMPILATION CRASHED (No JSON output):\n{result.stderr}\n{result.stdout}"

    # 3. 错误过滤 (Error Filtering)
    # Foundry build 的 JSON 输出顶层通常包含 "errors" 列表
    if data and "errors" in data:
        # 筛选出 severity 为 error 的项 (忽略 warnings)
        errors = [e for e in data["errors"] if e.get("severity") == "error"]

        # 进一步筛选：只关心 sourceLocation.file 匹配当前 filename 的错误
        # Foundry 返回的路径可能是 "Target.sol" 或 "/app/Target.sol"
        target_errors = []
        for e in errors:
            file_path = e.get("sourceLocation", {}).get("file", "")
            # 使用 endswith 匹配文件名，处理绝对/相对路径差异
            if file_path and file_path.endswith(filename):
                target_errors.append(e)

        if target_errors:
            # 格式化错误信息
            error_msg_list = []
            for e in target_errors:
                line = e.get('sourceLocation', {}).get('start', '?')
                msg = e.get('formattedMessage', e.get('message', 'Unknown Error'))
                error_msg_list.append(f"Line {line}: {msg}")

            return False, f"COMPILATION FAILED in {filename}:\n" + "\n".join(error_msg_list)

    # 如果没有找到针对当前文件的 Error，即使 returncode != 0 (可能是别的文件错了)，我们也认为当前文件是 Valid 的
    return True, "Compilation Passed"


def run_forge_test(test_file_name: str = "Exploit.t.sol"):
    """
    [Executor] 执行器，只负责跑逻辑
    """
    print(f"🐳 [Executor] 正在启动容器运行测试: {test_file_name}...")
    create_foundry_config()

    cmd_str = (
        f"forge test "
        f"--match-path /app/{test_file_name} "
        f"--json "
        f"--remappings forge-std/=/opt/foundry/lib/forge-std/src/"
    )

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{WORKSPACE_DIR}:/app",
        "foundry-box",
        cmd_str
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        data = extract_json_from_stdout(result.stdout)

        if data:
            # 使用递归查找找到 test_results
            test_results = find_recursive(data, "test_results")

            if test_results:
                logs_summary = ""
                is_attack_success = False

                for test_name, res in test_results.items():
                    status = res.get("status")
                    reason = res.get("reason", "None")
                    logs_summary += f"Test: {test_name} | Status: {status} | Reason: {reason}\n"

                    if status == "Success":
                        is_attack_success = True

                if is_attack_success:
                    return "success", f"ATTACK SUCCESS!\n{logs_summary}"
                else:
                    return "failed", f"ATTACK FAILED (Logic).\n{logs_summary}"

        if result.returncode != 0:
            return "error", f"CRITICAL: Execution Failed (Code {result.returncode}).\nSTDERR:\n{result.stderr}"

        return "error", f"Unknown Error (No JSON found).\nSTDOUT:\n{result.stdout}"

    except Exception as e:
        return "error", f"System Exception: {str(e)}"