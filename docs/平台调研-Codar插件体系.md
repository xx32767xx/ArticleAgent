# 平台调研：Codar 插件体系

> 主题：Codar 平台的事实性调研（插件格式、安装结构、发布流程）。只记录平台事实，不记录我们的决策（决策见 `docs/决策记录.md`）。
> 调研对象：科搭 Codar（SpeedAI 出品）桌面端 v0.3.14 + SpeedSkills 插件市场（skill.speedai.com）
> 调研方式：解包安装目录 `E:\codar\codar-desktop`（app.asar）、分析本地数据目录 `~/.codar`、抓取官方 OpenAPI / v4 契约文档
> 日期：2026-11

## 1. 平台与运行形态

- Codar 是桌面端科研 Agent 工作台（Windows/macOS），Web 版为 `codar-web.speedai.com`。
- 内核：基于 Codex 系 agent 运行时（`context_manager` 支持 codar / codex / claude-code / vanilla 等），Electron 外壳 + Go sidecar 守护进程。
- 本地数据根目录：`%USERPROFILE%\.codar\`（工程数据、插件、会话、工作区）。
- 桌面用户数据：`%APPDATA%\codar-desktop`（Electron 缓存）；安装状态账本在 `~/.codar/desktop/`。

## 2. 插件三级模型（v4 契约）

```
Marketplace ──收录──> Plugin ──包含──> Component (skill / mcp)
独立来源 ───────────> Plugin（也可独立存在）
```

- **Marketplace**：目录与策展容器（SpeedSkills = 官方市场）；不可直接安装。
- **Plugin**：可安装、可版本化的能力包，是安装/升级/权限确认/启停/卸载的原子单位。
- **Component**：Skill（含 SKILL.md 的目录）或 MCP（`.mcp.json` 配置）；可 standalone 独立安装，也可由 Plugin 固定携带。
- ID 规则：`规范化名称-8位短hash`，如 `pdf-btgerqw7`；本机导入生成 `local-skill-xxx`。
- 官方以 v4 API 为准（`/api/v4/...`），v3 路由保留兼容。

## 3. Plugin 包格式

```
plugin-root/
  .codex-plugin/plugin.json    # 清单（必需）
  skills/<skill-name>/SKILL.md # 技能
  skills/<skill-name>/references/ scripts/ assets/ agents/ ...
  .mcp.json                    # MCP 配置（可选）
  README.md                    # 使用文档（建议）
```

`plugin.json` 示例（内置 codar-foundation 实测）：

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

发布包由 SpeedSkills 以 tar.gz 分发，envelope 结构（`speedskills.plugin-package.v4`）：
`schemaVersion / kind=plugin / plugin{id,name,version,permissions,capabilities} / manifest=".codex-plugin/plugin.json" / components[{componentId,componentVersion,kind,sha256,required,defaultEnabled,path}] / download{url,sha256,sizeBytes} / issuedAt`。

## 4. Skill 格式（Agent Skills 规范，通用）

- 一个目录 = 一个 Skill，根目录必须有 **`SKILL.md`**。
- frontmatter 必填：
  ```yaml
  ---
  name: arxiv-preflight            # 英文短名，Agent 用它识别
  description: "做什么 + 什么时候用（触发条件写全）"
  license: MIT                     # 可选
  author: AIPOCH                   # 可选
  ---
  ```
- 正文建议结构：何时使用 / 输入 / 工作流程（分步、可复现）/ 输出格式 / 安全与边界。
- 支持子目录：`scripts/`（Python/Node 脚本）、`references/`（规则库、参考文档）、`assets/`（模板）、`agents/openai.yaml`（界面展示配置：display_name / short_description / default_prompt，用 `$skill-name` 引用）、`evals/`、`tests/`。
- 兼容 Claude Code（`~/.claude/skills/`）与 Codex（`~/.codex/skills/`）及 Codar（导入本地 Skill）。
- 权限：Skill 目录本身不声明权限；组件级 `permissions`（filesystem / network 为基础；shell / desktop / browser / downloads / mcp / clipboard 为高权限，安装前需用户确认）在发布/安装账本层维护。
- MCP：`.mcp.json` 顶层 key 即 entryKey；Plugin 内路径写作 `.mcp.json#entryKey`。

