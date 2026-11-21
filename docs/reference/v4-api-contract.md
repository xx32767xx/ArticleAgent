# Skill Market API v4

状态：设计基线
日期：2026-08-19
适用范围：SpeedSkills Catalog API、SpeedClaw Skill Market 客户端与本地插件运行时

## 1. 目标

v4 将 Skill Market 的目录和安装模型统一为三个层级：

~~~text
Marketplace ──收录──> Plugin
                     ├── Skill
                     └── MCP

独立来源 ───────────> Plugin
~~~

本协议解决 v3 将 Plugin 删除后产生的几个问题：

- v3 Domain 由 skill.domain 自动聚合，无法独立维护版本、所有者和来源。
- v3 Domain 直接包含 Skill/MCP，导致分类层同时承担导航、组合和安装职责。
- 客户端只能把 v3 Domain 渲染成 plugin-like card，没有真正的 Plugin 安装单元。
- Skill 和 MCP 分别安装、更新和启停，无法保证一组能力的版本一致性。

v4 的核心变化是：

- Marketplace 与 Claude Code Marketplace 语义对齐，是 Plugin 的发现、分发和策展容器。
- Plugin 是安装、升级、权限确认、安全审计、启停和卸载的原子单位之一，也可以脱离 Marketplace 独立存在。
- Skill 和 MCP 使用统一的 Component 模型，既可以独立安装，也可以固定到 Plugin release。
- source 是 Marketplace 或 Plugin 的属性，不是额外的目录层级。
- Marketplace 不是可运行的安装单元。SpeedSkills 平台可以将 Marketplace 来源注册到 Catalog 并同步其清单；用户从同步后的目录中选择并安装 Plugin。

## 2. 非目标

v4 首期不包含：

- 将 Marketplace 作为运行时包安装，或默认安装其中全部 Plugin。
- 跨 Plugin 的依赖求解。
- Plugin 内的 App、Hook、Agent、Connector 等新组件类型。
- 面向第三方开发者开放的自助发布、审核后台和计费协议。
- 用 v4 强制替换本地导入的独立 Skill/MCP。

组件模型必须允许以后新增 kind，但 v4 客户端只要求支持 skill 和 mcp。

## 3. 术语与关系

### 3.1 Marketplace

Marketplace 是 v4 的顶层目录和策展边界。它负责：

- 提供自身维护和分发的 Plugin 列表。
- 声明来源、展示信息和策展策略。
- 指定推荐或置顶 Plugin。

Marketplace 不要求对应单一知识领域。领域、行业和任务分类通过 Plugin 的 domains、tags 和 capabilities 表达。

Marketplace 自身不提供可执行 package，也不进入 Plugin/Component 安装账本。SpeedSkills 可以单独维护 Marketplace 来源的注册、启用、同步时间和同步状态；这些 Catalog 状态不代表其中任何 Plugin 已安装。SpeedClaw 首期只消费同步后的 Marketplace 目录，不直接注册第三方 Marketplace 来源。

### 3.2 Plugin

Plugin 是可安装、可版本化的能力包。它负责：

- 固定一个 Plugin release 的组件集合。
- 聚合所需权限、能力和安全报告。
- 提供可校验的安装包。
- 作为本地启停、更新、卸载和故障归属的边界。

Plugin 的稳定身份不依赖 Marketplace。Plugin 可以由 Marketplace 提供，也可以来自 SpeedSkills registry、Git、URL 等独立来源；一个独立 Plugin 还可以同时被多个 Marketplace 收录。

Plugin 的规范来源由 plugin.source 表示，Marketplace 收录关系由 marketplace_plugins 表示。移除普通收录只解除关联，不会改变已经安装到客户端的内容。

### 3.3 Component

Component 是 Skill 和 MCP 共用的基本单位，由稳定的 componentId 标识。Catalog、
Plugin 携带及由 SpeedSkills 托管的 standalone Component 使用 SpeedSkills 分配的
远端身份；仅存在于单台 SpeedClaw 本机的 standalone Skill/MCP 使用本地身份：

- kind=skill：包含 SKILL.md 的 Skill 目录。
- kind=mcp：MCP server 配置及可选辅助文件。

Skill/MCP 使用相同的数据类型，通过 standalone 字段区分是否允许独立展示和安装：

- standalone：自身是安装、更新、启停和卸载单位。
- plugin-bundled：包含在 Plugin package 中，版本和生命周期由 Plugin release 管理。

Component 与不可变的 ComponentRelease 分开保存。PluginComponentRef 只保存 Plugin release 与 ComponentRelease 的关联；PluginComponent API 返回体在关联上聚合完整的 Component 和 ComponentRelease。关联必须固定 componentId、componentVersion，已经保存的 Plugin release 不得因上游组件更新而发生内容漂移。

### 3.4 Source

source 是属性：

- marketplace.source：Marketplace 清单来自哪里。
- plugin.source：Plugin 的规范来源，以及其生命周期是否附属于某个 Marketplace。
- component.source：Component 的规范来源；Plugin 私有 Component 记录所属
  `pluginId + path`，SpeedSkills 托管的 standalone Component 可以来自 registry、
  Git 或 URL。SpeedClaw 本机导入不进入公共 Component wire，来源只记录在本地账本。

source 不构成第四层资源。服务端可以隐藏内部对象存储路径，只返回可公开的来源元数据。

### 3.5 Domain

Domain 是 SpeedSkills 维护的领域展示和策展边界。它保存稳定 ID、中英文名称、展示信息
和领域级 `sortOrder`。Component 可以属于多个 Domain；Component 在各领域中的展示
顺序属于 Domain–Component 关联，不属于 Component 自身。

## 4. 标识规则

### 4.1 ID

Marketplace、Plugin 和 Component 统一使用 `id` 表示稳定身份，不再提供重复的
`slug` 字段。ID 必须：

- 使用小写 ASCII。
- 只包含 a-z、0-9 和连字符。
- 不能以连字符开头或结尾。
- 创建后不可修改。

`name` 和 `name_cn` 是可重复、可修改的展示字段，不参与数据库关联，也不得作为
API 路径或本地安装状态的身份键。

### 4.2 Marketplace、Plugin 与 Component ID

规范 ID：

~~~text
marketplaceId = Marketplace.id
pluginId = Plugin.id
componentId = Component.id
~~~

示例：

~~~text
speedskills-official
empirical-research
empirical-economics-writing-odatospd
~~~

所有 detail、package、update 和 install event 请求使用规范 pluginId。pluginId 不包含 marketplaceId；Marketplace 只通过关联关系筛选 Plugin。

组件接口、PluginComponentRef 和本地状态统一使用 componentId，不增加 `skill:`、
`mcp:` 等冗余前缀。客户端必须把所有 ID 当作不可解析的稳定字符串。

Component ID 分配规则：

- Catalog、Plugin 携带及由 SpeedSkills 托管的 standalone Component 使用
  `规范化名称-8位稳定短 hash`，例如 `pdf-btgerqw7`，只能由 SpeedSkills 分配。
- `name`、`name_cn` 是展示字段，可以重复或修改，不作为数据库身份。
- 官方 Component 的 hash 来自稳定的平台身份；Plugin 私有 Component 的 hash 来自
  `pluginId + kind + componentName`，因此不同 Plugin 的同名 Skill/MCP 可以共存。
- 未来用户自助创建 standalone Component 时，由 SpeedSkills 服务端首次分配稳定身份。
- hash 不得取自 release 内容、版本、压缩包摘要或本地路径；后续更新必须显式引用
  首次返回的 componentId。
- Plugin 携带的内容与已有官方 Component 完全一致时，引用已有官方 componentId；
  内容不同时保留各自的 Plugin-scoped componentId。
- 对非 local Component，客户端必须把 componentId 当作不可解析的稳定字符串，
  不自行生成或重算。
