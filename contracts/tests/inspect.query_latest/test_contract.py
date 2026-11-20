"""契约断言（参考示例）：inspect.query_latest 的返回必须符合 inspect.summary.v1。

本文件被 tools/devkit/run_contract_tests.py 自动发现执行。约定：
  run(connector) —— connector 是异步上下文管理器，产出已初始化的 MCP 会话
  （连的是桩服务还是真服务，由 runner 用 --mode 决定，本文件不用关心）。

新增接口时，照这个文件写 contracts/tests/<接口名>/test_contract.py：
- 提供方断言：我按契约返回（字段、类型、枚举、空结果、错误码）；
- 消费方断言：我拿到数据后能正确使用（分区写在文件后半部分）。
"""
import json

SEVERITIES = {"P0", "P1", "P2"}


def validate_summary(raw):
    """按契约校验返回：字段、类型、枚举、必填。"""
    assert isinstance(raw, dict), "顶层必须是对象"
    assert raw.get("schemaVersion") == "inspect.summary.v1", "版本号不对"
    for key in ("runId", "docVersion", "checkedAt", "summary", "moduleScore"):
        assert key in raw, f"缺字段: {key}"
    summary = raw["summary"]
    for key in ("P0", "P1", "P2"):
        assert isinstance(summary.get(key), int) and summary[key] >= 0, f"{key} 必须是非负整数"
    for issue in raw.get("topIssues", []):
        for key in ("issueId", "category", "title", "severity", "anchor"):
            assert key in issue, f"问题缺字段: {key}"
        assert issue["severity"] in SEVERITIES, f"severity 非法: {issue['severity']}"
        anchor = issue["anchor"]
        assert "section" in anchor and "paragraph" in anchor, "anchor 缺定位字段"


def _payload(result):
    """把 MCP 工具结果转成 dict / None（兼容 structuredContent 与文本 JSON 两种返回）。"""
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    text = result.content[0].text if getattr(result, "content", None) else ""
    return json.loads(text) if text and text.strip() else None


async def run(connector):
    async with connector() as session:
        # ---------- 提供方断言：我按契约返回 ----------
        r = await session.call_tool(
            "inspect_query_latest", {"project_id": "proj-001", "module_id": "abstract"}
        )
        validate_summary(_payload(r))

        r2 = await session.call_tool(
            "inspect_query_latest", {"project_id": "empty-proj", "module_id": "abstract"}
        )
        assert _payload(r2) is None, "没检测过的项目应返回 null"

        # ---------- 消费方断言（由用这个接口的人补写，这里给示例） ----------
        # 3 辅导拿到结果后要能按问题类别做统计，所以类别必须可用、是单字母编码
        r3 = await session.call_tool(
            "inspect_query_latest", {"project_id": "proj-001", "module_id": "abstract"}
        )
        data = _payload(r3)
        for cat in data.get("topIssueCategories", []):
            assert isinstance(cat, str) and len(cat) == 1, "问题类别必须是单字母编码（A-F）"
