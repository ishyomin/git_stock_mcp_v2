"""호출 로그 집계. 실행: python log_report.py"""
import json
from pathlib import Path

import call_log


def read_logs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize(records: list[dict]) -> dict[str, dict]:
    stats = {}
    for r in records:
        s = stats.setdefault(r["tool"], {"calls": 0, "errors": 0, "total_ms": 0.0})
        s["calls"] += 1
        if not r["ok"]:
            s["errors"] += 1
        s["total_ms"] += r["elapsed_ms"]
    return {
        tool: {
            "calls": s["calls"],
            "errors": s["errors"],
            "error_rate_pct": round(s["errors"] / s["calls"] * 100, 1),
            "avg_ms": round(s["total_ms"] / s["calls"], 1),
        }
        for tool, s in stats.items()
    }


def main() -> None:
    summary = summarize(read_logs(call_log.LOG_PATH))
    if not summary:
        print("기록이 없습니다.")
        return
    print(f"{'tool':<12}{'calls':>7}{'errors':>8}{'err%':>7}{'avg_ms':>9}")
    for tool, s in sorted(summary.items()):
        print(f"{tool:<12}{s['calls']:>7}{s['errors']:>8}{s['error_rate_pct']:>7}{s['avg_ms']:>9}")


if __name__ == "__main__":
    main()