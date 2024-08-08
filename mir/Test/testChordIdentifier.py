import unittest
import numpy as np
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Chord import ChordIdentifier, get_dummy_chroma
from MusicRetrieval import AudioSignal
AUDIO_PATH = 'song&samples/polyphonic.wav'

class TestChordIdentifier(unittest.TestCase):

    def setUp(self):
        self.chroma = get_dummy_chroma(path=AUDIO_PATH)
        self.audio = AudioSignal(AUDIO_PATH)
        self.chord_identifier = ChordIdentifier(self.audio)

    def test_initialization(self):
        self.assertTrue(np.array_equal(self.chord_identifier.chroma, self.chroma))

    def test_chord_labels(self):
        expected_labels = [
            "S","C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
            "Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm",
            "C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7"
        ]
        np.testing.assert_array_equal(self.chord_identifier.chord_labels, expected_labels)

    def test_chord_template(self):
        chord_template = self.chord_identifier.chord_template
        self.assertEqual(chord_template.shape, (12, 37))
        # Test a few specific templates to ensure they are as expected
        major_template = np.array([1,0,0,0,1,0,0,1,0,0,0,0])/np.sqrt(3)
        minor_template = np.array([1,0,0,1,0,0,0,1,0,0,0,0])/np.sqrt(3)
        dominant_7th_template = np.array([1,0,0,0,1,0,0,0,0,0,1,0])/np.sqrt(3)
        silence_template = np.ones(12)/np.sqrt(12)

        # Check the first silence template
        np.testing.assert_array_equal(chord_template[:, 0], silence_template)
        # Check the first major template
        np.testing.assert_array_equal(chord_template[:, 1], major_template)
        # Check the first minor template (shifted by 12 positions)
        np.testing.assert_array_equal(chord_template[:, 1 + 12], minor_template)
        # Check the first dominant 7th template (shifted by 24 positions)
        np.testing.assert_array_equal(chord_template[:, 1 + 24], dominant_7th_template)


    def test_observation_matrix(self):
        mask, obs = self.chord_identifier.observation_matrix
        # Check the shape of the matrices
        self.assertEqual(mask.shape, (37, self.chroma.shape[1]))
        self.assertEqual(obs.shape, (37, self.chroma.shape[1]))
        # Check that the mask is binary (only 0s and 1s)
        self.assertTrue(np.all((mask == 0) | (mask == 1)))
        # Check that each column of the mask has exactly one 1
        self.assertTrue(np.all(np.sum(mask, axis=0) == 1))


    def test_simple_notation(self):
        simple_notation = self.chord_identifier.simple_notation()
        expected_notation = [('S', 0.0, 4.20281179138322), ('B7', 4.20281179138322, 2.229115646258504),
            ('S', 6.431927437641724, 0.5340589569160992), ('E7', 6.965986394557823, 1.1145578231292523),
            ('S', 8.080544217687075, 0.6037188208616779), ('D7', 8.684263038548753, 1.3931972789115648),
            ('S', 10.077460317460318, 0.9287981859410426), ('G', 11.00625850340136, 1.787936507936509),
            ('S', 12.79419501133787, 1.5789569160997718)]
        for i in range(len(simple_notation)):
            self.assertEqual(simple_notation[i][0], expected_notation[i][0])
            self.assertAlmostEqual(simple_notation[i][1], expected_notation[i][1], delta=1e-3)
            self.assertAlmostEqual(simple_notation[i][2], expected_notation[i][2], delta=1e-3)

    @unittest.skip("Just to avoid showing the plot during testing.")
    def test_show_method(self):
        # Since show() produces a plot, we can't directly test it in the same way.
        # We can, however, ensure it runs without error.
        try:
            self.chord_identifier.show(this="result")
        except Exception as e:
            self.fail(f"show() method raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
