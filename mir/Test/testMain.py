import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import os


# Assuming the main script is saved as 'music_transcription.py'
# add the ../mir.py to the path so that we can import it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mir.__main__ import main,create_parser

class TestArgumentParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = create_parser()

    def test_no_args(self):
        with self.assertRaises(SystemExit):
            with patch('sys.argv', ['mir']):
                args = self.parser.parse_args()
            args = self.parser.parse_args()
if __name__ == '__main__':
    unittest.main()
