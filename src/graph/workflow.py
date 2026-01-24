from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.agent.blue_agent import blue_team_patch
from src.tools.file_utils import save_to_workspace
from src.tools.docker_runner import check_compilation
from src.tools.slither_runner import run_slither_scan
from src.tools.fuzzer import run_fuzz_test


# === 节点定义 ===
def node_static_scan(state: AgentState):
    """静态扫描节点"""
    print("\n" + "=" * 50)
    print("🔍 [静态扫描] 运行Slither分析...")

    # 保存当前合约
    save_to_workspace("Target.sol", state["target_source"])

    # 运行Slither扫描
    report = run_slither_scan("Target.sol")

    # 检查是否有漏洞
    has_vulnerabilities = "No obvious vulnerabilities found" not in report

    if has_vulnerabilities:
        print(f"⚠️  [静态扫描] 发现漏洞")
        print(f"📄 漏洞报告摘要: {report[:200]}..." if len(report) > 200 else f"📄 漏洞报告: {report}")

        # 增加重试计数
        new_retry_count = state.get("static_retry_count", 0) + 1
        print(f"🔄 第{new_retry_count}次重试")

        return {
            "slither_report": report,
            "execution_status": "static_fail",
            "current_phase": "static",
            "static_retry_count": new_retry_count
        }
    else:
        print("✅ [静态扫描] 通过 - 未发现明显漏洞")
        return {
            "slither_report": report,
            "execution_status": "static_pass",
            "current_phase": "static"
        }


def node_fuzz_test_1(state: AgentState):
    """第一轮动态扫描节点"""
    print("\n" + "=" * 50)
    print("🎯 [动态扫描1] 运行第一轮模糊测试...")

    # 保存合约
    save_to_workspace("Target.sol", state["target_source"])

    # 运行模糊测试
    status, logs = run_fuzz_test("Target.sol", iteration=1)

    # 输出测试结果
    print(f"📊 [动态扫描1] 结果: {status}")
    if "失败" in logs or status != "success":
        print(f"📄 失败详情: {logs[:300]}..." if len(logs) > 300 else f"📄 详情: {logs}")

    if status == "success":
        print("✅ [动态扫描1] 通过")
        return {
            "test_logs": logs,
            "execution_status": "fuzz1_pass",
            "current_phase": "fuzz1"
        }
    else:
        # 增加重试计数
        new_retry_count = state.get("fuzz1_retry_count", 0) + 1
        print(f"🔄 第{new_retry_count}次重试")

        return {
            "test_logs": logs,
            "execution_status": "fuzz1_fail",
            "current_phase": "fuzz1",
            "fuzz1_retry_count": new_retry_count
        }


def node_fuzz_test_2(state: AgentState):
    """第二轮动态扫描节点"""
    print("\n" + "=" * 50)
    print("🎯 [动态扫描2] 运行第二轮模糊测试...")

    # 保存合约
    save_to_workspace("Target.sol", state["target_source"])

    # 运行模糊测试
    status, logs = run_fuzz_test("Target.sol", iteration=2)

    # 输出测试结果
    print(f"📊 [动态扫描2] 结果: {status}")
    if "失败" in logs or status != "success":
        print(f"📄 失败详情: {logs[:300]}..." if len(logs) > 300 else f"📄 详情: {logs}")

    if status == "success":
        print("✅ [动态扫描2] 通过")
        return {
            "test_logs": logs,
            "execution_status": "fuzz2_pass",
            "current_phase": "fuzz2"
        }
    else:
        # 增加重试计数
        new_retry_count = state.get("fuzz2_retry_count", 0) + 1
        print(f"🔄 第{new_retry_count}次重试")

        return {
            "test_logs": logs,
            "execution_status": "fuzz2_fail",
            "current_phase": "fuzz2",
            "fuzz2_retry_count": new_retry_count
        }


def node_code_fix(state: AgentState):
    """代码修复节点"""
    current_phase = state.get("current_phase", "static")
    print("\n" + "=" * 50)
    print(f"🔧 [代码修复] 修复{current_phase}阶段发现的问题...")

    if current_phase == "static":
        # 基于Slither报告修复
        new_code = fix_code_based_on_report(
            state["target_source"],
            state["slither_report"]
        )
    elif current_phase == "fuzz1":
        # 基于测试日志修复
        new_code = fix_code_based_on_test(
            state["target_source"],
            state["test_logs"],
            1
        )
    else:  # fuzz2
        new_code = fix_code_based_on_test(
            state["target_source"],
            state["test_logs"],
            2
        )

    # 编译检查
    save_to_workspace("Target.sol", new_code)
    is_valid, error = check_compilation("Target.sol")

    if not is_valid:
        print("❌ [代码修复] 修复后的代码编译失败")
        return {
            "target_source": new_code,
            "compiler_feedback": error,
            "execution_status": "compile_error"
        }

    print("✅ [代码修复] 修复完成并编译通过")
    return {
        "target_source": new_code,
        "compiler_feedback": "",
        "execution_status": "fixed"
    }


