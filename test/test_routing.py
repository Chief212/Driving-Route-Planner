import unittest
from routing import shortest_path


class TestRouting(unittest.TestCase):

    def test_shortest_path(self):
        with self.assertRaises(NotImplementedError):
            shortest_path("Stephenville", "Dublin")


if __name__ == "__main__":
    unittest.main()
