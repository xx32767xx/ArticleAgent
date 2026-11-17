# 平台调研：Codar 插件体系

> **文档编号：DOC-005** · 状态：生效
> 这个文件记录科搭 Codar 平台的事实：插件由什么组成、长什么样、怎么装、怎么上架。
> 只写平台事实，不写我们的决定（决定见 DOC-002）。平台机制变了，这里跟着更新。
> 调研对象：科搭 Codar（SpeedAI 出品）桌面端 v0.3.14，以及插件市场 SpeedSkills（skill.speedai.com）。
> 调研方式：拆开安装目录 `E:\codar\codar-desktop`、查看本地数据目录 `~/.codar`、抓取官方接口文档。

## 1. 平台和运行方式

- Codar 是桌面端科研智能体工作台（Windows/macOS），网页版在 `codar-web.speedai.com`。
- 底层是 Codex 系的智能体运行时（可切换 codar / codex / claude-code 等运行方式），界面用 Electron，后台有一个 Go 写的守护进程。
- 本地数据放在 `%USERPROFILE%\.codar\`（项目、插件、会话、工作区都在这里）。
- 桌面端界面缓存放在 `%APPDATA%\codar-desktop`；安装记录在 `~/.codar/desktop/`。

## 2. 插件的三层结构

```
市场（Marketplace）──收录──> 插件（Plugin）──包含──> 组件（Component：Skill 或 MCP）
独立来源 ─────────────> 插件（也可以不经过市场）
```

- **市场**：目录和策展的地方（SpeedSkills 是官方市场），本身不能直接安装。
- **插件**：可安装、可版本化的能力包，安装、升级、权限确认、启用停用、卸载都以它为单位。
- **组件**：Skill（一个包含 SKILL.md 的目录）或 MCP（一份 `.mcp.json` 配置）。组件可以单独安装，也可以由插件固定携带。
- 组件编号规则：名称加 8 位短哈希，比如 `pdf-btgerqw7`；本机导入的编号是 `local-skill-xxx` 这种。
- 官方以 v4 接口为准（`/api/v4/...`），v3 的旧接口还保留兼容。

## 3. 插件包长什么样

```
plugin-root/
  .codex-plugin/plugin.json    # 插件清单（必须有）
  skills/<技能名>/SKILL.md      # 技能目录
  skills/<技能名>/references/ scripts/ assets/ agents/ ...
  .mcp.json                    # MCP 配置（可选）
  README.md                    # 使用说明（建议有）
```

`plugin.json` 的实际例子（从内置插件 codar-foundation 里拆出来的）：

```json
{
  "author": { "name": "Codar" },
  "description": "...",
  "interface": {
    "developerName": "Codar",
    "displayName": "Codar Foundation",
    "shortDescription": "Codar 基础能力",
    "longDescription": "..."
  },
  "name": "codar-foundation",
  "skills": "./skills/",
  "version": "1.0.18"
}
```

上架时的发布包是 tar.gz，包里有一份清单（`speedskills.plugin-package.v4` 格式），包含：版本号、插件名称和版本、权限、包含的组件（编号、版本、哈希、是否需要、默认是否启用、路径）、下载地址和校验值。

## 4. Skill 的格式（通用，Claude Code 和 Codex 也能用）

- 一个目录就是一个 Skill，目录根下必须有 **`SKILL.md`**。
- 文件开头有 YAML 头（frontmatter），必须写：
  ```yaml
  ---
  name: arxiv-preflight            # 英文短名，智能体靠它识别
  description: "做什么 + 什么时候用（触发条件写全）"
  license: MIT                     # 可选
  author: AIPOCH                   # 可选
  ---
  ```
- 正文建议按这个顺序写：什么时候用 / 输入是什么 / 步骤（可复现）/ 输出什么 / 安全边界。
- 可以带子目录：`scripts/`（Python、Node 脚本）、`references/`（规则、参考文档）、`assets/`（模板）、`agents/openai.yaml`（界面展示信息，用 `$技能名` 引用）、`evals/`（测试用例）、`tests/`。
- 同一份 Skill 也能给 Claude Code（放 `~/.claude/skills/`）和 Codex（放 `~/.codex/skills/`）用；Codar 里用"导入本地 Skill"。
- 权限：Skill 目录本身不写权限；权限记在组件层——`filesystem`（读写文件）、`network`（联网）是基础权限，不用额外交代；`shell`、`desktop`、`browser`、`downloads`、`mcp`、`clipboard` 是高权限，安装前要用户确认。
- MCP：`.mcp.json` 里最外层的键名就叫 entryKey；在插件里引用写作 `.mcp.json#entryKey`。

