# 독립 Sandbox 검증

[English](SANDBOX_VALIDATION.md)

> 영문 원문이 유지보수 기준이며, 번역 기준 커밋은 `ae6b0c5886db4ea3ca1800b444cfdcd960c8d8e0`입니다.

이 문서는 coquid 포크의 검증 절차와 근거의 적용 범위를 설명합니다. [Idris 보고서](VALIDATION.ko-KR.md)는
제3자가 과거에 기록한 근거이며, 이 포크가 검증을 통과했다는 의미는 아닙니다. 정적 검사·패키지 검사와 실제 에디터에서
관측한 결과를 구분하여 기록합니다. 모든 UE 버전과 호환된다고 주장하지 않습니다.

## 프로젝트 범위

이 플러그인 저장소 외부에 콘텐츠와 AngelScript로 구성된 독립적인 `.uproject`를 만들고, 자체 `Script`,
`Content`, `Config`, `.codex/config.toml`, `AGENTS.md`를 둡니다. 기존의 호환되는 에디터 바이너리를 사용하며,
스킬 검증만을 위해 프로젝트 네이티브 모듈을 만들지 않습니다. `Angelscript`, `ModelContextProtocol`, `ToolsetRegistry`,
`EditorToolset`, `AutomationTestToolset`, `SlateInspectorToolset`, `PythonScriptPlugin` 및 프로젝트 로컬 EmmsUI를 활성화합니다.
확인한 엔진에서는 ToolsetRegistry가 AgentSkill API를 제공합니다. 다른 빌드에서는 이 이름들을 다시 확인해야 합니다.
관련 없는 게임플레이 모듈이나 에셋을 복사하지 않습니다. 프로젝트와 해당 종속성 바이너리는 로컬 검증 입력이며,
플러그인 배포본에 포함되는 내용이 아닙니다. 시작 전에 네이티브 플러그인의 BuildId를 비교합니다.

## 정리된 배포본의 설치 범위

