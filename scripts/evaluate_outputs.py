#!/usr/bin/env python
"""
MarketMind AI Dashboard — Structural Evaluation Script
Runs deterministic checks on saved or live analysis results.
Usage:
    python scripts/evaluate_outputs.py --file result.json
    python scripts/evaluate_outputs.py --file result.json --trace-file trace.json
    python scripts/evaluate_outputs.py --api http://localhost:8001 --analysis-id <id>
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import textwrap
from typing import Optional


CHECK_RESULTS: list[dict] = []

EXPECTED_AGENTS = ["research", "sentiment", "valuation", "bull", "bear", "risk", "debate", "cio"]
OPTIONAL_AGENTS = ["memo"]

_USE_UNICODE = False


def _stdout_supports_unicode() -> bool:
    """Check if stdout encoding supports Unicode (e.g. UTF-8)."""
    encoding = getattr(sys.stdout, "encoding", None) or ""
    return "utf" in encoding.lower()


def _record(name: str, passed: Optional[bool], detail: str = "") -> None:
    use_emoji = _USE_UNICODE and _stdout_supports_unicode()
    if use_emoji:
        if passed is True:
            status = "\u2705 PASS"
        elif passed is False:
            status = "\u274c FAIL"
        else:
            status = "\u26a0\ufe0f SKIP"
    else:
        if passed is True:
            status = "PASS"
        elif passed is False:
            status = "FAIL"
        else:
            status = "SKIP"
    CHECK_RESULTS.append({"name": name, "passed": passed, "status": status, "detail": detail})


def run_result_checks(data: dict) -> None:
    """Run all structural checks against an analysis result dict."""
    _record("CIO decision exists",
            bool(data.get("cio_decision")),
            f"cio_decision={'present' if data.get('cio_decision') else 'missing'}")

    cio = data.get("cio_decision") or {}
    action = cio.get("action", "")
    _record("CIO action is valid",
            action in ("BUY", "HOLD", "SELL") if cio else None,
            f"action={action or 'N/A'}")

    conf = cio.get("confidence")
    _record("CIO confidence in [0, 1]",
            isinstance(conf, (int, float)) and 0 <= conf <= 1 if conf is not None else None,
            f"confidence={conf}")

    bull = data.get("bull_case") or {}
    _record("Bull case thesis present",
            bool(bull.get("thesis")),
            f"thesis={'present' if bull.get('thesis') else 'missing'}")
    _record("Bull case evidence present",
            bool(bull.get("evidence")),
            f"evidence_count={len(bull.get('evidence', []))}")

    bear = data.get("bear_case") or {}
    _record("Bear case thesis present",
            bool(bear.get("thesis")),
            f"thesis={'present' if bear.get('thesis') else 'missing'}")
    _record("Bear case evidence present",
            bool(bear.get("evidence")),
            f"evidence_count={len(bear.get('evidence', []))}")

    risk = data.get("risk") or {}
    _record("Risk summary exists",
            bool(risk.get("summary")),
            f"summary={'present' if risk.get('summary') else 'missing'}")

    research = data.get("research") or {}
    news_count = research.get("news_count", 0) or len(research.get("news_articles", []))
    has_data_issue = bool(research.get("data_issues"))
    _record("Research has >=1 source or data issue",
            news_count >= 1 or has_data_issue,
            f"news_count={news_count}, has_data_issues={has_data_issue}")

    lang = data.get("language", "en")
    if lang == "th":
        has_th = False
        if cio.get("reasoning_th"):
            has_th = True
        if research.get("summary_th"):
            has_th = True
        if (data.get("bull_case") or {}).get("thesis_th"):
            has_th = True
        _record("Thai fields present (lang=th)",
                has_th,
                f"at_least_one_th_field={'present' if has_th else 'missing'}")
    else:
        _record("Thai fields present (lang=th)", None, "language is not 'th', skipping")

    eq = data.get("evidence_quality")
    if eq:
        score = eq.get("overall_reliability_score")
        _record("Evidence quality score in [0, 1]",
                isinstance(score, (int, float)) and 0 <= score <= 1,
                f"overall_reliability_score={score}")
    else:
        _record("Evidence quality score exists",
                False,
                "evidence_quality field is missing")

    # ── Evidence Library Checks ──
    evidence_lib = data.get("evidence_library")
    has_research_data = bool(research.get("news_articles") or research.get("reddit_posts"))
    if evidence_lib is not None:
        min_expected = 3 if has_research_data else 1
        _record("Evidence library has sufficient items",
                len(evidence_lib) >= min_expected,
                f"evidence_count={len(evidence_lib)}, min_expected={min_expected}")
        ids = [item.get("id") for item in evidence_lib if item.get("id")]
        _record("Evidence IDs are unique",
                len(ids) == len(set(ids)),
                f"total={len(ids)}, unique={len(set(ids))}")
        expected_ids = [f"E{i}" for i in range(1, len(ids) + 1)]
        _record("Evidence IDs are sequential",
                ids == expected_ids,
                f"found={ids[:5]}, expected={expected_ids[:5]}")
    else:
        _record("Evidence library exists",
                not has_research_data,
                f"evidence_library={'present' if evidence_lib else 'missing'}")

    # ── Investment Memo Checks ──
    memo = data.get("investment_memo")
    if memo is not None:
        _record("Investment memo exists",
                True,
                f"title={memo.get('title', 'N/A')[:50]}")
        sections = memo.get("sections", [])
        _record("Memo has at least 3 sections",
                len(sections) >= 3,
                f"section_count={len(sections)}")
        all_content = memo.get("executive_summary", "")
        for sec in sections:
            all_content += " " + sec.get("content", "")
        citation_matches = re.findall(r"\[E\d+\]", all_content)
        _record("Memo contains valid citation patterns",
                len(citation_matches) > 0,
                f"citation_count={len(citation_matches)}")

        grounding = memo.get("grounding_report")
        if grounding is not None:
            gscore = grounding.get("grounded_score")
            _record("Grounding report exists",
                    True,
                    f"grounded_score={gscore}")
            _record("Grounded score in [0, 1]",
                    isinstance(gscore, (int, float)) and 0 <= gscore <= 1,
                    f"grounded_score={gscore}")
            if evidence_lib:
                ev_ids = {item.get("id") for item in evidence_lib}
                cited_ids = set(re.findall(r"E\d+", all_content))
                # Also collect from structured CitationRef objects
                for sec in sections:
                    for cit in sec.get("citations", []):
                        eid = cit.get("evidence_id", "")
                        if eid:
                            cited_ids.add(eid)
                for kc in memo.get("key_citations", []):
                    eid = kc.get("evidence_id", "")
                    if eid:
                        cited_ids.add(eid)
                unknown = cited_ids - ev_ids
                _record("No unknown evidence IDs in memo citations",
                        len(unknown) == 0,
                        f"unknown={sorted(unknown)[:5]}" if unknown else "all valid")
    else:
        _record("Investment memo exists",
                False,
                "investment_memo field is missing")

    errors = data.get("errors", [])
    fatal_keywords = ["Fatal pipeline error", "all agents failed"]
    has_fatal = any(kw.lower() in str(err).lower() for err in errors for kw in fatal_keywords)
    _record("No fatal pipeline errors",
            not has_fatal,
            f"errors_count={len(errors)}, has_fatal={has_fatal}")


def run_trace_checks(trace: dict | None) -> None:
    """Run checks against the trace data."""
    if trace is None:
        _record("Trace exists", False, "no trace data provided")
        _record("Trace contains all expected agents", None, "no trace data — skipped")
        _record("Trace agent statuses are valid", None, "no trace data — skipped")
        _record("Trace agent durations >= 0", None, "no trace data — skipped")
        _record("Research agent has tool/data-fetch entries", None, "no trace data — skipped")
        return

    _record("Trace exists", True, "trace data present")

    agents = trace.get("agents", [])
    agent_names = [a.get("agent_name", "") for a in agents]
    missing_required = set(EXPECTED_AGENTS) - set(agent_names)
    extra = set(agent_names) - set(EXPECTED_AGENTS) - set(OPTIONAL_AGENTS)
    _record("Trace contains all expected agents",
            len(missing_required) == 0,
            f"found={len(agent_names)} agents, missing={list(missing_required)}" if missing_required
            else f"found {len(agent_names)} agents"
            + (f" (extra: {list(extra)})" if extra else ""))

    valid_statuses = {"pending", "running", "complete", "failed"}
    invalid_statuses = []
    for a in agents:
        st = a.get("status", "")
        if st not in valid_statuses:
            invalid_statuses.append(f"{a.get('agent_name')}={st}")
    _record("Trace agent statuses are valid",
            len(invalid_statuses) == 0,
            f"invalid: {invalid_statuses}" if invalid_statuses else "all statuses valid")

    bad_durations = []
    for a in agents:
        dur = a.get("duration_ms", 0)
        st = a.get("status", "")
        if st in ("complete", "failed") and (dur is None or dur < 0):
            bad_durations.append(f"{a.get('agent_name')}={dur}")
    _record("Trace agent durations >= 0",
            len(bad_durations) == 0,
            f"bad durations: {bad_durations}" if bad_durations else "all durations valid")

    research_agent = next((a for a in agents if a.get("agent_name") == "research"), None)
    has_tools = False
    if research_agent:
        tool_calls = research_agent.get("tool_calls", [])
        has_tools = len(tool_calls) > 0
    _record("Research agent has tool/data-fetch entries",
            has_tools,
            f"tool_calls_count={len(research_agent.get('tool_calls', [])) if research_agent else 0}")


def load_from_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_from_api(base_url: str, analysis_id: str) -> dict:
    import urllib.request
    import urllib.error
    url = f"{base_url.rstrip('/')}/api/analysis/{analysis_id}/result"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}")
        sys.exit(1)


def load_trace_from_api(base_url: str, analysis_id: str) -> dict | None:
    import urllib.request
    import urllib.error
    url = f"{base_url.rstrip('/')}/api/analysis/{analysis_id}/trace"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MarketMind AI -- Structural Evaluation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python scripts/evaluate_outputs.py --file result.json
          python scripts/evaluate_outputs.py --file result.json --trace-file trace.json
          python scripts/evaluate_outputs.py --api http://localhost:8001 --analysis-id abc123
        """),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to a JSON file containing an analysis result")
    group.add_argument("--api", type=str, help="Base URL of the running API")
    parser.add_argument("--analysis-id", type=str, help="Analysis ID (required when using --api)")
    parser.add_argument("--trace-file", type=str, help="Path to a JSON file containing trace data")
    parser.add_argument("--unicode", action="store_true", help="Use emoji status labels")

    args = parser.parse_args()
    global _USE_UNICODE
    _USE_UNICODE = args.unicode
    data: dict = {}
    trace: dict | None = None

    if args.api:
        if not args.analysis_id:
            parser.error("--analysis-id is required when using --api")
        print(f"Loading result from API: {args.api}/api/analysis/{args.analysis_id}/result")
        data = load_from_api(args.api, args.analysis_id)
        print(f"Loading trace from API: {args.api}/api/analysis/{args.analysis_id}/trace")
        trace = load_trace_from_api(args.api, args.analysis_id)
    elif args.file:
        print(f"Loading from file: {args.file}")
        raw = load_from_file(args.file)
        if "result" in raw and isinstance(raw["result"], dict):
            data = raw["result"]
            if "trace" in raw:
                trace = raw["trace"]
        else:
            data = raw
        if args.trace_file:
            print(f"Loading trace from file: {args.trace_file}")
            trace = load_from_file(args.trace_file)

    print(f"\nSymbol: {data.get('symbol', 'N/A')}")
    print(f"Status: {data.get('status', 'N/A')}")
    print(f"CIO Action: {data.get('cio_decision', {}).get('action', 'N/A')}")
    print()

    run_result_checks(data)
    run_trace_checks(trace)

    print("=" * 60)
    print("  EVALUATION REPORT")
    print("=" * 60)
    total = len(CHECK_RESULTS)
    passed = sum(1 for r in CHECK_RESULTS if r["passed"] is True)
    failed = sum(1 for r in CHECK_RESULTS if r["passed"] is False)
    skipped = sum(1 for r in CHECK_RESULTS if r["passed"] is None)

    for check in CHECK_RESULTS:
        detail_str = f"  ({check['detail']})" if check["detail"] else ""
        print(f"  {check['status']}  {check['name']}{detail_str}")

    print("-" * 60)
    print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())