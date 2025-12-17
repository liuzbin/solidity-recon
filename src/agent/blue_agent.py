from langchain_core.prompts import ChatPromptTemplate
from src.llm.client import get_llm
from src.agent.red_agent import extract_code

CODE_MARK = "```"


def blue_team_patch(original_code: str, exploit_code: str, test_logs: str, feedback: str = "") -> str:
    llm = get_llm()

    # 1. 基础模板
    template = (
            "你是一个资深的区块链安全专家。\n"
            "刚才红队成功攻破了你的合约，你需要立即修复它。\n\n"
            "=== 原始合约 ===\n" +
            CODE_MARK + "solidity\n"
                        "{original_code}\n" +
            CODE_MARK + "\n\n"
                        "=== 红队的攻击脚本 ===\n" +
            CODE_MARK + "solidity\n"
                        "{exploit_code}\n" +
            CODE_MARK + "\n\n"
                        "=== 攻击执行日志 (Foundry Output) ===\n"
                        "{test_logs}\n\n"
    )

    # 2. 如果有编译器反馈（Checker 报错）
    if feedback:
        template += (
            "⚠️ 注意：你上一次生成的修复代码无法通过编译！报错如下：\n"
            "{compiler_feedback}\n"
            "请修正语法错误。\n\n"
        )

    # 3. 任务要求
    template += (
        "**修复要求：**\n"
        "1. **核心原则**：只修复漏洞，绝对不要破坏原有的业务逻辑（存款/取款功能必须保留且可用）。\n"
        "2. 分析攻击脚本是利用了什么漏洞（如 Reentrancy, Overflow, Access Control）。\n"
        "3. 应用最佳实践进行修复（如使用 Check-Effects-Interactions 模式，或添加 `ReentrancyGuard`）。\n"
        "4. 直接输出完整的、修复后的合约代码。\n"
        "5. **只输出 Solidity 代码，不要包含任何解释。**"
    )

    prompt = ChatPromptTemplate.from_template(template)

    print("🔵 [Blue Team] 正在分析攻击路径并进行代码修复...")

    # 防止 Log 太长
    short_logs = test_logs[-2000:] if len(test_logs) > 2000 else test_logs

    # 4. 准备变量
    input_vars = {
        "original_code": original_code,
        "exploit_code": exploit_code,
        "test_logs": short_logs
    }
    if feedback:
        input_vars["compiler_feedback"] = feedback

    # 5. 执行
    chain = prompt | llm
    response = chain.invoke(input_vars)

    return extract_code(response.content)