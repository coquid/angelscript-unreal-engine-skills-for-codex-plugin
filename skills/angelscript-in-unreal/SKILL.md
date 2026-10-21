---
name: angelscript-in-unreal
description: Find and use Unreal Engine APIs in a Hazelight AngelScript project, edit .as gameplay code, and verify compilation or runtime behavior. Use for AngelScript bindings, engine extensions, delegates, subsystems, and source iteration; exclude unrelated scripting languages.
---

# AngelScript in Unreal Engine

Start with the target project's instructions, `.uproject`, engine location and enabled plugins. An empty EngineAssociation can indicate a source engine; do not assume a launcher installation or a fixed sibling directory.

## Find the actual API

1. Search the project's `Script/` and nearby working `.as` implementations first.
2. Search the installed AngelScript plugin's bindings, mixins and extensions. Locate its descriptor instead of assuming a capitalization or directory layout. Optional GAS and Enhanced Input integrations have separate plugins in some builds.
3. Inspect Blueprint-callable C++ declarations in the target engine and plugins. Blueprint exposure is a useful starting point, but binding exclusions, mixins, overloads, hidden world-context arguments and engine versions can change the callable AngelScript signature.
4. Consult version-matched official documentation only when local sources leave a real gap. Do not invent local documentation or example folders that the package does not contain.

Exclude generated/cache trees from broad searches. Search a specific generated binding or stub file only when it is the relevant source of truth.

## Translation and lifecycle

- UObject references normally use `UObject Value`, member access uses `.`, and names use `n"Name"`.
- Bind delegates to a reflected callback with the project's supported delegate API and a function-name literal; do not translate C++ member-function pointers literally.
- Follow nearby cast, reference, container and math syntax. Do not assume every C++ template or pure C++ function is bound.
- Check the installed script-specific subsystem bases before deriving from a native subsystem. For example, a build may provide `UScriptGameInstanceSubsystem` and `Subsystem::GetGameInstanceSubsystem()`.
- Follow project reflection, lifetime and component conventions. Mark callback functions and exposed members as required by the actual binding. Keep increment expressions separate when the script compiler warns about side effects.
- Edit `.as` files directly; use supported editor tools for `.uasset` and `.umap` files. Keep the existing editor and hot reload when possible.

A minimal independent actor illustrates script-owned state without a native game module:

```angelscript
class ASampleCounterActor : AActor
{
	UPROPERTY(DefaultComponent, RootComponent)
	USceneComponent SceneRoot;

	UPROPERTY(EditAnywhere)
	int Counter = 0;

	UFUNCTION(BlueprintCallable)
	int AddToCounter(int Amount)
	{
		Counter += Amount;
		return Counter;
	}
}
```

Confirm the macros and types in the target build before adapting an example.

## Verify the change

Use current compatible editor binaries for AngelScript-only work. Script edits alone are not a reason to rebuild native modules or the engine. If binaries cannot load, report the concrete cause before expanding into a build.

Read compiler/hot-reload diagnostics and then exercise the changed behavior at the appropriate level. Compiled source, live property readback, saved/reloaded assets and gameplay behavior are different evidence. Re-query state after a timeout before retrying a mutation.

Follow the project's runner and execution policy for authored Unit/Integration/Automation tests. An explicit test trigger, where required by that project, does not prohibit ordinary compilation and direct behavior checks. Do not invoke registered tests through another entry point to bypass that policy.

The Hazelight `AngelscriptTest` commandlet commonly runs the unit-test suite as well as compilation; do not use it as a compile-only check or assume an arbitrary per-test CLI filter works. Inspect the installed commandlet for supported options and exit codes. World/PIE/latent scenarios require integration or gameplay verification rather than a unit-test result alone.

For separate validation processes, preserve project-specific settings isolation, distinct or ephemeral debugger ports, disabled unsolicited remote servers and bind-cache write protection where supported. Record processes that you start and clean them up without controlling unrelated editors.

Report files changed, observed compilation/runtime results, tests actually executed and anything still unverified.
