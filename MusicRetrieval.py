import librosa
import scipy.io.wavfile as wav
import numpy as np
from enum import Enum
from MIR_lib import classify_case, Situation, Note_State, MusicDynamics
from scipy.sparse import lil_matrix, csr_matrix

# TODO utiliser la librairy HMMlearn pour implémenter un modèle HMM
# from hmmlearn import hmm
# h = hmm.Categorical()

"""
Le model suivant est basé sur le travail de Tiago Fernandes Tavares et son projet audio_to_midi

https://github.com/tiagoft/audio_to_midi/blob/master/sound_to_midi/monophonic.py
"""



class Note:
    def __init__(self, name: str, octave: int):
        self.name : str = name
        self.octave : int = octave
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
        self.note_max = Note("E", 6)
        self.frame_length: int = 2048
        self.hop_length: int = 512
        self.window_length = int(self.frame_length / 2)
        self.n_notes: int = self.note_max.midi - self.note_min.midi + 1
        self.hop_time = self.hop_length / self.sampling_rate


class AudioSignal(AudioParams):
    def __init__(self, audio_path: str):
        super(AudioSignal,self).__init__()
        self.y, _ = librosa.load(audio_path,sr=self.sampling_rate)
        self.y_harmonic = librosa.effects.harmonic(self.y)
        self.y_percussive = librosa.effects.percussive(self.y)
        tempo =  librosa.feature.tempo(y=self.y_percussive, sr=self.sampling_rate, hop_length=self.hop_length)
        self.tempo = tempo[0] if type(tempo) == np.ndarray else tempo

class Params(AudioParams):
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
        super(Params,self).__init__()
        self.pitch_acc: float = 0.9
        self.voiced_acc: float = 0.9
        self.onset_acc: float = 0.9
        self.spread: float = 0.2



class Prior(Params):
    """
    Estimate prior (observed) probabilities from audio signal

    Parameters
    ----------
    audio_signal : 1-D numpy array
        Array containing audio samples

    Returns
    -------
    priors : 2D numpy array.
        priors[j,t] is the prior probability of being in state j at time t.

    """
    def __init__(self, audio_harmonic, audio_percussive):
        super(Prior,self).__init__()
        self.audio_harmonic = audio_harmonic
        self.audio_percussive = audio_percussive

    def pyin(self):
        f0, voiced_flag, voiced_prob = librosa.pyin(
                y=self.audio_harmonic, fmin=float(self.note_min.hz * 0.9), fmax=float(self.note_max.hz * 1.1),
                sr=self.sampling_rate, frame_length=self.frame_length, win_length=self.window_length,
                hop_length=self.hop_length)
        return f0, voiced_flag, voiced_prob

    @property
    def probability(self) -> np.array:
        """
        Use Pyin to estimate pitch and voicing, and onset detection to estimate onset frame.
        Initialise a priors matrix with the estimated probabilities.

        Parameters
        ----------
        self : a Prior object



        """
        # pitch and voicing
        pitch, voiced_flag, voiced_prob = self.pyin()
        tuning = librosa.pitch_tuning(pitch)
        f0_ = np.round(librosa.hz_to_midi(pitch - tuning)).astype(int)
        onsets = librosa.onset.onset_detect(
            y=self.audio_percussive, sr=self.sampling_rate,
            hop_length=self.hop_length, backtrack=True)

        priors = np.zeros((self.n_notes * 2 + 1, len(pitch)))

        priors[0,~voiced_flag] = self.voiced_acc
        priors[0,voiced_flag] = 1 - self.voiced_acc

        onset_flags = np.zeros(len(pitch), dtype=bool)
        onset_flags[onsets] = True

        priors[1::2, onset_flags] = self.onset_acc  # Set priors for onsets
        priors[1::2, ~onset_flags] = (1 - self.onset_acc) / self.n_notes  # Set priors for non-onsets
        # # TODO enlever la for loop et vectoriser la procédure
        sustain_indices = np.arange(self.n_notes) + self.note_min.midi
        # sustain_flag = (sustain_indices[:] == f0_)
        # spread_flag = (np.abs(sustain_indices[:] - (f0_)) == 1)
        for j in range(self.n_notes):
            sustain_flag = (sustain_indices[j] == f0_)
            spread_flag = (np.abs(sustain_indices[j] - f0_) == 1)
            priors[(j*2) + 2, sustain_flag] = voiced_prob[sustain_flag] * self.pitch_acc
            priors[(j*2) + 2, spread_flag] = voiced_prob[spread_flag] * self.pitch_acc * self.spread
            priors[(j*2) + 2, ~sustain_flag & ~spread_flag] = (1 - self.pitch_acc * voiced_prob[~sustain_flag & ~spread_flag]) / self.n_notes

        # priors[2::2, sustain_flag] = voiced_prob[sustain_flag] * self.pitch_acc
        # priors[2::2, spread_flag] = voiced_prob[spread_flag] * self.pitch_acc * self.spread
        # priors[2::2, ~sustain_flag & ~spread_flag] = (1 - self.pitch_acc * voiced_prob[~sustain_flag & ~spread_flag]) / self.n_notes

        # Normalize priors for each frame

        priors /= np.sum(priors, axis=0, keepdims=True)
        return priors

