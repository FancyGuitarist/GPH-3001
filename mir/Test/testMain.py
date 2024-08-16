import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import os
from io import StringIO
import subprocess
# Assuming the main script is saved as 'py'
# add the ../mir.py to the path so that we can import it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mir')))

from mir.__main__ import parse_args, main, CapitalizedHelpFormatter, error, pgb, pcb
avaible_modes = ['monophonic', 'polyphonic','chord-only']
class TestUtilityFunctions(unittest.TestCase):
    @patch('builtins.print')
    @patch('termcolor.colored')
    def test_error_function(self, mock_print):
        error("Test error message")
        mock_print.assert_called_once_with('\x1b[1m\x1b[31mError:\x1b[0m', 'Test error message')

    @patch('termcolor.colored')
    @patch('builtins.print')
    def test_pgb_function(self, mock_print):
        pgb("Test green message")
        mock_print.assert_called_once_with('\x1b[1m\x1b[32mTest green message\x1b[0m')

    @patch('termcolor.colored')
    @patch('builtins.print')
    def test_pcb_function(self, mock_print):
        pcb("Test cyan message")
        mock_print.assert_called_once_with('\x1b[1m\x1b[36mTest cyan message\x1b[0m')


class TestArgumentParsing(unittest.TestCase):

    def test_parse_args_no_arguments(self):
        # mock sys.argv to simulate no arguments
        # relative path of the current file
        f = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mir'))
        with patch.object(sys, 'argv', [f]):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stdout', new=StringIO()):
                    parse_args(sys.argv)
            self.assertEqual(cm.exception.code, 1)

    def test_parse_args_monophonic_mode(self):
        args = parse_args(['monophonic', '-f', 'test.wav'])
        self.assertEqual(args.Modes, 'monophonic')
        self.assertEqual(args.file, 'test.wav')

    def test_parse_args_polyphonic_mode(self):
        args = parse_args(['polyphonic', '-f', 'test.wav'])
        self.assertEqual(args.Modes, 'polyphonic')
        self.assertEqual(args.file, 'test.wav')

    def test_parse_args_chord_only_mode(self):
        with patch('sys.stdout', new=StringIO()):
            args = parse_args(['chord-only', '-f', 'test.wav'])
        self.assertEqual(args.Modes, 'chord-only')
        self.assertEqual(args.file, 'test.wav')

    def test_invalid_argument(self):
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new=StringIO()):
                parse_args(['invalid'])
        self.assertEqual(cm.exception.code, 2)

    @unittest.expectedFailure
    def test_invalid_mode(self):
        with patch('sys.stderr', new=StringIO()):
            args = parse_args(['falcophonic', '-f', 'test.wav'])

class TestIntegration(unittest.TestCase):
    def setUp(self):
            self.file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'C_scale_dirty.wav'))
            self.output_file = os.path.join(os.path.dirname(__file__), 'output_file_name.pdf')  # Adjust this path as needed
            assert os.path.exists(self.file)

    def tearDown(self):
        # Clean up any output files created by the test
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        # Close the PDF viewer if it's opened
        try:
            # This example assumes 'Preview' on macOS. Replace with the actual process name if different.
            if sys.platform == 'darwin':  # macOS
                subprocess.call(["pkill", "Preview"])
            elif sys.platform == 'win32':  # Windows
                subprocess.call(["taskkill", "/f", "/im", "AcroRd32.exe"])  # Example for Adobe Reader
            elif sys.platform == 'linux':  # Linux
                subprocess.call(["pkill", "evince"])  # Example for Evince PDF viewer
        except Exception as e:
            print(f"Failed to close PDF viewer: {e}")

    def test_main_monophonic(self):
        with patch('sys.stdout', new=StringIO()):
            main(['monophonic', '-f', self.file, '-o', self.output_file])

        # Assert that the output file was created
        self.assertTrue(os.path.exists(self.output_file))

class TestMusicTranscription(unittest.TestCase):

    def test_capitalized_help_formatter(self):
        # Test that help strings are capitalized correctly
        formatter = CapitalizedHelpFormatter(prog="test")
        action = argparse.Action(option_strings=['-e', '--extract'], dest='extract', help='extract the audio of an instrument')
        formatted_help = formatter._get_help_string(action)
        self.assertEqual(formatted_help, 'Extract the audio of an instrument')



if __name__ == '__main__':
    unittest.main()
