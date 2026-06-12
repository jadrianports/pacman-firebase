---
type: codebase-map
focus: quality
doc: TESTING
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# Testing

## Framework & Tooling

- **Runner:** `pytest`.
- **Mocking:** `unittest.mock` (`patch`, `MagicMock`) + pytest's `monkeypatch` and `tmp_path` fixtures.
- **No config file:** there is no `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, or `conftest.py`. pytest runs with defaults; the repo root is added to `sys.path`, so tests import client modules by top-level name.
- **Not in requirements:** `pytest` is not declared in any `requirements.txt`; it must be installed separately in the dev environment.
- **No coverage tooling**, no CI (`.github/workflows` absent) — tests are run manually.

## How to Run

```bash
pytest                                                  # all tests
pytest tests/test_api_service.py                        # one file
pytest tests/test_api_service.py::test_submit_score_new_best   # one test
```
(Run from the repo root so imports resolve.)

## Test Layout

```
tests/
├── __init__.py                 # empty (makes tests a package)
├── test_api_service.py         # 6 tests
└── test_local_storage.py       # 5 tests
```

Total: **11 tests across 2 files.** Test files mirror the module under test (`test_<module>.py`). Test functions are `test_<behavior>` and read as behavior descriptions (`test_submit_score_network_error`, `test_save_initials_overwrites`).

## Patterns

### Fixtures
- `test_api_service.py` — a `service` fixture returns an `ApiService` pointed at fake URLs:
  ```python
  @pytest.fixture
  def service():
      return ApiService("https://fake-submit.run.app", "https://fake-leaderboard.run.app")
  ```
- `test_local_storage.py` — a `temp_dir` fixture isolates the filesystem with `tmp_path` + `monkeypatch.chdir(tmp_path)`, and tests pass explicit paths (`str(temp_dir / "machine_id.txt")`) into the functions under test (which accept a `path` override arg).

### Mocking the network (no real HTTP)
`api_service.urlopen` is patched directly. A helper builds a context-manager-capable mock response:
```python
def _mock_response(data, status=200):
    mock = MagicMock()
    mock.status = status
    mock.read.return_value = json.dumps(data).encode()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock

with patch("api_service.urlopen", return_value=response):
    result = service.submit_score("machine-1", "JAM", 5000)
```
Network failures are simulated with `side_effect=Exception("timeout")` to assert the `None` (offline) return path.

## Coverage Map

| Module | Tested? | Notes |
|--------|---------|-------|
| `api_service.py` | ✅ | new-best / not-best / network-error for submit; success / empty / network-error for leaderboard |
| `local_storage.py` | ✅ | machine-id creation + idempotency; initials none/save/get/overwrite |
| `game.py` | ❌ | No tests — game loop, scoring, collisions, win/lose |
| `ghost.py` | ❌ | No tests — the 4 movement AIs and turn logic (highest-risk, untested) |
| `player.py` | ❌ | No tests — movement, direction, wrap-around |
| `menu.py` | ❌ | No tests — screen loops |
| `board.py` | ❌ | Static data, no logic |
| `sound.py` | ❌ | No tests |
| `paths.py` | ❌ | No tests (dev/frozen branching) |
| `cloud_functions/submit_score` | ❌ | No tests — validation + Firestore transaction logic |
| `cloud_functions/get_leaderboard` | ❌ | No tests |

**Summary:** tests cover the two thin, pure-Python service modules that are easy to isolate (network + file I/O). The bulk of the logic — ghost AI, the game loop, player movement — and **all** backend code are untested. The pygame/display-dependent modules are hard to unit-test as written (rendering and logic are interleaved), but the ghost AI and the cloud-function validators are pure enough to be testable with modest refactoring or by exercising `Ghost.check_collisions`/`move_*` against a fixed board.

## Gaps / Opportunities

- No tests for `cloud_functions` validators (`^[A-Z]{3}$`, score range, best-score upsert) — these are pure and high-value to lock down.
- Ghost movement/turn-legality (`Ghost.check_collisions`, `_tile`, the `move_*` methods) could be unit-tested with a stub `screen` and the real `boards` grid.
- No integration test exercising `main.py`'s state flow.
- No fixtures for a headless pygame surface (would enable testing `Game`/`Player` logic via `pygame.Surface` without a display).
