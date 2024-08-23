from numpy._typing import _VoidCodes
from numpy.typing import NDArray
from typing_extensions import Any
import librosa
#import scipy.io.wavfile as wav
import numpy as np
from enum import Enum
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mir.MIR_lib import  Situation, Note_State, MusicDynamics, build_transition_matrix, classify_case
import matplotlib.pyplot as plt
# TODO utiliser la librairy HMMlearn pour implémenter un modèle HMM
# from hmmlearn import hmm
# h = hmm.Categorical()
import warnings
warnings.filterwarnings("ignore")
"""
Le model suivant est basé sur le travail de Tiago Fernandes Tavares et son projet audio_to_midi
https://github.com/tiagoft/audio_to_midi/blob/master/sound_to_midi/monophonic.py
"""


class Note:
    def __init__(self, name: str, octave: int):
        nl = "ABCDEFG"
        notelist = nl + "".join([f"{l}#" for l in nl]) + "".join([f"{l}b" for l in nl])
        if name not in notelist:
            raise ValueError("Invalid note name, please provide a name in the format 'A#4'")
        if not (0 <= octave <= 8):
            raise ValueError("Invalid octave, please provide an octave between 0 and 8")
        self.name : str = name
        self.octave : int = octave
    @classmethod
    def from_midi(cls, midi: int):
        note = librosa.midi_to_note(midi)
        self = cls(note[:-1], int(note[-1]))
        return self
    @property
    def string(self) -> str:
        return f"{self.name}{self.octave}"
    @property
    def midi(self) -> int:
        return int(librosa.note_to_midi(self.string))
    @property
    def hz(self) -> float:
        return float(librosa.note_to_hz(self.string))

class AudioParams:
    """
    note_min : string, 'A#4' format
        Lowest note supported by this estimator
    note_max : string, 'A#4' format
        Highest note supported by this estimator
    sampling_rate : int
        Sample rate.
    frame_length : int
    window_length : int
    hop_length : int
        Parameters for FFT estimation
    """
    def __init__(self):
        self.sampling_rate: int = 22050
        self.note_min = Note("E", 2)
        self.note_max = Note("C", 7)
        self.frame_length: int = 2048
        self.hop_length: int = 512
        self.window_length = int(self.frame_length / 2)
        self.hop_time = self.hop_length / self.sampling_rate
    @property
    def n_notes(self):
        return self.note_max.midi - self.note_min.midi + 1

class AudioSignal(AudioParams):
    def __init__(self, audio: str | np.ndarray):
        super(AudioSignal,self).__init__()
        if type(audio) == np.ndarray:
            self.y = audio
        elif type(audio) == str:
            self.y, _ = librosa.load(audio, sr=self.sampling_rate)
        else:
            raise ValueError("Audio must be a path to a file or a numpy array")
        self.y_harmonic = librosa.effects.harmonic(self.y)
        self.y_percussive = librosa.effects.percussive(self.y)
        tempo =  librosa.feature.tempo(y=self.y_percussive, sr=self.sampling_rate, hop_length=self.hop_length)
        self.tempo = tempo[0] if type(tempo) == np.ndarray else tempo

class MonoParams(AudioParams):

    """"
    pitch_acc : float, between 0 and 1
        Probability (estimated) that the pitch estimator is correct.
    voiced_acc : float, between 0 and 1
        Estimated accuracy of the "voiced" parameter.
    onset_acc : float, between 0 and 1
        Estimated accuracy of the onset detector.
    spread : float, between 0 and 1
        Probability that the singer/musician had a one-semitone deviation
        due to vibrato or glissando.
    """
    def __init__(self):
        super(MonoParams,self).__init__()
        self.pitch_acc: float = 0.9
        self.voiced_acc: float = 0.9
        self.onset_acc: float = 0.9
        self.spread: float = 0.2
        self.onset_slice = slice(1,None,2)
        self.sustain_slice = slice(2,None,2)
        self.silence_slice = 0