- SpeedClaw 可以为仅存在于本机、不进入公共 Catalog 的 standalone Skill/MCP 分配
  `local-{kind}-{normalizedName}-{stableRandomSuffix}`。`kind` 只能为 `skill` 或
  `mcp`；随机后缀首次导入时生成并随账本持久化，不得从名称、路径、内容或版本推导。
- `local-` 是 SpeedSkills Component ID 的保留前缀。SpeedSkills 不得分配、导入或
  返回以该前缀开头的 Component ID。
- 本地 Component 不支持原地更新或修改来源路径。路径不存在、manifest 无效或内容
  SHA-256 与首次导入记录不同时，SpeedClaw 将其标记为失效并注销运行时；用户删除旧
  记录后重新导入，生成新的 local componentId。不得根据名称、旧路径或 SHA-256
  猜测、恢复或复用原身份。

### 4.3 Version

- Plugin 和独立组件使用 SemVer。
- Plugin release 一经发布不可原地覆盖。
- 相同 pluginId + version 必须始终解析到相同 package sha256。
- Marketplace version 用于清单同步，不参与 Plugin 更新比较。
- local Component 当前不支持更新，每次新导入固定使用 `0.0.0-local.1`；重新导入
  会获得新的 componentId，而不是递增旧身份的版本。

## 5. 通用约定

### 5.1 Base path

v4 使用显式版本前缀：

~~~text
/api/v4
~~~

v3 的未版本化路由保持兼容，不在 v4 上线时改变语义。

### 5.2 JSON 命名

- Wire 字段统一使用 camelCase。
- 时间统一使用 RFC 3339 UTC 字符串。
- 空数组返回 []，不返回 null。
- 可选对象不存在时可以省略。
- ID 在 API 边界保持字符串，不要求客户端解析数据库 ID。

### 5.3 列表响应

~~~json
{
  "items": [],
  "total": 0,
  "page": 1,
  "pageSize": 24
}
~~~

page 从 1 开始。pageSize 默认 24，最大 100。

Marketplace 列表的 items 为 Marketplace summary；Plugin 列表的 items 为
Plugin summary。Plugin 列表不会返回 description、readme、source 或 components，
这些字段只由详情接口返回。列表中的 `securityStatus` 是当前 release 审核状态的投影。

### 5.4 展示文案与 package 文档

- `summary` 是 Catalog 卡片和搜索结果使用的一句话摘要。
- `description` 是安装前详情页使用的功能说明，也是客户端“说明”区域的数据源。
- `readme` JSON 字段是旧 Catalog 的兼容字段，已废弃；客户端不得将它作为用户文档，
  SpeedSkills 也不再要求发布或管理流程维护该字段。
- Plugin 或 Component 的完整文档以对应 release package 内的 `README.md` 为准。
  客户端取得 package 后自行读取并安全渲染；Skill package 没有 `README.md` 时可以回退
  展示 `SKILL.md` 正文。
- package 尚未下载时，客户端只展示 Catalog 的 `summary` 和 `description`，不得为了
  获取 README 而把数据库兼容字段当作 package 内容。

来源仓库、旧目录、迁移批次等内部信息由结构化 `source` 或 SpeedSkills 内部记录维护，
不得写入面向用户展示的 README。客户端渲染 Markdown 时必须禁用或清理不安全 HTML。

### 5.5 错误响应

~~~json
{
  "error": {
    "code": "plugin_not_found",
    "message": "Plugin not found",
    "requestId": "req_..."
  }
}
~~~

`requestId` 是可选字段。服务端接入请求链路追踪后填写；当前只读目录接口
稳定返回 `code` 和 `message`。

稳定错误码：

| HTTP | code | 含义 |
| --- | --- | --- |
| 400 | invalid_request | 参数或 JSON 无效 |
| 400 | invalid_plugin_id | Plugin ID 格式无效 |
| 404 | marketplace_not_found | Marketplace 不存在 |
| 404 | plugin_not_found | Plugin 不存在 |
| 409 | version_conflict | 同版本对应不同制品 |
| 410 | plugin_unavailable | Plugin 已撤回且不可安装 |
| 422 | package_unavailable | 条目存在但缺少可安装制品 |
| 503 | catalog_unavailable | Catalog 存储或上游同步不可用 |

## 6. 资源模型

Marketplace、Plugin 和 Component 的 `iconUrl` 只要出现，就必须是客户端可以直接
访问的完整 HTTP(S) URL。SpeedSkills 可以在数据库内部保存对象存储相对路径，但不得
把 `skills_icon/v1/example.png` 这类内部相对路径直接返回给 SpeedClaw。

### 6.1 Domain

~~~json
{
  "id": "computer-science",
  "name": "Computer Science",
  "name_cn": "计算机",
  "summary": "面向计算机与人工智能研究的能力集合。",
  "description": "覆盖机器学习、软件工程、系统研究与 AI 应用研发。",
  "iconUrl": "https://skills.cn-wlcb.ufileos.com/plugins_icon/v1/computer-science.png",
  "sortOrder": 20
}
~~~

领域顺序由 SpeedSkills 返回结果决定。`sortOrder` 较小的领域优先展示，同值时按 `id`
升序稳定排序。SpeedClaw 不自行重排。

### 6.2 Marketplace summary

~~~json
{
  "id": "speedskills-official",
  "name": "SpeedSkills Official",
  "name_cn": "SpeedSkills 官方市场",
  "summary": "由 SpeedSkills 官方维护的研究能力 Plugin 市场。",
  "description": "提供经过策展、构建和安全审核的研究工作流 Plugin。",
  "iconUrl": "https://cdn.example.com/marketplaces/speedskills-official.png",
  "source": {
    "type": "git",
    "url": "https://github.com/speedai/speedskills-official-marketplace",
    "ref": "main",
    "manifestPath": ".speedskills/marketplace.json"
  },
  "sync": {
    "enabled": true,
    "status": "ready",
    "lastSyncedAt": "2026-08-18T00:00:00Z"
  },
  "version": "1.0.0",
  "official": true,
  "tags": ["official", "research", "curated"],
  "featuredPluginIds": [
    "empirical-research",
    "literature-review"
  ],
  "sortOrder": 30,
  "updatedAt": "2026-08-18T00:00:00Z"
}
~~~

Marketplace source.type v4 支持：

- registry：由 SpeedSkills 内部 Catalog 管理。
- git：Git 仓库中的 Marketplace manifest。
- url：可直接获取的 Marketplace manifest。

管理员从本机上传的 Marketplace 压缩包在发布后由 SpeedSkills 接管，规范来源记录为
`registry`，不使用 `local`，也不返回上传主机路径。

### 6.3 Plugin summary

~~~json
{
  "id": "empirical-research",
  "name": "Empirical Research",
  "name_cn": "实证研究",
  "summary": "从研究设计、数据分析到论文写作的实证研究能力包。",
  "iconUrl": "https://cdn.example.com/plugins/empirical-research.png",
  "publisher": {
    "name": "SpeedAI Research",
    "type": "official",
    "website": "https://speedai.com"
  },
  "version": "1.2.0",
  "installPolicy": "manual",
  "official": true,
  "tags": ["econometrics", "causal-inference"],
  "domains": ["economics"],
  "capabilities": ["research", "files", "datasets"],
  "permissions": ["filesystem", "network"],
  "componentCounts": {
    "skills": 3,
    "mcps": 1
  },
  "securityStatus": "verified",
  "rating": 4.8,
  "downloads": 1200,
  "installsLast30d": 240,
  "updatedAt": "2026-08-18T00:00:00Z"
}
~~~

### 6.4 Plugin detail

详情接口返回完整 Plugin、当前 PluginRelease 和完整 Components 聚合。
与列表 summary 不同，version、capabilities、permissions 和 securityStatus 位于
`release` 中，不在顶层重复返回：

