#!/usr/bin/env python3
"""
계약 문서 시간 표기 린트 — ADR-0010 래칫.

    python3 .claude/scripts/contract-lint.py            # 전체
    python3 .claude/scripts/contract-lint.py <경로...>  # 지정 파일만

에러 0 이어야 통과. **경고는 전수를 ①ADR참조/②협의이력/③취소선사료/④그외 로 분류해 ④ 가 0건이어야** 넘어간다.
("확인했다"는 검증 가능한 진술이 아니다 — 2026-08-06 첫 사용에서 그렇게 보고했다가 ④ 2건이 새어나갔다.)

════════════════════════════════════════════════════════════════════════
왜 있나
════════════════════════════════════════════════════════════════════════
ADR-0010(2026-07-31)이 wire 시간 포맷을 `Instant`/ISO-8601 UTC 에서
`LocalDateTime`/`yyyy-MM-dd HH:mm:ss` (KST) 로 바꿨다. 그런데 **계약 문서 갱신이
일부만 됐다** — `friends` 계약은 2026-08-06 까지 옛 포맷 그대로였고,
`challenge-create` 는 헤더에 취소선만 있고 본문 14곳이 낡은 채였다.

**계약이 서버가 보내지 않는 것을 보낸다고 말하는 상태**였고, 이건 누락이 아니라
능동적 오류다. nullable 표를 아무리 잘 만들어도 이 축은 안 잡힌다.

════════════════════════════════════════════════════════════════════════
🔴 이 스크립트의 한계 — 정확히 알고 써라
════════════════════════════════════════════════════════════════════════
1. **시간 축만 본다.** enum 값·필드 존재·타입 일치는 안 본다.
   응답 shape(키 제거·개명)은 서버의 `WireShapeContractTest` 가 덮는다.

2. **발견 도구가 아니라 래칫이다.** 지금 위반 0 인 것은 2026-08-06 에 사람이
   14+6+2 곳을 고쳤기 때문이지 이 스크립트가 찾아준 게 아니다.
   **역할은 "깨끗한 상태로 되돌아가지 못하게 잠그는 것"** 이다.

3. **T2(산문)는 경고일 뿐 판정이 아니다.** ADR 참조·협의 이력·취소선 사료처럼
   **정당한 등장이 많다.** 에러로 만들면 사람이 억지로 지우거나 린트를 끈다.
   목표는 "위반 0" 이 아니라 **사람이 한 번 눈으로 보게 만드는 것**이다.

4. **아무도 안 돌리면 없느니만 못하다.** PM 레포 문서 대상이라 자동으로 돌 게 없다.
   구동 지점은 `.claude/skills/api-contract/SKILL.md` 체크리스트 하나뿐이다.
"""
import json
import re
import sys
from pathlib import Path

# ── ADR-0010 wire 포맷 ────────────────────────────────────────────────
ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$")
WIRE_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
WIRE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# ── T2 산문 토큰 ──────────────────────────────────────────────────────
# `Z` 단독은 오탐이 너무 많아 넣지 않는다. 시간 문맥에서만 의미 있는 토큰만 본다.
PROSE_TOKENS = [
    (re.compile(r"ISO-?8601"), "ISO-8601 표기"),
    (re.compile(r"\bInstant\b"), "`Instant` 타입"),
    (re.compile(r"→\s*UTC|->\s*UTC"), "UTC 변환 표기"),
    (re.compile(r"OffsetDateTime"), "`OffsetDateTime` 타입"),
]

DEFAULT_GLOBS = [
    "docs/features/*/api-contract*.md",
    # 🔴 스킬 템플릿도 본다 — **새 계약이 여기서 나온다.**
    # 2026-08-06 실측: 이 파일이 "시간 포맷은 ISO-8601 UTC 고정" 을 규칙으로 적고 있었다.
    # 계약만 고치고 발원지를 두면 다음 계약이 같은 오류를 갖고 태어난다.
    ".claude/skills/api-contract/SKILL.md",
]


def json_blocks(md: str):
    """```json 블록을 (블록번호, 시작줄, 본문) 으로."""
    for i, m in enumerate(re.finditer(r"```json\s*\n(.*?)```", md, re.S), 1):
        yield i, md[: m.start()].count("\n") + 1, m.group(1)


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def lint(path: Path):
    """(errors, warnings) 반환. 각 원소는 (줄번호, 설명)."""
    md = path.read_text()
    errors, warnings = [], []

    # ── T1: json 블록 안의 시간 리터럴 (에러) ──
    for _, line, body in json_blocks(md):
        try:
            doc = json.loads(body)
        except json.JSONDecodeError:
            continue  # 플레이스홀더가 아니라 진짜 깨진 블록. 여기서 판정하지 않는다.
        for key, val in walk_strings(doc):
            if ISO_Z.match(val):
                errors.append((line, f"{key} = \"{val}\" — ADR-0010 위반. 기대: \"yyyy-MM-dd HH:mm:ss\" (KST)"))

    # ── T2: 산문 토큰 (경고) ──
    for lineno, text in enumerate(md.splitlines(), 1):
        for pat, label in PROSE_TOKENS:
            if pat.search(text):
                warnings.append((lineno, f"{label} — 정당한 등장인지 확인 (ADR 참조·협의 이력·취소선 사료는 정상)"))
                break

    return errors, warnings


def main(argv):
    root = Path(__file__).resolve().parents[2]
    if argv:
        targets = [Path(a) for a in argv]
    else:
        targets = sorted({p for g in DEFAULT_GLOBS for p in root.glob(g)})

    n_err = n_warn = 0
    for p in targets:
        if not p.exists():
            continue
        errors, warnings = lint(p)
        if not (errors or warnings):
            continue
        rel = p.relative_to(root) if p.is_absolute() and root in p.parents else p
        print(f"\n📄 {rel}")
        for line, msg in errors:
            print(f"  🔴 ERROR  L{line}: {msg}")
        for line, msg in warnings:
            print(f"  🟡 WARN   L{line}: {msg}")
        n_err += len(errors)
        n_warn += len(warnings)

    print(f"\n{'─' * 60}")
    print(f"  검사 {len(targets)}개 파일 — 🔴 ERROR {n_err} / 🟡 WARN {n_warn}")
    if n_err:
        print("  ❌ 에러가 있다. json 예시의 시간 리터럴을 ADR-0010 포맷으로 고쳐라.")
    else:
        print("  ✅ ERROR 0. 이제 WARN 을 전수로 ①ADR참조 / ②협의이력 / ③취소선사료 / ④그외 로 분류해라.")
        print("     🔴 통과 조건은 \"확인했다\" 가 아니라 \"④ 0건\" 이다. 건수를 줄이는 게 목표가 아니다 —")
        print("        제대로 된 정정은 옛 문구를 인용으로 남기므로 경고가 오히려 는다.")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
