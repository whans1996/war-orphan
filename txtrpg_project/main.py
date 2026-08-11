"""《전란고아》 모듈형 프로젝트 실행 진입점."""

from __future__ import annotations

from game.character import Character


def new_game() -> Character:
    print("\n=== 《전란고아》 ===")
    print("정마전쟁이 끝난 뒤, 너는 홀로 남았다.")
    print("지금 확실히 아는 것은 네가 열 살이라는 사실뿐이다.\n")
    name = input("지금 쓰고 있는 이름 > ").strip()
    return Character.new_war_orphan(name)


def main() -> None:
    player = new_game()
    print("\n캐릭터가 생성되었습니다.\n")
    print(player.status_text())
    print("\n현재 구현 단계: 캐릭터 코어 v1")
    print("다음 연결 대상: 내공 상태 → 생존 상태 → 판정 시스템 → 전투")


if __name__ == "__main__":
    main()