~~~json
{
  "description": "完整描述",
  "source": {
    "type": "marketplace",
    "marketplaceId": "speedskills-official",
    "path": "plugins/empirical-research"
  },
  "currentVersion": "1.2.0",
  "installPolicy": "manual",
  "release": {
    "pluginId": "empirical-research",
    "version": "1.2.0",
    "capabilities": ["research", "files", "datasets"],
    "permissions": ["filesystem", "network"],
    "securityStatus": "verified"
  },
  "components": [
    {
      "pluginId": "empirical-research",
      "pluginVersion": "1.2.0",
      "componentId": "empirical-economics-writing-odatospd",
      "componentVersion": "0.1.48",
      "required": true,
      "defaultEnabled": true,
      "path": "skills/empirical-economics-writing",
      "component": {
        "id": "empirical-economics-writing-odatospd",
        "kind": "skill",
        "name": "Empirical Economics Writing",
        "name_cn": "实证经济学写作",
        "source": {"type": "registry"},
        "standalone": true
      },
      "release": {
        "componentId": "empirical-economics-writing-odatospd",
        "version": "0.1.48",
        "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
      }
    },
    {
      "pluginId": "empirical-research",
      "pluginVersion": "1.2.0",
      "componentId": "fred-data",
      "componentVersion": "1.0.0",
      "required": false,
      "defaultEnabled": false,
      "path": ".mcp.json#fred-data",
      "component": {
        "id": "fred-data",
        "kind": "mcp",
        "name": "FRED Data",
        "source": {
          "type": "plugin",
          "pluginId": "empirical-research",
          "path": ".mcp.json#fred-data"
        },
        "standalone": false
      },
      "release": {
        "componentId": "fred-data",
        "version": "1.0.0",
        "sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
      }
    }
  ]
}
~~~

Plugin source.type 支持 marketplace、registry、git 和 url。type=marketplace 时
marketplaceId 必填，path 是相对于 Marketplace source 根目录的安全相对路径；其他
类型不得填写 marketplaceId。管理员直接上传的独立 Plugin 发布后使用 registry。
公开发布的 Plugin 必须具有规范来源。

required=true 的组件必须包含在 Plugin package 中，并随 Plugin 启停。required=false 的组件可以由用户单独启停，其默认状态由 defaultEnabled 指定。

`installPolicy` 是 SpeedSkills 平台维护的 SpeedClaw 默认配置策略，只支持 `default`
和 `manual`；缺失或空值按 `manual` 处理。Plugin 来源包及第三方作者不能自行把它设置
为 `default`。`installPolicy=default` 决定整个 Plugin 是否在默认配置阶段自动安装，
`components[].defaultEnabled` 决定安装完成后哪些 Component 初始启用。

### 6.5 共享模型契约

Marketplace、Plugin、Component、Release 及 API 聚合类型统一定义在
[models_v4.md](./models_v4.md)。本文件只说明 HTTP 路由、请求、响应和流程，
不重复维护字段定义。

## 7. HTTP API

### 7.1 Bootstrap

~~~text
GET /api/client-config
GET /api/openapi.json
GET /api/health
GET /api/ready
~~~

client-config 增加：

~~~json
{
  "skillMarketApiVersions": ["v3", "v4"],
  "preferredSkillMarketApiVersion": "v4",
  "pluginPackageSchemaVersion": "speedskills.plugin-package.v4",
  "componentPackageSchemaVersion": "speedskills.component-package.v4",
  "endpoints": {
    "v4Domains": "/api/v4/domains",
    "marketplaces": "/api/v4/marketplaces",
    "marketplacePluginDisplayPrompts": "/api/v4/marketplaces/{marketplaceId}/plugin-display-prompts",
    "plugins": "/api/v4/plugins",
    "pluginPackage": "/api/v4/plugins/{pluginId}/package",
    "pluginUpdates": "/api/v4/plugins/updates/check",
    "v4Skills": "/api/v4/skills",
    "v4MCPs": "/api/v4/mcps",
    "v4SkillPackage": "/api/v4/skills/{componentId}/package",
    "v4MCPPackage": "/api/v4/mcps/{componentId}/package",
    "componentUpdates": "/api/v4/components/updates/check",
    "componentLegacyResolve": "/api/v4/components/legacy/resolve"
  }
}
~~~

`skillMarketApiVersions` 声明服务端支持的协议版本，`endpoints` 声明具体接口；
`marketplacePluginDisplayPrompts` 声明 Marketplace 首页 Plugin 推荐展示数据的聚合接口；
`pluginUpdates` 和 `componentUpdates` 分别声明 Plugin 与 standalone Component
批量更新检查能力；`componentLegacyResolve` 声明 v3 slug 到正式 v4 Component ID
的批量解析能力；`v4Domains` 声明 SpeedSkills 提供 v4 领域策展数据，同时保留 v3
`domains=/api/domains`。客户端只有在服务端声明
支持 v4 且相应 endpoint 非空时，才应调用。
client-config 不再重复维护 v4 feature flags。客户端当前以 v4 为首选，同时继续保留
v3 路由供旧客户端使用。

### 7.2 Domains

~~~text
GET /api/v4/domains
GET /api/v4/domains/{domainId}
~~~

列表响应不分页，始终按 `sortOrder ASC, id ASC` 返回：

~~~json
{
  "items": [
    {"id": "general", "name": "General", "name_cn": "通用", "sortOrder": 10},
    {"id": "computer-science", "name": "Computer Science", "name_cn": "计算机", "sortOrder": 20}
  ]
}
~~~

SpeedClaw 只消费该顺序和展示字段，不维护 Domain，也不调用 SpeedSkills 管理接口。

### 7.3 Marketplaces

~~~text
GET /api/v4/marketplaces
GET /api/v4/marketplaces/{marketplaceId}
GET /api/v4/marketplaces/{marketplaceId}/plugin-display-prompts
~~~

查询参数：

- q：搜索名称、描述和 tags。
- official：true 或 false。
- sort：updated、name。首期暂不支持 featured 排序。
- page、pageSize：分页。

Marketplace 详情返回 Marketplace summary，并增加 description 和完整 featuredPlugins 摘要。它不返回所有 Plugin；完整列表通过 plugins?marketplaceId= 获取。

`plugin-display-prompts` 是面向客户端首页推荐区的轻量 Plugin 聚合接口。它一次返回
指定 Marketplace 中可展示的全部 Plugin 使用示例，避免客户端先获取 Plugin 列表，
再为每个 Plugin 请求详情。
该接口不分页，服务端按最终展示顺序返回 `items`：

~~~json
{
  "items": [
    {
      "id": "biomed-research",
      "name": "Biomed Research",
      "name_cn": "通用科研与数据服务",
      "displayPrompt": "围绕《你的疾病、基因、通路或技术主题》梳理已有研究和关键争议。",
      "iconUrl": "https://cdn.example.com/plugins/biomed-research.png"
    }
  ]
}
~~~

返回规则：

- Plugin 必须属于该 Marketplace，且 `displayPrompt` 去除首尾空白后非空。
- 接口只返回 Plugin，不返回 standalone Skill、MCP 或其他 Component。未来如需在首页
  推荐 Component，应另行定义明确的接口或查询能力，不扩展本接口的条目类型。
- Plugin 使用 Marketplace 策展顺序；响应顺序即客户端展示顺序。
- `displayPrompt` 只是用户可见的填入文案，客户端不得自动执行。
- 响应不返回 `permissions` 或 `securityStatus`。客户端发起安装前必须请求对应的
  Plugin 详情，并使用详情中的当前 release 权限和安全状态完成确认与校验。
- 本地安装、启用状态不属于 SpeedSkills Catalog；客户端通过本地状态接口单独获取。