## 5. 本地安装结构（实机确认）

```
~/.codar/
  plugins/releases/{pluginId}/{version}/.codex-plugin/plugin.json + skills/...
  components/skills/{componentId}/     # standalone skill
  components/mcps/{componentId}/       # standalone mcp
  plugins/data/{pluginId}/             # MCP 授权等可变数据
  desktop/installed-plugins.json       # 插件账本（含 integrityManifest 文件哈希）
  desktop/installed-components.json    # 组件账本（33 个组件：name/version/sha256/owners/installPath）
  desktop/profile-marketplace-state.json # profile 级启停状态
```

- 桌面端「插件 → 管理 → 导入本地 Skill」：选择**包含 SKILL.md 的目录**即可导入（云电脑目标另有导入接口）。
- 桌面端相关 API（客户端侧）：`/api/skill-market/v4/*`（installed / skills|mcps 列表、详情、install、update、import-local）、`/api/v4/...`（官方市场）。

## 6. 发布与上架

- **自助发布暂未开放**（v4 文档明确列为非目标）。流程：把 Skill/Plugin 压缩包交给管理员 → 管理后台「发布」上传 → 自动识别为独立 Skill / Plugin 并进入审核 → 审核通过上架 SpeedSkills。
- 管理接口（服务端）：`POST /api/v4/admin/releases`（发布 Marketplace/Plugin/standalone Skill/MCP 归档）、`POST /api/v4/admin/releases/inspect`（预览）、`/api/v4/admin/*` 系列管理接口。
- 安全：`securityStatus` = verified / unverified / blocked；高权限组件安装前必须确认。
- 市场信息：SpeedSkills 收录 591 个科研 Skill、30 个领域插件、25 个 MCP；每次更新生成新版本与内容摘要。

## 7. 与论文辅导需求（3/4/7）的映射建议

| 需求编号 | Codar 插件形态建议 | 关键点 |
|---|---|---|
| 3 论文辅导智能体 | Skill：`paper-coaching-tutor`（讲解型辅导） | SKILL.md 固定六段式讲解流程（是什么/写多少/怎么写/常见错误/范例对照/自检清单）；辅导话术与课程知识库放 references/；可选 scripts/ 做骨架与句式生成 |
| 4 论文检测智能体 | Skill：`paper-quality-inspector`（检测型辅导） | scripts/ 放检测脚本（结构性/逻辑性/语言/规范/一致性五类规则，对标 14.3 的 CK-* 规则）；输出问题清单（位置/严重度/依据/修改建议）；references/ 放规则表与北航规范 |
| 7 导师反馈落实追踪 | Skill：`advisor-feedback-tracker` | 待办模型、批注拆条、状态机（待处理→已修改→待复核→已关闭）、说明表；跨格式锚定（Word/PDF 批注回 LaTeX）；可用 MCP 对接批注/待办服务，或纯工作区文件 + scripts 实现 |

- 建议先以纯 Skill（SKILL.md + scripts + references）做 MVP，验证通过后再考虑打包成 Plugin（一个 Plugin 携带三个 Skill），或发布为三个独立 Skill。
- 与需求文档的对应：讲解型/检测型辅导 ↔ M4（8.4 FR-M4-01~09、14.2/14.3）；导师反馈落实追踪 ↔ M5（9.2~9.5、AC-06/AC-09）+ M9 留痕（FR-M9-06）。

## 8. 关键链接

- Codar 官网/下载：https://codar.speedai.com / https://codar.speedai.com/download
- Codar 用户文档：https://codar.speedai.com/docs/plugins
- SpeedSkills 市场：https://skill.speedai.com（在线生成 SKILL.md：/publish）
- v4 API 契约：https://skill.speedai.com/docs/api/v4/api_v4.md
- v4 数据模型：https://skill.speedai.com/docs/api/v4/models_v4.md
- OpenAPI：https://skill.speedai.com/api/openapi.json
- Agent 安装指引：https://skill.speedai.com/install/speedskills.md
