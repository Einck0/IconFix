from __future__ import annotations

import unittest

from iconfix.workflow import parse_selection


class WorkflowSelectionTests(unittest.TestCase):
    def test_parse_zero_as_select_all(self) -> None:
        self.assertEqual(parse_selection("0", 3), [1, 2, 3])

    def test_parse_whitespace_and_commas(self) -> None:
        self.assertEqual(parse_selection("1, 3 2", 3), [1, 2, 3])

    def test_parse_invalid_index_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_selection("4", 3)


if __name__ == "__main__":
    unittest.main()
