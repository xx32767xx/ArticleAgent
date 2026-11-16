# SpeedSkills Models v4

本文档是 SpeedSkills 与 SpeedClaw 两个 Go 后端共同遵守的 v4 JSON wire
contract。双方可以采用不同 package 和文件划分，但导出的 JSON 字段名、类型、
可选性与嵌套关系必须一致。

约定：

- 所有时间使用 RFC 3339 字符串。
- 数组没有内容时返回 `[]`，不返回 `null`。
- Marketplace、Plugin、Component 不提供 `slug` 字段，统一使用 `id` 表示身份。
- `id` 必须是 URL-safe 的稳定标识，创建后不可修改；数据库关联、API 路径、
  Plugin 引用和安装状态均使用 `id`。非 local Component ID 由 SpeedSkills 分配；
  `local-` 前缀保留给 SpeedClaw 本机账本中的 standalone Skill/MCP。
- `name` 和 `name_cn` 是可修改的展示字段，不承担唯一身份。
- Marketplace、Plugin 和 Component 的 `iconUrl` 出现在 wire 中时必须是客户端可直接
  访问的完整 HTTP(S) URL，不得返回对象存储内部相对路径。
- Plugin 和 Component release 的版本内容不可变，不维护发布生命周期状态机。
- `official` 是 Plugin/Component 资源级来源标记；`securityStatus` 是 release 级
  安全状态。两者不得互相推导。
- `currentVersion` 负责选择目录当前展示和安装的 release。
- 下列 Go 类型是公共协议模型，不包含数据库专用字段。

## 1. 通用值类型

~~~go
type Publisher struct {
	Name    string `json:"name"`
	Type    string `json:"type"`
	Website string `json:"website,omitempty"`
}

type Download struct {
	URL       string `json:"url"`
	SHA256    string `json:"sha256"`
	SizeBytes int64  `json:"sizeBytes"`
}
~~~

## 2. Domain

~~~go
type Domain struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	NameCN      string `json:"name_cn,omitempty"`
	Summary     string `json:"summary,omitempty"`
	Description string `json:"description,omitempty"`
	IconURL     string `json:"iconUrl,omitempty"`
	SortOrder   int    `json:"sortOrder"`
}

type DomainListResponse struct {
	Items []Domain `json:"items"`
}
~~~

Domain 是 SpeedSkills 维护的 Catalog 策展数据。`SortOrder` 决定领域在客户端的展示
顺序；同值时按 `ID` 升序稳定排序。SpeedClaw 必须保持接口返回顺序，不自行按名称或
本地偏好重新排序。

Component 的 `domains` 继续返回 Domain ID 数组，但领域成员关系和领域内排序由
SpeedSkills 维护，不由 SpeedClaw 根据数组位置推导。

## 3. Marketplace

~~~go
type MarketplaceSource struct {
	Type         string `json:"type"`
	URL          string `json:"url,omitempty"`
	Ref          string `json:"ref,omitempty"`
	ManifestPath string `json:"manifestPath,omitempty"`
}

type MarketplaceSync struct {
	Enabled      bool   `json:"enabled"`
	Status       string `json:"status"`
	LastSyncedAt string `json:"lastSyncedAt,omitempty"`
	Error        string `json:"error,omitempty"`
}

type Marketplace struct {
	ID                string            `json:"id"`
	Name              string            `json:"name"`
	NameCN            string            `json:"name_cn,omitempty"`
	Summary           string            `json:"summary"`
	Description       string            `json:"description,omitempty"`
	IconURL           string            `json:"iconUrl,omitempty"`
	Source            MarketplaceSource `json:"source"`
	Sync              MarketplaceSync   `json:"sync"`
	Version           string            `json:"version"`
	Official          bool              `json:"official"`
	Tags              []string          `json:"tags"`
	FeaturedPluginIDs []string          `json:"featuredPluginIds"`
	SortOrder         int               `json:"sortOrder"`
	UpdatedAt         string            `json:"updatedAt"`
}

type MarketplacePlugin struct {
	MarketplaceID string `json:"marketplaceId"`
	PluginID      string `json:"pluginId"`
	Featured      bool   `json:"featured"`
	SortOrder     int    `json:"sortOrder"`
}
~~~

