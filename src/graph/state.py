from typing import TypedDict


class AgentState(TypedDict):
    target_source: str  # 目标合约源码
    exploit_source: str  # 攻击脚本源码
    test_logs: str  # 运行日志
    compiler_feedback: str  # 存放 Checker 的报错信息
    slither_report: str  # Slither 静态分析报告

    # 执行状态
    execution_status: str  # pending, static_pass, static_fail, fuzz1_pass, fuzz1_fail, fuzz2_pass, fuzz2_fail, compile_error, fixed
    current_phase: str  # static, fuzz1, fuzz2

    # 重试计数器re
    static_retry_count: int
    fuzz1_retry_count: int
    fuzz2_retry_count: int

    round_count: int