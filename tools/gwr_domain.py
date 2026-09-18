from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gwr.domain_sdk import DomainSDK


def main():
    ap = argparse.ArgumentParser(prog="gwr-domain")
    sub = ap.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("path")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("path")

    scaffold = sub.add_parser("scaffold")
    scaffold.add_argument("domain_id")
    scaffold.add_argument("--display-name")
    scaffold.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.command == "validate":
        report = DomainSDK.validate(args.path).to_dict()
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report["ok"] else 1)
    if args.command == "inspect":
        print(json.dumps(DomainSDK.inspect(args.path), indent=2))
        return
    text = DomainSDK.scaffold(args.domain_id, display_name=args.display_name)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