## 5. 本地装好之后的结构（实机确认过）

```
~/.codar/
  plugins/releases/{插件编号}/{版本}/.codex-plugin/plugin.json + skills/...
  components/skills/{组件编号}/     # 单独安装的 Skill
  components/mcps/{组件编号}/       # 单独安装的 MCP
  plugins/data/{插件编号}/          # 授权、密钥等可变数据
  desktop/installed-plugins.json    # 插件安装记录（含每个文件的校验值）
  desktop/installed-components.json # 组件安装记录（我们机器上有 33 个组件）
  desktop/profile-marketplace-state.json  # 各模式下哪些组件启用
```

- 桌面端菜单"插件 → 管理 → 导入本地 Skill"：选一个**包含 SKILL.md 的目录**就能导入（云端电脑另有导入接口）。
- 客户端用到的接口：`/api/skill-market/v4/*`（安装状态、列表、详情、安装、更新、导入本地），以及 `/api/v4/...`（官方市场）。

## 6. 上架流程

- **暂时没有开放自助上架**（v4 文档里明确列为非目标）。现在的方式：把 Skill 或插件的压缩包交给管理员 → 管理员在后台"发布"里上传 → 系统自动识别为独立 Skill 或插件并进入审核 → 审核通过后上架 SpeedSkills。
- 管理员接口：发布接口（`/api/v4/admin/releases`）、预览接口（inspect），以及一组后台管理接口。
- 安全状态分三档：已验证、未验证、已拦截；带高权限的组件安装前必须确认。
- 市场规模：SpeedSkills 目前收录约 591 个科研 Skill、30 个领域插件、25 个 MCP；每次更新生成新版本和内容摘要。

## 7. 和我们的 3/4/7 怎么对应

| 我们的模块 | 建议的插件形态 | 要点 |
|---|---|---|
| 3 论文辅导 | Skill：`paper-coach` | SKILL.md 里固定六段式讲解流程（是什么/写多少/怎么写/常见错误/范例对照/自检清单）；讲解话术和课程知识放 references；需要的话用 scripts 生成骨架和句式 |
| 4 论文检测 | Skill：`paper-inspector` | scripts 里放检测逻辑（结构、逻辑、语言、规范、一致性五类，对应需求 14.3 的检查规则）；输出带位置、严重程度、依据、修改建议的问题清单；references 放规则表和规范原文 |
| 7 导师反馈追踪 | Skill：`advisor-tracker` | 待办、批注拆条、状态流转（待处理→已修改→待复核→已关闭）；能做跨格式锚定（Word/PDF 批注对回 LaTeX 源码）；可以用 MCP 对接批注/待办服务，也可以纯本地文件加脚本 |

- 建议先用纯 Skill（SKILL.md + scripts + references）做原型，跑通后再考虑打包成一个插件，或者作为三个独立 Skill 发布。
- 和需求文档的对应：讲解型/检测型辅导对应 M4（8.4 和 14.2/14.3）；导师反馈追踪对应 M5（9.2~9.5、验收场景 AC-06/AC-09）和 M9 留痕。

## 8. 有用链接

- 官网和下载：https://codar.speedai.com / https://codar.speedai.com/download
- 用户文档：https://codar.speedai.com/docs/plugins
- 市场：https://skill.speedai.com（在线生成 SKILL.md 在 /publish）
- 平台接口文档：https://skill.speedai.com/docs/api/v4/api_v4.md
- 平台数据结构：https://skill.speedai.com/docs/api/v4/models_v4.md
- 接口总览：https://skill.speedai.com/api/openapi.json
- 给智能体的安装指引：https://skill.speedai.com/install/speedskills.md