class Mono(MonoParams):
    """
    Mono class is used to estimate the pitch of a monophonic audio signal.
    ----------
    Methods:
        prepare_chroma() -> return : chroma
        pyin() -> return : f0, voiced_flag, voiced_prob
    ----------
    attributes:
        priors -> return : np.array
        transition_matrix -> return : [2N+1, 12N+1] np.array
        p_init -> return : np.array
        simple_notation -> return : [()...()]
        pianoroll -> return : (slience, onset, sustain)
    """
    def __init__(self, audio: AudioSignal):
        super(Mono, self).__init__()
        self.audio_harmonic = audio.y_harmonic
        self.audio_percussive = audio.y_percussive
        self.pitch, self.voiced_flag, self.voiced_prob = self.pyin()
        self.tuning = librosa.pitch_tuning(self.pitch)

    def prepare_chroma(self):
        chroma = librosa.feature.chroma_cqt(y=self.audio_harmonic, sr=self.sampling_rate, hop_length=self.hop_length,
            tuning=self.tuning, threshold=0.4, n_octaves=4, bins_per_octave=12, fmin=self.note_min.hz)
        # TODO: maybe do some logarithmic compression to increase the robustness to timbre and volume
        return chroma

    def pyin(self):
        f0, voiced_flag, voiced_prob = librosa.pyin(
                y=self.audio_harmonic, fmin=float(self.note_min.hz * 0.9), fmax=float(self.note_max.hz * 1.1),
                sr=self.sampling_rate, frame_length=self.frame_length, win_length=self.window_length,
                hop_length=self.hop_length)
        return f0, voiced_flag, voiced_prob

    def no_hmm(self, threshold=0.7) -> np.ndarray:
        pitch, voiced_flag, voiced_prob = (self.pitch, self.voiced_flag, self.voiced_prob)

        f0_ = np.round(librosa.hz_to_midi(pitch - self.tuning)).astype(int)
        # make a pinaoroll with the notes
        pianoroll = np.zeros((self.n_notes, len(pitch)))
        for index, (note, voice) in enumerate(list(zip(f0_, voiced_flag))):
            pianoroll[note - self.note_min.midi, index] = 1 if ( voiced_prob[index] > threshold) else 0
            #print(note, voice, voiced_prob[index])
        return pianoroll

    def show_piano_roll(self):
        pianoroll = self.no_hmm()
        plt.figure(figsize=(12, 4))
        librosa.display.specshow(pianoroll, x_axis='time', y_axis='cqt_note', hop_length=self.hop_length)
        plt.xlabel('Time')
        plt.ylabel('Note')
        plt.title('Piano roll')
        plt.show()


    @property
    def priors(self) -> np.array:
        """
        Use Pyin to estimate pitch and voicing, and onset detection to estimate onset frame.
        Initialise a priors matrix with the estimated probabilities.

        Parameters
        ----------
        self : a Prior object

        """
        # pitch and voicing
        pitch, voiced_flag, voiced_prob = (self.pitch, self.voiced_flag, self.voiced_prob)

        f0_ = np.round(librosa.hz_to_midi(pitch - self.tuning)).astype(int)
        onsets = librosa.onset.onset_detect(
            y=self.audio_percussive, sr=self.sampling_rate,
            hop_length=self.hop_length, backtrack=True)

        priors = np.zeros((self.n_notes * 2 + 1, len(pitch)))

        priors[self.silence_slice, ~voiced_flag] = self.voiced_acc
        priors[self.silence_slice, voiced_flag] = 1 - self.voiced_acc

        onset_flags = np.zeros(len(pitch), dtype=bool)
        onset_flags[onsets] = True

        priors[self.onset_slice, onset_flags] = self.onset_acc  # Set priors for onsets
        priors[self.onset_slice, ~onset_flags] = (1 - self.onset_acc) / self.n_notes  # Set priors for non-onsets
        # TODO remove for loop and vectorize the procedure
        sustain_indices = np.arange(self.n_notes) + self.note_min.midi

        for j in range(self.n_notes):
            sustain_flag = (sustain_indices[j] == f0_)
            spread_flag = (np.abs(sustain_indices[j] - f0_) == 1)
            priors[(j*2) + 2, sustain_flag] = voiced_prob[sustain_flag] * self.pitch_acc
            priors[(j*2) + 2, spread_flag] = voiced_prob[spread_flag] * self.pitch_acc * self.spread
            priors[(j*2) + 2, ~sustain_flag & ~spread_flag] = (1 - self.pitch_acc * voiced_prob[~sustain_flag & ~spread_flag]) / self.n_notes

        # Normalize priors for each frame

        priors /= np.sum(priors, axis=0, keepdims=True)
        return priors

    @property
    def transition_matrix(self):

        """
        Initialize the transition matrix for the HMM model.

        Parameters
        ----------
        prob_stay_note : float
            The probability of staying in the same note state.
        prob_stay_silence : float
            The probability of staying in the silence state.
        Return
        ------
        transition_matrix : 2D np.array
            The transition matrix for the HMM model.
        """
        # state 1, 3, 5 ... are onsets
        # state 2, 4, 6 ... are sustains
        N = 2 * self.n_notes + 1  # +1 for silence state
        transition_matrix = np.zeros((N,N))

        prob_stay_note=0.9
        prob_stay_silence=0.5

        for i in range(N):
            for j in range(N):
                match classify_case(i,j):
                    case Situation.SILENCE_to_SILENCE:
                        transition_matrix[i,j] = prob_stay_silence
                    case Situation.SILENCE_to_ONSET:
                        transition_matrix[i,j] = (1 - prob_stay_silence)/self.n_notes
                    case Situation.ONSET_to_SUSTAIN: # assuming window is to small to go from onset to onset or onset to silence
                        transition_matrix[i,j] = 1
                    case Situation.SUSTAIN_to_SUSTAIN:
                        transition_matrix[i,j] = prob_stay_note
                    case Situation.SUSTAIN_to_SILENCE:
                        transition_matrix[i,j] = (1 - prob_stay_note)/(self.n_notes+1)
                    case Situation.SUSTAIN_to_ONSET:
                        transition_matrix[i,j] = (1 - prob_stay_note)/(self.n_notes+1)
        return transition_matrix

    @property
    def p_init(self) -> np.array:
        """
        Initialise initial probabilities with uniform distribution over onset and silence states
        """
        p_init = np.zeros(self.transition_matrix.shape[0])
        p =  1/ (self.n_notes + 1)
        p_init[0] = p
        p_init[1::2] = p
        return p_init

    @property
    def decoded_states(self):
        """return a list of note value."""
        self.encoded_state = librosa.sequence.viterbi(self.priors, self.transition_matrix, p_init=self.p_init)
        result = []
        for i in self.encoded_state:
            if i == 0:
                result.append("N")
            elif i % 2 == 0:
                result.append(librosa.midi_to_note(i // 2 - 1 + self.note_min.midi))
            else:
                result.append(librosa.midi_to_note(i // 2 + self.note_min.midi))

        return np.array(result)


    def simple_notation(self, result ):
        """
        Convert HMM result to simple notation.

        Parameters
        ----------
        result : np.array of note as string format e.g. 'C4', 'N'

        Returns
        -------
        simple_notation : list of tuple (note: string, onset_time: float, note_duration: float)
        """

        change_index = np.insert(np.where(result[1:] != result[:-1])[0] + 1, 0, 0)
        onset_time = change_index * self.hop_time
        duration = np.append(onset_time[1:], len(result) * self.hop_time) - onset_time
        return list(zip(result[change_index], onset_time, duration))


if __name__ == "__main__":
    audio = AudioSignal("song&samples/gamme_C.wav")
    mono = Mono(audio)
    piano = mono.no_hmm()
    notes = []
    for t in range(piano.shape[1]):
        if np.any(piano[:,t]):
            notes += librosa.midi_to_note(np.argwhere(piano[:,t]) + mono.note_min.midi)
        else:
            notes.append("N")
    simple_notation = mono.simple_notation(notes)
    mono.show_piano_roll()
