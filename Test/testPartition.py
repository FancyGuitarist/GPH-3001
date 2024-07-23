import unittest
import abjad
import numpy as np

# Assuming the Partition class is defined in a module named `partition`
from anotation import Partition

class TestPartition(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.simple_notation = [
            ('C4', 0, 4),  # Whole note
            ('D4', 4.0, 2),  # Half note
            ('E4', 6, 1),  # Quarter note
            ('N', 7, 1)   # Rest
        ]
        self.tempo = 60
        self.partition = Partition(self.simple_notation, self.tempo)

    def test_initialization(self):
        self.assertEqual(self.partition.tempo, self.tempo)
        self.assertEqual(self.partition.simple_notation, self.simple_notation)

    def test_get_closest_duration(self):
        self.assertEqual(self.partition._get_closest_duration(1), "1/4")
        self.assertEqual(self.partition._get_closest_duration(1/2), "1/8")
        self.assertEqual(self.partition._get_closest_duration(1/4), "1/16")
        self.assertEqual(self.partition._get_closest_duration(1 + 1/2), "3/8")
        self.assertEqual(self.partition._get_closest_duration( 1/2 + 1/4), "3/16")
        self.assertEqual(self.partition._get_closest_duration(  1/4 + 1/8), "3/32")



    def test_convert_notes_to_abjad(self):
        treble_notes, bass_notes = self.partition.convert_notes_to_abjad(self.simple_notation)

        # Check that the correct number of notes were created
        self.assertEqual(len(treble_notes), len(self.simple_notation))

        # Check specific note types and durations
        self.assertIsInstance(treble_notes[0], abjad.Note)
        self.assertEqual(treble_notes[0].written_duration, abjad.Duration(1, 1))  # Whole note

        self.assertIsInstance(treble_notes[1], abjad.Note)
        self.assertEqual(treble_notes[1].written_duration, abjad.Duration(1, 2))  # Half note

        self.assertIsInstance(treble_notes[2], abjad.Note)
        self.assertEqual(treble_notes[2].written_duration, abjad.Duration(1, 4))  # Quarter note

        self.assertIsInstance(treble_notes[3], abjad.Rest)
        self.assertEqual(treble_notes[3].written_duration, abjad.Duration(1, 4))  # Quarter rest

    def test_score_property(self):
        score = self.partition.score

        # Check if the score contains both treble and bass staffs
        self.assertEqual(len(score), 2)

        treble_staff = score[0]
        bass_staff = score[1]

        # Check if clefs and tempo markings are attached correctly
        self.assertEqual(treble_staff.name, 'treble')

        self.assertEqual(bass_staff.name, 'bass')


    def test_save_score(self):
        # For this test, we will create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.ly') as temp_file:
            self.partition.save_score(temp_file.name)
            # Check that the file is not empty
            temp_file.seek(0)
            content = temp_file.read()
            self.assertTrue(len(content) > 0)

if __name__ == '__main__':
    unittest.main()
