---
name: as-integration-tests
description: Author, investigate, and validate Hazelight Unreal AngelScript integration tests involving PIE worlds, actors, possession, timers, movement, abilities, or multi-frame latent checks. Use for IntegrationTest_ and ComplexIntegrationTest_ functions and choosing integration versus unit coverage; exclude pure logic that needs no world lifecycle.
---

# AngelScript integration tests

Read the target project's test policy and existing integration tests before selecting paths, maps, runners or execution settings. This skill has no dependency on a particular game's test harness, asset catalog, gameplay modules or map.

## Choose the correct boundary

Use a unit test for deterministic calculations and transient state that does not need a running world. Use an integration test when the contract depends on BeginPlay, possession, map loading, world ticks, latent timers, physics, animation, input or replicated gameplay.

Locate the installed AngelScript test implementation and working examples to confirm entrypoint signatures, latent APIs and supported network mode. Common entrypoints are global `IntegrationTest_<Name>(FIntegrationTest& T)` and `ComplexIntegrationTest_<Name>(FIntegrationTest& T)`. A corresponding `<TestName>_GetMapName()` may supply a map; verify its signature in the target engine.

Prefer the project's established test location and naming. For a new isolated fixture, use an owned minimal map and default engine gameplay classes unless the feature itself requires more. Avoid loading a production HUD, gameplay subsystem or content catalog solely for convenience.

## Build meaningful latent checks

- Give each command a bounded timeout appropriate to the operation. Poll observable readiness instead of sleeping a fixed number of frames and assuming success.
- A latent `Update()` returning `false` normally means it is still waiting. Returning `true` ends the command; record an assertion or failure first if the completed state violates the contract.
- Obtain the active test through the supported latent-command API after registration. Keep a concise status description so a timeout reports the missing condition.
- Validate UObject references before dereferencing them. Do not retain objects across map teardown unnecessarily.
- Start on the required map instead of changing maps midway through a scenario unless map travel is what the scenario verifies.
- Own and clean up only the fixture actors, assets and modified settings. Make repeated execution independent of prior runs.

Assertions should cover observable outcomes, meaningful failure cases and boundary conditions. Avoid assertions that mirror internal call order or freeze unrelated asset names and total test counts.

## Run and assess

Follow the project's explicit test-execution policy. Author and inspect tests before an execution trigger when required, but do not run them indirectly through an editor tool to bypass that policy. Ordinary source compilation and direct implementation checks remain separate activities.

`AngelscriptTest` commonly executes unit tests rather than PIE integration tests. Discover the installed Unreal Automation selectors and runner capabilities instead of assuming a commandlet filter will select integration tests.

Use the existing project runner when it supports the target project. If it is tied to another game, explain that constraint and use the independently authorized runner rather than renaming or copying the project to satisfy its assumptions. Preserve its process, settings, debugger-port, MCP/Python-server and bind-cache isolation requirements.

Configure standalone versus client/server execution from the intended contract and the installed `AngelscriptTestSettings`. Do not force standalone for a networking test. Use NullRHI only when rendering is irrelevant.

After execution, check that every selected test appears in the completed results. Zero executed tests, a returned job handle or a successful process exit is insufficient. Report failures, missing results, timeouts, deferred coverage and binary freshness separately from successful scenarios.
