"""真接口参考示例：inspect.query_latest。

和"桩"（tools/devkit/stubs/inspect.query_latest.py）注册同样的工具名、参数、返回字段，
只是内部换成"真的算"。总开关用 --mode real 时会拉起本文件，对同一套断言验收。

真实现的写法建议：
- 核心逻辑放在模块自己的代码里（如 skills/paper-inspector/），本文件只做"壳"：
  把工具调用转发给核心逻辑，协议细节交给 MCP 框架；
- 工具名、参数名、返回字段必须与契约一致（三层一致性里的"规范 ↔ 实现"）。
"""
from pathlib import Path

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # pragma: no cover - mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

mcp = _Server("real-inspect-query-latest")


@mcp.tool()
def inspect_query_latest(project_id: str, module_id: str) -> dict | None:
    """查询某项目某模块的最新检测结果。

    参数:
        project_id: 论文项目编号,如 proj-001
        module_id:  模块编号,如 abstract(摘要)
    返回:
        最新的检测结果摘要(CheckSummary);该项目还没检测过时返回 null。
    """
    if project_id.startswith("empty-"):
        return None
    # 真实现"算"出来的结果（演示用，字段与样例数据保持一致）
    return {
        "schemaVersion": "inspect.summary.v1",
        "runId": "real-run-0001",
        "docVersion": "v12",
        "checkedAt": "2026-11-16T09:00:00Z",
        "summary": {"P0": 1, "P1": 2, "P2": 0},
        "topIssueCategories": ["A"],
        "topIssues": [
            {
                "issueId": "real-issue-0001",
                "category": "A",
                "title": "摘要缺结论要素",
                "severity": "P0",
                "anchor": {"section": "摘要", "paragraph": 2},
            }
        ],
        "moduleScore": {"structure": 4, "content": 3, "logic": 4, "language": 4, "standard": 3},
    }


if __name__ == "__main__":
    mcp.run()