该接口返回 `MarketplacePluginDisplayPromptsResponse`，其中 `items` 的元素类型为
`PluginPromptSummary`；字段定义见 [models_v4.md](./models_v4.md)。Marketplace 不存在时返回
`404 marketplace_not_found`。

### 7.4 Plugins

~~~text
GET  /api/v4/plugins
GET  /api/v4/plugins/{pluginId}
GET  /api/v4/plugins/{pluginId}/package
POST /api/v4/plugins/updates/check
POST /api/v4/plugins/{pluginId}/install-events
~~~

列表查询参数：

- marketplaceId：按 Marketplace 过滤。
- q：搜索名称、summary、tags 和 capabilities。
- capability、permission、securityStatus：精确过滤。
- official：true 或 false。
- sort：downloads、updated、rating、name。首期暂不支持 featured 排序。
- page、pageSize：分页。

列表返回 `PluginSummary`；详情返回 `PluginEntry`。传入 `sort=featured`
会返回 `400 invalid_request`，待后续定义明确的推荐机制后再开放。

### 7.5 Standalone skills and MCPs

独立 Skill/MCP 继续是一等 Catalog 资源：

~~~text
GET  /api/v4/skills
GET  /api/v4/skills/{componentId}
GET  /api/v4/skills/{componentId}/package
POST /api/v4/skills/{componentId}/install-events

GET  /api/v4/mcps
GET  /api/v4/mcps/{componentId}
GET  /api/v4/mcps/{componentId}/package
POST /api/v4/mcps/{componentId}/install-events

POST /api/v4/components/updates/check
~~~

Plugin 内的组件不通过这些 endpoint 在安装时逐个下载。Plugin package 已固定并携带本次 release 所需的组件内容。独立 endpoint 用于浏览和安装 standalone 资源。

Skill/MCP 列表支持 `domain={domainId}`。指定领域且未传 `sort` 时，SpeedSkills 默认按
该领域的策展顺序返回；同值按 Component ID 稳定排序。显式 `sort` 支持：

- `curated`：领域内策展顺序；必须同时传 `domain`。
- `downloads`：下载量降序。
- `updated`：更新时间降序。
- `rating`：评分降序。
- `name`：名称升序。

未指定领域和 sort 时继续使用 SpeedSkills 的全局推荐顺序。无论使用哪种排序，接口
返回顺序都是最终展示顺序，SpeedClaw 不进行二次排序。

Skill 和 MCP 的批量更新检查统一使用 Component endpoint。SpeedSkills 根据
Component 记录中的 `kind` 判断类型，客户端不需要拆分请求。

当前后端已实现 Skill/MCP 的列表和详情 GET 接口。列表返回 `Component`，详情返回
`ComponentEntry`，并且只展示 `standalone=true`、当前 release 和独立安装制品均
存在的组件。列表支持 `q`、`domain`、`official`、`sort`、`page` 和
`pageSize`；`sort` 支持 `curated`、`downloads`、`updated`、`rating`、`name`。

Component 详情中的用户说明读取 `description`。完整使用文档不由 Component JSON
元数据承载；客户端下载或安装 package 后读取 package 内的 `README.md`，Skill 在缺少
README 时可以回退读取 `SKILL.md` 正文。

Plugin 和 Component 详情可以返回可选的 `displayPrompt`，用于展示一段可复制的使用
示例。该字段是 Catalog 展示元数据，不是系统提示词；客户端不得自动执行，也不得用它
替代 package 内的 `SKILL.md`、README 或 MCP 配置。

standalone package endpoint 返回 `ComponentPackageEnvelope`：

~~~json
{
  "schemaVersion": "speedskills.component-package.v4",
  "kind": "skill",
  "component": {
    "id": "empirical-economics-writing-odatospd",
    "name": "Empirical Economics Writing",
    "version": "1.0.0",
    "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "permissions": ["filesystem"],
    "capabilities": ["research"]
  },
  "manifest": "SKILL.md",
  "download": {
    "url": "https://cdn.example.com/components/skill/empirical-economics-writing-odatospd/1.0.0/package.tar.gz",
    "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "sizeBytes": 20480
  },
  "sourceUrl": "https://skill.speedai.com/api/v4/skills/empirical-economics-writing-odatospd/package",
  "issuedAt": "2026-08-20T00:00:00Z"
}
~~~

`component.sha256` 校验组件内容，`download.sha256` 校验压缩包。Skill 的
`manifest` 为 `SKILL.md`，MCP 为 `.mcp.json`。standalone MCP envelope 还必须返回
`.mcp.json` 中的原始顶层 key：

~~~json
{
  "kind": "mcp",
  "component": {
    "id": "biomart-y4743ctp",
    "name": "biomart",
    "version": "0.1.0"
  },
  "manifest": ".mcp.json",
  "entryKey": "biomart"
}
~~~

`component.id` 是 SpeedSkills 分配的全局稳定身份，用于 Catalog、安装账本、更新和卸载；
`entryKey` 只用于在原始 `.mcp.json` 中定位连接配置。SpeedSkills 和 SpeedClaw 都不得用
componentId 改写安装包中的原始 key。SpeedClaw 校验并解压原包后，以 componentId 定位
安装记录，以 entryKey 读取配置并建立 MCP session；生成的运行时注册数据不属于安装包，
不会参与 package SHA 或内容 SHA。

Plugin 中的 MCP 使用 `PluginPackageComponent.path` 表达同一映射，例如
`.mcp.json#biomart`；fragment 即 entryKey。旧 standalone MCP envelope 缺少 entryKey 时，
客户端仅可在 `.mcp.json` 恰好包含一个顶层 entry 时兼容推断，其他情况必须按 package
contract 错误处理。v4 更新检查和 install event 仍尚未实现。

### 7.6 Workflows

Codar 预置工作流是只读目录资源，不是 Component，也不进入 Plugin package：

~~~text
GET /api/v4/workflows
GET /api/v4/workflows/{workflowId}
GET /api/v4/workflows/{workflowId}/releases/{version}
~~~

服务端支持时，`/api/client-config` 的 `endpoints.v4Workflows` 为 `/api/v4/workflows`；
未声明时客户端应使用内置模板。

列表只返回上架工作流，不分页，返回顺序即最终展示顺序（official DESC、sortOrder ASC、
name ASC、id ASC），客户端不再排序：

~~~json
{
  "items": [
    {
      "id": "bulk-rnaseq-k3f9a2xq",
      "version": 3,
      "sha256": "…",
      "schemaVersion": 1,
      "name": "Bulk RNA-seq 标准分析",
      "name_cn": "",
      "domainLabel": "生物信息学",
      "domains": ["biomedicine"],
      "description": "…",
      "nodeCount": 7,
      "source": {"type": "marketplace", "marketplaceId": "codar-biomed", "path": "workflows/bulk-rnaseq"},
      "requires": [{"pluginId": "codar-transcriptomics", "pluginName": "转录组学", "componentIds": ["rnaseq-deg-abcd1234"]}],
      "official": true,
      "sortOrder": 0,
      "updatedAt": "2026-11-18T00:00:00Z"
    }
  ],
  "checkedAt": "2026-11-18T00:00:00Z"
}
~~~

- 响应带强 ETag，计算范围是 `items`，不包含每次变化的 `checkedAt`；请求头
  `If-None-Match` 命中时返回 304 且无响应体。比较采用弱比较规则，代理压缩后返回的
  `W/"…"` 同样可以命中。列表使用 `Cache-Control: no-cache`。
- `version` 是正整数，由 SpeedSkills 分配；同一 `id + version` 的 Markdown 不可变。
- `sha256` 是对外 Markdown UTF-8 字节的 SHA-256。客户端只在摘要变化时下载正文，并在
  保存前自行校验摘要。
