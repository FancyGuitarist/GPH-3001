import numpy as np
import librosa
import soundfile as sf
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from MusicRetrieval import AudioParams
param = AudioParams()
def generate_simple_note_progression():
    duration = 0.5  # Duration of each note in seconds
    note_names = ['C4', 'E4', 'G4', 'C5']  # Note names for the progression
    audio = np.array([])

    for note in note_names:
        hz = librosa.note_to_hz(note)
        t = np.linspace(0, duration, int(param.sampling_rate * duration), endpoint=False)
        sine_wave = 0.5 * np.sin(2 * np.pi * hz * t)
        audio = np.concatenate([audio, sine_wave])
    # Save the generated audio to a file for testing purposes
    sf.write('simple_note_progression.wav', audio, param.sampling_rate)

import soundfile as sf
import tempfile
class MusicGenerator(AudioParams):
    def __init__(self) -> None:
        super().__init__()
        self.harmonics = 5
        self.duration = 1.5
        self.chords = []
    @property
    def t(self):
        return np.linspace(0, self.duration, int(self.sampling_rate * self.duration), endpoint=False)


    def from_pianoroll(self,pianoroll, note_min, hop_time):
        raise NotImplementedError
        result = []
        for note in range(pianoroll.shape[0]):
            note_onsets = np.where(np.diff(np.concatenate(([0], pianoroll[note, :], [0]))) == 1)[0]
            note_offsets = np.where(np.diff(np.concatenate(([0], pianoroll[note, :], [0]))) == -1)[0]
            result.append(list(zip([note + note_min for i in range(note_onsets.__len__())], note_onsets, note_offsets)))

    def _generate_note(self,note:str):
        acc = np.zeros_like(self.t)
        for n in range(0,self.harmonics+1):
            hz = librosa.note_to_hz(note+"4")
            amplitudes = np.exp(-self.t)
            sine_wave = amplitudes * amplitudes * np.sin(2 * np.pi * hz*n * self.t)/librosa.db_to_amplitude(13*n)
            acc += sine_wave
        return acc

    def _generate_chord(self,notes:list):
        audio = np.zeros((np.ceil(self.sampling_rate * self.duration).astype(int)))
        for note in notes:
            audio += self._generate_note(note)
        return audio

    def _map_chord_to_notes(self,chord:str):
        notes = librosa.key_to_notes("C:maj")
        notes = np.roll(notes, 12-notes.index(chord[0]))
        if chord.__contains__("m"):
            third = notes[3]
        else:
            third = notes[4]
        if chord.__contains__("7"):
            seventh = notes[10]
        else:
            seventh = None
        fifth = notes[7]
        return [notes[0], third, fifth, seventh] if seventh else [notes[0], third, fifth]

    def _generate_chord_audio(self,chord:str):
        notes = self._map_chord_to_notes(chord)
        return self._generate_chord(notes)

    def generate_audio(self,chord_list:list):
        acc = np.zeros([0])
        for chord in chord_list:
            acc = np.append(acc, self._generate_chord_audio(chord))
            noise = np.random.normal(0, 0.01, acc.shape)
            acc += noise
        return acc
    @property
    def in_memory_audio(self):
        if not self.chords:
            return None
        audio = self.generate_audio(self.chords)
        return audio

    def play(self,aud:np.array):
          # Play the audio
        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as f:
            filename = f.name
            sf.write(filename, aud, samplerate=self.sampling_rate)
            os.system(f"ffplay -nodisp -autoexit {filename}")

        return None

    def write(self,audio:np.array, filename:str):
        sf.write(filename, audio, samplerate=self.sampling_rate)



import unittest
class TestMusicGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = MusicGenerator()
        self.t = np.linspace(0, self.generator.duration, int(self.generator.sampling_rate * self.generator.duration), endpoint=False)  # 1 second of audio at 44100Hz sampling rate
        self.harmonics = self.generator.harmonics
        self.sampling_rate = self.generator.sampling_rate
        self.duration = self.generator.duration

    def test_generate_note(self):
        note = 'C4'
        result = self.generator._generate_note(note)
        self.assertEqual(len(result), len(self.t))
        self.assertTrue(np.any(result))  # Check that result is not all zeros

    def test_generate_chord(self):
        notes = ['C4', 'E4', 'G4']
        result = self.generator._generate_chord(notes)
        self.assertEqual(len(result), int(np.ceil(self.sampling_rate * self.duration)))
        self.assertTrue(np.any(result))  # Check that result is not all zeros

    def test_map_chord_to_notes_major(self):
        chord = 'C'
        result = self.generator._map_chord_to_notes(chord)
        expected = ['C', 'E', 'G']
        self.assertEqual(result[:3], expected)  # Only check the first three notes

    def test_map_chord_to_notes_minor(self):
        chord = 'Cm'
        result = self.generator._map_chord_to_notes(chord)
        expected = ['C', 'D♯', 'G']
        self.assertEqual(result[:3], expected)  # Only check the first three notes

    def test_map_chord_to_notes_seventh(self):
        chord = 'C7'
        result = self.generator._map_chord_to_notes(chord)
        expected = ['C', 'E', 'G', 'A♯']
        self.assertEqual(result, expected)

if __name__ == '__main__':
    #unittest.main()
    music = MusicGenerator()
    aud = music.generate_audio(['Am','E','G7','Cmaj7','Fmaj7','Dm7','G7','Cmaj7'])
    a = music.play(aud)
