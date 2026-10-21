# 선택적 UE 세션 문맥

[English](OPTIONAL_HOOK.md)

> 영문 원문이 유지보수 기준이며, 번역 기준 커밋은 `ae6b0c5886db4ea3ca1800b444cfdcd960c8d8e0`입니다.

이 플러그인은 훅 없이 동작합니다. `scripts/session_context.py`는 훅의 `cwd`를 읽고 상위 디렉터리로 올라가며
`.uproject` 또는 `GenerateProjectFiles.*`를 찾아 Unreal 디렉터리인 경우에만 문맥을 반환합니다. 이 스크립트는 설정을
쓰거나 에디터를 시작하지 않으며, 설정 파일의 존재를 연결이 확인되었다는 근거로 취급하지 않습니다. 프로젝트 파일명과
파일 내용은 지침에 삽입하지 않습니다.

## 명시적인 로컬 설정

자동으로 업데이트되는 캐시 경로 대신 안정적인 체크아웃이나 압축을 푼 패키지를 사용합니다. 기존 훅을 보존하면서 아래 내용을
`<project>/.codex/hooks.json` 또는 `~/.codex/hooks.json`에 병합합니다. 적용 범위는 하나만 선택합니다.
PATH에서 Python 3.11+를 `python`으로 실행할 수 있어야 합니다. 예제의 스크립트 경로를 자신의 체크아웃 경로로 바꿉니다.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact|fork",
        "hooks": [
          {
            "type": "command",
            "command": "python \"H:/Unreal-Skill/unreal-engine-skills-for-codex-plugin/scripts/session_context.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

macOS/Linux에서는 예를 들어 `python3 "/home/user/plugin/scripts/session_context.py"`를 사용합니다.
이를 지원하는 Codex CLI에서 `/hooks`를 열어 정의를 검토하고 신뢰하도록 승인합니다. 프로젝트 훅을 사용하려면 프로젝트가
신뢰된 상태여야 합니다. 이 저장소는 해당 파일을 설치하거나 신뢰 절차를 우회하지 않습니다. 되돌리려면 자신이 추가한 항목만 제거합니다.

## 수동 확인

```powershell
python scripts/session_context.py --cwd "F:\MyProject\Source"
```

관련 없는 디렉터리는 `{}`를 반환하고, UE 디렉터리는 `SessionStart`용
`hookSpecificOutput.additionalContext`를 반환합니다. 일반적인 훅 실행에서는 stdin의 JSON을 읽습니다.
[Codex Hooks](https://learn.chatgpt.com/docs/hooks)를 참고하세요.
공개 디렉터리 제출에는 생명주기 훅에 관한 별도의 제한이 있습니다. 이 도우미는 자동으로 로드되는 플러그인 훅으로 선언되어 있지 않습니다.