- `requires` 列出节点工具契约解析出的 Plugin 依赖；`source.type=plugin` 时所属 Plugin
  总是第一项。`pluginName` 在读取时按 Plugin 当前中文名或名称生成。

详情返回列表字段加当前 `markdown` 和 `releases`（`version`、`sha256`、`notes`、
`releasedAt`，按版本倒序）。工作流不存在或已下架时返回 404
`{"error":{"code":"not_found",…}}`。

`releases/{version}` 返回 `id`、`version`、`sha256`、`schemaVersion`、`markdown`，使用
`Cache-Control: public, max-age=31536000, immutable`。即使工作流已下架，历史版本仍可读取；
版本不存在时返回 404。同一工作流 ID 的版本号永不复用：工作流删除后重新发布，版本从
删除前的最大版本 + 1 开始。

对外 Markdown 由 SpeedSkills 规范化：统一 LF 换行，移除来源中的 `id`、`version`、
`updated`、`domains`、`basedOn`，并在 `schemaVersion`/`layoutDirection` 之后写入
`id: "<workflowId>"` 和 `version: <n>`。

## 8. Plugin package

### 8.1 Envelope

~~~json
{
  "schemaVersion": "speedskills.plugin-package.v4",
  "kind": "plugin",
  "plugin": {
    "id": "empirical-research",
    "name": "Empirical Research",
    "version": "1.2.0",
    "permissions": ["filesystem", "network"],
    "capabilities": ["research", "files", "datasets"]
  },
  "manifest": ".codex-plugin/plugin.json",
  "components": [
    {
      "componentId": "empirical-economics-writing-odatospd",
      "componentVersion": "0.1.48",
      "kind": "skill",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "required": true,
      "defaultEnabled": true,
      "path": "skills/empirical-economics-writing"
    },
    {
      "componentId": "fred-data",
      "componentVersion": "1.0.0",
      "kind": "mcp",
      "sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      "required": false,
      "defaultEnabled": false,
      "path": ".mcp.json#fred-data"
    }
  ],
  "download": {
    "url": "https://cdn.example.com/plugins/empirical-research/1.2.0/package.tar.gz",
    "sha256": "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
    "sizeBytes": 1048576
  },
  "sourceUrl": "https://skill.speedai.com/api/v4/plugins/empirical-research/package",
  "issuedAt": "2026-08-18T00:00:00Z"
}
~~~

### 8.2 Package requirements

- download.url、download.sha256 和 download.sizeBytes 必须存在。
- tar.gz 解压后必须包含 `manifest` 指向的 `.codex-plugin/plugin.json`。
- Claude Code 来源由 SpeedSkills 构建器转换成上述规范布局；SpeedClaw 不识别或
  转换 `.claude-plugin/plugin.json`。
- 每个 required 组件必须存在，且内容 digest 与 components[].sha256 一致。
- manifest 不能引用包根目录以外的路径。
- 包内不允许绝对路径、..、符号链接和硬链接。
- MCP secret、OAuth token 和用户配置不得进入 package。
- 列表或详情中的 metadata 不能直接作为可执行配置；运行时只信任校验后的 package。

## 9. 安装与运行语义

### 9.1 安装流程

v4 permission 分为两级：

- 基础权限：`filesystem`、`network`。它们是 Codar Skill 的通用运行能力，继续用于
  展示、审计和更新差异，但不要求额外授权，也不阻止默认安装或静默更新。
- 高权限：`shell`、`desktop`、`browser`、`downloads`、`mcp`、`clipboard`。
  首次安装或更新新增任一高权限时必须获得用户确认。客户端遇到未知 permission 时
  必须按高权限处理。

只有 `official=true`、`installPolicy=default`、当前 release 的 `securityStatus` 不是
`blocked` 且不包含待确认
高权限的 Plugin，才允许在默认配置阶段静默安装。`installPolicy=default` 不豁免高权限
确认；普通手动安装仍应展示全部 permissions 与 `securityStatus`。

~~~text
1. GET plugin detail
2. 展示 permissions 与 release.securityStatus
3. 如包含新增高权限，获得用户确认
4. GET plugin package envelope
5. 校验 schemaVersion、pluginId、version 和 download digest
6. 下载 tar.gz 到临时目录
7. 安全解压并校验 manifest 与组件 digest
8. 检查 Skill/MCP 命名和版本冲突
9. 原子移动到不可变 Plugin release 目录
10. 原子更新 InstalledPlugin 和 InstalledComponent 状态
11. 注册默认启用组件
12. 上报 install event
~~~

任一步失败都必须回滚本次安装产生的 release 目录、注册项和本地记录。用户数据目录不在失败回滚中删除。

### 9.2 本地布局

~~~text
~/.codar/
  plugins/
    releases/
      {pluginId}/
        {version}/
          .codex-plugin/plugin.json  # SpeedSkills 统一生成或校验
          skills/
          .mcp.json
          README.md
    data/
      {pluginId}/
        mcp-state.json
        secrets.enc
  components/
    skills/
      {componentId}/
    mcps/
      {componentId}/
  desktop/
    installed-plugins.json
    installed-components.json
~~~

各目录职责：

- components/skills/ 和 components/mcps/：standalone 组件的安装内容。
- plugins/releases/：Plugin package 解压后的不可变、版本化发布内容。
- plugins/data/：用户配置、MCP 授权和 secret 等跨版本可变数据。
- installed-plugins.json：Plugin 级安装、版本、release、权限和运行状态。
- installed-components.json：所有 standalone 与 plugin-bundled Skill/MCP 的统一安装账本。

### 9.3 启停规则

- Plugin enabled=false 时，其所有 Skill 和 MCP 都不可见、不可调用。
- required 组件的有效状态与 Plugin 一致。
- optional 组件的有效状态为 plugin.enabled && component.enabled。
- 禁用 Plugin 时先从工具和 Skill registry 注销组件，再关闭 MCP client。
- 启用 Plugin 失败时保留安装记录，并记录 runtimeStatus=error 和 lastError。

### 9.4 命名与归属

- Plugin release 目录内的组件不复制到 standalone components/skills 或 components/mcps 目录。
- 每个运行时组件必须能追溯到 standalone 或 Plugin owner。
- MCP server 的内部运行时名称由 `pluginId + serverName` 生成，避免不同 Plugin 的
  同名 server 冲突；该运行时名称不属于公共目录身份。
- UI 可以显示原始 server 名称，但运行时注册必须使用规范名避免冲突。
- 同一组件被多个 Plugin 携带时，各 Plugin 使用自己 release 中固定的安装路径。
- 底层可以按 sha256 去重制品，但去重不能改变 Plugin 的所有权和卸载语义。

### 9.5 Component 安装账本

installed-components.json 是本地所有 Skill/MCP 的唯一组件安装账本。无论组件来自 standalone 安装还是 Plugin 安装，都必须在这里记录。

~~~json
{
  "schemaVersion": 1,
  "components": [
    {
      "componentId": "empirical-economics-writing-odatospd",
      "kind": "skill",
      "name": "Empirical Economics Writing",
      "version": "0.1.48",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "source": {
        "type": "speedskills"
      },
      "owners": [
        {
          "type": "standalone",
          "enabled": true,
          "installPath": "~/.codar/components/skills/empirical-economics-writing-odatospd"
        },
        {
          "type": "plugin",
          "pluginId": "empirical-research",
          "pluginVersion": "1.2.0",
          "required": true,
          "enabled": true,
          "installPath": "~/.codar/plugins/releases/empirical-research/1.2.0/skills/empirical-economics-writing"
        }
      ]
    },
    {
      "componentId": "local-skill-pdf-k7m2x9pq",
      "kind": "skill",
      "name": "PDF",
      "version": "0.0.0-local.1",
      "sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      "securityStatus": "local",
      "source": {
        "type": "local",
        "localPath": "/Users/example/skills/pdf"
      },
      "owners": [
        {
          "type": "standalone",
          "enabled": true,
          "installPath": "~/.codar/components/skills/local-skill-pdf-k7m2x9pq"
        }
      ]
    }
  ]
}
~~~