`MarketplaceSource.Type` 支持 `registry`、`git`、`url`。管理员从本机上传的来源在
发布后由 SpeedSkills 接管并规范化为 `registry`，不保留上传主机路径。
`MarketplaceSync.Status` 支持 `pending`、`syncing`、`ready`、`error`、
`disabled`。`MarketplacePlugin` 只表示收录关系。

## 4. Plugin

~~~go
type PluginSource struct {
	Type          string `json:"type"`
	MarketplaceID string `json:"marketplaceId,omitempty"`
	Path          string `json:"path,omitempty"`
	URL           string `json:"url,omitempty"`
	Ref           string `json:"ref,omitempty"`
}

type Plugin struct {
	ID              string       `json:"id"`
	Name            string       `json:"name"`
	NameCN          string       `json:"name_cn,omitempty"`
	Summary         string       `json:"summary"`
	Description     string       `json:"description,omitempty"`
	DisplayPrompt   string       `json:"displayPrompt,omitempty"`
	Readme          string       `json:"readme,omitempty"`
	IconURL         string       `json:"iconUrl,omitempty"`
	Publisher       Publisher    `json:"publisher"`
	Source          PluginSource `json:"source"`
	CurrentVersion  string       `json:"currentVersion"`
	InstallPolicy   string       `json:"installPolicy"`
	Official        bool         `json:"official"`
	Tags            []string     `json:"tags"`
	Domains         []string     `json:"domains"`
	Rating          float64      `json:"rating"`
	Downloads       int          `json:"downloads"`
	InstallsLast30d int          `json:"installsLast30d"`
	CreatedAt       string       `json:"createdAt"`
	UpdatedAt       string       `json:"updatedAt"`
}

type PluginRelease struct {
	PluginID      string         `json:"pluginId"`
	Version       string         `json:"version"`
	Permissions   []string       `json:"permissions"`
	Capabilities  []string       `json:"capabilities"`
	SecurityStatus string        `json:"securityStatus"`
	Notes         string         `json:"notes,omitempty"`
	PackageSHA256 string         `json:"packageSha256"`
	ReleasedAt    string         `json:"releasedAt,omitempty"`
	CreatedAt     string         `json:"createdAt"`
}
~~~

`Plugin.Readme` 是旧 Catalog 的兼容字段，已废弃，不属于新的展示或发布契约。安装前的
说明使用 `Summary` 和 `Description`；完整文档由客户端从选定 Plugin release package
内的 `README.md` 读取。兼容期服务端可以继续返回该字段，但客户端必须忽略。

`Plugin.DisplayPrompt` 是可选的用户可见使用示例，可以由界面提供复制或快速填入功能。
它不是系统提示词，不会自动执行，也不参与权限或安全状态判断。通过管理 PATCH 修改时
不改变 release；若修改来源包内的 `.codar/plugin.json`，该文件本身仍可能改变 Plugin
package SHA。

`PluginSource.Type` 支持 `marketplace`、`registry`、`git`、`url`。Type 为
`marketplace` 时 `MarketplaceID` 必填，其他类型不得填写；`git`、`url` 必须填写
`URL`。管理员直接上传的独立 Plugin 在发布后规范化为 `registry`。

`Plugin.InstallPolicy` 是 SpeedSkills 平台维护的 SpeedClaw 默认配置策略，只支持
`default` 和 `manual`。`default` 表示 SpeedClaw 在默认配置阶段自动安装该 Plugin；
`manual` 表示仅由用户主动安装。缺失或空值按 `manual` 处理。该字段不是 Plugin 作者
可以通过来源包自行声明的权限，第三方 Plugin 不得借此触发客户端自动安装。

`Plugin.Official` 只表示该资源是否由 SpeedSkills 官方发布，不表示其任一版本已经
完成安全验证。`PluginRelease.SecurityStatus` 表示具体 release 的安全状态，只支持
`verified`、`unverified`、`blocked`。当前通过 SpeedSkills 管理发布流程导入的新
release 默认是 `verified`；需要重新审核时可以改为 `unverified`，发现风险时可以改为
`blocked`。release 的版本、package、摘要、权限和
能力仍然不可变，`securityStatus` 是允许由管理端修改的审核结论。

