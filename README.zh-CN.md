# AngelScript Unreal Engine Skills for Codex

[English](README.md)

基于 [Epic Games 官方技能仓库](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin)的
**Codex 社区适配版**。保留上游 Git 历史和 MIT 版权，不代表 Epic Games 或 OpenAI 官方发行。
本分支基于 [Idris173 的固定提交](https://github.com/Idris173/unreal-engine-skills-for-codex-plugin/commit/a6c25ac96cea4cdfb93029e31423efd109d90895)，
保留其三个 UE Skill 的内容，增加三个通用 AngelScript Skill。详细来源见 [UPSTREAM.md](UPSTREAM.md)。
本插件提供官方 MCP 工具的工作流，不包含 UE 引擎或引擎侧插件。

| Skill | 用途 |
| --- | --- |
| `unreal-mcp` | 连接、查询、操作编辑器，以及连接排障 |
| `create-toolset` | 编写和扩展 C++ / Python Toolset |
| `unreal-skill` | 编写 UE 内部的 Agent Skill（Python 类或 UAsset） |
| `angelscript-in-unreal` | 查找实际绑定并编写 AngelScript 游戏逻辑 |
| `as-integration-tests` | 按目标工程规则编写世界、PIE 和 latent 测试 |
| `emmsui` | 使用已有 EmmsUI 插件编写和检查 AngelScript 调试/编辑器界面 |

## 环境要求

本地 Codex 需支持 Skills/MCP，通过插件安装还需支持插件机制。UE 安装需包含 `ModelContextProtocol`、
`ToolsetRegistry` 和所需的独立 Toolset；编辑器和 MCP Server 必须启动。辅助脚本需要 Python 3.11+。
AS 功能需要兼容的 AngelScript 引擎，EmmsUI 需另外安装。
本分支的[验证状态](docs/SANDBOX_VALIDATION.md)与 [Idris 历史记录](docs/VALIDATION.md)分开记录，不能相互替代。

## 从干净分发包安装到目标工程

把开发 checkout 与安装源分开。已检查的 Codex 本地 installer 会递归复制源目录中的普通目录和文件，
不会排除 `.git`、`.venv`、`dist` 或 `tests`。直接安装开发仓库会把这些开发数据复制到插件缓存。
具体行为见[固定提交的复制实现](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/store.rs#L736)。
先通过 allowlist 打包，再解压到新的空分发目录：

```powershell
$pluginRepo = 'C:\Plugins\angelscript-unreal-engine-skills-for-codex-plugin'
$packagePython = "$pluginRepo\.venv\Scripts\python.exe"
# 仅首次创建隔离的开发环境时需要。
python -m venv "$pluginRepo\.venv"
& $packagePython -m pip install -r "$pluginRepo\requirements-dev.txt"
& $packagePython "$pluginRepo\scripts\validate_plugin.py"
& $packagePython "$pluginRepo\scripts\package_plugin.py"
$packageZip = "$pluginRepo\dist\angelscript-unreal-engine-skills-for-codex-0.1.0.zip"
$distributionRoot = "$pluginRepo\dist\local-plugin-0.1.0-build1"
if (Test-Path -LiteralPath $distributionRoot) { throw 'Choose a new distribution directory; do not merge into an old copy.' }
Expand-Archive -LiteralPath $packageZip -DestinationPath $distributionRoot
```

每次更新使用新的 `local-plugin-<version-or-build>` 目录，不把新包覆盖混入旧文件。ZIP 包含六个 Skill、
清单、文档和运行辅助脚本，排除 Git、虚拟环境、测试和外部 UE 工程依赖。Shell 的 cwd 遵守工作区规则。

把以下配置合并到目标工程的 `.codex/config.toml`，替换分发目录和端口。`source` 必须指向解压后的分发目录，
而不是开发仓库根目录；包内 catalog 的 `./` 只引用该分发目录。

```toml
[marketplaces.angelscript-unreal-engine-skills-for-codex]
source_type = "local"
source = 'C:\Plugins\angelscript-unreal-engine-skills-for-codex-plugin\dist\local-plugin-0.1.0-build1'

[plugins."angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex"]
enabled = true

[mcp_servers.unreal-mcp]
url = "http://127.0.0.1:58241/mcp"
```

**必须实际执行安装。** 配置只声明来源与启用状态，不会安装文件；Codex 读取安装后的缓存副本。
信任目标工程后，让 CLI 子进程的 cwd 指向该工程，再执行：

```powershell
codex plugin list --marketplace angelscript-unreal-engine-skills-for-codex --json
codex plugin add angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex --json
```

若列表没有该 marketplace，先解决配置/信任加载问题。原生桌面 UI/API 的 Install 是等价操作，显示名称为
**AngelScript Unreal Codex**。首次官方安装会写用户范围的 enabled 设置，即使工程已经启用。
需要时先取得这次用户配置写入的授权。若只在目标工程激活，安装后在 `~/.codex/config.toml` 将此插件设为
false，同时保持目标工程 config 的 true：

```toml
# 用户默认关闭，目标工程配置覆盖为 true。
[plugins."angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex"]
enabled = false
```

保留其他插件和用户配置。如果用户配置必须完全不变，在安装前解决这一约束，不能把 config-only 当成安装完成。
隔离的 client home 可以单独验证安装，但不能证明现有桌面会话已加载插件。
见[官方说明](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work)与
[用户启用写入实现](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/manager.rs#L2307)。

安装后先启动目标 Editor 和 MCP server，核对监听端口所属 PID、可执行文件和工程，再开启受信任目标工程的新会话。
本次客户端观察到：Editor 关闭时启动会话，六个 Skill 可以加载，但最初 MCP handshake 失败；之后才启动 server
不能证明原会话已经重新连接。确认六个实际 Skill、零个插件生命周期 Hook，以及一次成功的原生 MCP 调用。
源文件更新后要重新安装刷新缓存，只修改 source 路径不能证明缓存已更新。不要同时安装独立的同名 Skill 副本。

### 可选直接仓库安装

```powershell
codex plugin marketplace add coquid/angelscript-unreal-engine-skills-for-codex-plugin
codex plugin add angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex
```

这种方式注册到用户范围，并直接复制仓库源，不使用 ZIP allowlist。开发文件可能进入缓存；本地 checkout
还可能包含 `.venv`、`.git` 和旧输出。仅在确实需要这个来源和配置范围时使用。验证和部署优先使用干净分发包。
两种 manifest 均不自动注册固定 MCP 地址，也不运行生命周期 Hook。

## 连接工程

在项目编辑器启用 `ModelContextProtocol`、`ToolsetRegistry` 和所需的独立 Toolset 并按提示重启，运行
`ModelContextProtocol.StartServer`。默认地址 `http://127.0.0.1:8000/mcp`；端口占用时使用
`ModelContextProtocol.StartServer <空闲端口>`。检查现有连接后选择以下一种配置方式。

**独立工程推荐：** 显式合并上面的项目配置，或用下面的 helper 预览目标工程的确切配置文件。

**可选引擎生成器：** 确认输出位置后才在 UE 控制台执行：

```text
ModelContextProtocol.GenerateClientConfig Codex
```

安装版写入 `.uproject` 旁的 `.codex/config.toml`；源码版写入 `Engine/` 旁的工作区根目录，可能在独立 sandbox 工程之外。
项目需被 Codex 信任。已有 TOML 不会被生成器覆盖，可在本仓库目录预览追加：

```powershell
python scripts/configure_mcp.py --config "F:\MyProject\.codex\config.toml" --url "http://127.0.0.1:8000/mcp"
```

加 `--apply` 后才写入。脚本保留无关内容及注释、备份旧文件并验证结果；相同配置不变，冲突停止。
它只检查指定文件，其他配置作用域和插件连接需另外检查。已有连接改端口请明确编辑；带自定义 ACL/
扩展属性的配置建议手工合并。

**用户配置：** 也可直接使用：

```powershell
codex mcp add unreal-mcp --url http://127.0.0.1:8000/mcp
```

这会写入用户配置。不要再注册同一编辑器的重复项目连接或代理。多工程并行时区分实例和端口。

## 验证与开发

`codex mcp list` 只证明配置存在。先确认目标 MCP server 已就绪且进程身份正确，再开启目标工程新会话：

> 使用 $unreal-mcp 读取当前关卡并列出几个 Actor，不修改工程。

确认实际返回的目标项目。工具使用 `list_toolsets → describe_toolset → call_tool`，
关闭 tool-search 时使用实际原生 schema。资产创建、保存和重启后回读分别验证。
完整[连接说明](skills/unreal-mcp/references/setup.md)与[排障说明](skills/unreal-mcp/references/operations.md)。

核心功能不依赖 Bash；[Python SessionStart Hook](docs/OPTIONAL_HOOK.md)需单独配置和信任，默认不安装。
代理自动安装不在首版范围，不能把上游 `--mcp-json` 直接指向 TOML。

开发请使用 Git checkout（ZIP 不含开发工具/测试）。仅在目标工程政策允许时运行已编写的测试；静态验证和打包可单独执行：

```powershell
python -m pip install -r requirements-dev.txt
python scripts/validate_plugin.py
python -m unittest discover -s tests -v
python scripts/package_plugin.py
```

ZIP 输出到 `dist/`，可解压为本地安装源，不包含 Git、虚拟环境或原始 UE 日志。
继承的 CI 配置覆盖 Windows/Linux 与 Python 3.11/3.14，不代表本分支已通过 CI。
独立 Windows UE 工程的启动和清理步骤见 [sandbox runner](docs/SANDBOX_VALIDATION.md)。

- [完整改造方案](docs/MIGRATION_PLAN.zh-CN.md)
- [验证记录与限制](docs/VALIDATION.md)
- [上游基线与同步](UPSTREAM.md)
- [MIT 许可证](LICENSE)

MCP 可修改编辑器及磁盘内容。保持 loopback 连接、确认目标项目，并为批量变更保留恢复点。
安装不要求关闭 Codex 权限控制。仓库 MIT 不改变外部 UE 组件许可。公开插件目录发布是独立后续工作。