class CustomHMM(Params):
    def __init__(self, priors: Prior, transition_matrix: np.array = None, algorithm: str = 'viterbi'):
        super(CustomHMM,self).__init__()
        self.priors = priors.probability
        if transition_matrix is None:
            self.transition_matrix = self._transition_matrix()
        else:
            self.transition_matrix = transition_matrix

    def _transition_matrix(self):

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
        prob_stay_note=0.9
        N = 2 * self.n_notes + 1  # +1 for silence state
        prob_stay_silence=0.5
        transition_matrix = np.zeros((N,N))
         # Initialize a sparse matrix in List of Lists (LIL) format

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
    def _resolved_states(self) -> np.array :
        """
        Use viterbi algorithm to find the most likely states

        Parameters
        ----------
        priors : 2D numpy array.
            priors[j,t] is the prior probability of being in state j at time t.

        transmat : 2D numpy array.
            transmat[i,j] is the probability of transitioning from state i to state j.
        """
        p_init = np.zeros(self.transition_matrix.shape[0])
        p =  1/ (self.n_notes + 1)
        p_init[0] = p
        p_init[1::2] = p
        states  = librosa.sequence.viterbi(self.priors, self.transition_matrix, p_init=p_init)
        return states

    def decode_result(self):
        """return a tuple of 3 lists: silence, onset, sustain. Each list contains a False value if the state is not present, otherwise it contains the note value."""
        encoded_state: np.array = self._resolved_states
        silence = np.array([i == 0 for i in encoded_state])
        sustain = np.array([librosa.midi_to_note(i // 2 - 1 + self.note_min.midi) if i % 2 == 0 and i != 0 else False for i in encoded_state])
        onset = np.array([librosa.midi_to_note(i // 2 + self.note_min.midi) if i % 2 != 0 else False for i in encoded_state])
        return (silence, onset, sustain)


class Postprocessor(Params):
    def __init__(self, hmm :CustomHMM):
        super(Postprocessor,self).__init__()
        # pour l'instant, on n'utilise pas le sustain, peut-être pourrait-on simplifier le HMM et ne pas le calculer
        self.hmm = hmm
        self.silence, self.onset, _ = hmm.decode_result()

    @property
    def simple_notation(self):
        """
        Convert hmm result to simple notation

        Parameters
        ----------
            self.silence : list of 0 and 1 representing on/off of silence state
            self.onset : list of string (ex: "A#4") or False representing onset state of a certain note pitch
            self.sustain : list of string (ex: "A#4") or False representing sustain state of a certain note pitch
        Returns
        -------
        simple_notation : list of tuple (note : string , onset_time : float, note_duration : float)
        """
        if type(self.hmm) == CustomHMM:
            def get_index(some_list):
                for i, item in enumerate(some_list):
                    if item != "False":
                        yield i, item
            def get_length(indexes):
                # doesn't handle last element correctly
                return np.diff(indexes)

            def mysimple_notation(index:dict):
                i = np.array(list(index.keys()))
                length = get_length(i)
                return list(zip(index.values(),i*self.hop_time, self.hop_time*length))

            s = np.diff(np.array(self.silence).astype(int),prepend=0)
            fullon = np.where(s == 1, s, self.onset) # add virtual onset representing begining of silence
            np.append(fullon,1)

            # add a virtual onset to the end of the song to handle hanging sustain

            for i in range(len(fullon) -1,0,-1):
                item = fullon[i]
                if item != "False" and item != 1:
                    fullon = np.append(fullon, item)
                    break

            fu = dict(list(get_index(fullon)))
            return mysimple_notation(fu)
        else:
            raise ValueError("hmm should be a CustomHMM object")