## 5. Component

~~~go
type ComponentSource struct {
	Type     string `json:"type"`
	PluginID string `json:"pluginId,omitempty"`
	Path     string `json:"path,omitempty"`
	URL      string `json:"url,omitempty"`
	Ref      string `json:"ref,omitempty"`
}

type Component struct {
	ID              string    `json:"id"`
	Kind            string    `json:"kind"`
	Name            string    `json:"name"`
	NameCN          string    `json:"name_cn,omitempty"`
	Summary         string    `json:"summary"`
	Description     string    `json:"description,omitempty"`
	DisplayPrompt   string    `json:"displayPrompt,omitempty"`
	Readme          string    `json:"readme,omitempty"`
	IconURL         string    `json:"iconUrl,omitempty"`
	Publisher       Publisher `json:"publisher"`
	Source          ComponentSource `json:"source"`
	CurrentVersion  string    `json:"currentVersion,omitempty"`
	Standalone      bool      `json:"standalone"`
	Official        bool      `json:"official"`
	Tags            []string  `json:"tags"`
	Domains         []string  `json:"domains"`
	Rating          float64   `json:"rating"`
	Downloads       int       `json:"downloads"`
	InstallsLast30d int       `json:"installsLast30d"`
	CreatedAt       string    `json:"createdAt"`
	UpdatedAt       string    `json:"updatedAt"`
}

type ComponentRelease struct {
	ComponentID   string         `json:"componentId"`
	Version       string         `json:"version"`
	SHA256        string         `json:"sha256"`
	Permissions   []string       `json:"permissions"`
	Capabilities  []string       `json:"capabilities"`
	SecurityStatus string         `json:"securityStatus"`
	Notes         string         `json:"notes,omitempty"`
	PackageSHA256 string         `json:"packageSha256,omitempty"`
	ReleasedAt    string         `json:"releasedAt,omitempty"`
	CreatedAt     string         `json:"createdAt"`
}

type PluginComponentRef struct {
	PluginID         string `json:"pluginId"`
	PluginVersion    string `json:"pluginVersion"`
	ComponentID      string `json:"componentId"`
	ComponentVersion string `json:"componentVersion"`
	Required         bool   `json:"required"`
	DefaultEnabled   bool   `json:"defaultEnabled"`
	Path             string `json:"path"`
}

type PluginComponent struct {
	PluginComponentRef
	Component Component        `json:"component"`
	Release   ComponentRelease `json:"release"`
}
~~~

`Component.Readme` 是旧 Catalog 的兼容字段，已废弃。`Summary` 用于列表和卡片，
`Description` 用于安装前详情说明；完整使用文档以所选 Component release package 中的
`README.md` 为准。Skill 缺少 README 时，客户端可以回退到 `SKILL.md` 正文。兼容期
服务端可以继续返回 `readme`，但客户端不得读取、展示或据此覆盖 package 文件。

旧来源目录、迁移提示和 license hint 不属于用户 README，应保存在结构化 `Source` 或
SpeedSkills 内部迁移记录中。

`Component.Kind` 支持 `skill` 和 `mcp`。`Domains` 表示 Component 适用的领域，
允许一个 Skill/MCP 同时属于多个领域。`currentVersion` 仅在 Component
作为 standalone 目录资源时选择当前版本；Plugin 内始终固定
`componentId + componentVersion`。`Required=true` 时 `DefaultEnabled`
必须为 `true`。

`PluginComponentRef.DefaultEnabled` 表示 SpeedClaw 首次应用该 Plugin 默认配置时，
对应 Component 的初始启用状态。它与 `Plugin.InstallPolicy` 共同描述一个 Plugin 的
默认 loadout：Plugin 决定是否默认安装，关联中的 `DefaultEnabled` 决定安装后默认
启用哪些 Component。它不是 standalone Component 的全局固有属性。

