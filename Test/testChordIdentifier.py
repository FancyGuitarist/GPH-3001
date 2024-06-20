import unittest
import numpy as np
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Chord import ChordIdentifier, get_dummy_chroma

class TestChordIdentifier(unittest.TestCase):

    def setUp(self):
        self.chroma = get_dummy_chroma()
        self.chord_identifier = ChordIdentifier(self.chroma)

    def test_initialization(self):
        self.assertTrue(np.array_equal(self.chord_identifier.chroma, self.chroma))

    def test_chord_labels(self):
        expected_labels = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
            "Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm",
            "C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7"
        ]
        np.testing.assert_array_equal(self.chord_identifier.chord_labels, expected_labels)

    def test_chord_template(self):
        chord_template = self.chord_identifier.chord_template
        self.assertEqual(chord_template.shape, (12, 36))
        # Test a few specific templates to ensure they are as expected
        major_template = np.array([1,0,0,0,1,0,0,1,0,0,0,0])
        minor_template = np.array([1,0,0,1,0,0,0,1,0,0,0,0])
        dominant_7th_template = np.array([1,0,0,0,1,0,0,0,0,0,1,0])

        # Check the first major template
        np.testing.assert_array_equal(chord_template[:, 0], major_template)
        # Check the first minor template (shifted by 12 positions)
        np.testing.assert_array_equal(chord_template[:, 12], minor_template)
        # Check the first dominant 7th template (shifted by 24 positions)
        np.testing.assert_array_equal(chord_template[:, 24], dominant_7th_template)

    def test_observation_matrix(self):
        mask, obs = self.chord_identifier.observation_matrix
        # Check the shape of the matrices
        self.assertEqual(mask.shape, (36, self.chroma.shape[1]))
        self.assertEqual(obs.shape, (36, self.chroma.shape[1]))
        # Check that the mask is binary (only 0s and 1s)
        self.assertTrue(np.all((mask == 0) | (mask == 1)))
        # Check that each column of the mask has exactly one 1
        self.assertTrue(np.all(np.sum(mask, axis=0) == 1))

    @unittest.skip("Just to avoid showing the plot during testing.")
    def test_show_method(self):
        # Since show() produces a plot, we can't directly test it in the same way.
        # We can, however, ensure it runs without error.
        try:
            self.chord_identifier.show()
        except Exception as e:
            self.fail(f"show() method raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