`scripts/validate_plugin.py`가 성공한 후 `scripts/package_plugin.py`로 허용 목록 기반 ZIP을 만듭니다. 이를 새롭고 비어 있는
`dist/local-plugin-<version-or-build>` 디렉터리에 풉니다. 대상이 이미 존재하면 이전 파일과 병합하지 말고 중단합니다.
전체 준비 과정은 [README 설치 명령](../README.ko-KR.md#install-a-clean-distribution-for-one-project)에 나와 있습니다.
대상 프로젝트의 `[marketplaces.<name>].source`를 이 압축 해제된 배포본의 루트로 설정합니다.
배포본 안의 카탈로그는 `./`를 배포본 내부에서 해석합니다. 설치 프로그램이 개발 저장소 루트를 가리키도록 설정하지 않습니다.

이 구분은 실제 캐시에 영향을 줍니다. 확인한 네이티브 설치 프로그램은 `.git`, `.venv`, `dist`, `tests`를 제외하지 않고
일반 파일과 디렉터리를 재귀적으로 복사합니다. 확인한 복사 구현은
[Codex store.rs L736](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/store.rs#L736)에
커밋으로 고정되어 있습니다. ZIP 허용 목록은 이러한 개발 파일과 외부 UE 프로젝트의 종속성을 제외합니다. GitHub marketplace에서
직접 설치하면 해당 ZIP 허용 목록이 아닌 저장소 내용을 사용하며, 이는 별도의 선택적 설치 경로입니다.

대상 프로젝트의 Codex 설정에서 이 플러그인을 활성화하고 선택한 루프백 MCP 엔드포인트를 설정합니다. 네이티브 클라이언트가
이 프로젝트의 신뢰된 설정을 로드하고 의도한 marketplace를 인식하는지 확인합니다. CLI는 자식 프로세스의 cwd를 대상 프로젝트로
설정하여 실행해야 합니다. 데스크톱 프로젝트의 신뢰 상태가 독립 실행 CLI의 상태와 같지 않을 수 있습니다.
그런 다음 공식 CLI `plugin add` 또는 이에 해당하는 네이티브 UI/API Install 작업을 한 번 수행합니다. 설정만으로는 파일이
설치되지 않습니다. 런타임은 설치된 캐시 사본을 로드합니다. 업데이트 후에는 다시 설치하여 해당 사본을 갱신합니다.

확인한 설치 프로그램은 프로젝트 활성화 설정이 이미 있는 경우에도 설치 후 이 플러그인의 사용자 활성화 설정을 무조건 기록합니다.
구현은 [manager.rs L2307](https://github.com/openai/codex/blob/c7234c1174b27d9c55199fba0d546dc27d1b0415/codex-rs/core-plugins/src/manager.rs#L2307)에
있습니다. 그 외 사용자 설정을 유지해야 하는 상황에서는 이 예외에 대한 승인을 받습니다. 프로젝트에서만 활성화하려면 설치 후
이 플러그인의 사용자 항목만 `enabled = false`로 설정하고 대상 프로젝트의 `enabled = true`를 유지합니다.
관련 없는 모든 항목을 보존합니다. 캐시 디렉터리를 복사하는 방식으로 설치 절차를 임의로 우회하지 않습니다.
승인받은 격리된 클라이언트 홈은 대체 환경일 뿐, 기존 데스크톱 세션이 패키지를 로드했다는 근거가 아닙니다.
설치가 승인되지 않았다면 전체 플러그인 검증이 완료되었다고 주장하지 말고 그 제한을 보고합니다.

설치 후 선택한 에디터를 시작하고 MCP 리스너가 준비될 때까지 기다립니다. 새 대상 프로젝트 채팅을 시작하기 전에 PID, 생성 시각,
실행 파일, 프로젝트 명령줄, 포트 소유권을 확인합니다. 관측한 클라이언트는 채팅 시작 시 에디터가 꺼져 있을 때 스킬은 로드했지만
초기 MCP 핸드셰이크에 실패했습니다. 이후 서버를 시작한 것만으로는 재연결이 입증되지 않았습니다. 스킬 6개 모두가 설치된
플러그인에서 왔고, 기본 훅 목록이 비어 있으며, 다른 프로젝트의 활성화 설정이 유지되었고, 네이티브 MCP 호출이 성공하는지 확인합니다.
실행 도우미는 플러그인을 설치하거나 Codex 설정을 쓰거나 Codex를 시작하지 않습니다.

## 명시적인 생명주기 도우미

`scripts/sandbox_runner.py`는 Windows, Python 3.11+ 및 명시적으로 지정한 프로젝트·엔진·포트·결과 경로를 지원합니다.
결과 디렉터리는 선택한 프로젝트의 `Saved` 디렉터리 안에 있어야 하며 이 플러그인 저장소 외부여야 합니다.
선택적인 Codex 실행 파일 인자는 경로를 확인하고 기록할 뿐, 실행 파일을 실행하지 않습니다.

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

위 경로들은 예시입니다. 셸은 로컬 지침에서 요구하는 작업공간에 유지합니다. 자식 에디터 프로세스는 선택한 프로젝트 디렉터리를
사용합니다. 시작 시 기존 바이너리와 `-Multiprocess`, 개발용 AS, 임시 AS 디버거 포트를 사용하고, bind cache 쓰기를 금지하며,
MCP 포트를 명시합니다. Python remote execution과 자동 MCP 시작 설정은 사용하지 않습니다.
생명주기 잠금으로 실행 도우미의 동시 작업을 방지합니다. 포트가 사용 중이면 중단합니다.
실행 도우미는 정확한 PID, 생성 시각, 실행 파일, 명령줄, 로그 경로, 인자를 기록합니다.

UI 검증에는 화면을 렌더링하는 모드가 기본입니다. `--nullrhi`는 시각적 확인이 필요 없는 직접 검사에만 적합합니다.
도우미가 소유한 PID가 포트를 수신하고 있다는 것은 `ready_for_mcp_probe` 상태라는 뜻이며, 도구나 스킬이 동작한다는 근거는 아닙니다.
변경 작업 전에 공식 네이티브 MCP 클라이언트로 실제 프로젝트와 제공되는 도구 스키마를 확인합니다.
검증을 위해 커스텀 프록시, 직접 구현한 MCP 클라이언트 또는 Python 원격 브리지를 추가하지 않습니다.

실패하거나 중단된 실행을 포함하여 작업 후에는 도우미가 실행한 에디터를 항상 종료합니다. `stop`은 정상 종료 전에 저장된
프로세스 식별 정보를 확인하고, 프로세스와 포트가 해제되었는지 확인합니다. 화면이 있는 에디터가 닫히지 않으면 저장 대화상자부터
해결합니다. `--force-after-grace`는 정확히 해당 소유 PID만 강제 종료하도록 명시적으로 허용합니다.
NullRHI에는 대화형 종료 경로가 없어 기록된 PID를 정리해야 할 수 있습니다. 관련 없는 에디터는 절대 종료하지 않습니다.

## 직접 동작 확인

프로젝트 로컬에 직접 만든 작은 예제를 사용합니다. 카운터와 호출 가능한 변경 함수가 있는 AS Actor, Increment/Reset 동작을
눈으로 확인할 수 있는 EmmsUI 에디터 탭, 증가량이 양수여야 한다는 조건을 가진 Python ToolsetDefinition, Python AgentSkill을 만듭니다.
생성한 에셋은 전용 `/Game/CodexSkillSandbox` 폴더 아래에 유지합니다. 실제 바인딩과 도구 스키마를 확인합니다.

1. 새 Codex 채팅에서 스킬 6개와 예상한 marketplace가 보이고, 플러그인 생명주기 훅이 없는지 확인합니다.
2. 공식 MCP 도구로 프로젝트를 식별하고 등록된 툴셋을 탐색하여 스키마를 확인한 뒤,
   정상 입력과 거부되어야 하는 입력으로 Python 도구를 호출합니다. AgentSkill의 이름, 설명, 지침을 확인합니다.
3. AS 컴파일을 확인하고 Actor의 동작을 호출하여 속성 변경을 관측합니다. AS 파일에서 메서드 본문을 변경하고,
   hot reload 성공을 관측한 뒤 동일한 호출이 의도한 다른 결과를 내는지 확인합니다.
   표식만 변경하면 소스 교체를 확인할 수 있지만, 메서드 동작이 갱신되었다는 근거는 되지 않습니다.
4. 기존 에디터 API로 작은 검증용 에셋이나 맵을 만들고 자신이 만든 검증용 패키지만 저장한 뒤,
   언로드/리로드 또는 통제된 에디터 재시작 후 속성을 확인합니다. 생성만으로는 저장 상태의 보존이 입증되지 않습니다.
5. 화면을 렌더링하는 에디터에서 EmmsUI 탭을 엽니다. SlateInspector 도구로 표시되는 텍스트를 관측하고
   Increment와 Reset을 조작한 뒤 시각적 근거를 캡처합니다. NullRHI, 컴파일 또는 로그 한 줄만으로는 UI 동작이 입증되지 않습니다.
6. 정리 결과와 누락된 기능을 기록합니다. 필요할 때는 대상 엔진의 실제 테스트 실행 체계를 사용하는 AS 통합 시나리오를 작성합니다.
   테스트를 작성하거나 발견한 것을 실행한 것으로 혼동하지 않습니다.

대상 프로젝트의 테스트 실행 조건을 준수합니다. 최초 로컬 검증 작업공간에서는 사용자가 `!test`를 요청하기 전까지 작성된
Unit/Integration 및 Automation 테스트를 실행하지 않습니다. 실행 도우미는 해당 테스트를 실행하지 않습니다.
직접 컴파일, MCP, PIE 동작, UI, 저장/리로드 확인은 별도의 구현 검증입니다.
모듈이나 에셋이 하드코딩된 프로젝트 전용 실행 도우미가 이 독립 프로젝트를 받아들이도록 파일 이름을 바꾸어서는 안 됩니다.

## 현재 근거

2026-10-21에 관측한 결과: 공식 설치, 세션에서 스킬 6개의 자동 발견, 요청된 설치 플러그인의 네이티브 MCP·저장 상태·화면 UI·정리
검증이 통과했습니다. 패키지 검증, 스킬 6개 전체의 메타데이터 검사, Python 문법 컴파일, ZIP 범위 확인이 통과했습니다.
기존 UE 스킬 3개는 고정한 Idris 기준과 동일하게 유지됩니다.
독립 프로젝트에는 네이티브 프로젝트 모듈이 없으며, 로컬 네이티브 플러그인의 BuildId는 엔진과 일치합니다.
BuildId는 `3c6a4263-8d5a-4b20-a676-deccedf5fce2`입니다.

첫 검증 시도에서는 스킬 소스 파일을 수동으로 읽고 네이티브 MCP로 에디터를 조작했습니다.
당시 패키징된 스킬 6개는 자동으로 로드되지 않았습니다. 초기 진단 결과는 `enabled = true`,
`installed = false`, 일치하는 스킬 0개였으며 marketplace 로드 오류도 0개였습니다. 이 과거 실패는
`plugin-installation-boundary.json`에 기록되어 있습니다. 아래 초기 직접 검증 결과를 플러그인 로드의 근거로 소급해서 사용하지 않습니다.

사용자의 명시적인 승인 후 공식 `plugin/install`로 정리된 배포본을 설치했습니다. 설치 프로그램이 기록한 사용자 활성화 값은
즉시 `false`로 바꾸고 대상 프로젝트는 `true`를 유지했습니다. 관련 없는 사용자 설정은 변경하지 않았습니다.
이후 네이티브 목록 조회 결과는 `installed = true`, `enabled = true`이며, 이 플러그인의 설치 캐시에서 스킬 6개 모두를 표시합니다.
새 실제 채팅도 스킬 카탈로그에서 6개 모두를 받았습니다. 해당 설치 시점에 캐시의 28개 파일은 정리된 배포본 준비 디렉터리의
파일과 해시가 일치했습니다. 이는 해당 설치 스냅샷에서 기록한 관측이며, 이후 문서 패키지나 재설치에도 해시가 영구히
일치한다는 주장은 아닙니다. 관련 없는 게임 프로젝트에서는 새 플러그인을 활성화하지 않았습니다.
근거는 `plugin-installation-result.json`에 기록되어 있습니다.

해당 새 채팅은 에디터가 꺼져 있을 때 시작했으므로 스킬 로드에는 성공했지만 초기 네이티브 MCP 핸드셰이크는 실패했습니다.
이 과거 실패는 `INSTALLED_PLUGIN_VALIDATION.md`와 해당 JSON 보고서에 보존되어 있습니다.
조정 담당 에이전트가 검증된 에디터(PID `167916`)를 시작하고 MCP 서버가 준비된 후, 같은 프로젝트의 기존 검증 채팅에서
새 턴이 설치 플러그인의 스킬 6개와 네이티브 MCP 메타 도구 3개를 모두 받았습니다.
스킬 파일을 읽기 전에 카탈로그를 관측했으며, 이후 설치 캐시의 `unreal-mcp`와 `emmsui` 지침을 적용했습니다.
이는 실제로 관측한 복구 경로이며, 앞서 실패한 세션이 자동으로 재연결되었다는 주장은 아닙니다.

설치된 플러그인으로 연결한 후속 검증에서 다음을 독립적으로 확인했습니다.

- 접근 전에 PID, 생성 시각, 엔진 실행 파일, 프로젝트 명령줄, 포트 `58241`의 소유권이 일치했습니다.
- 실제 프로젝트 식별 정보 조회를 포함하여 네이티브 `list_toolsets`, `describe_toolset`, `call_tool`이 성공했습니다.
- Python `advance_counter(7, 3) = 10`과 Python AgentSkill 지침의 발견·조회가 확인되었습니다.
- 저장된 맵의 카운터 `23`, 표식 `persisted-after-hot-reload-v2`, 저장된 Agent Skill 에셋의 리비전 2가 확인되었습니다.
- 실제 화면의 Slate Increment/Reset 클릭으로 표시 값과 모델 값이 모두 `0 -> 1 -> 0`으로 변했습니다.
- 실행 도우미가 종료 코드 0으로 정상 종료되었고, PID `167916`은 존재하지 않으며, `58241`과 `58240`에 리스너가 없었습니다.

최종 연결 검증 보고서는 `INSTALLED_PLUGIN_CONNECTED_VALIDATION.md`와
`INSTALLED_PLUGIN_CONNECTED_VALIDATION.json`입니다. 근거에는 `installed-plugin-native-evidence.json`,
`installed-plugin-emmsui-increment.png`, `installed-plugin-emmsui-reset.png`, `installed-plugin-cleanup.json`,
`installed-plugin-preservation-check.json`이 포함됩니다. 이전 보고서, 맵, Skill 에셋, Probe 소스의 해시는 유지되었습니다.
이 후속 검증은 소스나 저장된 에셋을 변경하지 않았습니다. 이전의 전체 컴파일, 메서드 hot reload, PIE, 저장/재시작 시나리오를
반복하지 않았으며, 해당 결과는 아래의 별도 관측으로 유지됩니다.

최초에 스킬 소스를 참고하여 실행한 직접 구현 검증의 관측 결과는 다음과 같습니다.

- 선택한 독립 프로젝트에서 네이티브 MCP 도구 탐색, 스키마 확인, 호출이 성공했습니다.
- Python 툴셋이 `7 + 3`에 대해 `10`을 반환했으며, Python AgentSkill이 등록되고 조회되었습니다.
- AS Actor의 카운터가 `1 -> 4`로 변했습니다. 메서드 본문이 `Amount * 2`를 적용하도록 변경하고 hot reload한 후,
  같은 Actor가 `4 -> 10`으로 변하여 갱신된 메서드 동작을 입증했습니다.
- PIE에서 Actor는 `23 -> 31`로 변했고, 에디터 월드의 Actor는 `23`을 유지했습니다.
- 화면을 렌더링하는 에디터에서 실제 EmmsUI Increment 버튼 조작으로 표시된 카운터가 `0 -> 1 -> 2`로 변했으며,
  Reset을 누르자 `0`으로 돌아왔습니다. Slate 관측과 스크린샷으로 UI를 기록했습니다.
- 저장 후 다른 에디터 PID(`105112 -> 119572`)로 재시작한 뒤, 검증용 맵의 카운터 `23`과 표식,
  저장된 Agent Skill 에셋의 리비전 2 지침을 성공적으로 다시 읽었습니다.

근거는 이 플러그인 저장소 밖에 있는 독립 프로젝트의 `Saved/SkillValidation/`에 유지됩니다.
여기에는 `native-mcp-evidence.json`, `emmsui-increment.png`, `emmsui-reset.png`, 에디터 로그,
프로세스 식별 정보 기록이 있습니다. 완료된 `VALIDATION_REPORT.md`와 `VALIDATION_REPORT.json`은 초기 직접 검증 실행을 종합합니다.
정리 결과는 `cleanup-verification.json`에 기록되어 있습니다. 해당 확인 시점에 PID `119572`와 당시 추적하던 모든 Sandbox 에디터는
존재하지 않았고, 기록된 상태는 `stopped`였으며, `58241`과 `58240` 어느 포트에도 리스너가 없었습니다.
강제 종료 없이 정상 종료되었으며, 조정 담당 에이전트가 이를 독립적으로 확인했습니다. 설치된 플러그인에 대한 별도 정리 기록도
`06:44:58 UTC`에 해당 PID `167916`이 존재하지 않고 두 포트가 모두 비어 있음을 확인했습니다.
조정 담당 에이전트도 이 최종 상태를 독립적으로 점검했습니다. 두 검증 실행 모두 강제 종료를 사용하지 않았습니다.

최초 종료 과정에서는 프로세스가 종료되는 동안 식별 정보 필드가 비어 버리는 CIM 경합이 드러났습니다.
이제 실행 도우미는 종료 처리 중 동일한 PID/생성 시각을 제한된 범위에서 관측하도록 허용하지만, 프로세스를 제어하기 전에는
완전한 식별 정보를 요구합니다. 수정한 정상 종료 경로를 실제로 실행하여 성공을 확인했습니다.
추가된 시작 실패 시 대체 정리 경로는 원래 오류를 보존하고, 정리 실패를 별도로 기록하며, CIM 기반 정리가 실패하면
자신의 Popen 핸들만 사용합니다. 이 대체 경로에는 문법·정적 검사와 작성된 회귀 테스트가 있지만, 예외 분기는 실제로 실행하지 않았습니다.

엔진은 시작 중 내장 Smoke 검사도 자동 실행했으며 `LogAutomationTest` 오류를 기록했습니다.
설치 플러그인 검증용 에디터의 시작 로그에는 `Condition failed` 메시지가 15개 있었습니다. 이 수치는 테스트 케이스가 아닌 로그 메시지 수입니다.
이는 관측된 엔진 시작 오류이며, 의도적으로 선택하여 실행한 프로젝트 작성 테스트나 오류 없는 Smoke 통과 결과가 아닙니다.
직접 동작 검증이 성공했더라도 해당 오류를 보고서에 유지합니다. 엔진 Smoke 테스트의 케이스 수나 통과율은 주장하지 않습니다.

프로젝트 로컬 `Script/Tests/CodexProbe_UnitTest.as`와 `CodexProbe_IntegrationTest.as`를 작성하고 컴파일했지만,
테스트 함수는 호출하지 않았습니다. 확인한 엔진의 `DiscoverTests.cpp:171`은 `UnitTest_`가 아닌
`Test_`로 시작하는 유닛 함수를 발견합니다. 유닛 진입점은 `Test_CodexProbeCounterState`이고,
통합 진입점은 `IntegrationTest_CodexProbePIE`입니다. 이 파일들을 추가하기 전에 hot reload 시 유닛 테스트 실행을 명시적으로 비활성화했습니다.
`Content/Python/tests/test_codex_sandbox_tools.py`와 플러그인 저장소의 Python 회귀 테스트는 작성했지만 실행하지 않았습니다.
직접 에디터 검증으로 이 테스트의 유효성이나 결과를 추정하지 않습니다.

Unit/Integration Test 미실행 (!test 요청 전). 이번 변경에 대해 프로젝트에서 작성한 Unit/Integration 또는 Python unittest 모음은
실행하지 않았습니다. 앞서 설명한 엔진 시작 시 Smoke 실행은 별도로 관측한 예외입니다.
기존 CI 워크플로는 보존되어 있으며, 설정이 존재한다는 사실은 실행이 성공했다는 근거가 아닙니다.
