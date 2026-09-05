from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


MATRIX_PATH = Path(__file__).with_name("parecer_acceptance_matrix.json")


class ParecerAcceptanceMatrixTest(unittest.TestCase):
    def test_all_fourteen_acceptance_cases_reference_executable_tests(self) -> None:
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

        self.assertEqual([item["caso"] for item in matrix], list(range(1, 15)))
        self.assertEqual(len({item["descricao"] for item in matrix}), 14)
        for item in matrix:
            module_name, class_name, method_name = item["teste"].rsplit(".", 2)
            module = importlib.import_module(module_name)
            test_class = getattr(module, class_name)
            self.assertTrue(
                callable(getattr(test_class, method_name, None)),
                f"caso {item['caso']} sem teste executável",
            )


if __name__ == "__main__":
    unittest.main()
