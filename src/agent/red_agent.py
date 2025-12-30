import re
from langchain_core.prompts import ChatPromptTemplate
from src.llm.client import get_llm

# 定义 Markdown 代码块标记
CODE_MARK = "```"


def extract_code(text: str) -> str:
    pattern = r"```(?:solidity)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def red_team_attack(contract_code: str, slither_report: str, feedback: str = "") -> str:
    llm = get_llm()

    # 1. 基础模板 (注意：这里用 {contract_code} 占位，不要把真实代码拼进来)
    template = (
            "你是一个世界顶级的智能合约黑客。你的任务是攻破以下目标合约。\n\n"
            "目标合约代码:\n" +
            CODE_MARK + "solidity\n"
                        "{contract_code}\n" +  # <--- 这里留占位符
            CODE_MARK + "\n\n"
    )

    # 2. 注入 Slither 侦察报告 (这是精确制导的关键)
    template += (
        "=== 🕵️ 静态分析侦察报告 (Slither) ===\n"
        "以下是自动化工具扫描出的潜在漏洞，请重点关注：\n"
        "{slither_report}\n\n"
    )

    # 3. 注入编译器反馈 (如果有)
    if feedback:
        template += (
            "=== ❌ 编译错误反馈 ===\n"
            "你上一次生成的代码编译失败！报错如下：\n"
            "{compiler_feedback}\n"
            "请修正语法错误。\n\n"
        )

    # 4. 任务指令
    template += (
        "=== ⚔️ 任务指令 ===\n"
        "请根据合约代码和侦察报告，编写一个 Foundry 测试脚本 (`ExploitTest`)。\n"
        "如果你在报告中看到了明确的漏洞（如 Reentrancy, Unchecked Return），请优先攻击该点。\n\n"
        "**代码规范要求：**\n"
        "1. 导入 `forge-std/Test.sol`。\n"
        "2. 开头必须 `import \"./Target.sol\";`。\n"
        "3. 继承 `Test`，包含 `setUp()` (部署+注资) 和 `testExploit()` (攻击+断言)。\n"
        "4. **只输出 Solidity 代码**，不包含解释。\n"
    )

    prompt = ChatPromptTemplate.from_template(template)

    # 准备变量
    input_vars = {
        "contract_code": contract_code,
        "slither_report": slither_report
    }
    if feedback:
        input_vars["compiler_feedback"] = feedback

    print("🔴 [Red Team] 正在结合 Slither 报告分析漏洞并编写脚本...")

    chain = prompt | llm
    response = chain.invoke(input_vars)

    return extract_code(response.content)