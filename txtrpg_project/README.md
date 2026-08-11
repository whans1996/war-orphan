# 《전란고아》 txtrpg 프로젝트

## 1. 요구 환경

- Python 3.11 이상 권장
- 별도 외부 패키지 없음

Python 설치 확인:

```bash
python --version
```

Windows에서 `python` 명령이 없다면 다음도 확인합니다.

```bash
py --version
```

## 2. 새 모듈형 개발본 실행

프로젝트 최상위 폴더(`main.py`가 있는 위치)에서 실행합니다.

### Windows PowerShell / CMD

```bash
cd txtrpg_project
python main.py
```

`python` 대신 `py`를 사용하는 환경:

```bash
py main.py
```

### macOS / Linux

```bash
cd txtrpg_project
python3 main.py
```

현재 새 개발본은 10세 전쟁고아 캐릭터를 생성하고 능력치/HP/ST 상태창을 출력합니다.

## 3. 이전 플레이 가능 버전 실행

기존 단일 파일 버전은 `legacy/`에 보존되어 있습니다.

Windows:

```bash
python legacy/txtrpg_playable.py
```

macOS / Linux:

```bash
python3 legacy/txtrpg_playable.py
```

## 4. 테스트 실행

프로젝트 최상위 폴더에서:

```bash
python -m unittest discover -s tests -v
```

macOS / Linux에서 필요하면:

```bash
python3 -m unittest discover -s tests -v
```

## 5. 현재 구현 상태

- `game/stats.py`
  - STR / AGI / CON / PER / INT / WIL / SEN
  - 10세 시작 능력치 범위
  - 최대 기혈 HP 공식
  - 최대 체력 ST 공식
- `game/character.py`
  - 10세 전쟁고아 생성
  - 무인 이전 시작
  - 단전 미개방 / 내력 0 시작
  - 직렬화/역직렬화 기초
  - 상태창 출력
- `main.py`
  - 새 캐릭터 생성 및 상태창 확인
- `legacy/`
  - 이전 플레이 가능 프로토타입 보존

## 6. 다음 구현 순서

1. `game/martial/internal_energy.py` — 축기치, 현재/최대 내력, 내공 숙련도, 운기 제어, 경맥 안정도, 단전 계수
2. `game/survival.py` — 허기, 갈증, 피로, 체온
3. 공통 1d100 TN 판정 시스템
4. 부상 부위 및 전투 엔진
5. 저장/불러오기 정식 연결
