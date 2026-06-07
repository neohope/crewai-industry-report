"""Pytest fixtures for the legacy script-style tests.

The original tests in this repository are written so they can be run as
standalone scripts, passing imported classes/results from one function to the
next manually.  Pytest interprets function parameters as fixture names, so this
file provides those fixtures without changing the script entry points.
"""

import pytest


@pytest.fixture
def WebSearchTool():
    from src.tools.search_tool import WebSearchTool

    return WebSearchTool


@pytest.fixture
def NewsSearchTool():
    from src.tools.search_tool import NewsSearchTool

    return NewsSearchTool


@pytest.fixture
def tool(WebSearchTool):
    return WebSearchTool()


@pytest.fixture
def FeishuDocumentTool():
    from src.tools.feishu_tool import FeishuDocumentTool

    return FeishuDocumentTool


@pytest.fixture
def FeishuMessageTool():
    from src.tools.feishu_tool import FeishuMessageTool

    return FeishuMessageTool


@pytest.fixture
def IndustryResearchCrew():
    from src.main import IndustryResearchCrew

    return IndustryResearchCrew


@pytest.fixture
def crew(IndustryResearchCrew):
    return IndustryResearchCrew("测试行业")
