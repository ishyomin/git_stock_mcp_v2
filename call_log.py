"""도구 호출 기록(JSONL)과 에러 변환 데코레이터."""
import functools
import inspect
import json
import time
from datetime import datetime
from pathlib import Path

from mcp.server.mcpserver.exceptions import ToolError

LOG_PATH = Path(__file__).parent / "logs" / "calls.jsonl"


def write_log(record: dict, path: Path | None = None) -> None:
    """기록 한 건을 JSON 한 줄로 파일 끝에 추가한다."""
    path = path or LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def logged(func):
    """도구 함수를 감싸 호출을 기록하고, 에러를 ToolError로 바꾼다."""
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "tool": func.__name__,
            "args": dict(bound.arguments),
        }
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            record["ok"] = True
            return result
        except ValueError as e:
            record["ok"] = False
            record["error"] = str(e)
            raise ToolError(str(e)) from e
        except Exception as e:
            record["ok"] = False
            record["error"] = f"{type(e).__name__}: {e}"
            raise ToolError("데이터를 가져오는 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.") from e
        finally:
            record["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 1)
            write_log(record)

    return wrapper