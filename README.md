# opencode-trading

> **OpenCode용 TradingCodex 어댑터** — Codex 전용 트레이딩 하니스를 OpenCode + oh-my-openagent 워크플로우에 통합

<a id="english"></a>

> **OpenCode adapter for TradingCodex** — Bring the Codex-native trading harness into OpenCode + oh-my-openagent workflows.

---

## 왜 이게 필요한가? / Why?

TradingCodex 0.2.0은 **Codex 전용 하니스**입니다 (`.codex/agents/*.toml`, `.codex/prompts/*`, `.codex/hooks/*`에 깊이 종속). OpenCode + oh-my-openagent 환경에서 그 역할 토폴로지(1+9 specialists)와 MCP 실행 경계를 그대로 쓰려면 변환 계층이 필요합니다.

| 갭 / Gap | TradingCodex (Codex) | OpenCode | 해결 / Solution |
|---|---|---|---|
| 에이전트 정의 / Agent definitions | `.codex/agents/*.toml` | `opencode.json` `agent` 객체 | `tcx_opencode/converters/codex_to_opencode.py` |
| 슬래시 커맨드 / Slash commands | `.codex/prompts/$orchestrate-workflow` | TUI 명령 + skills | 변환 후 `~/.config/opencode/command/*.md` |
| 훅 / Hooks | `.codex/hooks/UserPromptSubmit` 등 | OpenCode hooks (`opencode.json` `hooks` 객체) | `converters/hooks.py` |
| MCP 실행 경계 / MCP execution boundary | TradingCodex MCP (Django) | TradingCodex MCP (동일) | **그대로 재사용** ✅ |
| 로컬 대시보드 / Local dashboard | `http://127.0.0.1:48267/` | 동일 | **그대로 재사용** ✅ |
| SQLite 영속 상태 / Persistent state | `~/.tradingcodex/state/tradingcodex.sqlite3` | 동일 | **그대로 재사용** ✅ |

TradingCodex is a **Codex-only harness** (deeply tied to `.codex/agents/*.toml`, `.codex/prompts/*`, `.codex/hooks/*`). To use the same 1+9 specialist role topology and MCP execution boundary in OpenCode + oh-my-openagent, you need a translation layer — that's what this adapter does.

---

## 설치 / Installation

```bash
# v1.0.0 (GitHub 직접 설치 / direct from GitHub)
pip install git+https://github.com/sigco3111/opencode-trading.git@v1.0.0

# 또는 uv (PEP 668 호환 / PEP 668 compatible)
uv pip install git+https://github.com/sigco3111/opencode-trading.git@v1.0.0

# 이전 LTS / Previous LTS (v0.4.0)
pip install git+https://github.com/sigco3111/opencode-trading.git@v0.4.0
```