def fix_code_based_on_report(original_code: str, slither_report: str) -> str:
    """基于Slither报告修复代码"""
    from src.agent.blue_agent import blue_team_patch
    # 创建一个模拟的攻击脚本来触发蓝队修复
    exploit_template = f"""// 静态扫描发现漏洞
// Slither报告：
{slither_report[:1000]}

// 请修复合约中的漏洞"""

    return blue_team_patch(original_code, exploit_template, "静态扫描发现漏洞", "")


def fix_code_based_on_test(original_code: str, test_logs: str, iteration: int) -> str:
    """基于测试日志修复代码"""
    from src.agent.blue_agent import blue_team_patch
    # 创建一个模拟的攻击脚本
    exploit_template = f"""// 动态扫描{iteration}发现测试失败
// 测试日志：
{test_logs[:1000]}

// 请修复合约中的问题"""

    return blue_team_patch(original_code, exploit_template, test_logs, "")


# === 路由函数（关键修复）===
def router_static_scan(state: AgentState):
    """静态扫描后的路由"""
    status = state.get("execution_status", "")

    if status == "static_pass":
        print("➡️  进入动态扫描1")
        return "fuzz_test_1"
    elif status == "static_fail":
        # 检查重试次数
        retry_count = state.get("static_retry_count", 0)
        if retry_count >= 3:  # 最大重试3次
            print("❌ 静态扫描重试超过3次，标记为未通过")
            return END
        print(f"➡️  进入代码修复 (第{retry_count}次重试)")
        return "code_fix"
    return END


def router_fuzz_test_1(state: AgentState):
    """动态扫描1后的路由"""
    status = state.get("execution_status", "")

    if status == "fuzz1_pass":
        print("➡️  进入动态扫描2")
        return "fuzz_test_2"
    elif status == "fuzz1_fail":
        # 检查重试次数
        retry_count = state.get("fuzz1_retry_count", 0)
        if retry_count >= 3:  # 最大重试3次
            print("❌ 动态扫描1重试超过3次，标记为未通过")
            return END
        print(f"➡️  进入代码修复 (第{retry_count}次重试)")
        return "code_fix"
    return END


def router_fuzz_test_2(state: AgentState):
    """动态扫描2后的路由"""
    status = state.get("execution_status", "")

    if status == "fuzz2_pass":
        print("✅ 所有扫描通过")
        return END
    elif status == "fuzz2_fail":
        # 检查重试次数
        retry_count = state.get("fuzz2_retry_count", 0)
        if retry_count >= 3:  # 最大重试3次
            print("❌ 动态扫描2重试超过3次，标记为未通过")
            return END
        print(f"➡️  进入代码修复 (第{retry_count}次重试)")
        return "code_fix"
    return END


def router_code_fix(state: AgentState):
    """代码修复后的路由"""
    status = state.get("execution_status", "")
    current_phase = state.get("current_phase", "static")

    if status == "compile_error":
        print("➡️  编译错误，继续修复")
        return "code_fix"
    elif status == "fixed":
        # 修复完成，返回到原阶段
        print(f"➡️  返回{current_phase}阶段重新扫描")
        if current_phase == "static":
            return "static_scan"
        elif current_phase == "fuzz1":
            return "fuzz_test_1"
        elif current_phase == "fuzz2":
            return "fuzz_test_2"

    return END


# === 构建工作流 ===
def create_graph():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("static_scan", node_static_scan)
    workflow.add_node("fuzz_test_1", node_fuzz_test_1)
    workflow.add_node("fuzz_test_2", node_fuzz_test_2)
    workflow.add_node("code_fix", node_code_fix)

    # 设置入口
    workflow.set_entry_point("static_scan")

    # 添加条件边
    workflow.add_conditional_edges(
        "static_scan",
        router_static_scan,
        {
            "fuzz_test_1": "fuzz_test_1",
            "code_fix": "code_fix",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "fuzz_test_1",
        router_fuzz_test_1,
        {
            "fuzz_test_2": "fuzz_test_2",
            "code_fix": "code_fix",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "fuzz_test_2",
        router_fuzz_test_2,
        {
            "code_fix": "code_fix",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "code_fix",
        router_code_fix,
        {
            "static_scan": "static_scan",
            "fuzz_test_1": "fuzz_test_1",
            "fuzz_test_2": "fuzz_test_2",
            "code_fix": "code_fix",
            END: END
        }
    )

    return workflow.compile()