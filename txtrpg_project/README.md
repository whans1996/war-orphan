# 《전란고아》 txtrpg 프로젝트

## 실행

현재 모듈형 구조는 골격 단계입니다.

```bash
python main.py
```

기존 플레이 가능 버전:

```bash
python legacy/txtrpg_playable.py
```

## 개발 원칙

- `game/` : Python 게임 로직
- `data/` : 아이템/무공/적/세력/세계 데이터
- `saves/` : 저장 데이터
- `tests/` : 자동 테스트
- `legacy/` : 이전 단일 파일 버전 보존

다음 구현 순서는 `game/stats.py` → `game/character.py` → 기존 인벤토리/생존 코드 이전 → 전투 엔진 분리입니다.
