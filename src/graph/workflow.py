from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.agent.red_agent import red_team_attack
from src.agent.blue_agent import blue_team_patch
from src.tools.file_utils import save_to_workspace
from src.tools.docker_runner import run_forge_test


# === 节点函数 (Nodes) ===

def node_red_agent(state: AgentState):
    """红队节点：生成攻击代码"""
    code = red_team_attack(state["target_source"])
    save_to_workspace("Exploit.t.sol", code)  # 保存到磁盘供 Docker 读取
    return {"exploit_source": code}


def node_sandbox(state: AgentState):
    """沙盒节点：执行测试"""
    # 确保 Target.sol 是最新的（可能是蓝队修过的）
    save_to_workspace("Target.sol", state["target_source"])

    # 运行红队的攻击脚本
    success, logs = run_forge_test("Exploit.t.sol")

    # 注意：在 Foundry 测试中，PASS (success=True) 意味着测试通过了 -> 即攻击逻辑执行成功了 -> 合约是脆弱的
    return {
        "is_vulnerable": success,
        "test_logs": logs
    }


def node_blue_agent(state: AgentState):
    """蓝队节点：修复代码"""
    patched_code = blue_team_patch(
        state["target_source"],
        state["exploit_source"],
        state["test_logs"]
    )
    return {
        "target_source": patched_code,
        "round_count": state["round_count"] + 1
    }


# === 条件边 (Edges) ===

def check_status(state: AgentState):
    if not state["is_vulnerable"]:
        # 攻击失败（测试不通过），说明合约是安全的（或者红队太菜）
        print("✅ [System] 攻击失败，合约暂时安全。")
        return "secure"

    if state["round_count"] > 3:
        # 防止无限循环
        print("🛑 [System] 达到最大轮次，停止。")
        return "max_rounds"

    print("⚠️ [System] 攻击成功！漏洞存在，转交蓝队修复。")
    return "vulnerable"


# === 构建图 ===

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
            "secure": END,  # 安全 -> 结束
            "max_rounds": END,  # 超时 -> 结束
            "vulnerable": "blue_agent"  # 脆弱 -> 蓝队修
        }
    )

    # 蓝队修完 -> 回到红队继续测（回归测试）
    workflow.add_edge("blue_agent", "red_agent")

    return workflow.compile()
