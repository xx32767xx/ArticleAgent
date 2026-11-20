"""契约测试总开关（参考示例）。

用法（在仓库根目录）:
    python tools/devkit/run_contract_tests.py                    # 连桩(假接口)跑全部接口
    python tools/devkit/run_contract_tests.py --mode real        # 连"真接口"跑全部接口
    python tools/devkit/run_contract_tests.py --only inspect.query_latest   # 只跑某个接口

机制:
1. 扫描 contracts/tests/ 下每个接口文件夹里的 test_contract.py（自动发现，新增接口不用改这里）；
2. 按 --mode 为每个接口拉起对应的 MCP 服务：
   - stub 模式：tools/devkit/stubs/<接口名>.py
   - real 模式：tools/devkit/real_examples/<接口名>.py（正式落地后换成各模块的真实服务）
3. 逐个执行接口的 run(connector)，按接口名报告通过/失败。

新增接口时需要做的事（三步，不用改本文件）：
    contracts/fixtures/<接口名>/xyz.json   ← 样例数据
    contracts/tests/<接口名>/test_contract.py ← 断言（提供方 + 消费方）
    tools/devkit/stubs/<接口名>.py          ← 桩
"""
import argparse
import asyncio
import importlib.util
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]  # 仓库根
TESTS = ROOT / "contracts" / "tests"
STUB_DIR = ROOT / "tools" / "devkit" / "stubs"
REAL_DIR = ROOT / "tools" / "devkit" / "real_examples"
SERVICE_DIRS = {"stub": STUB_DIR, "real": REAL_DIR}


def discover(only: str | None):
    """扫描 contracts/tests/ 下的接口文件夹，返回 [(接口名, 测试文件路径)]。"""
    results = []
    for d in sorted(TESTS.iterdir()):
        if not d.is_dir():
            continue
        if only and d.name != only:
            continue
        f = d / "test_contract.py"
        if f.exists():
            results.append((d.name, f))
    return results


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_connector(mode: str, iface: str):
    """按模式+接口名生成连接器（一个接口对应一个 MCP 服务文件）。"""
    service_dir = SERVICE_DIRS[mode]
    server_file = service_dir / f"{iface}.py"
    if not server_file.exists():
        raise FileNotFoundError(
            f"缺少服务文件：{server_file}（{mode} 模式下接口 {iface} 的桩/真实现）"
        )

    @asynccontextmanager
    async def connector():
        params = StdioServerParameters(command=sys.executable, args=[str(server_file)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    return connector


async def main(mode: str, only: str | None) -> int:
    ifaces = discover(only)
    if not ifaces:
        print("没有发现任何接口测试（contracts/tests/<接口名>/test_contract.py）")
        return 1

    results = []
    for iface, path in ifaces:
        mod = load_module(f"iface_{iface.replace('.', '_')}", path)
        try:
            await mod.run(make_connector(mode, iface))
            results.append((iface, True, ""))
            print(f"[PASS] {iface}")
        except Exception as e:  # noqa: BLE001 —— 报告里要点名到接口
            results.append((iface, False, f"{type(e).__name__}: {e}"))
            print(f"[FAIL] {iface}\n   {type(e).__name__}: {e}")
            traceback.print_exc()

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} 个接口通过（mode={mode}）")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="契约测试总开关（参考示例）")
    ap.add_argument("--mode", choices=["stub", "real"], default="stub", help="桩/真接口")
    ap.add_argument("--only", default=None, help="只跑指定接口，如 inspect.query_latest")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.mode, args.only)))
