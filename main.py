from src.graph.workflow import create_graph
from src.tools.file_utils import read_from_workspace, save_to_workspace
import json


def main():
    print("🚀 === 区块链合约安全扫描系统启动 === 🚀")
    print("📊 流程: 静态扫描 → 动态扫描1 → 动态扫描2")
    print("🔄 每阶段最多重试3次")
    print("=" * 50)

    # 1. 读取初始目标合约
    initial_contract = read_from_workspace("Target.sol")
    if not initial_contract:
        print("❌ 错误：未找到 workspace/Target.sol")
        print("💡 请将目标合约保存为 workspace/Target.sol")
        return

    # 2. 初始化状态
    initial_state = {
        "target_source": initial_contract,
        "exploit_source": "",
        "test_logs": "",
        "compiler_feedback": "",
        "slither_report": "",
        "execution_status": "pending",
        "current_phase": "static",
        "static_retry_count": 0,
        "fuzz1_retry_count": 0,
        "fuzz2_retry_count": 0,
        "round_count": 0
    }

    # 3. 创建并运行工作流
    app = create_graph()

    print("开始执行扫描流程...")
    print("=" * 50)

    try:
        # 运行工作流
        final_state = app.invoke(initial_state)

        # 4. 输出详细结果
        print("\n" + "=" * 50)
        print("🏁 安全扫描完成")
        print("=" * 50)

        # 输出扫描摘要
        print("📊 扫描摘要:")
        print(f"  - 静态扫描重试次数: {final_state.get('static_retry_count', 0)}")
        print(f"  - 动态扫描1重试次数: {final_state.get('fuzz1_retry_count', 0)}")
        print(f"  - 动态扫描2重试次数: {final_state.get('fuzz2_retry_count', 0)}")

        # 判断最终结果
        final_status = final_state.get("execution_status", "")

        if final_status == "fuzz2_pass":
            print("\n✅ 最终结果: 通过")
            print("📈 所有扫描通过，合约安全")

            # 保存最终的安全合约
            save_to_workspace("Target_Secure.sol", final_state["target_source"])
            print(f"💾 安全合约已保存: workspace/Target_Secure.sol")

        elif "fail" in final_status or final_status in ["static_fail", "fuzz1_fail", "fuzz2_fail"]:
            print(f"\n❌ 最终结果: 未通过")
            print(f"📉 失败阶段: {final_state.get('current_phase', 'unknown')}")

            # 保存有问题的合约
            save_to_workspace("Target_Vulnerable.sol", final_state["target_source"])
            print(f"💾 有漏洞的合约已保存: workspace/Target_Vulnerable.sol")

            # 输出详细报告
            if final_state.get("slither_report"):
                print(f"\n📄 静态扫描报告:")
                print("-" * 30)
                print(final_state["slither_report"][:500])
                if len(final_state["slither_report"]) > 500:
                    print("... (报告过长，已截断)")

            if final_state.get("test_logs"):
                print(f"\n📄 测试日志:")
                print("-" * 30)
                print(final_state["test_logs"][:500])
                if len(final_state["test_logs"]) > 500:
                    print("... (日志过长，已截断)")

        else:
            print(f"\n⚠️ 最终结果: 异常结束 (状态: {final_status})")

    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()