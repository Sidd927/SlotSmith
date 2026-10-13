"""Command line: generate | allocate | verify | revise."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .export import summary, write_workbook
from .generator import generate, make_revision
from .ingest import read_mdb
from .pipeline import run
from .revision import revise
from .rules import RuleSet, default_ruleset
from .verifier import load_allocation, summarize, total_violations, verify


def _rules(path: str | None) -> RuleSet:
    return RuleSet.load(path) if path else default_ruleset()


# Exit codes (documented in README and the dossier): 0 = every verification family ran and found no violation;
# 2 = at least one violation (takes precedence); 3 = no violation but verification is incomplete (a family was SKIPPED
# because its rule is switched off). 1 is left to argparse/uncaught errors.
EXIT_OK, EXIT_VIOLATIONS, EXIT_INCOMPLETE = 0, 2, 3


def _exit_code(check: list[dict]) -> int:
    if total_violations(check) or summarize(check)["failed"]:
        return EXIT_VIOLATIONS
    return EXIT_INCOMPLETE if summarize(check)["outcome"] != "passed" else EXIT_OK


def _outcome(check: list[dict]) -> str:
    """One truthful line about the verification: counts and outcome (a skipped family is not a pass)."""
    sm = summarize(check)
    txt = f"verification: {sm['passed']} passed, {sm['failed']} failed, {sm['skipped']} skipped of {sm['total']} -> {sm['outcome']}"
    if sm["skipped_rules"]:
        txt += " (skipped: " + "; ".join(f"{r} {n}" for r, n in sm["skipped_rules"]) + ")"
    return txt


def _warn_if_incomplete(check: list[dict]) -> None:
    if summarize(check)["outcome"] != "passed":
        print(_outcome(check), file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="slotsmith")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="write a SYNTHETIC IO MDB (and optional Rev B)")
    g.add_argument("--signals", type=int, default=2000)
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--errors", type=int, default=0, help="number of injected data errors")
    g.add_argument("--out", required=True)
    g.add_argument("--rev-b", help="also write a Rev B derived from this MDB")

    a = sub.add_parser("allocate", help="MDB(s) -> filled allocation workbook + rule check")
    a.add_argument("mdb", nargs="+")
    a.add_argument("--rules")
    a.add_argument("--out", required=True)

    v = sub.add_parser("verify", help="independently re-check an allocation workbook")
    v.add_argument("allocation")
    v.add_argument("--mdb", nargs="+", required=True)
    v.add_argument("--rules")

    r = sub.add_parser("revise", help="Rev A allocation + Rev B MDB -> Rev B allocation with fewest moves")
    r.add_argument("--prev", required=True, help="Rev A allocation workbook")
    r.add_argument("--mdb", nargs="+", required=True, help="Rev B MDB file(s)")
    r.add_argument("--rules")
    r.add_argument("--out", required=True)

    sub.add_parser("rules", help="print the default rule set as JSON")

    args = ap.parse_args(argv)
    if args.cmd == "generate":
        gr = generate(args.signals, seed=args.seed, inject_errors=args.errors)
        gr.df.to_excel(args.out, index=False, sheet_name="IO MDB (SYNTHETIC)")
        if gr.injected:
            Path(args.out).with_suffix(".injected.json").write_text(json.dumps(gr.injected, indent=1))
        if args.rev_b:
            make_revision(gr.df, seed=args.seed + 1).to_excel(args.rev_b, index=False, sheet_name="IO MDB (SYNTHETIC)")
        print(f"wrote {args.out} ({len(gr.df)} rows, synthetic)")
    elif args.cmd == "allocate":
        res = run(args.mdb, _rules(args.rules), args.out)
        print(json.dumps({**res.metrics, **{k: round(t, 3) for k, t in res.timings.items()}}, indent=1))
        _warn_if_incomplete(res.check)
        return _exit_code(res.check)
    elif args.cmd == "verify":
        rules = _rules(args.rules)
        rep = verify(load_allocation(args.allocation), read_mdb(args.mdb).df, rules)
        for c in rep:
            print(f"{c['Result']:7s} {c['Rule']:8s} {c['Violations']:5d}  {c['Check']}  {(c['Examples'] or c.get('Note', ''))[:120]}")
        print(_outcome(rep))
        return _exit_code(rep)
    elif args.cmd == "revise":
        rules = _rules(args.rules)
        prev = load_allocation(args.prev)
        mdb_b = read_mdb(args.mdb).df
        rr = revise(prev, mdb_b, rules)
        meta = {"tool": "SlotSmith revise", "prev": args.prev, "rev_b": ", ".join(args.mdb)}
        write_workbook(args.out, rr.rows, rr.summary, rr.tqs, [], rules, meta, impact=rr.impact)
        rr.check = verify(load_allocation(args.out), mdb_b, rules)      # re-check the file actually written
        rr.metrics["violations"] = total_violations(rr.check)
        write_workbook(args.out, rr.rows, rr.summary, rr.tqs, rr.check, rules, meta, impact=rr.impact)
        print(json.dumps({k: v for k, v in rr.metrics.items() if k != "cabinets_hit"} |
                         {"cabinets_hit": len(rr.metrics["cabinets_hit"])}, indent=1))
        _warn_if_incomplete(rr.check)
        return _exit_code(rr.check)
    elif args.cmd == "rules":
        print(default_ruleset().model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