账本规则：

- 组件身份只由 componentId 确定；`name` 和 `name_cn` 不参与身份判断。
- version 和 sha256 描述当前允许注册的唯一内容版本。
- installed-components.json 从首次发布起使用 schemaVersion=1，`source` 是每条
  Component 的必填字段；缺少或包含非法 source 的账本视为无效，不做静默推断。
- `source.type` 只使用 `speedskills` 和 `local`。`local` 表示 Component 只存在于
  本机，不代表内容最初一定来自本地目录。
- SpeedSkills release 的 `securityStatus` 仍只使用 `verified`、`unverified` 和
  `blocked`。仅当 `source.type=local` 时，SpeedClaw 本地账本允许使用客户端扩展值
  `securityStatus=local`，表示该组件只在本机管理且没有 SpeedSkills release 安全审核
  结论；它不表示组件已经验证，也不得作为远端 release 状态使用。
- `source.localPath` 记录本地目录导入时的原始绝对路径；`source.url` 记录旧
  `install_skill(url)` 的第三方 URL。两者只用于本地展示和来源追溯，不参与身份、
  SHA 或运行时判断，也不得进入任何 SpeedSkills 请求、遥测或远端错误上报。
- standalone owner 的 enabled 表示用户是否启用该独立组件。
- Plugin owner 的 enabled 表示该组件在 Plugin 内是否被选择；required 组件固定为 true。
- Plugin 的总开关保存在 installed-plugins.json。Plugin owner 的有效状态为 plugin.enabled && owner.enabled。
- 组件的最终有效状态是任意 owner 有效，不单独持久化 effectiveEnabled。
- componentId + version + sha256 相同的 owner 合并到同一组件记录。
- componentId 相同但 version 或 sha256 不同视为冲突，必须在安装提交前处理，不能静默覆盖。

### 9.6 状态更新

- 安装 standalone：写入组件内容，创建或更新 standalone owner。
- 安装 Plugin：写入 Plugin release 目录和 InstalledPlugin，并为 package 中每个组件创建 Plugin owner。
- 卸载 standalone：删除 standalone owner；仍有其他 owner 时保留组件记录和运行时注册。
- 卸载 Plugin：删除该 pluginId 的全部 owner；组件没有 owner 时删除记录并注销运行时。
- 更新 Plugin：先验证新 release 的完整组件集合和冲突，再一次性替换 Plugin owner。
- 启停 Plugin：只更新 Plugin 总开关并重新计算 owner 有效状态，不批量改写 required owner。
- 启停 optional 组件：更新对应 Plugin owner 的 enabled。
- 导入 local standalone Skill：校验原始目录并安全复制到 staging，生成新的 local
  componentId，在 staging 计算规范 SHA-256，再原子移动到
  `~/.codar/components/skills/{componentId}`；账本提交后只从 owner.installPath
  注册运行时。固定使用 `0.0.0-local.1`，不支持原地更新。
- 卸载 local standalone Skill：注销运行时，删除 standalone owner、无其他 owner
  的 Component 记录和受管理安装副本；绝不删除 source.localPath 指向的原始目录。

InstalledPlugin 与 InstalledComponent 的跨文件修改必须由同一个 InstallStateStore 串行执行。实现使用文件锁、临时文件、fsync、原子 rename 和 transaction journal；启动 reconcile 根据 Plugin manifest 和两个账本完成中断恢复。任何时候都不能让两个 HTTP handler 分别直接写这两个文件。

### 9.7 local Skill 受管理副本与失效状态

local Skill 的原始 `source.localPath` 或 `source.url` 失效不影响已安装内容。SpeedClaw
在启动 reconcile 和运行时注册前只校验 owner.installPath 指向的受管理副本：

- SKILL.md 缺失或无效：`local_manifest_invalid`。
- 规范目录 SHA-256 与账本不同：`local_content_changed`。

两种状态都会停止注册并提示用户卸载后重新导入。它们只属于 SpeedClaw 本地运行时，
不进入 SpeedSkills 公共模型或 HTTP wire。本轮不定义 local MCP 的复制和迁移规则。

### 9.8 local Skill 规范目录摘要

local Skill 与 SpeedSkills v4 Skill package 使用同一摘要语义。递归收集普通文件，拒绝
符号链接、设备和 socket 等非普通文件；现有算法不单独拒绝硬链接，而是按每个相对
路径的普通文件内容处理。忽略 `.git`、`node_modules`、`__pycache__`、
`.pytest_cache` 目录以及 `.DS_Store`、`*.pyc`、`*.pyo` 文件。

相对路径统一使用 `/` 并按字节顺序排序。每个文件依次向 SHA-256 写入：

~~~text
relativePath UTF-8 bytes
0x00
uint32 big-endian normalizedMode
uint64 big-endian fileSize
fileContent
~~~

任意可执行位存在时 normalizedMode 为 `0755`，否则为 `0644`。摘要不包含目录条目、
mtime、owner/group、绝对路径或来源信息，并且必须在 staging 副本上计算。

## 10. 更新检查

更新检查接口：

~~~text
POST /api/v4/plugins/updates/check
POST /api/v4/components/updates/check
~~~

Skill 和 MCP 共用 Component 更新检查接口。SpeedSkills 根据 Catalog 中 Component
自身的 `kind=skill|mcp` 判断类型。v4 只使用 `id`，不使用或解析 slug。

SpeedClaw 组装更新检查请求时，必须根据本地账本 `source.type` 排除 local Component。
SpeedSkills 不通过 `local-` 前缀推断来源，也不为 local Component 提供更新状态；如果
客户端误传 local ID，服务端仍按普通未知 ID 处理。

### 10.1 Plugin 更新检查

请求：

~~~json
{
  "plugins": [
    {
      "id": "empirical-research",
      "version": "1.1.0",
      "packageSha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "permissions": ["filesystem"],
      "capabilities": ["research"]
    }
  ]
}
~~~

响应：

~~~json
{
  "items": [
    {
      "id": "empirical-research",
      "status": "update_available",
      "latestVersion": "1.2.0",
      "latestPackageSha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "latestUpdatedAt": "2026-08-25T00:00:00Z",
      "permissionsChanged": true,
      "permissionsAdded": ["network"],
      "permissionsRemoved": [],
      "capabilitiesChanged": true,
      "securityStatus": "verified",
      "notes": "Add data integration",
      "reason": "",
      "recommendation": ""
    }
  ],
  "checkedAt": "2026-08-25T00:00:00Z"
}
~~~

### 10.2 standalone Component 更新检查

请求：

~~~json
{
  "components": [
    {
      "id": "empirical-writing-odatospd",
      "version": "0.1.0",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "permissions": ["filesystem"],
      "capabilities": ["writing"]
    }
  ]
}
~~~

响应：

~~~json
{
  "items": [
    {
      "id": "empirical-writing-odatospd",
      "status": "update_available",
      "latestVersion": "0.2.0",
      "latestSha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "latestPackageSha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "latestUpdatedAt": "2026-08-25T00:00:00Z",
      "permissionsChanged": false,
      "permissionsAdded": [],
      "permissionsRemoved": [],
      "capabilitiesChanged": false,
      "securityStatus": "verified",
      "notes": "",
      "reason": "",
      "recommendation": ""
    }
  ],
  "checkedAt": "2026-08-25T00:00:00Z"
}
~~~

### 10.3 状态与原因

`status` 表示资源当前是否可以继续使用或更新：

- current
- update_available
- unavailable
- blocked

