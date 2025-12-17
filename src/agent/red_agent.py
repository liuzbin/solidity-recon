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


def red_team_attack(contract_code: str, feedback: str = "") -> str:
    llm = get_llm()

    # 1. 基础模板 (注意：这里用 {contract_code} 占位，不要把真实代码拼进来)
    template = (
            "你是一个世界顶级的智能合约黑客。你的任务是攻破以下目标合约。\n\n"
            "目标合约代码:\n" +
            CODE_MARK + "solidity\n"
                        "{contract_code}\n" +  # <--- 这里留占位符
            CODE_MARK + "\n\n"
    )

    # 2. 如果有反馈，动态添加反馈部分的模板
    if feedback:
        template += (
            "❌ 上一次生成的代码编译失败！编译器报错如下：\n"
            "{compiler_feedback}\n"  # <--- 这里留占位符
            "请根据报错修正你的代码。不要重复同样的错误。\n\n"
        )

    # 3. 添加任务要求
    template += (
        "请编写一个 Foundry 测试脚本 (`ExploitTest`) 来复现漏洞并窃取资金。\n"
        "**严格遵守以下要求：**\n"
        "1. 必须导入 `forge-std/Test.sol`。\n"
        "2. 合约名必须是 `ExploitTest` 并且继承自 `Test`。\n"
        "3. 必须包含 `setUp()` 函数：\n"
        "   - 部署目标合约。\n"
        "   - 给目标合约转入初始资金（例如 10 ether）。\n"
        "4. 必须包含 `testExploit()` 函数：\n"
        "   - 编写具体的攻击逻辑（如重入、权限绕过）。\n"
        "   - 使用 `vm.prank(attacker)` 或 `vm.deal` 模拟攻击者环境。\n"
        "   - 最终必须断言攻击成功（例如 `assertGt(attacker.balance, 0)`）。\n"
        "5. 如果需要辅助合约（如恶意重入合约），请将辅助合约代码也写在同一个文件里。\n"
        "6. **必须在文件开头加上 `import \"./Target.sol\";` 以引入目标合约定义。**\n"
        "7. **只输出 Solidity 代码，不要包含任何解释或注释。**"
    )

    # 4. 创建 Prompt 模板
    prompt = ChatPromptTemplate.from_template(template)

    # 5. 准备输入数据
    input_variables = {"contract_code": contract_code}
    if feedback:
        input_variables["compiler_feedback"] = feedback

    print("🔴 [Red Team] 正在分析漏洞并编写攻击脚本...")

    # 6. 安全执行 (LangChain 会自动处理转义)
    chain = prompt | llm
    response = chain.invoke(input_variables)

    return extract_code(response.content)