`Permissions` 中的 `filesystem` 和 `network` 是基础权限，不要求额外授权；`shell`、
`desktop`、`browser`、`downloads`、`mcp` 和 `clipboard` 是高权限。未知 permission
按高权限处理。权限集合始终保留在 release 和更新响应中用于展示、审计与差异比较；
只有新增高权限才阻止默认安装或静默更新。

`Name` 与 `NameCN` 是可重复、可修改的展示名称，不承担唯一身份。Catalog、Plugin
携带及 SpeedSkills 托管的 standalone Component ID 使用
`规范化名称-8位稳定短 hash`，只能由 SpeedSkills 分配。官方 Component 和 Plugin
私有 Component 分别使用平台身份、Plugin 身份生成 hash；未来用户创建由服务端首次
分配身份。hash 不得根据 release 内容、版本、来源路径或压缩包摘要计算。后续更新
必须沿用已分配的 `componentId`。

`local-` 是 SpeedSkills Component ID 的保留前缀。仅存在于本机且不进入公共 Catalog
的 standalone Skill/MCP 由 SpeedClaw 首次导入时生成
`local-{kind}-{normalizedName}-{stableRandomSuffix}`，并持久化在本地账本。local
Component 不支持更新；失效后删除并重新导入会生成新 ID，版本固定为
`0.0.0-local.1`。SpeedSkills 不得分配、导入或返回该前缀的 Component ID。

`ComponentSource.Type` 支持 `plugin`、`registry`、`git`、`url`。
`plugin` 表示 Component 的规范来源是某个 Plugin，此时 `pluginId` 和 `path` 必填；
`git`、`url` 必须填写 `url`，其他类型不得填写 `pluginId`。来源只描述 Component
从哪里维护，不决定其是否
standalone，也不改变 PluginComponentRef 的版本固定关系。

`Component.Official` 与 `Plugin.Official` 语义相同，只表示官方来源。
`ComponentRelease.SecurityStatus` 与 Plugin release 使用相同的三个稳定值：
`verified`、`unverified`、`blocked`。

SpeedClaw 的 `installed-components.json` 另行使用以下本地持久化类型；它不属于
SpeedSkills HTTP wire：

~~~go
type InstalledComponentSource struct {
	Type      string `json:"type"` // speedskills 或 local
	LocalPath string `json:"localPath,omitempty"`
	URL       string `json:"url,omitempty"`
}
~~~

`Type=local` 表示 Component 只存在于本机，不等同于“最初来自本地目录”。本地目录
导入使用 `LocalPath` 保存首次导入的绝对路径；旧 `install_skill(url)` 迁移使用 `URL`
保存第三方来源。两者只用于本地展示和追溯，不参与身份、SHA 或运行时判断，也不得
发送给 SpeedSkills。SpeedClaw 组装 Catalog、更新检查和 install event 请求时依据
`Type` 排除 local Component，不通过 ID 前缀推断来源。

SpeedClaw 的本地 `InstalledComponent.SecurityStatus` 在 `source.type=local` 时允许使用
客户端扩展值 `local`。它表示该 Component 仅由本机管理且不存在 SpeedSkills release
安全审核结论，不表示已经验证。这个值只属于本地安装账本，不属于 `ComponentRelease`
或任何 SpeedSkills HTTP wire；不得上传、用于远端过滤，或与 `verified` 等价处理。
来自 SpeedSkills 的 InstalledPlugin/InstalledComponent 仍只保存对应 release 的
`verified`、`unverified` 或 `blocked`。

## 6. API 聚合类型

~~~go
type PluginComponentCounts struct {
	Skills int `json:"skills"`
	MCPs   int `json:"mcps"`
}

type PluginSummary struct {
	ID              string                `json:"id"`
	Name            string                `json:"name"`
	NameCN          string                `json:"name_cn,omitempty"`
	Summary         string                `json:"summary"`
	IconURL         string                `json:"iconUrl,omitempty"`
	Publisher       Publisher             `json:"publisher"`
	Version         string                `json:"version"`
	InstallPolicy   string                `json:"installPolicy"`
	Official        bool                  `json:"official"`
	Tags            []string              `json:"tags"`
	Domains         []string              `json:"domains"`
	Capabilities    []string              `json:"capabilities"`
	Permissions     []string              `json:"permissions"`
	ComponentCounts PluginComponentCounts `json:"componentCounts"`
	SecurityStatus  string                `json:"securityStatus"`
	Rating          float64               `json:"rating"`
	Downloads       int                   `json:"downloads"`
	InstallsLast30d int                   `json:"installsLast30d"`
	UpdatedAt       string                `json:"updatedAt"`
}

