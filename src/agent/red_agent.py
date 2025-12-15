import re
from langchain_core.prompts import ChatPromptTemplate
from src.llm.client import get_llm


def extract_code(text: str) -> str:
    """
    工具函数：从 LLM 的回复中提取代码块。
    """
    # 匹配 ```solidity ... ``` 或 ``` ... ```
    pattern = r"```(?:solidity)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def red_team_attack(contract_code: str) -> str:
    """
    [红队入口] 分析合约并生成 Foundry 攻击测试脚本
    """
    llm = get_llm()

    # 使用 f-string 拼接，这样复制进去绝对不会错
    template = f"""
你是一个世界顶级的智能合约黑客。你的任务是攻破以下目标合约。

目标合约代码:
```solidity
{{contract_code}}
```

请编写一个 Foundry 测试脚本 (`ExploitTest`) 来复现漏洞并窃取资金。
**严格遵守以下要求：**
1. 必须导入 `forge-std/Test.sol`。
2. 合约名必须是 `ExploitTest` 并且继承自 `Test`。
3. 必须包含 `setUp()` 函数：
   - 部署目标合约。
   - 给目标合约转入初始资金（例如 10 ether）。
4. 必须包含 `testExploit()` 函数：
   - 编写具体的攻击逻辑（如重入、权限绕过）。
   - 使用 `vm.prank(attacker)` 或 `vm.deal` 模拟攻击者环境。
   - 最终必须断言攻击成功（例如 `assertGt(attacker.balance, 0)`）。
5. 如果需要辅助合约（如恶意重入合约），请将辅助合约代码也写在同一个文件里。
6. **只输出 Solidity 代码，不要包含任何解释或注释。**
"""

    prompt = ChatPromptTemplate.from_template(template)

    print("🔴 [Red Team] 正在分析漏洞并编写攻击脚本...")

    # 运行 Chain
    chain = prompt | llm
    response = chain.invoke({{"contract_code": contract_code}})

    return extract_code(response.content)
