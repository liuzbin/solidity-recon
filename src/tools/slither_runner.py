import subprocess
import json
import os
from .file_utils import WORKSPACE_DIR


def format_slither_report(json_data):
    """
    [清洗] 将 Slither 复杂的 JSON 简化为 LLM 易读的文本摘要
    """
    if not json_data or "results" not in json_data or "detectors" not in json_data["results"]:
        return "Slither Scan: No vulnerabilities detected or scan failed."

    detectors = json_data["results"]["detectors"]
    if not detectors:
        return "Slither Scan: No obvious vulnerabilities found."

    report = "=== Slither Static Analysis Report ===\n"
    count = 1

    for item in detectors:
        # 提取关键信息
        check = item.get("check", "Unknown")
        description = item.get("description", "No description")
        impact = item.get("impact", "Informational")

        # 提取受影响的代码行位置 (Source Mapping)
        lines = []
        if "elements" in item:
            for elem in item["elements"]:
                if "source_mapping" in elem:
                    start_line = elem["source_mapping"].get("lines", [])
                    if start_line:
                        lines.extend(start_line)

        lines_str = f"Lines: {list(set(lines))}" if lines else "Lines: Unknown"

        report += f"{count}. [Type: {check}] [Impact: {impact}]\n"
        report += f"   Description: {description}\n"
        report += f"   Location: {lines_str}\n\n"
        count += 1

    return report


def run_slither_scan(filename: str = "Target.sol") -> str:
    """
    [Runner] 在 Docker 中运行 Slither 并返回清洗后的报告
    """
    print(f"👁️ [Recon] 正在启动 Slither 进行静态分析: {filename}...")

    # 1. 组装命令
    # 这里的 solc-select use 是为了确保版本匹配，虽然 Dockerfile 里装了，但防一手
    # slither . --json - 表示输出 json 到 stdout
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{WORKSPACE_DIR}:/app",
        "foundry-box",
        f"/bin/sh -c 'solc-select use 0.8.20 && slither /app/{filename} --json -'"
    ]

    try:
        # 2. 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        # Slither 即使发现漏洞，返回码通常也是 0 或 1，所以主要看 stdout
        stdout = result.stdout

        # 3. 提取 JSON
        # Slither 的 stdout 可能会混杂 "Compiling..." 等日志
        # 我们寻找第一个 '{' 和最后一个 '}'
        start = stdout.find('{')
        end = stdout.rfind('}')

        if start != -1 and end != -1:
            json_str = stdout[start:end + 1]
            try:
                data = json.loads(json_str)
                return format_slither_report(data)
            except json.JSONDecodeError:
                return f"Slither Execution Error: JSON parse failed.\nRaw output: {stdout[:200]}..."
        else:
            # 如果没找到 JSON，可能是 Slither 报错了（比如编译失败）
            return f"Slither Failed to Run. Stdout: {stdout}\nStderr: {result.stderr}"

    except Exception as e:
        return f"System Exception during Slither: {str(e)}"