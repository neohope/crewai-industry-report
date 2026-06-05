#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试套件 - 运行所有测试，验证所有功能
"""
import sys
import os
import subprocess
import json
from datetime import datetime


def run_test_script(script_name):
    """运行测试脚本"""
    print(f"\n{'='*80}")
    print(f"  运行: {script_name}")
    print(f"{'='*80}")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return False


def check_project_structure():
    """检查项目结构"""
    print("\n" + "="*80)
    print("  检查项目结构")
    print("="*80)

    required_files = [
        "pyproject.toml",
        "requirements.txt",
        ".env.example",
        "README.md",
        "src/__init__.py",
        "src/main.py",
        "src/tools/__init__.py",
        "src/tools/search_tool.py",
        "src/tools/feishu_tool.py",
        "tests/test_search_tools.py",
        "tests/test_feishu_tools.py",
        "tests/test_crew.py",
        "tests/test_crew_full.py",
    ]

    all_exist = True
    for f in required_files:
        exists = os.path.exists(f)
        status = "✅" if exists else "❌"
        print(f"  {status} {f}")
        if not exists:
            all_exist = False

    return all_exist


def check_environment():
    """检查环境"""
    print("\n" + "="*80)
    print("  检查环境")
    print("="*80)

    # Python版本
    print(f"Python版本: {sys.version}")
    version_ok = sys.version_info >= (3, 10)
    print(f"版本要求: 3.10+ -> {'✅ 满足' if version_ok else '❌ 不满足'}")

    # 环境变量
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        if openai_key.startswith("sk-"):
            print("OPENAI_API_KEY: ✅ 已配置")
        else:
            print("OPENAI_API_KEY: ⚠️  已配置 (格式可能不正确)")
    else:
        print("OPENAI_API_KEY: ❌ 未配置")
        print("  (需要配置后才能运行完整的CrewAI工作流)")

    return version_ok


def run_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("  运行完整测试套件")
    print("="*80)

    results = {}

    # 检查项目结构
    print("\n[1/5] 检查项目结构...")
    results["结构检查"] = check_project_structure()

    # 检查环境
    print("\n[2/5] 检查环境...")
    results["环境检查"] = check_environment()

    # 测试搜索工具
    print("\n[3/5] 测试搜索工具...")
    results["搜索工具"] = run_test_script("tests/test_search_tools.py")

    # 测试飞书工具
    print("\n[4/5] 测试飞书工具...")
    results["飞书工具"] = run_test_script("tests/test_feishu_tools.py")

    # 测试主程序
    print("\n[5/5] 测试主程序...")
    results["主程序"] = run_test_script("tests/test_crew_full.py")

    return results


def generate_report(results):
    """生成测试报告"""
    print("\n" + "="*80)
    print("  测试报告")
    print("="*80)

    print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{'测试项':<20} {'状态':<10}")
    print("-"*30)

    passed = 0
    total = len(results)

    for name, ok in results.items():
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{name:<20} {status}")
        if ok:
            passed += 1

    print("-"*30)
    print(f"{'总计':<20} {passed}/{total}")

    print("\n" + "="*80)
    if passed == total:
        print("  🎉 所有测试通过！")
        print("\n项目已准备就绪，可以使用！")
        print("\n下一步:")
        print("1. 配置 .env 文件（设置 OPENAI_API_KEY）")
        print("2. 安装依赖: poetry install 或 pip install -r requirements.txt")
        print("3. 运行主程序: python src/main.py")
    else:
        print(f"  ⚠️  {total - passed} 个测试失败")
        print("\n请检查上述失败项并修复。")
    print("="*80)

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "passed": passed,
        "total": total,
    }

    report_file = "test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存: {report_file}")

    return passed == total


def main():
    """主函数"""
    print("\n" + "="*80)
    print("  行业研究报告生成系统 - 完整测试套件")
    print("="*80)

    # 切换到项目目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    # 运行测试
    results = run_tests()

    # 生成报告
    all_passed = generate_report(results)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
