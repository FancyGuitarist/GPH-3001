import unittest
import abjad
import numpy as np
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functools import partial
# Assuming the Partition class is defined in a module named `partition`
from mir.anotation import Partition, full_notes
def capture_locals(func):
    def wrapper(*args, **kwargs):
        f_locals = {}
        def profiler(frame, event, _):
            nonlocal f_locals
            if event == 'return':
                f_locals = frame.f_locals.copy()
        orig_profiler = sys.getprofile()
        sys.setprofile(profiler)
        try:
            return func(*args, **kwargs), f_locals
        finally:
            sys.setprofile(orig_profiler)
    return wrapper

class TestPartition(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.simple_notation = [
            ('C4', 0, 4),  # Whole note
            ('D4', 4.0, 2),  # Half note
            ('E4', 6, 1),  # Quarter note
            ('N', 7, 1)   # Rest
        ]
        self.abj_simple_notation = [
            ("c'", 0, 4),  # Whole note
            ("d'", 4.0, 2),  # Half note
            ("e'", 6, 1),  # Quarter note
            ("N", 7, 1)]   # Rest
        self.tempo = 60
        self.simple_notation_with_chords = [
            (['C3','E3','G4'], 0, 4),  # Whole note
            (['D4','F4','A4'], 4.0, 2),  # Half note
            (['E4','G2','B4'], 6, 1),  # Quarter note
            ('N', 7, 1)   # Rest
        ]
        self.partition = Partition(self.tempo)


    def test_initialization(self):
        self.assertEqual(self.partition.tempo, self.tempo)
        # self.assertEqual(self.partition.simple_notation(), self.simple_notation)
    def test_note_name_to_abjad_format(self):
        self.assertEqual(self.partition.note_name_to_abjad_format('C4',join=True), "c'")
        self.assertEqual(self.partition.note_name_to_abjad_format('D#4',join=True), "ds'")

    def test_note_name_to_abjad_format_vectorized(self):
        vec_simple_notation = [note[0] for note in self.simple_notation]
        note_name_to_abjad_join = partial(self.partition.note_name_to_abjad_format, join=True)
        abj_list = list(map(note_name_to_abjad_join, vec_simple_notation))
        for i, abj_note in enumerate(abj_list):
            self.assertEqual(abj_note, self.abj_simple_notation[i][0])



    def test_get_closest_duration(self):
        self.assertEqual(self.partition._get_closest_duration(1), "1/4")
        self.assertEqual(self.partition._get_closest_duration(1/2), "1/8")
        self.assertEqual(self.partition._get_closest_duration(1/4), "1/16")
        self.assertEqual(self.partition._get_closest_duration(1 + 1/2), "3/8")
        self.assertEqual(self.partition._get_closest_duration( 1/2 + 1/4), "3/16")
        self.assertEqual(self.partition._get_closest_duration(  1/4 + 1/8), "3/32")

    def test_full_notes(self):
        self.assertEqual(type(full_notes(self.tempo)), list)

    def test_duration_mapping(self):
        dic = self.partition.duration_mapping_dict
        self.assertEqual(type(dic), dict)
        for k,v in dic.items():
            self.assertEqual(type(k), str)
            self.assertEqual(type(v), float)




    def test_is_bass_treble(self):
        self.assertTrue(self.partition.is_bass_treble(self.simple_notation[0]) == 'bass')

    def test_seperate_treble_bass(self):
        treble_notes, bass_notes = self.partition.separate_treble_bass(self.simple_notation)
        for treb_note in treble_notes:
            self.assertTrue(self.partition.is_bass_treble(treb_note[0]) == 'treble')
        for bass_note in bass_notes:
            self.assertTrue(self.partition.is_bass_treble(bass_note[0]) == 'bass')

    def test_extract_bass_treble_staff(self):
        correct_treb, correct_bass = self.partition.extract_bass_treble_staff(self.simple_notation)
        # verifiy that the correct notes are extracted
        self.assertEqual([note[0] for note in correct_bass], ['C4', 'D4', 'E4', 'N'])
        self.assertEqual([note[0] for note in correct_treb], [])

    def test_to_abjad_staff(self):pass
    def test_separate_treble_bass(self):pass
    def test_sequential_correction(self):pass
    def test_get_duration_rationnal(self):pass
    def test_get_melody_chords_estimate(self):pass
    def test_is_almost_equal(self):pass

    def test_convert_notes_to_abjad(self):
        treble_notes, bass_notes = self.partition.convert_notes_to_abjad(self.simple_notation)

        # Check specific note types and durations
        self.assertIsInstance(treble_notes[0], abjad.Note| abjad.Rest | abjad.Skip)
        self.assertEqual(treble_notes[0].written_duration, abjad.Duration(1, 1))  # Whole note

        self.assertIsInstance(treble_notes[1], abjad.Note | abjad.Rest | abjad.Skip)
        self.assertEqual(treble_notes[1].written_duration, abjad.Duration(1, 2))  # Half note

        self.assertIsInstance(treble_notes[2], abjad.Note| abjad.Rest | abjad.Skip)
        self.assertEqual(treble_notes[2].written_duration, abjad.Duration(1, 4))  # Quarter note

        self.assertIsInstance(treble_notes[3], abjad.Rest| abjad.Rest | abjad.Skip)
        self.assertEqual(treble_notes[3].written_duration, abjad.Duration(1, 4))  # Quarter rest

    def test_score_property(self):
        score = self.partition.score(self.simple_notation)

        # Check if the score contains both treble and bass staffs
        self.assertEqual(len(score), 1) # one staff group of two staffs
        self.assertEqual(len(score[0]), 2) # two staffs (treble and bass]))

        treble_staff = score[0][0]
        bass_staff = score[0][1]

        # Check if clefs and tempo markings are attached correctly
        self.assertEqual(treble_staff.name, 'treble_staff')

        self.assertEqual(bass_staff.name, 'bass_staff')


    def test_save_score(self):
        # For this test, we will create a temporary file
        import tempfile
        import os
        score = self.partition.score(self.simple_notation)
        with tempfile.NamedTemporaryFile() as temp_file:
            out_path, elapsed,formating_time,render_time = self.partition.save_score(score, output_path=temp_file.name)
            self.assertTrue(os.path.exists(out_path))
            self.assertTrue(os.path.getsize(out_path) > 0)




if __name__ == '__main__':
    unittest.main()
