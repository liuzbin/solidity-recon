from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.agent.red_agent import red_team_attack
from src.agent.blue_agent import blue_team_patch
from src.tools.file_utils import save_to_workspace
from src.tools.docker_runner import run_forge_test


# === Nodes (节点) ===

def node_red_agent(state: AgentState):
    """红队节点：生成攻击代码"""
    print(f"🔴 [Red Team] Round {state['round_count']} - Generating Exploit...")

    # 调用红队 Agent
    code = red_team_attack(state["target_source"])

    # 保存到文件，供 Docker 读取
    save_to_workspace("Exploit.t.sol", code)

    return {"exploit_source": code}


def node_sandbox(state: AgentState):
    """沙盒节点：执行测试"""
    # 确保 Target.sol 是最新的
    save_to_workspace("Target.sol", state["target_source"])

    # === 修改点：接收 status (str) 和 logs (str) ===
    status, logs = run_forge_test("Exploit.t.sol")

    print(f"🐳 [Sandbox] Execution Status: {status}")

    return {
        "execution_status": status,
        "test_logs": logs
    }


def node_blue_agent(state: AgentState):
    """蓝队节点：修复代码"""
    print(f"🔵 [Blue Team] Round {state['round_count']} - Patching Contract...")

    patched_code = blue_team_patch(
        state["target_source"],
        state["exploit_source"],
        state["test_logs"]
    )
    return {
        "target_source": patched_code,
        "round_count": state["round_count"] + 1
    }


# === Edges (条件边) ===

def check_status(state: AgentState):
    """根据执行状态决定下一步"""
    status = state["execution_status"]

    if status == "error":
        print("⚠️ [System] 检测到执行/语法错误，打回给红队重试...")
        return "retry"  # 路由到 red_agent

    if status == "failed":
        print("✅ [System] 攻击失败（断言不成立），合约暂时安全。")
        return "secure"  # 路由到 END

    if status == "success":
        print("🚨 [System] 攻击成功！合约被攻破！转交蓝队修复。")
        if state["round_count"] > 3:
            print("🛑 [System] 达到最大轮次，强制停止。")
            return "max_rounds"  # 路由到 END
        return "vulnerable"  # 路由到 blue_agent

    return "secure"


# === Graph Construction (建图) ===

def create_graph():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("red_agent", node_red_agent)
    workflow.add_node("sandbox", node_sandbox)
    workflow.add_node("blue_agent", node_blue_agent)

    # 设置入口
    workflow.set_entry_point("red_agent")

    # 连线：红队 -> 沙盒
    workflow.add_edge("red_agent", "sandbox")

    # 条件跳转
    workflow.add_conditional_edges(
        "sandbox",
        check_status,
        {
            "retry": "red_agent",  # 语法错误 -> 重试
            "secure": END,  # 攻击失败 -> 结束 (安全)
            "vulnerable": "blue_agent",  # 攻击成功 -> 修复
            "max_rounds": END  # 超时 -> 结束
        }
    )

    # 蓝队修完 -> 回到红队继续测
    workflow.add_edge("blue_agent", "red_agent")

    return workflow.compile()