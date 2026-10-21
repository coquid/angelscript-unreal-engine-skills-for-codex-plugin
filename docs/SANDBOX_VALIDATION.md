# Independent sandbox validation

This is the coquid fork's validation procedure and evidence boundary. The [Idris report](VALIDATION.md) is
historical third-party evidence, not a pass for this fork. Static/package checks and live editor observations are
recorded separately. No universal UE version compatibility is claimed.

## Project boundary

Create an independent content plus AngelScript `.uproject` outside this plugin repository, with its own `Script`,
`Content`, `Config`, `.codex/config.toml`, and `AGENTS.md`. Use existing compatible editor binaries; do not create
project native modules just to validate skills. Enable `Angelscript`, `ModelContextProtocol`, `ToolsetRegistry`,
`EditorToolset`, `AutomationTestToolset`, `SlateInspectorToolset`, `PythonScriptPlugin`, and a project-local EmmsUI.
The AgentSkill APIs are provided by ToolsetRegistry in the inspected engine. Recheck these names in another build.
Do not copy unrelated gameplay modules or assets. The project and its dependency binaries are local validation
inputs, not plugin distribution contents. Compare native plugin BuildIds before starting.

## Clean installation boundary

Build the allowlisted ZIP with `scripts/package_plugin.py` after `scripts/validate_plugin.py` succeeds. Extract it
into a new, empty `dist/local-plugin-<version-or-build>` directory; refuse an existing destination instead of merging
old files. The [README installation commands](../README.md#install-a-clean-distribution-for-one-project) show the
complete preparation. Set the target project's `[marketplaces.<name>].source` to this extracted distribution root.
Its catalog resolves `./` inside the distribution. Do not point the installer at the development repository root.

This distinction affects the actual cache: the inspected native installer recursively copies ordinary source files
and directories without excluding `.git`, `.venv`, `dist`, or `tests`. Its copy implementation is pinned at
[Codex store.rs L736](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/store.rs#L736).
The ZIP allowlist excludes these development files and the external UE project's dependencies. A direct GitHub
marketplace install uses repository contents rather than that ZIP allowlist and is a separate optional route.

Enable this plugin and configure the selected loopback MCP endpoint in the target project's Codex config. Verify
that the native client loads this project's trusted config and sees the intended marketplace. The CLI must run with
the target project as its child process cwd; a desktop project's trust state may not match a standalone CLI's state.
Then perform one official CLI `plugin add` or equivalent native UI/API Install operation. Config-only setup does not
install files: the runtime loads an installed cache copy. After an update, reinstall to refresh that copy.

The inspected installer unconditionally writes this plugin's user enablement after installation, including when
project enablement already exists: [manager.rs L2307](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/manager.rs#L2307).
Obtain authorization for that exception when user configuration must otherwise remain unchanged. For project-only
activation, set only this plugin's user entry to `enabled = false` after installation and retain the target project's
`enabled = true`; preserve every unrelated entry. Do not silently bypass the installer by copying a cache directory.
An authorized isolated client home is an alternative environment, not proof that an existing desktop session loaded
the package. If installation is not authorized, report that boundary without claiming full plugin validation.

Start a fresh target-project chat after installation. Confirm the six skills originate from the intended installed
plugin, its default hooks list is empty, and another project's enablement is unchanged. The runner does not install
the plugin, write Codex settings, or start Codex.

## Explicit lifecycle helper

`scripts/sandbox_runner.py` supports Windows, Python 3.11+, and explicit project, engine, port, and results paths.
The results directory must be inside the selected project's `Saved` directory and outside this plugin repository.
The optional Codex executable argument checks and records its path; it does not run it.

```powershell
$pluginRepo = 'C:\Plugins\angelscript-unreal-engine-skills-for-codex-plugin'
$projectFile = 'C:\Sandbox\SkillValidation\SkillValidation.uproject'
$engineRoot = 'C:\UnrealWorkspace\Engine'
$resultRoot = 'C:\Sandbox\SkillValidation\Saved\SkillValidation'
$codexExe = 'C:\Tools\Codex\codex.exe'
$runnerArgs = @('--project', $projectFile, '--engine', $engineRoot, '--port', '58241', '--results', $resultRoot,
    '--codex-executable', $codexExe)
python "$pluginRepo\scripts\sandbox_runner.py" preflight @runnerArgs
python "$pluginRepo\scripts\sandbox_runner.py" start @runnerArgs --startup-timeout 300
python "$pluginRepo\scripts\sandbox_runner.py" status @runnerArgs
python "$pluginRepo\scripts\sandbox_runner.py" stop @runnerArgs
```

Paths above are placeholders. Keep the shell in the workspace required by its local instructions. The child
editor uses the selected project directory. Startup uses existing binaries and `-Multiprocess`, development AS,
an ephemeral AS debugger port, no bind-cache writes, explicit MCP port, no Python remote execution, and no
automatic MCP startup setting. A lifecycle lock prevents concurrent runner operations. Refuse an occupied port.
The runner records the exact PID, creation time, executable, command line, log paths, and arguments.

Rendered mode is the default for UI validation. `--nullrhi` is suitable for nonvisual direct checks only.
A listening owned PID means `ready_for_mcp_probe`; it is not evidence that tools or skills work. Use the official
native MCP client to inspect the actual project and advertised tool schemas before any mutation. Do not add a
custom proxy, raw MCP client, or Python remote bridge for validation.

Always stop a runner-owned editor after the work, including failed or interrupted runs. `stop` checks its saved
identity before a graceful close and verifies the process and port are released. If a rendered editor cannot close,
resolve any save dialog first; `--force-after-grace` explicitly allows forced termination of that exact owned PID.
NullRHI has no interactive close path and may require the recorded PID cleanup. Never terminate an unrelated editor.

## Direct behavior checks

Use small original project-local examples: an AS actor with a counter and callable mutation, an EmmsUI editor tab
with visible increment/reset actions, a Python ToolsetDefinition with a positive-step contract, and a Python AgentSkill.
Keep created assets under a dedicated `/Game/CodexSkillSandbox` folder. Inspect actual bindings and tool schemas.

1. Verify that a fresh Codex chat sees all six skills, the expected marketplace, and no plugin lifecycle hooks.
2. Through the official MCP tools, identify the project, discover and describe the registered toolsets, and invoke
   the Python tool with normal and rejected inputs. Confirm the AgentSkill's name, description, and instructions.
3. Confirm AS compilation, invoke the actor's behavior, and observe changed properties. Change the method body in the AS file,
   observe successful hot reload, and verify that the same invocation now produces the intended different result.
   A marker-only change confirms source replacement but does not prove updated method behavior.
4. Create a small fixture asset or map through existing editor APIs, save only owned fixture packages, and check
   properties after unload/reload or a controlled editor restart. Creation alone does not prove persistence.
5. Open the EmmsUI tab in a rendered editor. Use SlateInspector tools to observe its visible text and interact with
   Increment and Reset; capture visual evidence. NullRHI, compilation, or a log line alone cannot prove UI behavior.
6. Record cleanup and any missing capabilities. Add an authored AS integration scenario using the target engine's
   real harness when required; do not confuse writing or discovering it with executing it.

Respect the target project's test gate. In the initial local validation workspace, authored Unit/Integration and
Automation cases remain unexecuted until the user requests `!test`. The runner never runs those cases. Direct
compilation, MCP, PIE behavior, UI, and save/reload checks are separate implementation checks. A project-specific
runner with hardcoded modules/assets must not be made to accept this independent project by renaming files.

## Current evidence

Direct implementation observations, 2026-10-21; complete plugin-installation validation remains pending. Package validation, all six skill metadata checks, Python syntax compilation,
and ZIP boundary inspection passed. The original three UE skills remain identical to the pinned Idris baseline.
The independent project has no native project modules, and its local native plugin BuildId matches the engine:
`3c6a4263-8d5a-4b20-a676-deccedf5fce2`.

The separate validation chat manually read the skill source files and exercised the editor through its native
MCP connection. **The six packaged skills were not automatically loaded as an installed Codex plugin.** The first
chat had project MCP access but no matching plugin cache. Clean distribution staging and project source configuration
are prepared; official installation awaits authorization for its initial user-setting write. These editor observations
therefore validate the demonstrated workflows, not native discovery or activation of the six-skill package.
The read-only native app-server diagnostic loaded the clean staging marketplace with zero load errors and reported
this plugin as `enabled = true`, `installed = false`, with zero matching loaded skills. The unrelated existing
project plugin was disabled in this target's effective configuration. These observations are preserved in
`plugin-installation-boundary.json`; no installation or user-config write was performed by that diagnostic.

Observed direct implementation checks:

- Native MCP tool discovery, schema inspection, and calls succeeded for the selected independent project.
- The Python Toolset returned `10` for `7 + 3`; the Python AgentSkill was registered and retrieved.
- The AS actor counter changed `1 -> 4`. After changing the method body to apply `Amount * 2` and hot reloading,
  the same actor changed `4 -> 10`, demonstrating updated method behavior.
- In PIE, the actor changed `23 -> 31`; the editor-world actor remained `23`.
- In a rendered editor, actual EmmsUI Increment button interactions changed the displayed counter `0 -> 1 -> 2`,
  and Reset returned it to `0`. Slate observations and screenshots captured the UI.
- After saving and restarting into a different editor PID (`105112 -> 119572`), the fixture map's counter `23`
  and marker, and the saved Agent Skill asset's revision-2 instructions, were read back successfully.

Evidence remains outside this plugin repository in the independent project's `Saved/SkillValidation/`:
`native-mcp-evidence.json`, `emmsui-increment.png`, `emmsui-reset.png`, editor logs, and process-identity records.
The completed `VALIDATION_REPORT.md` and `VALIDATION_REPORT.json` consolidate these observations. Final cleanup
is recorded in `cleanup-verification.json`: the latest state is `stopped`, PID `119572` and all tracked sandbox
editor processes are absent, and neither port `58241` nor `58240` has a listener. The final shutdown was graceful;
no forced termination was used. The coordinator independently confirmed the process and port results.

The initial shutdown exposed a CIM race as process identity fields became empty during exit. The runner now allows
bounded observation of the same PID/creation time during teardown, while requiring complete identity before control.
The corrected graceful shutdown path was exercised successfully. A further startup-failure fallback now retains the
original error, records cleanup failures separately, and uses only its own Popen handle if CIM-based cleanup fails.
That fallback has syntax/static checks and authored regression coverage; its exceptional branch has not been exercised.

The engine also automatically ran its built-in Smoke checks during startup and logged `LogAutomationTest` errors.
This is an observed engine-startup issue, not an intentionally selected authored test run or a clean startup-test pass.
Keep these errors in the final report rather than hiding them behind successful direct behavior checks.

Project-local `Script/Tests/CodexProbe_UnitTest.as` and `CodexProbe_IntegrationTest.as` were authored and compiled,
without invoking their test functions. The inspected engine's `DiscoverTests.cpp:171` discovers unit functions with
`Test_`, not `UnitTest_`; the unit entrypoint is `Test_CodexProbeCounterState`. The integration entrypoint is
`IntegrationTest_CodexProbePIE`. Unit execution on hot reload was explicitly disabled before adding these files.
`Content/Python/tests/test_codex_sandbox_tools.py` and the plugin repository's Python regressions were authored but
not executed. Do not infer their validity or results from the direct editor checks.

Unit/Integration Test 미실행 (!test 요청 전). No project-authored Unit/Integration or Python unittest suite was
executed for these changes. Engine-startup Smoke execution above is a separate observed exception. The existing CI
workflow is preserved; its configuration is not evidence of a successful run.
