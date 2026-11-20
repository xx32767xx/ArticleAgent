# tools/devkit/ 开发工具（公共）

放"让大家能并行干活"的工具，核心是**假接口（桩）**和**契约测试总开关**。

## 目录

```
tools/devkit/
├── stubs/<接口名>.py          # 假接口：按输入从 contracts/fixtures 挑样例返回
├── real_examples/<接口名>.py  # "真接口"示例：同工具名/参数，真算（用于演示切真）
└── run_contract_tests.py      # 总开关：自动发现、起服务、跑断言、点名报告
```

## 总开关怎么用

```powershell
# 在仓库根目录
python tools/devkit/run_contract_tests.py               # 连桩跑全部接口（快、离线）
python tools/devkit/run_contract_tests.py --mode real   # 连"真接口"跑（验证兼容性）
python tools/devkit/run_contract_tests.py --only inspect.query_latest
```

- **自动发现**：扫 `contracts/tests/` 下所有接口文件夹，新增接口不用改本文件；
- **桩/真只差一个开关**：`--mode` 决定拉 `stubs/` 还是 `real_examples/` 下的服务；
- **失败点名**：报告直接说"红的是哪个接口"。

## 新增一个接口（三步）

1. `contracts/fixtures/<接口名>/`：放样例（`success.json`、`empty.json`，需要的话 `invalid.json`）；
2. `contracts/tests/<接口名>/test_contract.py`：照 `inspect.query_latest` 的写法写断言；
3. `tools/devkit/stubs/<接口名>.py`：照桩模板写假接口（文件名 = 接口名）。

> 正式落地时，真接口的服务从 `real_examples/` 换成各模块自己的服务目录（`--mode real` 的实际指向）。
> 给 AI 参考时，把 `contracts/` 和 `tools/devkit/` 一起给它，它就知道这套约定（接口、样例、断言、桩、总开关）怎么配合。
