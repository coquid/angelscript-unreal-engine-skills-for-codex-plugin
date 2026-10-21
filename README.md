# AngelScript Unreal Engine Skills for Codex

[简体中文](README.zh-CN.md)

A community Codex adaptation of [Epic Games' Unreal Engine skills](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin).
Based on [Idris173's pinned Codex port](https://github.com/Idris173/unreal-engine-skills-for-codex-plugin/commit/a6c25ac96cea4cdfb93029e31423efd109d90895),
with three generic AngelScript skills. The three ported UE skill directories remain unchanged from that commit.
Not an official Epic Games or OpenAI release. Original MIT copyright and Git history are preserved.

This plugin teaches Codex to use **Unreal Engine's official MCP server and ToolsetRegistry**.
It does not include Unreal Engine, the engine-side plugins, or a replacement MCP server.

| Skill | Use it for |
| --- | --- |
| `unreal-mcp` | Connect to, inspect, and operate a live Unreal Editor; diagnose connections |
| `create-toolset` | Author or extend C++/Python tools registered with ToolsetRegistry |
| `unreal-skill` | Author Unreal's in-editor Agent Skills (Python classes or UAssets) |
| `angelscript-in-unreal` | Locate actual AngelScript bindings and implement UE gameplay safely |
| `as-integration-tests` | Design world/PIE/latent AngelScript tests using the target project's harness |
| `emmsui` | Build and verify AngelScript debug/editor UI using an installed EmmsUI plugin |

## Requirements

- A local Codex client supporting Skills and MCP; marketplace installation also requires plugin support.
- An engine containing `ModelContextProtocol`, `ToolsetRegistry`, and the specific toolset plugins needed for the task.
- AngelScript skills require a compatible AngelScript engine fork; EmmsUI guidance requires that separate plugin.
- A running editor and MCP server for live operations.
- Python **3.11+** for the optional configuration helper/development checks; manual MCP setup needs no Python.

There is no verified universal minimum UE version. See [this fork's validation procedure and status](docs/SANDBOX_VALIDATION.md).
The [Idris validation record](docs/VALIDATION.md) is third-party historical evidence, not a result from this fork.

## Install a clean distribution for one project

Keep the development checkout separate from the installed source. The inspected Codex local installer recursively
copies ordinary files and directories from the selected source; it does not exclude `.git`, `.venv`, `dist`, or
`tests`. Installing directly from a development checkout therefore copies development data into the plugin cache.
See [the pinned copy implementation](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/store.rs#L736).
Use the package allowlist to build a ZIP, then extract it to a new, empty distribution directory:

```powershell
$pluginRepo = 'C:\Plugins\angelscript-unreal-engine-skills-for-codex-plugin'
$packagePython = "$pluginRepo\.venv\Scripts\python.exe"
# Prepare this isolated development environment once if it does not exist.
python -m venv "$pluginRepo\.venv"
& $packagePython -m pip install -r "$pluginRepo\requirements-dev.txt"
& $packagePython "$pluginRepo\scripts\validate_plugin.py"
& $packagePython "$pluginRepo\scripts\package_plugin.py"
$packageZip = "$pluginRepo\dist\angelscript-unreal-engine-skills-for-codex-0.1.0.zip"
$distributionRoot = "$pluginRepo\dist\local-plugin-0.1.0-build1"
if (Test-Path -LiteralPath $distributionRoot) { throw 'Choose a new distribution directory; do not merge into an old copy.' }
Expand-Archive -LiteralPath $packageZip -DestinationPath $distributionRoot
```

For each updated package, choose a fresh `local-plugin-<version-or-build>` directory. The ZIP contains the six skills,
manifests, documentation, and runtime helpers; it excludes source-control internals, virtual environments, tests,
and external UE project dependencies. Keep the shell in the directory required by the workspace's instructions.

Merge the following into the target project's `.codex/config.toml`, replacing the distribution path and MCP port.
Point `source` at the extracted distribution, not the development checkout. The included catalog uses `./`, which
stays within that distribution root.

```toml
[marketplaces.angelscript-unreal-engine-skills-for-codex]
source_type = "local"
source = 'C:\Plugins\angelscript-unreal-engine-skills-for-codex-plugin\dist\local-plugin-0.1.0-build1'

[plugins."angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex"]
enabled = true

[mcp_servers.unreal-mcp]
url = "http://127.0.0.1:58241/mcp"
```

**An actual installation is required.** These settings select a source and enable the plugin; they do not install
its files. Codex loads the installed cache copy rather than the source directory. After making the project trusted,
run the following CLI commands with the target project as the child process's working directory. If the marketplace
is absent from the listing, resolve configuration/trust discovery before installing; do not treat an empty list as a pass.

```sh
codex plugin list --marketplace angelscript-unreal-engine-skills-for-codex --json
codex plugin add angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex --json
```

The native desktop UI/API install is an equivalent installation operation. The desktop marketplace label is
**AngelScript Unreal Codex**. Both the official installer and UI can write a user-level enabled setting, even when
the project already enables the plugin. Obtain authorization for that initial user-setting write when the workspace
requires it. For project-only activation, set this plugin's user entry in `~/.codex/config.toml` to `enabled = false`
after installation, while retaining `enabled = true` in the target project's config:

```toml
# User config: disabled by default; the target project overrides this to true.
[plugins."angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex"]
enabled = false
```

Preserve unrelated user settings and other plugin entries. If user settings must remain untouched, stop before the
install operation and resolve that constraint; config-only setup is not a completed installation. An independently
authorized isolated client home can validate installation separately, but does not prove loading in an existing
desktop session. See [official local-marketplace behavior](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work)
and [the unconditional user enablement write](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/manager.rs#L2307).

After installation, start the intended editor and its MCP server first. Verify the listening port belongs to the
recorded editor PID, executable, and project; then start a fresh Codex chat in that trusted target project. In the
observed client, starting a chat while the editor was off loaded the six skills but failed the initial MCP handshake;
starting the server later did not establish that the existing session had reconnected. Verify all six actual skill
entries, zero plugin lifecycle hooks, and a successful native MCP call. Reinstall after source updates to refresh
the installed cache; merely editing the source or switching its path does not prove the cache refreshed. Avoid a
second standalone copy of the same skills.

### Optional repository-source installation

A supporting CLI can instead register the GitHub repository directly:

```sh
codex plugin marketplace add coquid/angelscript-unreal-engine-skills-for-codex-plugin
codex plugin add angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex
```

This registers at user scope and installs the repository source without the ZIP allowlist. Development files from
that checkout may be copied into the cache; a local checkout can also contain `.venv`, `.git`, and prior outputs.
Use this route only when that source and wider configuration scope are intended. The clean distribution procedure
above is preferred for validation and deployment.

The package provides a portable `plugin.json` and a `.codex-plugin/plugin.json` compatibility manifest.
It does **not** automatically register a fixed MCP endpoint or run a lifecycle hook.

## Connect an editor

Enable `ModelContextProtocol`, `ToolsetRegistry`, and the required specific toolsets in the project editor, restarting if requested.
For a small validation project, use `EditorToolset`, `AutomationTestToolset`, and `SlateInspectorToolset`; enable others only when needed.
Run `ModelContextProtocol.StartServer` in the UE console; the default is `http://127.0.0.1:8000/mcp`.
For an occupied port, use `ModelContextProtocol.StartServer <free-port>`.
Choose **one** configuration route after checking existing connections:

**Recommended isolated-project configuration:** write or merge the MCP entry in the explicit project config
shown above, or preview the optional `configure_mcp.py` helper against that exact file. This avoids relying on an
engine generator's source-workspace location.

**Alternative engine generator:** run this in the UE console only after checking its destination:

```text
ModelContextProtocol.GenerateClientConfig Codex
```

Installed builds write `.codex/config.toml` beside the `.uproject`; source builds write at the workspace root
beside `Engine/`, which can be outside an independent sandbox project. Codex loads project configuration only in
trusted projects. The generator refuses to overwrite existing TOML. To preview an addition from this checkout:

```powershell
python scripts/configure_mcp.py --config "F:\MyProject\.codex\config.toml" --url "http://127.0.0.1:8000/mcp"
```

Add `--apply` to write. The helper backs up an existing file, preserves unrelated text/comments, validates TOML,
and refuses conflicting definitions. Identical entries remain unchanged. It checks only the selected file;
inspect other config scopes and installed connectors for duplicates. Edit an existing entry deliberately when
changing its port. Configs with custom ACLs/extended attributes should be merged manually.

**User configuration:** alternatively use Codex's own writer:

```sh
codex mcp add unreal-mcp --url http://127.0.0.1:8000/mcp
```

This writes user configuration. Do not also register a duplicate project connection or proxy for the same editor.
With multiple editors, identify the intended instance and use distinct endpoints with appropriate project scope.

## Verify

`codex mcp list` proves configuration, not live access. With the intended MCP server ready and its process identity
verified, start a fresh target-project chat:

> Use $unreal-mcp to inspect the current level and list a few actors without modifying the project.

The skill uses `list_toolsets → describe_toolset → call_tool`, or advertised native tools when search mode is off.
Check the returned project/editor information before changes. Asset creation, saving, and readback after restart
are separate evidence levels.

See [setup](skills/unreal-mcp/references/setup.md) and [operations](skills/unreal-mcp/references/operations.md).
Proxy automation is outside v0.1: do not pass TOML to the upstream proxy's `--mcp-json` installer.
The core plugin needs no Bash; [Python session context](docs/OPTIONAL_HOOK.md) is an explicit optional setup.

## Develop and package

Use a Git checkout for development (development tools/tests are excluded from the ZIP).
Create a virtual environment. Run validation and packaging directly; execute the authored test suite only when
the current project's test-execution policy permits it:

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_plugin.py
python -m unittest discover -s tests -v
python scripts/package_plugin.py
```

The deterministic ZIP under `dist/` can be extracted and registered as a local marketplace. It contains skills,
manifests, docs and helpers; it excludes Git, virtual environments, tests and raw editor logs.
The inherited CI workflow is configured for Windows/Linux with Python 3.11/3.14. This states its configuration,
not a claim that this fork's CI or authored tests have passed.

The optional [sandbox runner](docs/SANDBOX_VALIDATION.md) starts and cleans up an explicitly selected independent
Windows UE project. It does not build native code, execute authored tests, install plugins, or write Codex settings.

See the [historical Idris implementation plan](docs/MIGRATION_PLAN.zh-CN.md), [historical validation record](docs/VALIDATION.md), and
[upstream maintenance notes](UPSTREAM.md). Public plugin-directory submission is a separate follow-up;
a GitHub fork is not a directory listing.

## License and live access

[MIT](LICENSE), including Epic Games' original notice. External UE code/binaries retain their own terms.
MCP tools can change live objects and files. Keep the server on loopback, confirm the intended project, and keep
a recovery point for bulk changes. Installation does not require bypassing Codex permissions.
