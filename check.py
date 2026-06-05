#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目检查脚本 - 包含工具配置检查
"""
import sys
import os


def safe_print(text):
    """安全打印，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode())


def check_python_version():
    """检查Python版本"""
    safe_print("=" * 60)
    safe_print("  1. Python 版本检查")
    safe_print("=" * 60)

    version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    safe_print(f"\nPython version: {version_str}")
    version_ok = sys.version_info >= (3, 10)
    safe_print(f"版本要求: 3.10+ -> {'OK' if version_ok else 'FAIL'}")

    return version_ok


def check_project_structure():
    """检查项目结构"""
    safe_print("\n" + "=" * 60)
    safe_print("  2. 项目结构检查")
    safe_print("=" * 60)

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
        "src/tools/config.py",
        "src/tools/timeout_manager.py",
        "tests/test_crew.py",
        "tests/test_search_tools.py",
        "tests/test_feishu_tools.py",
        "tests/test_crew_full.py",
        "tests/run_all_tests.py",
    ]

    safe_print("\n检查必要文件:")
    all_exist = True
    for filepath in required_files:
        exists = os.path.exists(filepath)
        status = "OK" if exists else "MISSING"
        safe_print(f"  [{status}] {filepath}")
        if not exists:
            all_exist = False

    # 检查技能目录
    safe_print("\n检查技能目录:")
    skills_dir = os.path.exists("skills")
    safe_print(f"  [{'OK' if skills_dir else 'MISSING'}] skills/")
    if skills_dir:
        skills = ["byted-web-search", "lark-doc", "lark-drive", "lark-im"]
        for skill in skills:
            skill_path = os.path.join("skills", skill)
            skill_ok = os.path.exists(skill_path)
            status = "OK" if skill_ok else "MISSING"
            safe_print(f"    [{status}] {skill}")

    return all_exist


def check_config_files():
    """检查配置文件"""
    safe_print("\n" + "=" * 60)
    safe_print("  3. 配置文件检查")
    safe_print("=" * 60)

    has_env_example = os.path.exists(".env.example")
    safe_print(f"\n  [{'OK' if has_env_example else 'MISSING'}] .env.example")

    has_env = os.path.exists(".env")
    if has_env:
        safe_print("  [OK] .env")

        # 简单检查关键配置
        try:
            with open(".env", "r", encoding="utf-8") as f:
                content = f.read()

            safe_print("\n关键配置检查:")
            checks = [
                ("OPENAI_API_KEY", "OPENAI_API_KEY" in content),
                ("USE_BYTED_WEB_SEARCH", "USE_BYTED_WEB_SEARCH" in content),
                ("USE_LARK_SKILL", "USE_LARK_SKILL" in content),
                ("PROJECT_TIMEOUT", "PROJECT_TIMEOUT" in content),
                ("PASSING_SCORE", "PASSING_SCORE" in content),
            ]

            for name, present in checks:
                status = "OK" if present else "NOT FOUND"
                safe_print(f"  [{status}] {name}")

        except Exception as e:
            safe_print(f"  [WARN] 无法读取.env文件: {e}")
    else:
        safe_print("  [NOT CREATED YET] .env")
        safe_print("  提示: 请复制.env.example为.env并配置相应参数")

    return has_env_example


def try_import_config_module():
    """尝试导入配置模块"""
    safe_print("\n" + "=" * 60)
    safe_print("  4. 工具配置模块检查")
    safe_print("=" * 60)

    try:
        # 添加项目路径
        project_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_dir)

        from src.tools.config import Config

        safe_print("\n  [OK] 配置模块导入成功")

        # 打印配置摘要
        safe_print("\n当前配置摘要:")
        safe_print(f"  飞书配置已加载")

        return True
    except ImportError as e:
        safe_print(f"\n  [FAIL] 配置模块导入失败: {e}")
        safe_print("  提示: 请先安装依赖")
        return False
    except Exception as e:
        safe_print(f"\n  [FAIL] 配置模块检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主检查函数"""
    safe_print("\n" + "=" * 60)
    safe_print("  行业研究报告生成系统 - 完整检查")
    safe_print("=" * 60)

    results = []

    # 1. Python版本
    results.append(("Python版本", check_python_version()))

    # 2. 项目结构
    results.append(("项目结构", check_project_structure()))

    # 3. 配置文件
    results.append(("配置文件", check_config_files()))

    # 4. 配置模块
    results.append(("配置模块", try_import_config_module()))

    # 总结
    safe_print("\n" + "=" * 60)
    safe_print("  检查总结")
    safe_print("=" * 60)

    passed = sum(1 for name, ok in results if ok)
    total = len(results)

    safe_print("\n检查结果:")
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        safe_print(f"  {name}: {status}")

    safe_print("\n" + "=" * 60)
    if passed == total:
        safe_print("  所有检查通过！")
        safe_print("\n下一步:")
        safe_print("  1. 配置.env文件（设置OPENAI_API_KEY）")
        safe_print("  2. 安装依赖: pip install -r requirements.txt")
        safe_print("  3. 运行测试: python tests/run_all_tests.py")
        safe_print("  4. 运行主程序: python src/main.py")
    else:
        safe_print(f"  {total - passed} 个检查未通过，请检查相关问题")
        safe_print("\n提示: 请先解决上述问题后再继续")
    safe_print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        safe_print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
