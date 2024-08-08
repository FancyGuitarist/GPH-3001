
import unittest
import numpy as np
from unittest.mock import patch
import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from MIR_lib import build_transition_matrix
from MusicRetrieval import Note, AudioParams, AudioSignal, Mono
filepath = os.path.abspath(os.path.dirname(__file__))
AUDIO_PATH = f'{filepath}/simple_note_progression.wav'



class TestNoteClass(unittest.TestCase):
    def test_note_initialization(self):
        note = Note(name='C', octave=4)
        self.assertEqual(note.name, 'C')
        self.assertEqual(note.octave, 4)

    def test_note_string(self):
        note = Note(name='C', octave=4)
        self.assertEqual(note.string, 'C4')

    def test_note_midi(self):
        note = Note(name='C', octave=4)
        self.assertEqual(note.midi, 60)

    def test_note_hz(self):
        note = Note(name='A', octave=4)
        self.assertAlmostEqual(note.hz, 440.0, places=1)

    @unittest.expectedFailure
    def test_bad_note_name(self):
        note = Note(name='H', octave=4)

    @unittest.expectedFailure
    def test_bad_note_octave(self):
        note = Note(name='A', octave=-1)

class TestAudioParams(unittest.TestCase):
    def test_audio_params_initialization(self):
        audio_params = AudioParams()
        self.assertEqual(audio_params.sampling_rate, 22050)
        self.assertEqual(audio_params.frame_length, 2048)
        self.assertEqual(audio_params.hop_length, 512)
        self.assertEqual(audio_params.note_min.string, 'E2')
        self.assertEqual(audio_params.note_max.string, 'C7')

class TestAudioSignal(unittest.TestCase):
    def test_audio_signal_initialization(self):
        audio_signal = AudioSignal(AUDIO_PATH)
        self.assertEqual(audio_signal.sampling_rate, 22050)
        self.assertGreater(len(audio_signal.y), 0)

class TestPrior(unittest.TestCase):
    def test_prior_probability(self):
        audio_signal = AudioSignal(AUDIO_PATH)
        priors = Mono(audio_signal).priors
        n_note = audio_signal.n_notes
        state_size = 2 * n_note + 1
        self.assertEqual(priors.shape[0], state_size)

class TestMono(unittest.TestCase):
    def test_custom_hmm(self):
        audio_signal = AudioSignal(AUDIO_PATH)
        mono = Mono(audio_signal)
        resolved_states = mono.decoded_states
        self.assertEqual(len(resolved_states), mono.priors.shape[1])

class TestPostprocessor(unittest.TestCase):
    def test_postprocessor_simple_notation(self):
        audio_signal = AudioSignal(AUDIO_PATH)
        m = Mono(audio_signal)
        simple_notation = m.simple_notation(m.decoded_states)
        self.assertIsInstance(simple_notation, list)
        self.assertGreater(len(simple_notation), 0)

class TestCleanData(unittest.TestCase):
    def test_simple_notation(self):
        audio_signal = AudioSignal(AUDIO_PATH)
        mono = Mono(audio_signal)
        monophonic_simple_notation = mono.simple_notation(mono.decoded_states)

        note_names = ['C4', 'E4', 'G4', 'C5']
        note_time = 0.5

        for j, event in enumerate(monophonic_simple_notation):
            self.assertEqual(event[0], note_names[j])
            self.assertAlmostEqual(event[1], note_time*j, delta=0.1)
            self.assertAlmostEqual(event[2], note_time, delta=0.1)

class TestDirtyData(unittest.TestCase):
    def test_simple_notation(self):
        DIRTY_AUDIO_PATH = f'{filepath}/C_scale_dirty.wav'
        audio_signal = AudioSignal(DIRTY_AUDIO_PATH)
        m = Mono(audio_signal)
        monophonic_simple_notation = m.simple_notation(m.decoded_states)

        note_names = ["N", 'C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3', 'C4']
        time = [2.577, 0.51, 0.46, 0.48, 0.487, 0.51, 0.487, 0.44, 1.416]
        for j, event in enumerate(monophonic_simple_notation):
            self.assertEqual(event[0], note_names[j])
            self.assertAlmostEqual(event[1], np.sum(time[:j]), delta=0.1)
            self.assertAlmostEqual(event[2], time[j], delta=0.1)
if __name__ == '__main__':
    unittest.main()
