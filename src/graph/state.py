from typing import TypedDict


class AgentState(TypedDict):
    target_source: str  # 目标合约源码
    exploit_source: str  # 攻击脚本源码
    test_logs: str  # 运行日志

    # === 修改点：使用字符串状态，而不是布尔值 ===
    # 取值范围: "success" (攻击成功), "failed" (攻击失败), "error" (执行错误), "unknown" (初始)
    execution_status: str

    round_count: int  # 当前轮次
