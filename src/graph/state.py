from typing import TypedDict


class AgentState(TypedDict):
    target_source: str  # 目标合约源码
    exploit_source: str  # 攻击脚本源码
    test_logs: str  # 运行日志

    # === 新增：编译器反馈 ===
    compiler_feedback: str  # 存放 Checker 的报错信息
    slither_report: str  # Slither 静态分析报告

    execution_status: str  # success, failed, error
    round_count: int
