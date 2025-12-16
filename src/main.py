from src.graph.workflow import create_graph
from src.tools.file_utils import read_from_workspace


def main():
    print("🚀 === 区块链红蓝对抗系统启动 === 🚀")

    # 1. 读取初始目标合约 (请确保 workspace/Target.sol 已经存在，就是刚才那个 EtherVault)
    initial_contract = read_from_workspace("Target.sol")
    if not initial_contract:
        print("❌ 错误：未找到 workspace/Target.sol，请先创建目标合约文件。")
        return

    # 2. 初始化状态
    initial_state = {
        "target_source": initial_contract,
        "exploit_source": "",
        "test_logs": "",
        "is_vulnerable": True,  # 假设初始是不安全的
        "round_count": 1
    }

    # 3. 创建并运行图
    app = create_graph()

    # 运行流
    # recursion_limit 防止死循环
    final_state = app.invoke(initial_state, config={"recursion_limit": 10})

    print("\n🏁 === 对抗结束 ===")
    print(f"最终轮次: {final_state['round_count']}")
    print(f"最终合约状态: {'安全 ✅' if not final_state['is_vulnerable'] else '仍有漏洞 ❌'}")

    if not final_state['is_vulnerable']:
        print("\n🏆 最终修复后的代码已保存，请查看 workspace/Target.sol (内存中)")
        # 也可以选择把最终代码写回文件
        # from src.tools.file_utils import save_to_workspace
        # save_to_workspace("Target_Patched.sol", final_state["target_source"])


if __name__ == "__main__":
    main()
