from langchain_core.prompts import ChatPromptTemplate
from src.llm.client import get_llm
from src.agents.red_agent import extract_code


def blue_team_patch(original_code: str, exploit_code: str, test_logs: str) -> str:
    """
    [蓝队入口] 根据攻击脚本和错误日志修复合约
    """
    llm = get_llm()

    template = f"""
你是一个资深的区块链安全专家。
刚才红队成功攻破了你的合约，你需要立即修复它。

=== 原始合约 ===
```solidity
{{original_code}}
```

=== 红队的攻击脚本 ===
```solidity
{{exploit_code}}
```

=== 攻击执行日志 (Foundry Output) ===
{{test_logs}}

**修复要求：**
1. **核心原则**：只修复漏洞，绝对不要破坏原有的业务逻辑（存款/取款功能必须保留且可用）。
2. 分析攻击脚本是利用了什么漏洞（如 Reentrancy, Overflow, Access Control）。
3. 应用最佳实践进行修复（如使用 Check-Effects-Interactions 模式，或添加 `ReentrancyGuard`）。
4. 直接输出完整的、修复后的合约代码。
5. **只输出 Solidity 代码，不要包含任何解释。**
"""

    prompt = ChatPromptTemplate.from_template(template)

    print("🔵 [Blue Team] 正在分析攻击路径并进行代码修复...")

    # 截取日志防止 Token 溢出
    short_logs = test_logs[-2000:] if len(test_logs) > 2000 else test_logs

    chain = prompt | llm
    response = chain.invoke({{
        "original_code": original_code,
        "exploit_code": exploit_code,
        "test_logs": short_logs
    }})

    return extract_code(response.content)