type MarketplaceDetail struct {
	Marketplace
	FeaturedPlugins []PluginSummary `json:"featuredPlugins"`
}

// PluginPromptSummary 是推荐区使用的轻量 Plugin 提示词投影。
type PluginPromptSummary struct {
	ID            string `json:"id"`
	Name          string `json:"name"`
	NameCN        string `json:"name_cn,omitempty"`
	DisplayPrompt string `json:"displayPrompt"`
	IconURL       string `json:"iconUrl,omitempty"`
}

type MarketplacePluginDisplayPromptsResponse struct {
	Items []PluginPromptSummary `json:"items"`
}

type PluginEntry struct {
	Plugin
	Release    PluginRelease     `json:"release"`
	Components []PluginComponent `json:"components"`
}

// ComponentEntry 是 standalone Component 详情中当前选中版本的聚合返回体。
type ComponentEntry struct {
	Component
	Release ComponentRelease `json:"release"`
}

type PagedResponse[T any] struct {
	Items    []T `json:"items"`
	Total    int `json:"total"`
	Page     int `json:"page"`
	PageSize int `json:"pageSize"`
}

type PluginMetadataPatch struct {
	Name          *string       `json:"name,omitempty"`
	NameCN        *string       `json:"name_cn,omitempty"`
	Summary       *string       `json:"summary,omitempty"`
	Description   *string       `json:"description,omitempty"`
	DisplayPrompt *string       `json:"displayPrompt,omitempty"`
	IconURL       *string       `json:"iconUrl,omitempty"`
	InstallPolicy *string       `json:"installPolicy,omitempty"`
	Official      *bool         `json:"official,omitempty"`
	Source        *PluginSource `json:"source,omitempty"`
}

type ComponentMetadataPatch struct {
	Name        *string          `json:"name,omitempty"`
	NameCN      *string          `json:"name_cn,omitempty"`
	Summary     *string          `json:"summary,omitempty"`
	Description *string          `json:"description,omitempty"`
	DisplayPrompt *string        `json:"displayPrompt,omitempty"`
	IconURL     *string          `json:"iconUrl,omitempty"`
	Official    *bool            `json:"official,omitempty"`
	Source      *ComponentSource `json:"source,omitempty"`
}
~~~

Plugin 列表接口使用 `PluginSummary`，Plugin 详情接口使用 `PluginEntry`。
standalone Component 详情接口使用 `ComponentEntry`；Plugin 内固定版本的组件
详情使用 `PluginComponent`。

Marketplace plugin-display-prompts 聚合接口使用
`MarketplacePluginDisplayPromptsResponse`。该响应只包含 Plugin，不包含 standalone
Skill、MCP 或其他 Component。它只承载首页展示和后续详情请求所需的稳定 ID，
不携带 release 的 `permissions` 或
`securityStatus`；客户端在安装前必须通过 Plugin 详情取得最新值。

两个 metadata patch 只允许管理可变展示信息、官方来源标记和规范来源；Plugin 还允许
修改 `installPolicy`。`id`、`kind`、
`currentVersion`、release、Artifact 和统计字段不得通过 PATCH 修改。请求中未出现的
字段保持不变；`name`、`summary` 出现时不得为空，其他字符串字段允许显式传空字符串
进行清除。

`Component.DisplayPrompt` 与 Plugin 字段语义一致，是可选的用户可见使用示例。它不替代
Skill 的 `SKILL.md` 或 MCP 配置，也不得被客户端当作受信任的运行时指令自动执行。

## 7. Plugin package 类型

