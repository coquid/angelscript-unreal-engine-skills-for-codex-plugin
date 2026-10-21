---
name: emmsui
description: Build debug overlays, editor utility tabs, or immediate-mode developer interfaces with EmmsUI in Unreal AngelScript. Use for mm namespace widgets, layout, and hot-reload iteration; follow the project's UMG/CommonUI conventions for production game UI.
---

# EmmsUI with AngelScript

Verify that the target project has EmmsUI and a compatible AngelScript engine. Inspect its descriptor, local bindings and bundled examples; this skill distributes guidance, not the EmmsUI implementation or binaries.

EmmsUI maintains UMG widgets behind immediate-mode drawing calls. Store application data between draws and rebuild the desired UI structure inside the supported draw lifecycle. Do not assume every widget is destroyed and recreated on every frame.

## Establish a draw context

An editor utility derived from `UMMEditorUtilityTab` can use its `DrawTab(float DeltaTime)` override. A viewport overlay normally starts with `mm::BeginDrawViewportOverlay(...)` and ends with `mm::EndDraw()`. A `UMMWidget` has its own supported draw lifecycle. Confirm the installed overloads and world-context binding.

Calling `mm::Text()` or `mm::Button()` from an arbitrary Actor Tick without a draw context is not a complete implementation. Keep every explicit Begin/End pair balanced. Some `Within...` helpers manage the next widget automatically; inspect their actual scope rather than adding guessed closing calls.

This independent editor-tab example uses the tab's existing drawing context:

```angelscript
#if EDITOR
class USampleCounterTab : UMMEditorUtilityTab
{
	default TabTitle = "Counter Inspector";
	default Category = "Developer Tools";

	int Counter = 0;

	UFUNCTION(BlueprintOverride)
	void DrawTab(float DeltaTime)
	{
		mm::BeginVerticalBox();
		mm::Text(f"Counter: {Counter}");
		if (mm::Button("Increment"))
		{
			++Counter;
		}
		mm::EndVerticalBox();
	}
}
#endif
```

## Layout and state

- Apply slot alignment, fill and padding before creating the widget they affect.
- Use stable identity/key facilities for repeated or reordered rows when the installed API provides them; index alone can attach state to the wrong item after deletion.
- Do not remove container entries while iterating a list that the UI is reading. Collect the requested edit and apply it after the draw loop.
- Use `mm<UWidgetType>` wrappers for the current draw. Avoid retaining wrappers as long-lived handles; keep stable model data instead.
- For editor views holding world actors, use weak references and handle map teardown. Do not keep an old world alive through an inspector.
- Verify actual helper signatures for text, check boxes, numeric inputs, borders and generic widgets. Defaults and return types can vary between plugin versions.

Keep existing hot reload. Use the project's established retained UMG/CommonUI widgets when shipping UI, complex animation or ownership requirements make them a better fit; combine them with EmmsUI developer panels where useful.

## Verify in a rendered editor

Read compilation and hot-reload diagnostics, open the actual tab/overlay, and exercise its controls. Check updated text, model values, layout and behavior after reopening or hot reload. Screenshots establish visible layout; they do not establish gameplay correctness. NullRHI cannot verify this UI.

Use supported editor/MCP tools for opening tabs, inspecting the widget tree and interaction when available. Preserve unrelated tabs, selections and dirty assets. Report observed UI behavior and any deferred authored tests according to the project's execution policy.
