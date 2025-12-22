from typing import TypedDict

class AgentState(TypedDict):
    target_source: str      # 目标合约
    exploit_source: str     # 攻击脚本
    test_logs: str          # 测试运行日志

    # === 新增 ===
    compiler_feedback: str  # 编译器报错信息
    slither_report: str     # Slither 静态分析报告
    # ============

    execution_status: str   # success, failed, error...
    round_count: int
