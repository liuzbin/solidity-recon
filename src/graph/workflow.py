from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.agent.red_agent import red_team_attack
from src.agent.blue_agent import blue_team_patch
from src.tools.file_utils import save_to_workspace
from src.tools.docker_runner import run_forge_test, check_compilation
from src.tools.slither_runner import run_slither_scan  # <--- 新增引用


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


def node_recon(state: AgentState):
    """
    【Recon】侦察节点
    运行 Slither，将报告存入 State，供红队使用
    """
    # 如果已经是第二轮及以上（round_count > 1），或者是语法重试，其实不用重复跑 Slither
    # 但为了简单，我们每次都跑，确保针对 Patch 后的代码也能发现新漏洞
    report = run_slither_scan("Target.sol")
    # print(f"📄 [Recon] Slither 报告已生成:\n{report[:200]}...")
    return {"slither_report": report}


# === 2. 红队工作流 ===
def node_red_agent(state: AgentState):
    """【Red Team】攻击节点"""
    # 传入 slither_report
    code = red_team_attack(
        state["target_source"],
        state.get("slither_report", "No report"),
        state.get("compiler_feedback", "")
    )
    save_to_workspace("Exploit.t.sol", code)
    return {"exploit_source": code, "compiler_feedback": ""}


def node_check_exploit(state: AgentState):
    """【Checker】红队代码检查"""
    is_valid, error = check_compilation("Exploit.t.sol")
    if not is_valid:
        print(f"⚠️ [Checker] 攻击脚本编译失败，打回红队重写。")
        return {"execution_status": "compile_error", "compiler_feedback": error}
    return {"execution_status": "compile_pass"}


def node_sandbox(state: AgentState):
    """【Executor】执行节点"""
    status, logs = run_forge_test("Exploit.t.sol")
    print(f"🐳 [Sandbox] Execution Status: {status}")
    return {"execution_status": status, "test_logs": logs}


def node_blue_agent(state: AgentState):
    """【Blue Team】防御节点"""
    # 这里的 blue_agent 也应该适配 feedback 参数，这里省略展示
    code = blue_team_patch(state["target_source"], state["exploit_source"], state["test_logs"])
    return {"target_source": code, "round_count": state["round_count"] + 1, "compiler_feedback": ""}


def node_check_patch(state: AgentState):
    """【Checker】蓝队代码检查"""
    save_to_workspace("Target.sol", state["target_source"])
    is_valid, error = check_compilation("Target.sol")
    if not is_valid:
        print(f"⚠️ [Checker] 修复后的合约编译失败，打回蓝队重写。")
        return {"execution_status": "patch_error", "compiler_feedback": error}
    return {"execution_status": "patch_pass"}


# === Edges ===
# (路由逻辑函数保持不变，见上文)
def router_check_target(state: AgentState):
    if state["execution_status"] == "fatal_error": return END
    return "recon"  # <--- 修改：去侦察


def router_check_exploit(state: AgentState):
    if state["execution_status"] == "compile_error": return "red_agent"
    return "sandbox"


def router_sandbox(state: AgentState):
    status = state["execution_status"]
    if status == "success": return "blue_agent"
    if status == "failed": return END
    return END


def router_check_patch(state: AgentState):
    if state["execution_status"] == "patch_error": return "blue_agent"
    return "recon"  # <--- 修改：修复后，重新侦察一轮


# === Build Graph ===
def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("check_target", node_check_target)
    workflow.add_node("recon", node_recon)  # <--- 新节点
    workflow.add_node("red_agent", node_red_agent)
    workflow.add_node("check_exploit", node_check_exploit)
    workflow.add_node("sandbox", node_sandbox)
    workflow.add_node("blue_agent", node_blue_agent)
    workflow.add_node("check_patch", node_check_patch)

    workflow.set_entry_point("check_target")

    workflow.add_conditional_edges("check_target", router_check_target)

    # 连线：Check Target -> Recon -> Red Agent
    workflow.add_edge("recon", "red_agent")

    workflow.add_edge("red_agent", "check_exploit")
    workflow.add_conditional_edges("check_exploit", router_check_exploit)

    workflow.add_conditional_edges("sandbox", router_sandbox)

    workflow.add_edge("blue_agent", "check_patch")
    workflow.add_conditional_edges("check_patch", router_check_patch)

    return workflow.compile()