~~~go
type PluginPackageEnvelope struct {
	SchemaVersion string                   `json:"schemaVersion"`
	Kind          string                   `json:"kind"`
	Plugin        PluginPackageIdentity    `json:"plugin"`
	Manifest      string                   `json:"manifest"`
	Components    []PluginPackageComponent `json:"components"`
	Download      Download                 `json:"download"`
	SourceURL     string                   `json:"sourceUrl"`
	IssuedAt      string                   `json:"issuedAt"`
}

type PluginPackageIdentity struct {
	ID           string   `json:"id"`
	Name         string   `json:"name"`
	Version      string   `json:"version"`
	Permissions  []string `json:"permissions"`
	Capabilities []string `json:"capabilities"`
}

type PluginPackageComponent struct {
	ComponentID      string `json:"componentId"`
	ComponentVersion string `json:"componentVersion"`
	Kind             string `json:"kind"`
	SHA256           string `json:"sha256"`
	Required         bool   `json:"required"`
	DefaultEnabled   bool   `json:"defaultEnabled"`
	Path             string `json:"path"`
}

type ComponentPackageEnvelope struct {
	SchemaVersion string                   `json:"schemaVersion"`
	Kind          string                   `json:"kind"`
	Component     ComponentPackageIdentity `json:"component"`
	Manifest      string                   `json:"manifest"`
	EntryKey      string                   `json:"entryKey,omitempty"`
	Download      Download                 `json:"download"`
	SourceURL     string                   `json:"sourceUrl"`
	IssuedAt      string                   `json:"issuedAt"`
}

type ComponentPackageIdentity struct {
	ID           string   `json:"id"`
	Name         string   `json:"name"`
	Version      string   `json:"version"`
	SHA256       string   `json:"sha256"`
	Permissions  []string `json:"permissions"`
	Capabilities []string `json:"capabilities"`
}
~~~

`PluginPackageEnvelope.Manifest` 固定为 `.codex-plugin/plugin.json`。SpeedSkills
构建器负责把 Claude Code Plugin 转换成该规范布局，SpeedClaw 不识别或转换来源格式。

`ComponentPackageEnvelope.Manifest` 对 Skill 固定为 `SKILL.md`，对 MCP 固定为
`.mcp.json`。`component.sha256` 校验解压后的规范化组件内容，`download.sha256`
校验实际下载的 tar.gz；两者含义不同。standalone MCP 必须返回 `EntryKey`，其值是
安装包 `.mcp.json` 中的原始顶层 key；Skill 不返回该字段。`Component.ID` 是平台稳定
身份，`EntryKey` 只负责定位包内配置，两者不得互相替换。

## 8. 更新检查类型

~~~go
type InstalledPluginSnapshotV4 struct {
	ID             string   `json:"id"`
	Version        string   `json:"version"`
	PackageSHA256  string   `json:"packageSha256"`
	Permissions    []string `json:"permissions"`
	Capabilities   []string `json:"capabilities"`
}

type PluginUpdateCheckRequestV4 struct {
	Plugins []InstalledPluginSnapshotV4 `json:"plugins"`
}

type PluginUpdateCheckItemV4 struct {
	ID                  string   `json:"id"`
	Status              string   `json:"status"`
	LatestVersion       string   `json:"latestVersion,omitempty"`
	LatestPackageSHA256 string   `json:"latestPackageSha256,omitempty"`
	LatestUpdatedAt     string   `json:"latestUpdatedAt,omitempty"`
	PermissionsChanged  bool     `json:"permissionsChanged"`
	PermissionsAdded    []string `json:"permissionsAdded"`
	PermissionsRemoved  []string `json:"permissionsRemoved"`
	CapabilitiesChanged bool     `json:"capabilitiesChanged"`
	SecurityStatus      string   `json:"securityStatus,omitempty"`
	Notes               string   `json:"notes,omitempty"`
	Reason              string   `json:"reason,omitempty"`
	Recommendation      string   `json:"recommendation,omitempty"`
}

type PluginUpdateCheckResponseV4 struct {
	Items     []PluginUpdateCheckItemV4 `json:"items"`
	CheckedAt string                    `json:"checkedAt"`
}

type InstalledComponentSnapshotV4 struct {
	ID             string   `json:"id"`
	Version        string   `json:"version"`
	SHA256         string   `json:"sha256"`
	Permissions    []string `json:"permissions"`
	Capabilities   []string `json:"capabilities"`
}

