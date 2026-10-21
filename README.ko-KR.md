# AngelScript Unreal Engine Skills for Codex

[English](README.md)

> 영문 원문이 유지보수 기준이며, 번역 기준 커밋은 `ae6b0c5886db4ea3ca1800b444cfdcd960c8d8e0`입니다.

[Epic Games의 Unreal Engine 스킬](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin)을 Codex에 맞게 조정한 커뮤니티 프로젝트입니다.
[Idris173의 고정된 Codex 포팅 버전](https://github.com/Idris173/unreal-engine-skills-for-codex-plugin/commit/a6c25ac96cea4cdfb93029e31423efd109d90895)을 바탕으로
범용 AngelScript 스킬 세 개를 추가했습니다. 포팅된 UE 스킬 디렉터리 세 개는 해당 커밋의 상태를 그대로 유지합니다.
Epic Games나 OpenAI의 공식 배포판이 아닙니다. 원본 MIT 저작권 고지와 Git 이력을 보존합니다.

이 플러그인은 Codex가 **Unreal Engine의 공식 MCP 서버와 ToolsetRegistry**를 사용하는 방법을 안내합니다.
Unreal Engine, 엔진 측 플러그인, 대체 MCP 서버는 포함하지 않습니다.

| 스킬 | 용도 |
| --- | --- |
| `unreal-mcp` | 실행 중인 Unreal Editor 연결·조회·조작 및 연결 문제 진단 |
| `create-toolset` | ToolsetRegistry에 등록되는 C++/Python 도구 작성 및 확장 |
| `unreal-skill` | Unreal 에디터 내부 Agent Skill 작성(Python 클래스 또는 UAsset) |
| `angelscript-in-unreal` | 실제 AngelScript 바인딩 탐색 및 안전한 UE 게임플레이 구현 |
| `as-integration-tests` | 대상 프로젝트의 테스트 실행 환경을 사용한 월드/PIE/latent AngelScript 테스트 설계 |
| `emmsui` | 설치된 EmmsUI 플러그인을 사용한 AngelScript 디버그/에디터 UI 구현 및 검증 |

## 요구 사항

- Skills와 MCP를 지원하는 로컬 Codex 클라이언트. 마켓플레이스 설치에는 플러그인 지원도 필요합니다.
- `ModelContextProtocol`, `ToolsetRegistry`와 작업에 필요한 개별 툴셋 플러그인이 포함된 엔진.
- AngelScript 스킬에는 호환되는 AngelScript 엔진 포크가 필요하며, EmmsUI 안내를 따르려면 해당 별도 플러그인이 필요합니다.
- 실행 중인 에디터를 조작하려면 에디터와 MCP 서버가 실행 중이어야 합니다.
- 선택적 설정 도우미와 개발 검증에는 Python **3.11+**가 필요합니다. MCP를 수동으로 설정할 때는 Python이 필요하지 않습니다.

모든 환경에 공통으로 적용되는 최소 UE 버전은 검증되지 않았습니다. [이 포크의 검증 절차와 상태](docs/SANDBOX_VALIDATION.ko-KR.md)를 참고하세요.
[Idris 검증 기록](docs/VALIDATION.ko-KR.md)은 제3자의 과거 검증 근거이며, 이 포크의 검증 결과가 아닙니다.

<a id="install-a-clean-distribution-for-one-project"></a>

## 한 프로젝트에 정리된 배포본 설치

개발 체크아웃과 설치 원본을 분리하세요. 확인한 Codex 로컬 설치 프로그램은 선택한 원본의 일반 파일과 디렉터리를 재귀적으로 복사하며,
`.git`, `.venv`, `dist`, `tests`를 제외하지 않습니다. 따라서 개발 체크아웃에서 직접 설치하면 개발용 데이터까지 플러그인 캐시에 복사됩니다.
[고정된 커밋의 복사 구현](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/store.rs#L736)을 참고하세요.
패키지 허용 목록으로 ZIP을 만든 다음, 비어 있는 새 배포 디렉터리에 압축을 푸세요.

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

패키지를 업데이트할 때마다 새로운 `local-plugin-<version-or-build>` 디렉터리를 사용하세요. ZIP에는 스킬 여섯 개,
매니페스트, 문서, 런타임 도우미가 포함되며, 버전 관리 내부 파일, 가상환경, 테스트, 외부 UE 프로젝트 의존성은 제외됩니다.
셸의 작업 디렉터리는 워크스페이스 지침에서 요구하는 위치를 유지하세요.

아래 내용을 대상 프로젝트의 `.codex/config.toml`에 병합하고, 배포 경로와 MCP 포트를 바꾸세요.
`source`는 개발 체크아웃이 아니라 압축을 푼 배포본을 가리켜야 합니다. 포함된 카탈로그는 `./`를 사용하므로 배포본 루트 안에 머뭅니다.

```toml
[marketplaces.angelscript-unreal-engine-skills-for-codex]
source_type = "local"
source = 'C:\Plugins\angelscript-unreal-engine-skills-for-codex-plugin\dist\local-plugin-0.1.0-build1'

[plugins."angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex"]
enabled = true

[mcp_servers.unreal-mcp]
url = "http://127.0.0.1:58241/mcp"
```

**실제 설치가 필요합니다.** 이 설정은 원본을 선택하고 플러그인을 활성화할 뿐, 파일을 설치하지는 않습니다.
Codex는 원본 디렉터리가 아니라 설치된 캐시 복사본을 불러옵니다. 프로젝트를 신뢰하도록 설정한 다음,
대상 프로젝트를 자식 프로세스의 작업 디렉터리로 지정하여 아래 CLI 명령을 실행하세요. 목록에 마켓플레이스가 없다면
설치 전에 설정 및 신뢰 상태가 인식되지 않는 문제를 해결하세요. 빈 목록을 검증 통과로 취급하지 마세요.

```sh
codex plugin list --marketplace angelscript-unreal-engine-skills-for-codex --json
codex plugin add angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex --json
```

데스크톱의 네이티브 UI/API 설치도 같은 설치 작업입니다. 데스크톱 마켓플레이스의 표시 이름은 **AngelScript Unreal Codex**입니다.
공식 설치 프로그램과 UI는 프로젝트에서 이미 플러그인을 활성화했더라도 사용자 수준의 활성화 설정을 쓸 수 있습니다.
워크스페이스 지침이 요구한다면 최초 사용자 설정 쓰기에 대한 승인을 받으세요. 대상 프로젝트에서만 활성화하려면
설치 후 `~/.codex/config.toml`에 있는 이 플러그인의 사용자 항목을 `enabled = false`로 설정하고,
대상 프로젝트 설정의 `enabled = true`는 유지하세요.

```toml
# User config: disabled by default; the target project overrides this to true.
[plugins."angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex"]
enabled = false
```

관련 없는 사용자 설정과 다른 플러그인 항목은 보존하세요. 사용자 설정을 변경하면 안 되는 경우에는 설치 작업 전에 멈추고
그 제약을 해결하세요. 설정만 추가한 상태는 설치 완료가 아닙니다. 별도로 승인받은 격리된 클라이언트 홈에서는
설치를 따로 검증할 수 있지만, 그것으로 기존 데스크톱 세션에서의 로드를 입증할 수는 없습니다.
[공식 로컬 마켓플레이스 동작](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work)과
[항상 수행되는 사용자 활성화 설정 쓰기](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/manager.rs#L2307)를 참고하세요.

설치 후에는 대상 에디터와 MCP 서버를 먼저 시작하세요. 수신 대기 포트가 기록된 에디터 PID, 실행 파일, 프로젝트의 것인지 확인한 다음,
신뢰 설정이 된 대상 프로젝트에서 새 Codex 채팅을 시작하세요. 관측한 클라이언트에서는 에디터가 꺼진 상태로 채팅을 시작하면
스킬 여섯 개는 로드되었지만 최초 MCP 핸드셰이크는 실패했습니다. 나중에 서버를 시작한 것만으로 기존 세션의 재연결이 확인되지는 않았습니다.
실제 스킬 항목 여섯 개가 모두 제공되고, 플러그인 수명주기 훅이 0개이며, 네이티브 MCP 호출이 성공하는지 확인하세요.
원본을 업데이트한 뒤에는 다시 설치하여 설치 캐시를 갱신하세요. 원본을 수정하거나 경로만 바꾼 것으로는 캐시 갱신이 입증되지 않습니다.
같은 스킬의 독립된 복사본을 중복으로 추가하지 마세요.

### 선택 사항: 저장소 원본에서 설치

이를 지원하는 CLI에서는 GitHub 저장소를 직접 등록할 수도 있습니다.

```sh
codex plugin marketplace add coquid/angelscript-unreal-engine-skills-for-codex-plugin
codex plugin add angelscript-unreal-engine-skills-for-codex@angelscript-unreal-engine-skills-for-codex
```

이 방법은 사용자 범위에 등록하고, ZIP 허용 목록을 적용하지 않은 저장소 원본을 설치합니다. 해당 체크아웃의 개발용 파일이
캐시에 복사될 수 있으며, 로컬 체크아웃에는 `.venv`, `.git`, 이전 출력물도 있을 수 있습니다.
그 원본과 더 넓은 설정 범위를 사용하려는 경우에만 이 방법을 선택하세요. 검증과 배포에는 위의 정리된 배포본 설치 절차를 권장합니다.

패키지는 이식 가능한 `plugin.json`과 호환성 매니페스트 `.codex-plugin/plugin.json`을 제공합니다.
고정된 MCP 엔드포인트를 자동 등록하거나 수명주기 훅을 실행하지 **않습니다**.

## 에디터 연결

프로젝트 에디터에서 `ModelContextProtocol`, `ToolsetRegistry`와 필요한 개별 툴셋을 활성화하고, 요청받으면 재시작하세요.
소규모 검증 프로젝트에는 `EditorToolset`, `AutomationTestToolset`, `SlateInspectorToolset`을 사용하고, 나머지는 필요할 때만 활성화하세요.
UE 콘솔에서 `ModelContextProtocol.StartServer`를 실행하세요. 기본 주소는 `http://127.0.0.1:8000/mcp`입니다.
포트가 사용 중이라면 `ModelContextProtocol.StartServer <free-port>`를 사용하세요.
기존 연결을 확인한 뒤 설정 방법을 **하나만** 선택하세요.

**권장하는 독립 프로젝트 설정:** 위에 명시한 프로젝트 설정 파일에 MCP 항목을 작성하거나 병합하세요.
또는 선택적 도우미 `configure_mcp.py`로 정확히 그 파일에 적용될 변경을 미리 확인하세요.
이 방법은 엔진 생성기가 사용하는 소스 워크스페이스 위치에 의존하지 않습니다.

**대안인 엔진 생성기:** 출력 위치를 확인한 경우에만 UE 콘솔에서 다음 명령을 실행하세요.

```text
ModelContextProtocol.GenerateClientConfig Codex
```

설치형 빌드는 `.uproject` 옆에 `.codex/config.toml`을 작성하고, 소스 빌드는 `Engine/` 옆의 워크스페이스 루트에 작성합니다.
따라서 소스 빌드의 출력 위치는 독립된 샌드박스 프로젝트 밖일 수 있습니다. Codex는 신뢰하는 프로젝트의 설정만 불러옵니다.
생성기는 기존 TOML 덮어쓰기를 거부합니다. 이 체크아웃에서 추가 내용을 미리 확인하려면 다음 명령을 사용하세요.

```powershell
python scripts/configure_mcp.py --config "F:\MyProject\.codex\config.toml" --url "http://127.0.0.1:8000/mcp"
```

실제로 쓰려면 `--apply`를 추가하세요. 이 도우미는 기존 파일을 백업하고, 관련 없는 텍스트와 주석을 보존하며,
TOML을 검증하고 충돌하는 정의를 거부합니다. 동일한 항목은 변경하지 않습니다. 선택한 파일만 검사하므로
다른 설정 범위와 설치된 커넥터에 중복이 있는지도 확인하세요. 포트를 바꿀 때는 기존 항목을 의도적으로 수정하세요.
사용자 지정 ACL이나 확장 속성이 있는 설정 파일은 수동으로 병합해야 합니다.

**사용자 설정:** 대신 Codex 자체 설정 명령을 사용할 수도 있습니다.

```sh
codex mcp add unreal-mcp --url http://127.0.0.1:8000/mcp
```

이 명령은 사용자 설정을 작성합니다. 같은 에디터에 대한 프로젝트 연결이나 프록시를 중복 등록하지 마세요.
여러 에디터가 있다면 대상 인스턴스를 식별하고, 적절한 프로젝트 범위에서 서로 다른 엔드포인트를 사용하세요.

## 검증

`codex mcp list`로 확인되는 것은 설정이며, 실제 접근 가능 여부는 아닙니다. 대상 MCP 서버가 준비되었고
프로세스 신원을 확인한 상태에서 대상 프로젝트의 새 채팅을 시작하세요.

> $unreal-mcp를 사용하여 프로젝트를 변경하지 않고 현재 레벨을 확인하고 액터 몇 개를 나열하세요.

스킬은 `list_toolsets → describe_toolset → call_tool`을 사용하며, 검색 모드가 꺼져 있으면 제공된 네이티브 도구를 사용합니다.
변경 전에 반환된 프로젝트 및 에디터 정보를 확인하세요. 에셋 생성, 저장, 재시작 후 다시 읽기는 각각 별도로 확인해야 하는 검증 단계입니다.

[설정](skills/unreal-mcp/references/setup.md)과 [운영](skills/unreal-mcp/references/operations.md)을 참고하세요.
프록시 자동화는 v0.1 범위 밖입니다. 업스트림 프록시의 `--mcp-json` 설치 프로그램에 TOML을 전달하지 마세요.
핵심 플러그인에는 Bash가 필요하지 않습니다. [Python 세션 컨텍스트](docs/OPTIONAL_HOOK.ko-KR.md)는 명시적으로 선택하는 추가 설정입니다.

## 개발과 패키징

개발에는 Git 체크아웃을 사용하세요. 개발 도구와 테스트는 ZIP에서 제외됩니다.
가상환경을 만들고 검증과 패키징을 직접 실행하세요. 작성된 테스트 모음은 현재 프로젝트의 테스트 실행 정책이 허용하는 경우에만 실행하세요.

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_plugin.py
python -m unittest discover -s tests -v
python scripts/package_plugin.py
```

`dist/` 아래의 재현 가능한 ZIP은 압축을 풀어 로컬 마켓플레이스로 등록할 수 있습니다. 스킬, 매니페스트, 문서, 도우미를 포함하고,
Git, 가상환경, 테스트, 원시 에디터 로그는 제외합니다.
상속받은 CI 워크플로는 Windows/Linux와 Python 3.11/3.14를 대상으로 설정되어 있습니다. 이는 설정에 대한 설명이며,
이 포크의 CI나 작성된 테스트가 통과했다는 뜻은 아닙니다.

선택적 [샌드박스 실행 도우미](docs/SANDBOX_VALIDATION.ko-KR.md)는 명시적으로 선택한 독립 Windows UE 프로젝트를 시작하고 종료·정리합니다.
네이티브 코드를 빌드하거나, 작성된 테스트를 실행하거나, 플러그인을 설치하거나, Codex 설정을 작성하지 않습니다.

[Idris의 과거 검증 기록](docs/VALIDATION.ko-KR.md)과 [업스트림 유지보수 안내](UPSTREAM.ko-KR.md)를 참고하세요.
공개 플러그인 디렉터리 등록 신청은 별도 후속 작업입니다. GitHub 포크를 만드는 것만으로 디렉터리에 등록되지는 않습니다.

## 라이선스와 실행 중인 에디터 접근

Epic Games의 원본 고지를 포함한 [MIT](LICENSE) 라이선스를 따릅니다. 외부 UE 코드와 바이너리에는 각각의 이용 조건이 적용됩니다.
MCP 도구는 실행 중인 객체와 파일을 변경할 수 있습니다. 서버는 루프백에서만 사용하고, 대상 프로젝트를 확인하며,
대량 변경 전에는 복구할 수 있는 지점을 확보하세요. 설치를 위해 Codex 권한을 우회할 필요는 없습니다.
