# Upstream and maintenance

This community fork preserves Epic's history and adopts one pinned Codex port. It is not an official Epic Games or OpenAI release.

| Role | Repository | Baseline |
| --- | --- | --- |
| `upstream` | [Epic Games original](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin) | `a6aa73ada02a9fb1f5415bec491f9942c519b297` (3.1.1) |
| `port-origin` | [Idris173 Codex port](https://github.com/Idris173/unreal-engine-skills-for-codex-plugin) | `a6c25ac96cea4cdfb93029e31423efd109d90895` |
| `origin` | [coquid fork](https://github.com/coquid/angelscript-unreal-engine-skills-for-codex-plugin) | This repository |

The Idris baseline contains commits `5378fdf` and `a6c25ac` after the Epic baseline. Its history is merged intact.
No content from the mazelines fork is imported. The `create-toolset`, `unreal-mcp`, and `unreal-skill` directories
are unchanged from the pinned Idris tree. The Epic-to-Idris conversion adjusts those workflows for Codex;
this fork does not claim that they are byte-identical to Epic's original files.

This fork changes package identity, documents provenance, adds generic `angelscript-in-unreal`, `as-integration-tests`,
and `emmsui` skills, and supplies an optional independent-project lifecycle helper. The generic instructions and
small demonstration snippets are newly written. Project-specific source, assets, native plugin binaries, settings,
and validation logs are not distributed. Unreal Engine and EmmsUI retain their respective external licenses.
Epic's original [MIT notice](LICENSE) is preserved unchanged.

## Updating from Epic

Keep the three remotes above. Fetch `upstream`, review changes from the recorded Epic baseline, and merge a
reviewed upstream commit on a working branch. Keep the file layout and edit the original skills directly where
Codex requires a change; do not generate duplicate skill trees or introduce an overlay build step.

Resolve only the real Codex adaptation conflicts. Preserve Epic improvements to workflow content, examples,
and references. Preserve the Codex manifests and project-controlled connection setup. Do not restore the
removed `.claude-plugin` or automatic `hooks/` configuration: Codex can discover a conventional hooks file even
when a manifest does not explicitly reference it. Do not add a fixed endpoint or automatic configuration writes.
Review any new upstream script or dependency before adopting it.

The three AngelScript skill directories and sandbox helper are this fork's additions and normally do not overlap
with Epic's paths. A later Idris update is a separate, explicitly reviewed change; do not silently follow its HEAD.
Record new baseline SHAs and resolve license notices when importing updates.

## Validation after a merge

Run the package validator and deterministic packager, inspect the upstream skill diffs, and follow the target
project's policy for authored tests. Repeat direct editor checks when transport, discovery, API assumptions,
asset persistence, or UI behavior changes. Record the exact engine build and native plugin BuildId; a UE version
number alone does not establish compatibility. Keep historical third-party evidence separate from this fork's
[validation record](docs/SANDBOX_VALIDATION.md).
