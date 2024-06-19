import contextlib
import io
import logging
import os
import parser
import tempfile

import machine
import pytest


@pytest.mark.golden_test("tests/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.asm")
        target = os.path.join(tmpdirname, "target.json")
        input_file = os.path.join(tmpdirname, "input.txt")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_file, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            parser.main(source, target)
            print("=" * 60)
            machine.main(target, input_file)

        with open(target, encoding="utf-8") as file:
            code = file.read()
        logs = caplog.text.split("\n")
        if len(logs) <= 128:
            log = caplog.text
        else:
            log = "\n".join(
                [
                    *logs[0:64],
                    "\n\n...\n",
                    *logs[-64:],
                ]
            )
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert log == golden.out["out_log"]