type ComponentUpdateCheckRequestV4 struct {
	Components []InstalledComponentSnapshotV4 `json:"components"`
}

type ComponentUpdateCheckItemV4 struct {
	ID                  string   `json:"id"`
	Status              string   `json:"status"`
	LatestVersion       string   `json:"latestVersion,omitempty"`
	LatestSHA256        string   `json:"latestSha256,omitempty"`
	LatestPackageSHA256 string   `json:"latestPackageSha256,omitempty"`
	LatestUpdatedAt     string   `json:"latestUpdatedAt,omitempty"`
	PermissionsChanged  bool     `json:"permissionsChanged"`
	PermissionsAdded    []string `json:"permissionsAdded"`
	PermissionsRemoved  []string `json:"permissionsRemoved"`
	CapabilitiesChanged bool     `json:"capabilitiesChanged"`
	SecurityStatus      string   `json:"securityStatus,omitempty"`
	Notes               string   `json:"notes,omitempty"`
	Reason              string   `json:"reason,omitempty"`
	Recommendation      string   `json:"recommendation,omitempty"`
}

type ComponentUpdateCheckResponseV4 struct {
	Items     []ComponentUpdateCheckItemV4 `json:"items"`
	CheckedAt string                       `json:"checkedAt"`
}

type ComponentLegacyResolveRequestItem struct {
	Kind            string `json:"kind"`
	LegacySlug      string `json:"legacySlug"`
	Version         string `json:"version"`
	PackageChecksum string `json:"packageChecksum,omitempty"`
}

type ComponentLegacyResolveRequest struct {
	Components []ComponentLegacyResolveRequestItem `json:"components"`
}

type ComponentLegacyResolveItem struct {
	Kind          string `json:"kind"`
	LegacySlug    string `json:"legacySlug"`
	Status        string `json:"status"`
	ComponentID   string `json:"componentId,omitempty"`
	Version       string `json:"version,omitempty"`
	SHA256        string `json:"sha256,omitempty"`
	PackageSHA256 string `json:"packageSha256,omitempty"`
	Availability  string `json:"availability,omitempty"`
	Reason        string `json:"reason,omitempty"`
}

type ComponentLegacyResolveResponse struct {
	Items      []ComponentLegacyResolveItem `json:"items"`
	ResolvedAt string                       `json:"resolvedAt"`
}
~~~

Plugin 和 Component 分别通过 `/api/v4/plugins/updates/check` 和
`/api/v4/components/updates/check` 批量检查。Component 接口同时接收 Skill 和 MCP，
服务端根据 Catalog 中的 `kind` 判断类型。`status=unavailable` 时通过 `reason`
区分 `delisted`、`not_found`、release/package 缺失或摘要冲突。

`/api/v4/components/legacy/resolve` 使用 `kind + legacySlug` 查询稳定映射；Version
选择客户端当前安装的历史 release，提供 PackageChecksum 时还必须精确匹配历史包。
`matched` 仅表示身份匹配，不保证历史校验资料完整。缺失/冲突的历史包证据返回
`historical_package_unavailable` 且不返回摘要；完整的下架历史信息仍保留 `delisted`。
只有版本、packageSha256、sha256 均可信且通过客户端校验时才能迁移。
`unmatched` 或 `ambiguous` 时客户端不得修改旧 v3 状态。

## 9. 错误响应类型

~~~go
type APIErrorResponse struct {
	Error APIError `json:"error"`
}

type APIError struct {
	Code      string `json:"code"`
	Message   string `json:"message"`
	RequestID string `json:"requestId,omitempty"`
}
~~~

## 10. 服务端内部边界

`PackageArtifact.StoragePath` 是 SpeedSkills 服务端内部字段，不能出现在公共
列表、详情或 package envelope 中。SpeedClaw 只消费 envelope 的
`Download.URL`、`Download.SHA256` 和 `Download.SizeBytes`。

凡是修改 SpeedSkills Go v4 JSON 类型，都必须在同一次改动中同步更新本文档，
并保持 SpeedSkills 与 SpeedClaw 两份副本内容一致。
