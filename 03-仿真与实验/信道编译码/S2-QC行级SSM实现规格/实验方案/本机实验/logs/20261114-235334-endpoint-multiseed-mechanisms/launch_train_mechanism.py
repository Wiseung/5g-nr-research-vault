"""Supply the missing CLI declaration without editing the frozen training runner."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

LOG = Path(__file__).resolve().parent
ROOT = LOG.parent.parent
TARGET = LOG / "code/train_mechanism.py"
saved = json.loads((LOG / "campaign_code_frozen_before_test.json").read_text())["sha256"]
for relative, expected in saved.items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative

original_parse_args = argparse.ArgumentParser.parse_args


def parse_args_with_mechanism(self, args=None, namespace=None):
    if self.description == "Independent mechanism-control runner, copied from verified formal runner; same50k protocol.":
        assert not any("--mechanism" in action.option_strings for action in self._actions)
        self.add_argument("--mechanism", required=True, choices=["mlp", "ema", "gru"])
    return original_parse_args(self, args, namespace)


argparse.ArgumentParser.parse_args = parse_args_with_mechanism
sys.path.insert(0, str(TARGET.parent))
print(json.dumps({"event": "frozen_runner_cli_adapter", "target": str(TARGET),
                  "target_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
                  "adapter": str(Path(__file__).resolve()),
                  "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "change": "declare --mechanism mlp/ema/gru only"}), flush=True)
runpy.run_path(str(TARGET), run_name="__main__")
