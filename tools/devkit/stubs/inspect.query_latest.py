"""桩（假接口）参考示例：inspect.query_latest。

任何新接口的桩都照这个写：
1. 用条件导入兼容 mcp 1.x（FastMCP）与 2.x（MCPServer）；
2. 用 @mcp.tool() 注册与接口同名的工具，参数名/类型与契约一致；
3. 函数体不写真逻辑——按输入决定返回哪份样例：
   - 正常输入 → contracts/fixtures/<接口名>/success.json
   - 特殊输入（这里用 empty- 前缀约定）→ contracts/fixtures/<接口名>/empty.json
4. 文件放在 tools/devkit/stubs/<接口名>.py（文件名 = 接口名）。

真接口验证时不用改本文件，由总开关判断：
   python tools/devkit/run_contract_tests.py --mode real
"""
import json
from pathlib import Path

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # pragma: no cover - mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

ROOT = Path(__file__).resolve().parents[3]  # 仓库根（tools/devkit/stubs/xxx.py）
FIXTURES = ROOT / "contracts" / "fixtures"

mcp = _Server("stub-inspect-query-latest")


def _load(rel: str):
    return json.loads((FIXTURES / rel).read_text(encoding="utf-8"))


@mcp.tool()
def inspect_query_latest(project_id: str, module_id: str) -> dict | None:
    """查询某项目某模块的最新检测结果。

    参数:
        project_id: 论文项目编号,如 proj-001
        module_id:  模块编号,如 abstract(摘要)
    返回:
        最新的检测结果摘要(CheckSummary);该项目还没检测过时返回 null。
    """
    # 桩的约定:以 empty- 开头的 project_id 模拟"还没检测过"
    if project_id.startswith("empty-"):
        return _load("inspect.query_latest/empty.json")
    return _load("inspect.query_latest/success.json")


if __name__ == "__main__":
    mcp.run()  # stdio 模式,客户端拉起它并通信
