"""示例包必须一直能用：改了 P03 用例后，模板要跟着重生成。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "gen"))

import make_example_package                    # noqa: E402
import run_tests                               # noqa: E402


def test_example_package_replays_all_pass(tmp_path):
    run = make_example_package.build(tmp_path)
    assert (run / "source" / "final.st").exists()
    assert (run / "test" / "status.json.example").exists()
    assert len(list((run / "test" / "actual").glob("*.csv"))) == 6

    rc = run_tests.main([
        "--cases", str(HERE / "cases" / "P03.csv"),
        "--io", str(HERE / "cases" / "_fixtures" / "P03.io.json"),
        "--out", str(run / "test" / "cases_result.jsonl"),
        "--backend", "replay",
        "--actual", str(run / "test" / "actual"),
        "--run-dir", str(run),
    ])
    assert rc == 0
