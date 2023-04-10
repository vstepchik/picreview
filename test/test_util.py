import unittest

from parameterized import parameterized

from app.utils import sizeof_fmt


class TestSizeofFmt(unittest.TestCase):

    @parameterized.expand([
        (0, "0B"),
        (-0, "0B"),
        (1, "1B"),
        (-1, "-1B"),
        (1023, "1023B"),
        (1024, "1.00KiB"),
        (1024 ** 2 - 1, "1024.00KiB"),
        (1024 ** 2 - 8, "1023.99KiB"),
        (1024 ** 2, "1.00MiB"),
        (1024 ** 3, "1.00GiB"),
        (-1024 ** 3, "-1.00GiB"),
        (1024 ** 4, "1.00TiB"),
        (1024 ** 5, "1.00PiB"),
        (1024 ** 6, "1.00EiB"),
        (1024 ** 7, "1.00ZiB"),
        (1024 ** 8, "1.00YiB"),
        (1024 ** 9, "1024.00YiB"),
        (1024 ** 9 + 1, "1024.00YiB"),
        (1024 ** 9 + 1023 ** 8, "1024.99YiB"),
    ], name_func=lambda f, d, p: f"test_{p[0][0]}_bytes")
    def test_sizeof_fmt(self, input_bytes: int, expected_output: str):
        result = sizeof_fmt(input_bytes)
        self.assertEqual(expected_output, result)


if __name__ == "__main__":
    unittest.main()
