#!/usr/bin/env python3
"""
Grade an arm with Pipeline V5, same judge and settings as the baseline
======================================================================

Writes configs/<arm>.yaml from the narrative_v2 config of the arm's base
model (Terra 5.6, or Sol for arms named *_on_sol), pointing REUSE_LABELED_DDX
at work/<arm>.json and tagging the output folder (<base run folder>__<arm>),
then runs pipeline_v5/main/main.py.

Usage:
    py evaluate_arm.py arm_a_self_critique [arm_b_panel ...]
"""

import subprocess
import sys

import yaml

from poc_common import BASE_CONFIGS, EVAL_ROOT, HERE, base_of

PIPELINE_DIR = EVAL_ROOT / "bench" / "pipelines" / "pipeline_v5" / "main"


def write_config(arm: str):
    base = base_of(arm)
    config = yaml.safe_load((PIPELINE_DIR / BASE_CONFIGS[base]).read_text(encoding="utf-8"))
    config["EXPERIMENT_NAME"] = f"narrative_v2-agentic_poc-{arm}"
    config["EXPERIMENT_DESCRIPTION"] = (
        f"PoC de la capa agéntica, brazo {arm}, sobre las listas de {config['DXGPT_EMULATOR']['MODEL']} low "
        "(bench/agentic_poc). Mismo juez y evaluador que la línea base."
    )
    config["REUSE_LABELED_DDX"] = f"bench/agentic_poc/work/{arm}.json"
    config["OUTPUT_TAG"] = arm
    config["MAIN"] = {"SHOULD_EMULATE": False, "SHOULD_LABEL": False, "SHOULD_EVALUATE": True}
    config["TIMESTAMP"] = None
    path = HERE / "configs" / f"{arm}.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def main():
    for arm in sys.argv[1:]:
        config_path = write_config(arm)
        print(f"== {arm}: {config_path}")
        subprocess.run([sys.executable, "main.py", "--config", str(config_path)], cwd=PIPELINE_DIR, check=True)


if __name__ == "__main__":
    main()
