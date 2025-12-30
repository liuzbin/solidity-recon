from src.graph.workflow import create_graph
from src.tools.file_utils import read_from_workspace


def main():
    print("🚀 === 区块链红蓝对抗系统启动 === 🚀")

    # 1. 读取初始目标合约
    initial_contract = read_from_workspace("Target.sol")
    if not initial_contract:
        print("❌ 错误：未找到 workspace/Target.sol")
        return

    # 2. 初始化状态 (适配新的 AgentState 定义)
    initial_state = {
        "target_source": initial_contract,
        "exploit_source": "",
        "test_logs": "",
        "compiler_feedback": "",
        "slither_report": "",
        "execution_status": "unknown",
        "round_count": 1
    }

    # 3. 创建并运行图
    app = create_graph()

    # 运行流
    final_state = app.invoke(initial_state, config={"recursion_limit": 15})

    print("\n🏁 === 对抗结束 ===")
    print(f"最终轮次: {final_state['round_count']}")

    # === 修改点：根据字符串状态打印结果 ===
    status = final_state['execution_status']

    if status == "failed":
        print("🏆 最终结果: 合约安全 (红队攻击失败)")
    elif status == "success":
        print("❌ 最终结果: 合约仍不安全 (红队攻击成功)")
    else:
        print(f"⚠️ 最终结果: 异常结束 (状态: {status})")

    if status == "failed":
        print("\n💾 最终安全的合约代码已保留在 workspace/Target.sol (内存中)")


if __name__ == "__main__":
    main()
