from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.agent.red_agent import red_team_attack
from src.agent.blue_agent import blue_team_patch
from src.tools.file_utils import save_to_workspace
from src.tools.docker_runner import run_forge_test, check_compilation


# === 1. 初始化检查节点 ===
def node_check_target(state: AgentState):
    """【Checker】入口检查：原始合约是否合法"""
    save_to_workspace("Target.sol", state["target_source"])
    is_valid, error = check_compilation("Target.sol")

    if not is_valid:
        print(f"❌ [Checker] 原始合约编译失败！终止流程。\n{error}")
        return {"execution_status": "fatal_error", "compiler_feedback": error}

    print("✅ [Checker] 原始合约编译通过。")
    return {"execution_status": "target_valid"}


# === 2. 红队工作流 ===
def node_red_agent(state: AgentState):
    print(f"🔴 [Red Team] Generating Exploit... (Retry: {bool(state.get('compiler_feedback'))})")
    code = red_team_attack(state["target_source"], state.get("compiler_feedback", ""))
    save_to_workspace("Exploit.t.sol", code)
    # 生成完清除旧的反馈
    return {"exploit_source": code, "compiler_feedback": ""}


def node_check_exploit(state: AgentState):
    """【Checker】红队代码检查"""
    is_valid, error = check_compilation("Exploit.t.sol")
    if not is_valid:
        print(f"⚠️ [Checker] 攻击脚本编译失败，打回红队重写。")
        return {"execution_status": "compile_error", "compiler_feedback": error}
    return {"execution_status": "compile_pass"}


# === 3. 执行节点 ===
def node_sandbox(state: AgentState):
    """【Executor】只负责跑逻辑，不管语法"""
    # 此时可以确信 Target 和 Exploit 都是符合语法规范的
    status, logs = run_forge_test("Exploit.t.sol")
    print(f"🐳 [Sandbox] Execution Status: {status}")
    return {"execution_status": status, "test_logs": logs}


# === 4. 蓝队工作流 ===
def node_blue_agent(state: AgentState):
    print(f"🔵 [Blue Team] Patching... (Retry: {bool(state.get('compiler_feedback'))})")
    # 这里的 blue_team_patch 也要记得改，接收 feedback
    code = blue_team_patch(state["target_source"], state["exploit_source"], state["test_logs"])  # 这里简化，实际要加 feedback
    return {"target_source": code, "round_count": state["round_count"] + 1, "compiler_feedback": ""}


def node_check_patch(state: AgentState):
    """【Checker】蓝队代码检查"""
    save_to_workspace("Target.sol", state["target_source"])
    is_valid, error = check_compilation("Target.sol")
    if not is_valid:
        print(f"⚠️ [Checker] 修复后的合约编译失败，打回蓝队重写。")
        # 注意：这里可能需要回滚 Target.sol，或者让蓝队基于错误继续改
        return {"execution_status": "patch_error", "compiler_feedback": error}
    return {"execution_status": "patch_pass"}


# === 路由逻辑 ===
def router_check_target(state: AgentState):
    if state["execution_status"] == "fatal_error": return END
    return "red_agent"


def router_check_exploit(state: AgentState):
    if state["execution_status"] == "compile_error": return "red_agent"  # 重写
    return "sandbox"  # 通过，去执行


def router_sandbox(state: AgentState):
    status = state["execution_status"]
    if status == "success": return "blue_agent"  # 攻破了，修
    if status == "failed": return END  # 没攻破，安全
    return END  # 出错了


def router_check_patch(state: AgentState):
    if state["execution_status"] == "patch_error": return "blue_agent"  # 重写
    return "red_agent"  # 通过，下一轮红队攻击


# === 建图 ===
def create_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("check_target", node_check_target)
    workflow.add_node("red_agent", node_red_agent)
    workflow.add_node("check_exploit", node_check_exploit)
    workflow.add_node("sandbox", node_sandbox)
    workflow.add_node("blue_agent", node_blue_agent)
    workflow.add_node("check_patch", node_check_patch)

    # Entry
    workflow.set_entry_point("check_target")

    # Edges
    workflow.add_conditional_edges("check_target", router_check_target)

    workflow.add_edge("red_agent", "check_exploit")
    workflow.add_conditional_edges("check_exploit", router_check_exploit)

    workflow.add_conditional_edges("sandbox", router_sandbox)

    workflow.add_edge("blue_agent", "check_patch")
    workflow.add_conditional_edges("check_patch", router_check_patch)

    return workflow.compile()