更新结果中的 `status` 描述更新状态；`securityStatus` 描述 Catalog 当前 release 的
安全状态，两者不是同一字段。`securityStatus` 只支持 `verified`、`unverified`、
`blocked`。SpeedClaw 本地账本对 `source.type=local` 的 Component 使用的扩展值
`local` 不属于 HTTP wire；请求不提交本地保存的安全状态，响应始终返回服务端当前
结论。

`unavailable` 是状态，`reason` 是不可用原因。官方资源无论是软下架、从
Marketplace/Catalog 清单移除，还是已经删除数据库记录和安装制品，只要
SpeedSkills 能确认该 ID 以前存在，均统一返回：

~~~json
{
  "id": "empirical-research",
  "status": "unavailable",
  "reason": "delisted",
  "recommendation": "uninstall"
}
~~~

SpeedSkills 不向客户端区分软下架和硬删除。硬删除后的历史身份可由服务端内部
tombstone 记录识别；tombstone 不进入 Marketplace、Plugin 或 Component 的公共模型。

稳定的 `unavailable` 原因：

- `delisted`：该 ID 曾经存在，但官方资源现在已经下架或删除。
- `not_found`：无法确认该 ID 曾经存在，通常表示客户端提交了错误 ID。
- `release_unavailable`：资源存在，但没有可用的 current release。
- `package_unavailable`：current release 存在，但缺少可安装制品。
- `integrity_mismatch`：请求版本与 Catalog 版本相同，但摘要不一致。
- `version_not_catalogued`：客户端版本高于或不属于当前 Catalog 的版本。

所有 `unavailable` 结果默认返回 `recommendation=uninstall`。Catalog 数据库或服务
查询失败时，整个请求返回 HTTP 503 和 `catalog_unavailable`，不能把临时错误转换成
单项 `unavailable`。

服务端必须为每个请求项返回一次结果并保持请求顺序；不存在的 ID 不能被静默忽略。
空请求返回 `"items": []`。Plugin 根据 version 和 packageSha256 比较；Component
根据 version 和内容 sha256 比较。同版本摘要不同不能作为普通更新处理。

权限集合的全部变化仍通过更新检查返回。仅新增 `shell`、`desktop`、`browser`、
`downloads`、`mcp`、`clipboard` 或未知 permission 时阻止静默更新并要求重新确认；
只新增 `filesystem` 或 `network` 不阻止静默更新。

### 10.4 v3 Component 身份解析

SpeedSkills 在迁移 v3 Catalog 时保存 `kind + legacySlug → componentId` 的稳定映射。
v3 与 v4 的短 hash 规则不同，SpeedClaw 不得复制服务端算法，也不得根据名称、路径、
URL 或摘要推导正式 componentId。

~~~http
POST /api/v4/components/legacy/resolve
Content-Type: application/json
~~~

请求：

