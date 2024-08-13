import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import os


# Assuming the main script is saved as 'py'
# add the ../mir.py to the path so that we can import it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mir')))

from mir.__main__ import create_parser, main, CapitalizedHelpFormatter

class TestArgumentParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = create_parser()

    def test_no_args(self):
        with self.assertRaises(SystemExit):
            with patch('sys.argv', ['mir']):
                args = self.parser.parse_args()
            args = self.parser.parse_args()




class TestMusicTranscription(unittest.TestCase):

    def test_capitalized_help_formatter(self):
        # Test that help strings are capitalized correctly
        formatter = CapitalizedHelpFormatter(prog="test")
        action = argparse.Action(option_strings=['-e', '--extract'], dest='extract', help='extract the audio of an instrument')
        formatted_help = formatter._get_help_string(action)
        self.assertEqual(formatted_help, 'Extract the audio of an instrument')

    def test_create_parser(self):
        parser = create_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)

        # Check if specific arguments exist
        args = parser.parse_args(['-e', 'guitar'])
        self.assertEqual(args.extract, 'guitar')

        args = parser.parse_args(['monophonic', '-f', 'test.wav'])
        self.assertEqual(args.Modes, 'monophonic')
        self.assertEqual(args.file, 'test.wav')

        args = parser.parse_args(['polyphonic', '--benchmark', 'test.midi'])
        self.assertEqual(args.Modes, 'polyphonic')
        self.assertEqual(args.benchmark, 'test.midi')

    @patch('mir.AudioSignal')
    @patch('mir.anotation')
    @patch('os.path.exists')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_polyphonic_mode(self, mock_args, mock_exists, mock_partition, mock_audio_signal):
        mock_args.return_value = argparse.Namespace(
            Modes='polyphonic', file='test.wav', benchmark='test.midi',
            piano_roll=False, debug=None, threshold=0.55, gamma=50,
            standard_deviation=1e-3, output=None, recording=False, url=None
        )
        mock_exists.return_value = True

        with patch('benchmark') as mock_benchmark, \
             patch('sys.exit') as mock_exit:
            main()
            mock_benchmark.assert_called_once_with('test.midi', show_piano=False)
            mock_exit.assert_called_once_with(0)

    @patch('mir.AudioSignal')
    @patch('mir.anotation')
    @patch('os.path.exists')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_monophonic_mode(self, mock_args, mock_exists, mock_partition, mock_audio_signal):
        mock_args.return_value = argparse.Namespace(
            Modes='monophonic', file='test.wav', piano_roll=False,
            output=None, recording=False, url=None
        )

        with patch('sys.exit') as mock_exit:
            main()
            mock_audio_signal.assert_called_once_with('test.wav')
            mock_partition.assert_called_once()
            mock_exit.assert_not_called()

    @patch('mir.AudioSignal')
    @patch('mir.anotation')
    @patch('yt_dlp.YoutubeDL')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_url_mode(self, mock_args, mock_yt_dlp, mock_partition, mock_audio_signal):
        mock_args.return_value = argparse.Namespace(
            Modes='polyphonic', url='http://testurl.com', file=None, recording=False,
            piano_roll=False, debug=None, threshold=0.55, gamma=50,
            standard_deviation=1e-3, output=None
        )

        mock_yt_dlp_instance = MagicMock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_yt_dlp_instance
        mock_yt_dlp_instance.extract_info.return_value = {'format': 'bestaudio', 'ext': 'webm'}
        mock_yt_dlp_instance.prepare_filename.return_value = 'test.webm'

        main()

        mock_yt_dlp_instance.extract_info.assert_called_once_with('http://testurl.com', download=True)
        mock_audio_signal.assert_called_once_with('test.wav')
        mock_partition.assert_called_once()

    @patch('sys.exit')
    @patch('argparse.ArgumentParser.parse_args')
    def test_no_input_provided(self, mock_args, mock_exit):
        mock_args.return_value = argparse.Namespace(Modes=None, file=None, recording=None, url=None)

        with patch('builtins.print') as mock_print:
            main()
            mock_print.assert_called_once_with("No input provided")
            mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
