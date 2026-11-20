# contracts/ 接口定义（公共，改动要搭档确认）

接口的"合同"都放这里，是唯一权威。3、4、7 之间和另一小组之间，都拿这里的定义对接。

## 放什么（一个接口四件套）

```
contracts/
  v1/                           # 字段定义（按接口分文件；目前先以样例+断言为准）
  fixtures/<接口名>/             # 样例数据：success / empty / invalid
  tests/<接口名>/test_contract.py # 契约断言：提供方 + 消费方
  signatures/                   # 工具签名清单（工具名/参数/返回）
```

- **新建一个接口**：建 `fixtures/<接口名>/`、`tests/<接口名>/` 两个文件夹，再在 `tools/devkit/stubs/` 放一个同名桩文件即可——总开关自动扫到，不用改任何配置。
- **提供方**写"我按契约返回"的断言；**消费方**在同一个 `test_contract.py` 里追加"我拿到数据能正确用"的断言。
- 字段只加不改名；改名/删字段/改语义要升版本（v2），并在 DOC-002 记一条。

## 参考示例（可直接跑）

`inspect.query_latest` 是完整走通的一条链路，照着它写新接口即可：

| 文件 | 作用 |
|---|---|
| `contracts/fixtures/inspect.query_latest/{success,empty}.json` | 样例数据（正常 / 没检测过） |
| `contracts/tests/inspect.query_latest/test_contract.py` | 断言（提供方 + 消费方，分区写） |
| `tools/devkit/stubs/inspect.query_latest.py` | 桩（假接口，按输入挑样例返回） |
| `tools/devkit/real_examples/inspect.query_latest.py` | "真接口"示例（同工具名/参数，真算） |
| `tools/devkit/run_contract_tests.py` | 总开关（自动发现 + 桩/真切换 + 点名报告） |

跑法（仓库根目录）：

```powershell
python tools/devkit/run_contract_tests.py                  # 连桩跑(日常/PR 门禁)
python tools/devkit/run_contract_tests.py --mode real      # 连"真接口"跑(联调前)
```

## 执行流程（一条链路）

1. 总开关扫 `contracts/tests/`，找到每个接口的 `test_contract.py`；
2. 为接口拉起对应 MCP 服务（桩或真），用客户端连上；
3. 调工具 `inspect_query_latest(project_id, module_id)`；
4. 服务端执行工具函数：桩按输入读样例返回；真实现真算；
5. 客户端拿到返回，跑断言：字段/类型/枚举/空结果；
6. 报告按接口点名；全绿才算接口兼容。

> 用 AI 开发时，把这个目录 + `tools/devkit/` 一起发给 AI 当参考：它就知道"接口怎么定、样例怎么写、断言怎么写、桩怎么接"。
