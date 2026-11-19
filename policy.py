"""반출 정책: 서버 밖으로 나가는 결과는 반드시 여기를 거친다."""
MIN_WINDOW_SEC = 60      # 이보다 잘게 쪼개면 개별 주문이 드러날 수 있다
MAX_WINDOW_SEC = 3600
MIN_EVENTS = 20          # 이벤트가 적은 구간은 숨긴다(소수 주문 재식별 방지)
MAX_ROWS = 200           # 한 번에 내보내는 행 수 상한(대량 반출 방지)
FORBIDDEN_KEYS = {"order_id"}


def check_window(window_sec: int) -> None:
    if not MIN_WINDOW_SEC <= window_sec <= MAX_WINDOW_SEC:
        raise ValueError(
            f"window_sec는 {MIN_WINDOW_SEC}~{MAX_WINDOW_SEC}초 사이여야 합니다(반출 정책: 최소 {MIN_WINDOW_SEC}초 집계)."
        )


def apply_policy(rows: list[dict]) -> dict:
    for r in rows:
        leaked = FORBIDDEN_KEYS & r.keys()
        if leaked:
            raise PermissionError(f"반출 금지 항목 포함: {', '.join(sorted(leaked))}")
    visible = [r for r in rows if r["n_events"] >= MIN_EVENTS]
    return {
        "rows": visible[:MAX_ROWS],
        "suppressed_windows": len(rows) - len(visible),
        "truncated": len(visible) > MAX_ROWS,
    }