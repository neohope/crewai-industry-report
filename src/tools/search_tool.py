"""
网络搜索工具模块 - 使用byted-web-search (火山引擎联网搜索)
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from crewai.tools import BaseTool


class WebSearchTool(BaseTool):
    """网络搜索工具 - 使用byted-web-search技能"""
    name = "web_search"
    description = "使用火山引擎联网搜索获取最新的行业信息。输入：搜索关键词。输出：搜索结果列表。"

    def __init__(self):
        """初始化搜索工具"""
        self.skill_path = self._find_skill_path()
        super().__init__()

    def _find_skill_path(self) -> Optional[Path]:
        """查找byted-web-search技能路径"""
        current_dir = Path(__file__).parent.parent.parent
        skill_dir = current_dir / "skills" / "byted-web-search"
        if skill_dir.exists():
            return skill_dir
        return None

    def _search_with_skill(self, query: str, max_results: int = 10,
                         time_range: str = None,
                         auth_level: int = 0,
                         query_rewrite: bool = False) -> List[Dict[str, Any]]:
        """使用byted-web-search技能进行搜索"""
        if not self.skill_path:
            return [{"error": "byted-web-search技能不可用", "info": "请确认skills/byted-web-search目录存在"}]

        script_path = self.skill_path / "scripts" / "web_search.py"
        if not script_path.exists():
            return [{"error": "搜索脚本不存在", "info": "web_search.py未找到"}]

        cmd = [sys.executable, str(script_path), query, "--count", str(max_results)]
        if time_range:
            cmd.extend(["--time-range", time_range])
        if auth_level > 0:
            cmd.extend(["--auth-level", str(auth_level)])
        if query_rewrite:
            cmd.append("--query-rewrite")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                return self._parse_skill_output(result.stdout)
            else:
                return [{"error": "搜索执行失败", "stderr": result.stderr or "未知错误"}]
        except subprocess.TimeoutExpired:
            return [{"error": "搜索超时"}]
        except Exception as e:
            return [{"error": f"搜索异常: {str(e)}"}]

    def _parse_skill_output(self, stdout: str) -> List[Dict[str, Any]]:
        """解析byted-web-search技能输出"""
        lines = stdout.strip().split('\n')
        results = []
        current_item = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_item:
                    results.append(current_item)
                    current_item = {}
                continue

            if line.startswith('[') and ']' in line:
                if current_item:
                    results.append(current_item)
                current_item = {}

            if current_item:
                if line.startswith('http://') or line.startswith('https://'):
                    current_item['url'] = line
                elif not current_item.get('title'):
                    current_item['title'] = line
                elif not current_item.get('snippet'):
                    current_item['snippet'] = line
            else:
                if line.startswith('['):
                    continue
                if line.startswith('结果数'):
                    continue
                if line.strip():
                    current_item['title'] = line

        if current_item:
            results.append(current_item)

        return results

    def _run(self, query: str, max_results: int = 10,
            time_range: str = None,
            auth_level: int = 0,
            query_rewrite: bool = False) -> str:
        """执行搜索

        Args:
            query: 搜索关键词
            max_results: 最多返回结果数（默认10）
            time_range: 时间范围（OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD）
            auth_level: 权威等级（0=全部，1=仅权威来源）
            query_rewrite: 是否开启查询改写

        Returns:
            JSON格式的搜索结果
        """
        if not query or not query.strip():
            return json.dumps({"error": "搜索关键词不能为空"}, ensure_ascii=False)

        results = self._search_with_skill(query, max_results, time_range, auth_level, query_rewrite)

        return json.dumps({
            "query": query,
            "total_results": len(results),
            "results": results
        }, ensure_ascii=False)


class NewsSearchTool(BaseTool):
    """新闻搜索工具 - 使用byted-web-search技能"""
    name = "news_search"
    description = "搜索最新的行业新闻和资讯。输入：搜索关键词。输出：新闻列表。"

    def __init__(self):
        """初始化新闻搜索工具"""
        self.skill_path = self._find_skill_path()
        super().__init__()

    def _find_skill_path(self) -> Optional[Path]:
        """查找byted-web-search技能路径"""
        current_dir = Path(__file__).parent.parent.parent
        skill_dir = current_dir / "skills" / "byted-web-search"
        if skill_dir.exists():
            return skill_dir
        return None

    def _search_with_skill(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """使用byted-web-search技能进行新闻搜索"""
        if not self.skill_path:
            return [{"error": "byted-web-search技能不可用", "info": "请确认skills/byted-web-search目录存在"}]

        script_path = self.skill_path / "scripts" / "web_search.py"
        if not script_path.exists():
            return [{"error": "搜索脚本不存在", "info": "web_search.py未找到"}]

        cmd = [sys.executable, str(script_path), query, "--count", str(max_results)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                return self._parse_skill_output(result.stdout)
            else:
                return [{"error": "搜索执行失败", "stderr": result.stderr or "未知错误"}]
        except subprocess.TimeoutExpired:
            return [{"error": "搜索超时"}]
        except Exception as e:
            return [{"error": f"搜索异常: {str(e)}"}]

    def _parse_skill_output(self, stdout: str) -> List[Dict[str, Any]]:
        """解析搜索输出"""
        lines = stdout.strip().split('\n')
        results = []
        current_item = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_item:
                    results.append(current_item)
                    current_item = {}
                continue

            if line.startswith('[') and ']' in line:
                if current_item:
                    results.append(current_item)
                current_item = {}

            if current_item:
                if line.startswith('http://') or line.startswith('https://'):
                    current_item['url'] = line
                elif not current_item.get('title'):
                    current_item['title'] = line
                elif not current_item.get('snippet'):
                    current_item['snippet'] = line
            else:
                if line.startswith('['):
                    continue
                if line.startswith('结果数'):
                    continue
                if line.strip():
                    current_item['title'] = line

        if current_item:
            results.append(current_item)

        return results

    def _run(self, query: str, max_results: int = 10) -> str:
        """执行新闻搜索"""
        if not query or not query.strip():
            return json.dumps({"error": "搜索关键词不能为空"}, ensure_ascii=False)

        results = self._search_with_skill(query, max_results)

        return json.dumps({
            "query": query,
            "total_results": len(results),
            "results": results
        }, ensure_ascii=False)
