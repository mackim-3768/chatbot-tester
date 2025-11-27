from __future__ import annotations

from generate.generate_dataset import main as generate_main
from adb_run.run_on_device import main as adb_main
from evaluate.evaluate_results import main as eval_main


def main() -> None:
    # print("[1/3] Generating dataset...")
    # generate_main()

    print("[2/3] Running dataset on ADB device (adb-cli backend)...")
    adb_main()

    print("[3/3] Evaluating run results...")
    eval_main()


if __name__ == "__main__":  # pragma: no cover
    main()
