# 업스트림과 유지보수

[English](UPSTREAM.md)

> 영문 원문이 유지보수 기준이며, 번역 기준 커밋은 `ae6b0c5886db4ea3ca1800b444cfdcd960c8d8e0`입니다.

이 커뮤니티 포크는 Epic의 이력을 보존하고, 고정된 Codex 포팅 버전 하나를 채택합니다. Epic Games나 OpenAI의 공식 배포판이 아닙니다.

| 역할 | 저장소 | 기준 버전 |
| --- | --- | --- |
| `upstream` | [Epic Games 원본](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin) | `a6aa73ada02a9fb1f5415bec491f9942c519b297` (3.1.1) |
| `port-origin` | [Idris173 Codex 포팅 버전](https://github.com/Idris173/unreal-engine-skills-for-codex-plugin) | `a6c25ac96cea4cdfb93029e31423efd109d90895` |
| `origin` | [coquid 포크](https://github.com/coquid/angelscript-unreal-engine-skills-for-codex-plugin) | 이 저장소 |

Idris 기준 버전에는 Epic 기준 버전 이후의 커밋 `5378fdf`와 `a6c25ac`가 포함되어 있습니다. 이 이력은 그대로 병합되어 있습니다.
mazelines 포크의 내용은 가져오지 않았습니다. `create-toolset`, `unreal-mcp`, `unreal-skill` 디렉터리는 고정된 Idris 트리에서 변경하지 않았습니다.
Epic에서 Idris로의 전환 과정에서는 해당 작업 절차를 Codex에 맞게 조정했습니다.
따라서 이 포크의 파일이 Epic 원본과 바이트 단위로 동일하다는 뜻은 아닙니다.

이 포크는 패키지 식별 정보를 변경하고, 출처를 문서화하며, 범용 `angelscript-in-unreal`, `as-integration-tests`, `emmsui` 스킬을 추가하고,
독립 프로젝트의 시작과 종료를 관리하는 선택적 도우미를 제공합니다. 범용 지침과 작은 시연 코드 조각은 새로 작성했습니다.
프로젝트 전용 소스, 에셋, 네이티브 플러그인 바이너리, 설정, 검증 로그는 배포하지 않습니다.
Unreal Engine과 EmmsUI에는 각각의 외부 라이선스가 적용됩니다. Epic의 원본 [MIT 고지](LICENSE)는 변경 없이 보존합니다.

## Epic 업데이트 가져오기

위의 원격 저장소 세 개를 유지하세요. `upstream`을 fetch하고, 기록된 Epic 기준 버전 이후의 변경을 검토한 다음,
검토한 업스트림 커밋을 작업 브랜치에 병합하세요. 파일 배치를 유지하고 Codex에 필요한 변경은 원본 스킬에 직접 적용하세요.
중복된 스킬 트리를 생성하거나 오버레이 빌드 단계를 추가하지 마세요.

Codex 대응에 실제로 필요한 충돌만 해결하세요. Epic이 개선한 작업 절차, 예제, 참조 자료를 보존하세요.
Codex 매니페스트와 프로젝트에서 제어하는 연결 설정을 유지하세요. 삭제한 `.claude-plugin`이나 자동 `hooks/` 설정을 복원하지 마세요.
Codex는 매니페스트에 명시적인 참조가 없어도 정해진 경로의 훅 파일을 발견할 수 있습니다.
고정 엔드포인트나 자동 설정 쓰기를 추가하지 마세요. 새로운 업스트림 스크립트나 의존성은 도입 전에 검토하세요.

AngelScript 스킬 디렉터리 세 개와 샌드박스 도우미는 이 포크에서 추가한 것으로, 보통 Epic의 경로와 겹치지 않습니다.
이후의 Idris 업데이트는 별도로 명시적인 검토를 거쳐 반영해야 합니다. 그 저장소의 HEAD를 묵시적으로 따라가지 마세요.
업데이트를 가져올 때는 새 기준 SHA를 기록하고 라이선스 고지를 정리하세요.

## 병합 후 검증

패키지 검증기와 재현 가능한 패키지 생성기를 실행하고, 업스트림 스킬의 차이를 검토하며, 작성된 테스트에 대해서는 대상 프로젝트의 정책을 따르세요.
전송 방식, 도구·스킬 탐색, API 전제, 에셋 저장 후 유지 여부, UI 동작이 바뀌면 에디터에서 직접 검증을 반복하세요.
정확한 엔진 빌드와 네이티브 플러그인 BuildId를 기록하세요. UE 버전 번호만으로는 호환성을 입증할 수 없습니다.
제3자의 과거 검증 근거와 이 포크의 [검증 기록](docs/SANDBOX_VALIDATION.ko-KR.md)은 구분해서 관리하세요.