~~~json
{
  "components": [
    {
      "kind": "skill",
      "legacySlug": "empirical-economics-writing-1apxizo",
      "version": "0.1.48",
      "packageChecksum": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
~~~

`kind + legacySlug` 是唯一身份依据。`version` 用于选择旧安装对应的历史 release；
提供 `packageChecksum` 时，它是历史包的精确选择条件（接受裸 SHA-256 或 `sha256:`
前缀），不是仅用于诊断。同 slug/version 的不同包在批量请求中不会互相覆盖。
请求摘要不匹配任何可信历史记录时，仍可返回身份 `matched`，但返回
`availability=unavailable, reason=historical_package_unavailable`，不返回其他包的
`sha256` 或 `packageSha256`。客户端仍须验证权威包摘要和实际目录摘要。
不提供 checksum 时保留 canonical release 的原有行为；多个无明确优先级的历史包
不会任意选择。请求不得携带本地路径，服务端不使用 name、sourceURL 或 checksum 模糊匹配。

经原始包验证的补充历史凭证存放在独立的 `component_legacy_release_evidence` 表，
不覆盖 canonical release，不重新上架已删除/下架的 Component。相同包出现矛盾的
非空目录摘要时拒绝返回摘要。缺失的目录摘要不会从请求、当前版本或包摘要推算。

响应：

~~~json
{
  "items": [
    {
      "kind": "skill",
      "legacySlug": "empirical-economics-writing-1apxizo",
      "status": "matched",
      "componentId": "empirical-economics-writing-odatospd",
      "version": "0.1.48",
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "packageSha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "availability": "available",
      "reason": ""
    }
  ],
  "resolvedAt": "2026-08-26T00:00:00Z"
}
~~~

身份状态：

- `matched`：找到稳定映射，必须返回正式 componentId。
- `unmatched`：不存在映射，客户端保持原 v3 状态。
- `ambiguous`：保留给迁移脏数据保护；正常数据库唯一约束下不应产生。

`availability` 为 `available` 或 `unavailable`。稳定不可用原因包括 `delisted`、
`release_unavailable` 和 `package_unavailable`。软下架或带 tombstone 的硬删除仍返回
`matched + unavailable + delisted`；映射本身不会随 Component 硬删除而删除。

每个请求项返回一次并保持顺序，空数组返回 `"items": []`。`unmatched` 或
`ambiguous` 不能触发客户端账本修改；数据库临时失败时整个请求返回 HTTP 503 和
`catalog_unavailable`，不能伪装成 unmatched。

### 10.5 v3 本地状态迁移边界

- v3 `source` 与当前 SpeedSkills API Base 一致：调用 legacy resolve；API Base 比较
  需要规范化末尾 `/`，不能硬编码某个生产域名。
- v3 `source=local`：从现有安装目录复制为新的 local Skill 受管理副本；能确认真实
  原始目录时才填写 source.localPath。
- v3 `source=install_skill`：从现有安装目录复制，不重新下载 URL；迁为
  `source.type=local`，并将旧 source_url 保存为 source.url。
- 其他无法确认的 source 保持 v3，不猜测身份。
- 迁移成功前不修改旧账本；失败不影响旧 Skill 运行。成功后持久化 v3 slug 与新
  componentId 的迁移标记，避免重试产生重复 Component，并暂时保留旧目录用于恢复。

## 11. Install events

~~~json
{
  "version": "1.2.0",
  "desktopVersion": "0.5.0",
  "status": "completed",
  "stage": "runtime_registered",
  "errorCode": "",
  "error": ""
}
~~~

status：

- started
- completed
- failed

stage：

- package_resolved
- downloaded
- verified
- extracted
- recorded
- runtime_registered

事件不得上传本地路径、secret、MCP headers 或用户项目内容。SpeedClaw 必须根据本地
账本 `source.type` 排除 local Component，不为其发送 install event。

## 12. v3 兼容与迁移

### 12.1 路由兼容

- v3 /api/skills、/api/mcps 和 /api/domains 保持原行为。
- v4 不复用 v3 Domain includes 作为 Plugin。
- v4 Marketplace 来自一等 Marketplace 数据，不再由 skill.domain 即时聚合。
- v3 standalone Skill 安装记录不自动伪装成 Plugin。

### 12.2 Catalog 迁移

迁移顺序：

1. 先建立 v4 Marketplace、Plugin 和 release 框架，不自动转换现有 domain profile。
2. 后续按产品定义将现有 Skill 组合成 Plugin，不按 domain 字段自动生成单一大包。
   将 v3 基础能力整理为 General Plugin 时，旧 `install_policy=default` 汇总为
   `Plugin.installPolicy=default`；旧 `enable_policy=default` 映射为对应
   `PluginComponentRef.defaultEnabled=true`，其余映射为 false。
3. 为每个 Plugin 生成固定组件版本和 digest 的 release。
4. 生成真实 tar.gz 和 package sha256 后才允许 Plugin 出现在列表。
5. 保留所有 standalone Skill/MCP 条目。

### 12.3 客户端迁移

- 支持 v4 的客户端优先读取 /api/v4/marketplaces 和 /api/v4/plugins。
- 服务端不支持 v4 时，客户端可以回退到 v3 页面，但不得把 v3 Domain 记录为 InstalledPlugin。
- 现有 installed-speedskills.json 和 installed-speedmcps.json 条目迁移为 installed-components.json 中的 standalone owner。
- 通过有效 Plugin package 安装的历史组件迁移为对应的 Plugin owner。
- 迁移完成后旧组件文件只作为恢复备份，不再由 v4 写入；确认新账本稳定后再由用户选择清理。
- 已存在的 installed-plugins.json 记录必须在首次读取时校验 release 和 manifest；无有效 package 的历史记录标记为 legacy_invalid，不自动启用。

## 13. 持久化基线

### 13.1 远端 Catalog

推荐关系模型：

~~~text
marketplaces
  n ── n plugins（通过 marketplace_plugins 收录）

domains
  n ── n components（通过 domain_components 维护成员和领域内排序）

plugins
  1 ── n plugin_releases

plugin_releases
  1 ── n plugin_components
  1 ── 1 package_artifact

components（kind=skill|mcp）
  1 ── n component_releases

plugin_components
  n ── 1 component_release
~~~

最低唯一约束：

- marketplaces.id
- plugins.id
- marketplace_plugins(marketplace_id, plugin_id)
- domains.id
- domain_components(domain_id, component_id)
- plugin_releases(plugin_id, version)
- components.id
- component_releases(component_id, version)
- package_artifacts(sha256)

Plugin 和 Component 的 release 不维护 draft、published、withdrawn 或 isCurrent 等
发布生命周期状态。Plugin 通过 `currentVersion` 指向当前对外展示和安装的不可变
release；只有该版本存在且具备有效 package artifact 时，Plugin 才进入公开列表。
每个 release 另有 `securityStatus=verified|unverified|blocked`，它是可变的安全审核
结论，不是发布生命周期。当前 SpeedSkills 管理发布流程导入的新 release 默认
`verified`；`blocked` release 不得安装、
更新或返回 package。

### 13.2 本地安装状态

本地安装状态保持两个规范账本：

~~~text
installed-plugins.json
  Plugin 安装和运行状态

installed-components.json
  Skill/MCP 安装内容、source 与 owners（schemaVersion=1）
~~~

远端 Catalog 不存储本地 owners。owners 只描述某台 SpeedClaw 设备上一个组件由哪些本地安装持有。
远端 Catalog 同样不存储 local Component、`source.localPath`、`source.url` 或本地失效状态。
本地 Component 可以在 `source.type=local` 时保存 `securityStatus=local`，用于表示
仅限本机且没有 SpeedSkills release 审核结论；该扩展值不得进入 SpeedSkills 请求或
被解释为 `verified`。

## 14. 安全要求

- Catalog metadata 与可执行 package 严格分离。
- package 下载必须有大小上限和 SHA-256 校验。
- 当前 release 的 `securityStatus=blocked` 时不得返回可安装 package。
- MCP command、args、env key、URL 和 headers 模板必须纳入安全扫描。
- manifest 中的 secret 只能是用户配置引用，不能包含真实值。
- 安装与更新必须计算权限 diff。
- Plugin 卸载默认保留 data；删除用户数据需要单独明确操作。
- 所有运行时 Skill、MCP tool 和错误日志必须能追溯到 standalone 或 Plugin owner。

## 15. 验收标准

### Catalog

- Domain 列表按 `sortOrder ASC, id ASC` 稳定返回，并携带 `name`、`name_cn`。
- 指定 domain 的 Component 列表默认按 `domain_components.sortOrder` 返回。
- 管理端批量调整 Domain 或领域内 Component 顺序时，整批成功或整批回滚。
- 能创建两个以上 Marketplace，每个 Marketplace 返回不同 Plugin 列表。
- Marketplace plugin-display-prompts 通过一次请求返回全部符合条件的 Plugin，按最终
  展示顺序排列，不要求客户端逐个请求 Plugin 详情，也不混入 Component。
- Marketplace 不存在 package endpoint，也不产生 Plugin/Component installed 状态；Marketplace 来源的注册或同步状态与 Plugin 安装状态相互独立。
- Plugin 列表只返回具有有效 release package 的条目。
- Plugin detail 返回固定 version/digest 的 Skill/MCP 组件。
- 相同 pluginId + version 的 package sha256 永不变化。

### Install

- 可安装同时包含 Skill 和 MCP 的 Plugin。
- digest、路径或 manifest 校验失败时不会留下半安装状态。
- Plugin 禁用后，其 Skill 和 MCP 均从运行时消失。
- optional 组件可以单独启停，required 组件跟随 Plugin。
- 两个 Plugin 使用同名 MCP server 时不会发生注册冲突。
- standalone Skill/MCP 安装后会创建 standalone owner。
- Plugin 安装后会为所有组件创建 Plugin owner。
- 同版本、同 digest 的多个 owner 可以共存且运行时只注册一次。
- 不同版本或 digest 的同 componentId 组件会在提交安装前报告冲突。
- 删除一个 owner 后，只要仍有有效 owner，组件就保持安装和可用。

### Update

- Plugin 更新可以识别版本、权限、能力和安全状态变化。
- 权限增加会阻止静默更新。
- v3 standalone Skill/MCP 仍可浏览、安装和更新。
- v4 不可用时可以回退 v3，且不会污染 InstalledPlugin 状态。

## 16. 实施顺序

1. 冻结本协议与 OpenAPI schema。
2. 实现 v4 Domain 策展、Catalog 持久化和只读 Marketplace/Plugin API。（SpeedSkills 后端已完成）
3. 实现 Plugin/Component package endpoint（已完成）和 v4 install events（待实现）。
4. 实现 Marketplace plugin-display-prompts 聚合接口（SpeedSkills 后端已完成）。
5. 实现本地 Plugin package 校验、原子安装和 InstalledPlugin 状态。
6. 实现 Skill/MCP 运行时归属、启停和启动时 reconcile。
7. 实现更新检查与 v3 fallback。
8. 最后调整 Skill Market 前端为 Marketplace → Plugin → Components 导航。

前端改造不得早于 Plugin package 和本地运行时闭环，否则会再次出现“展示上像 Plugin、运行时仍是散装 Skill/MCP”的状态。

当前已完成 v4 持久化框架、只读目录和 Plugin package endpoint，包括以下接口：

~~~text
GET /api/v4/marketplaces
GET /api/v4/marketplaces/{marketplaceId}
GET /api/v4/domains
GET /api/v4/domains/{domainId}
GET /api/v4/plugins
GET /api/v4/plugins/{pluginId}
GET /api/v4/plugins/{pluginId}/package
GET /api/v4/skills
GET /api/v4/skills/{componentId}
GET /api/v4/skills/{componentId}/package
GET /api/v4/mcps
GET /api/v4/mcps/{componentId}
GET /api/v4/mcps/{componentId}/package
POST /api/v4/plugins/updates/check
POST /api/v4/components/updates/check
POST /api/v4/components/legacy/resolve
~~~

上述 v4 接口已使用统一的嵌套错误响应；Plugin 列表和 Marketplace 的
featuredPlugins 均返回轻量 `PluginSummary`，只有 Plugin 详情和 package
envelope 加载完整组件。standalone Component 列表返回 `Component`，详情返回
`ComponentEntry`。Plugin/Component package endpoint 和更新检查已经实现；v4 install
events 尚未实现。SpeedSkills 后台发布和目录运维接口不属于本共享客户端协议。

`GET /api/v4/marketplaces/{marketplaceId}/plugin-display-prompts` 已实现，
按 Marketplace 策展顺序一次返回全部具有非空 displayPrompt 的可展示 Plugin。
