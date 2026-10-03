"""Explain the canonical private-ingress reference chain as structured JSON."""

import json
from pathlib import Path

from .validate import explain_private_ingress


def main() -> int:
    root = Path(__file__).resolve().parents[1]

    def load(path):
        return json.loads((root / path).read_text())

    result = explain_private_ingress(load("examples/mintie/traffic-policy.json"),
                                    load("examples/mintie/deployment.json"),
                                    load("contracts/roles.json"),
                                    load("examples/mintie/health-profiles.json"),
                                    load("contracts/health-contract.json"))
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