**Python 3.14 requirement / Python 3.14 요구사항**:
The bundled `attach` subcommand works on Python 3.11+. The `convert`
subcommand against a **live** TradingCodex workspace (currently
`tradingcodex>=0.2.0`) requires Python 3.14 — see the
[FAQ](#faq) for the bundled-snapshot workaround.

**의존성 / Dependencies**: zero-deps (TradingCodex 본체는 별도 설치)

---

## 빠른 시작 / Quick Start

### 1단계 — TradingCodex 본체 준비 / Prepare TradingCodex

```bash
# TradingCodex 워크스페이스 attach (Codex 환경 한정, OpenCode로 attach는 v0.3.0+)
uvx --from tradingcodex tcx attach ~/opencode-trading
cd ~/opencode-trading && ./tcx doctor
```

### 2단계 — OpenCode 변환 실행 / Run OpenCode conversion

```bash
# (a) Convert an existing TradingCodex workspace to OpenCode:
opencode-trading convert --workspace ~/opencode-trading
# → <workspace>/.opencode/{agents.json, mcp.json, hooks.json, skills/}

# (b) Or scaffold a fresh OpenCode workspace from bundled TCX v0.2.0 templates
#     (no TCX install required — uses opencode-trading's bundled data):
opencode-trading attach --target ~/my-trading-ws
# → ~/my-trading-ws/.opencode/{agents.json, mcp.json, hooks.json, skills/}
```

### 3단계 — OpenCode에서 사용 / Use from OpenCode

```bash
# OpenCode 시작
opencode ~/my-trading-ws   # for (b) attach path
# 또는
opencode ~/opencode-trading  # for (a) convert path

# oh-my-openagent sisyphus가 TradingCodex MCP 도구 호출
> "@tradingcodex create_research_artifact for Apple — Q1 2026"
```

**로컬 대시보드 / Local dashboard**: `http://127.0.0.1:48267/` (TradingCodex 서비스가 떠있을 때)

---

## 변환 범위 (v0.2.0) / Conversion Scope

| TradingCodex 자산 / Asset | OpenCode 매핑 / Mapping | 상태 / Status |
|---|---|---|
| `head-manager` (메인) | OpenCode primary agent | ✅ 활성 / Active |
| 9개 specialist (fundamental/technical/news/macro/instrument/valuation/portfolio/risk/execution) | `oh-my-openagent.json`에 subagent로 등록 | ✅ 활성 / Active |
| `$orchestrate-workflow` 슬래시 커맨드 | OpenCode command + skill | ✅ 활성 / Active |
| `UserPromptSubmit` 훅 | OpenCode hook (`opencode.json` `hooks`) | ✅ 활성 / Active |
| `tradingcodex` MCP 서버 | `opencode.json` `mcp` 블록 | ✅ 활성 / Active |
| `~/.tradingcodex/state/tradingcodex.sqlite3` | 변경 없음 / unchanged | ✅ 그대로 사용 |
| 대시보드 / Dashboard | 변경 없음 / unchanged | ✅ 그대로 사용 |

---

## 사용 시나리오 / Use Cases

### 1. oh-my-openagent 스쿼드와 결합 / Combine with oh-my-openagent squad
- sisyphus(메인 코더)가 TradingCodex MCP 도구 호출 → 트레이딩 분석 위임
- `oracle`/`librarian`/`explore`가 specialist 역할 흉내 가능

### 2. TradingCodex 워크플로우를 IDE에서 직접 / Workflow from your IDE
- `$orchestrate-workflow analyze Apple with public equity research, valuation, portfolio, and risk review` (변환 후 OpenCode 명령)

### 3. 페이퍼 트레이딩 / Paper trading
- TradingCodex MCP의 `create_order_ticket` → `request_order_approval` → `submit_approved_order` 흐름을 OpenCode 안에서 실행
- 브로커 어댑터는 stub-execution / paper-trading만 (의도된 제약 / intentional)

### 4. 로컬 대시보드 모니터링 / Local dashboard monitoring
- OpenCode 세션과 별개로 `127.0.0.1:48267/`에서 정책/오더/포트폴리오/감사 로그 확인

---

## 다른 PC에서 작업 (Phase 0 v0.2.0) / Working from another PC

이 저장소는 **다른 PC에서 풀 부트스트랩**할 수 있도록 설계되었습니다. 빈 워크스페이스에서 시작:

```bash
# 1. 클론
git clone https://github.com/sigco3111/opencode-trading.git
cd opencode-trading

# 2. 개발 설치
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 3. TradingCodex 본체 클론 (별도 디렉토리)
cd ..
git clone https://github.com/monarchjuno/tradingcodex.git
pip install -e ./tradingcodex

# 4. 변환 함수 직접 호출 (또는 CLI 사용)
cd opencode-trading
python3 -c "from opencode_trading.converters.codex_to_opencode import convert_workspace; convert_workspace('../some-tcx-workspace', to='opencode')"

# 5. 테스트
pytest -v
```

To verify the conversion without a real TradingCodex installation, use the included sample fixture: `python -m opencode_trading convert --workspace tests/fixtures/sample-tcx-workspace --out /tmp/oc-out`

### 작업 순서 제안 / Suggested implementation order

1. **`models.py`** — `OpenCodeAgent`, `OpenCodeSkill`, `OpenCodeHook` 도메인 타입
2. **`converters/codex_to_opencode.py`** — TradingCodex TOML → OpenCode JSON 마샬링
3. **`converters/hooks.py`** — Codex UserPromptSubmit → OpenCode hook 매핑
4. **`converters/commands.py`** — `$orchestrate-workflow` → OpenCode command 변환
5. **`converters/mcp.py`** — TradingCodex MCP 서버를 opencode.json에 등록
6. **`cli.py`** — `convert` 서브 명령 + `--dry-run` 옵션
7. **테스트** — `tests/test_*.py` (변환 정확성 + round-trip + CLI)
8. **CI** — `.github/workflows/ci.yml` (Python 3.11/3.12/3.13/3.14, ruff, mypy, pytest, coverage ≥ 60%)
9. **v0.1.0 → v0.2.0** — `tcx-opencode attach` CLI (실제 워크스페이스 생성기)

---

## 로드맵 / Roadmap

| 버전 / Version | 목표 / Goal | 상태 / Status |
|---|---|---|
| **v0.1.0** | Phase 0: README/스켈레톤/문서/설계 (다른 PC 작업용) | ✅ Released |
| **v0.2.0** | 변환기 5종 (agent/hook/command/mcp/workflow) + 30+ 테스트 | ✅ Released |
| **v0.3.0** | `opencode-trading attach` CLI — OpenCode용 워크스페이스 생성기 (번들된 TCX v0.2.0 템플릿) | ✅ Released |
| **v0.4.0** | `verify` 서브커맨드 (라운드트립 무결성 검사) + `attach --with-tcx` 플래그 (`.codex`/`.tradingcodex`/`.agents` 동시 생성) | ✅ Released |
| **v1.0.0** | 거버넌스 + 커버리지 + 릴리스 CI — TradingCodex 업스트림 머지 가능 형태로 안정화 | ✅ Released |

---

## 디렉토리 구조 / Directory Structure

```
opencode-trading/
├── README.md
├── CHANGELOG.md                     # 버전별 변경 이력
├── LICENSE                          # MIT
├── CONTRIBUTING.md                  # 기여 가이드 (v1.0.0+)
├── CODE_OF_CONDUCT.md               # Contributor Covenant 2.1 (v1.0.0+)
├── SECURITY.md                      # 보안 신고 정책 (v1.0.0+)
├── AUTHORS                          # 메인테이너 + 업스트림 (v1.0.0+)
├── pyproject.toml                   # setuptools, zero-deps
├── .gitignore
├── src/opencode_trading/
│   ├── __init__.py                  # 공개 API (convert_workspace, attach_workspace, verify_workspace)
│   ├── __main__.py                  # python -m opencode_trading 진입점
│   ├── cli.py                       # argparse: convert, attach, verify 서브커맨드
│   ├── models.py                    # OpenCodeAgent, OpenCodeSkill, OpenCodeHook, OpenCodeWorkspace
│   ├── verify.py                    # v0.4.0+ verify_workspace() + VerifyResult
│   ├── attach.py                    # v0.3.0+ attach_workspace() (번들된 TCX 스냅샷)
│   ├── _frontmatter.py              # hand-rolled YAML frontmatter 파서
│   ├── _yaml_min.py                 # hand-rolled YAML 미니 파서 (zero-deps)
│   ├── exceptions.py                # ConversionError, MissingWorkspaceError, UnsupportedTradingCodexVersion
│   ├── _bundled/                    # v0.3.0+ 번들된 TCX v0.2.0 템플릿 (agents, hooks.json, mainagent, orchestrator, prompts, role-skills, workflows, tradingcodex)
│   └── converters/                  # 5종 변환기
│       ├── __init__.py
│       ├── codex_to_opencode.py     # 메인 변환 오케스트레이터
│       ├── agents.py                # 9 specialist TOML → OpenCodeAgent
│       ├── hooks.py                 # .codex/hooks.json → OpenCodeHook
│       ├── commands.py              # $orchestrate-workflow → OpenCode command + skill
│       ├── mcp.py                   # TradingCodex MCP 서버 등록
│       └── workflows.py             # workflow yaml → OpenCode workflow
├── tests/
│   ├── conftest.py                  # sample_tcx_workspace, tmp_tcx_workspace, tmp_opencode_workspace 픽스처
│   ├── fixtures/
│   │   └── sample-tcx-workspace/    # TradingCodex v0.2.0 워크스페이스 30+ 파일 미러
│   ├── test_models.py               # frozen dataclass + write() 라운드트립
│   ├── test_attach.py               # attach_workspace() + builder 단위 테스트
│   ├── test_with_tcx.py             # v0.4.0+ --with-tcx 시나리오 (S1-S4)
│   ├── test_verify.py               # v0.4.0+ verify_workspace() (S1-S5)
│   ├── test_bundled.py              # 번들된 TCX 템플릿 로드 검증
│   ├── test_codex_to_opencode.py
│   ├── test_agents.py
│   ├── test_hooks.py
│   ├── test_commands.py
│   ├── test_workflows.py
│   ├── test_mcp.py
│   ├── test_converters.py
│   ├── test_cli.py                  # CLI 서브커맨드 end-to-end (subprocess)
│   ├── test_frontmatter.py
│   └── test_yaml_min.py
├── docs/
│   ├── architecture.md              # 변환 파이프라인 + v0.4.0 verify/--with-tcx 섹션
│   ├── codex-vs-opencode.md         # 포맷 차이 매트릭스
│   └── decisions/                   # ADR (Architecture Decision Records)
└── .github/workflows/
    ├── ci.yml                       # Python 3.11-3.14 매트릭스 + ruff + mypy + pytest + coverage ≥ 60%
    └── release.yml                  # v1.0.0+ sdist+wheel 빌드 + PyPI trusted publishing + GitHub Release
```

---

## 의존성 / Dependencies

- **runtime**: zero (TradingCodex 본체는 `monarchjuno/tradingcodex` 별도 설치)
- **dev**: `pytest>=8`, `ruff`, `mypy`
- **TradingCodex 본체**: `pip install git+https://github.com/monarchjuno/tradingcodex.git@v0.2.0` (또는 PyPI `tradingcodex`)

---

## 기여 / Contributing

For the full contributor guide, see [CONTRIBUTING.md](CONTRIBUTING.md). See also [SECURITY.md](SECURITY.md) for security disclosure and our [Code of Conduct](CODE_OF_CONDUCT.md).

기여 환영합니다. 전체 가이드는 [CONTRIBUTING.md](CONTRIBUTING.md) 를 참조하세요. 보안 신고는 [SECURITY.md](SECURITY.md), 행동 강령은 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 를 참조하세요. 새 변환기 추가 시:
1. `src/opencode_trading/converters/` 에 `<name>.py` 작성
2. `tests/test_<name>.py` 단위 테스트 (TradingCodex 샘플 워크스페이스 fixture 기반)
3. `docs/architecture.md` 다이어그램 업데이트
4. PR — `feat(converter): add <name> converter` 형식 커밋 메시지

Contributions welcome. For new converters:
1. Add `<name>.py` under `src/opencode_trading/converters/`
2. Add unit tests in `tests/test_<name>.py` (use TradingCodex sample workspace fixtures)
3. Update `docs/architecture.md` pipeline diagram
4. PR with `feat(converter): add <name> converter` style commit

---

## 감사의 말 / Credits

- **[monarchjuno/tradingcodex](https://github.com/monarchjuno/tradingcodex)** v0.2.0 — 본체 (Apache-2.0)
- **[oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — OpenCode 에이전트 스쿼드 시스템
- **시그니처 시리즈 / Sigco signature series**: `md-doctor`, `cron-doctor`, `kakao-summary`와 동일 패턴

---

## FAQ

**Q. `convert` and `attach` produce nearly identical `.opencode/` directories — why both?**
A. `convert` reads a live TradingCodex workspace you already have
(`tcx attach <dir>` first). `attach` scaffolds a fresh OpenCode workspace
from the bundled TCX v0.2.0 templates without needing TradingCodex
installed — useful for OpenCode-only environments and CI.

**Q. `convert` fails with "tradingcodex requires Python >=3.14,<3.15" on my 3.13 system. What now?**
A. Use `attach` (works on 3.11+). The bundled TCX snapshot gives you
the same OpenCode workspace without the live TCX install. If you need
a true round-trip against your own TCX workspace, install Python 3.14
via pyenv and re-run.

**Q. The OpenCode workspace produced by `convert` and `attach` is byte-identical, right?**
A. Not always. `convert` reflects the **source** TCX workspace's
agents/skills/hooks (which may have been hand-edited). `attach` always
reflects the **bundled** TCX v0.2.0 snapshot. Use
`opencode-trading verify <path> --workspace <tcx_src>` to detect drift.

**Q. `convert --out <dir>` + `verify <dir>` composes cleanly, right?**
A. Yes. `convert --out <dir>` writes the OpenCode artifacts under
`<dir>/.opencode/` (the same layout `attach` uses), and `verify <dir>`
inspects that path. So the natural pairing `convert --out foo && verify
foo` works without manual path manipulation. Same for the `--out`
omitted default: `convert` writes to `<workspace>/.opencode/`, and
`verify <workspace>` reads from there.

**Q. Is this mergeable upstream into monarchjuno/tradingcodex?**
A. v1.0.0 is the merge-readiness release. The adapter is zero-deps,
MIT-licensed, and ships with governance (CONTRIBUTING/CODE_OF_CONDUCT/
SECURITY/AUTHORS), CI coverage (≥ 60%), and an automated release
workflow (`.github/workflows/release.yml` → PyPI trusted publishing).
Open an issue on monarchjuno/tradingcodex with a link to v1.0.0.

**Q. How do I report a security issue?**
A. See [SECURITY.md](SECURITY.md) — do not file a public issue.

---

## 라이선스 / License

MIT — see [LICENSE](LICENSE).

TradingCodex 본체는 Apache-2.0 (별도). 이 어댑터는 독립 프로젝트로 MIT.
The TradingCodex body is Apache-2.0 (separate). This adapter is an independent MIT project.
