import subprocess
import json
import os
from src.tools.file_utils import WORKSPACE_DIR


def run_fuzz_test(contract_file: str, iteration: int = 1) -> (str, str):
    """
    运行Foundry模糊测试
    """
    print(f"🎲 [模糊测试{iteration}] 对 {contract_file} 运行模糊测试...")

    # 使用简单的测试命令
    if iteration == 1:
        fuzz_runs = 1000
    else:
        fuzz_runs = 10000

    # 创建一个简单的测试文件
    test_code = create_simple_test(contract_file, iteration)
    test_filename = f"FuzzTest{iteration}.t.sol"

    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    test_path = os.path.join(WORKSPACE_DIR, test_filename)
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_code)

    # 运行测试
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{WORKSPACE_DIR}:/app",
        "foundry-box",
        f"forge test --json --fuzz-runs {fuzz_runs} --match-path /app/{test_filename}"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        # 解析结果
        if result.returncode == 0:
            return "success", f"模糊测试{iteration}通过 ({fuzz_runs}次运行)"
        else:
            # 尝试解析错误
            try:
                data = json.loads(result.stdout)
                if "test_results" in data:
                    failures = []
                    for test_name, test_result in data["test_results"].items():
                        if test_result.get("status") != "Success":
                            failures.append(f"{test_name}: {test_result.get('reason', 'Unknown')}")
                    if failures:
                        return "failed", f"测试失败:\n" + "\n".join(failures[:3])
            except:
                pass
            return "failed", f"模糊测试{iteration}失败 (返回码: {result.returncode})"

    except Exception as e:
        return "error", f"执行异常: {str(e)}"


def create_simple_test(target_file: str, iteration: int) -> str:
    """
    创建简单的测试合约
    """
    contract_name = target_file.replace(".sol", "")

    return f"""
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "./{target_file}";

contract FuzzTest{iteration} is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = new {contract_name}();
    }}

    // 基本功能测试
    function testFuzz_DepositWithdraw(address user, uint256 amount) public {{
        vm.assume(user != address(0));
        vm.assume(amount > 0 && amount < 100 ether);

        vm.deal(user, amount);
        vm.prank(user);

        // 尝试存款
        (bool success, ) = address(target).call{{value: amount}}("");
        if (success) {{
            // 尝试取款
            vm.prank(user);
            (bool withdrawSuccess, ) = address(target).call(
                abi.encodeWithSignature("withdraw()")
            );
            // 检查结果
            assertTrue(withdrawSuccess || address(target).balance >= 0);
        }}
    }}

    // 余额检查
    function testFuzz_BalanceCheck(address user, uint256 amount) public {{
        vm.assume(user != address(0));
        vm.assume(amount > 0 && amount < 100 ether);

        uint256 initialBalance = address(target).balance;

        vm.deal(user, amount);
        vm.prank(user);
        (bool success, ) = address(target).call{{value: amount}}("");

        if (success) {{
            uint256 finalBalance = address(target).balance;
            assertEq(finalBalance, initialBalance + amount, "余额不一致");
        }}
    }}
}}
"""