from typing import TypedDict


class AgentState(TypedDict):
    target_source: str  # 原始/当前的合约代码
    exploit_source: str  # 红队生成的攻击代码
    test_logs: str  # Docker 运行日志
    is_vulnerable: bool  # 是否被攻破 (True=攻击成功/不安全, False=攻击失败/安全)
    round_count: int  # 对抗轮次
