import librosa
from numpy.random.mtrand import sample
import scipy.io.wavfile as wav
import numpy as np
from enum import Enum
from MIR_lib import classify_case, Situation, Note_State, MusicDynamics
#test = "/Users/antoine/Desktop/GPH/E2024/PFE/80bpm.wav"
audiopath = './song&samples/Chopin_fantaisy_impromptu.wav'
#samples, sr = load(test)
#chroma = chroma_stft(y=samples,sr=sr)

# break musical note in their time fraction
# insert them in a sheet


# TODO: estimer les  prob_stay_note et prob_stay_silence en analysant l'échantillon
# state -> (ON, sustain, silence, vibrato(ON variant), bend( ON variant))


def transition_matrix(note_min="E2",note_max="E6", prob_stay_note=0.9,prob_stay_silence=0.5):
    # state 1, 3, 5 ... are onsets
    # state 2, 4, 6 ... are sustains
    number_of_notes =int(librosa.note_to_midi(note_max) - librosa.note_to_midi(note_min) + 1) # + 1 for it to be inclusive
    N = 2*number_of_notes + 1 # +1 for silence
    transition_matrix = np.zeros((N,N))
    for i in range(N):
        for j in range(N):
            match classify_case(i,j):
                case Situation.SILENCE_to_SILENCE:
                    transition_matrix[i,j] = prob_stay_silence
                case Situation.SILENCE_to_ONSET:
                    transition_matrix[i,j] = (1 - prob_stay_silence)/number_of_notes
                case Situation.ONSET_to_SUSTAIN: # assuming window is to small to go from onset to onset or onset to silence
                    transition_matrix[i,j] = 1
                case Situation.SUSTAIN_to_SUSTAIN:
                    transition_matrix[i,j] = prob_stay_note
                case Situation.SUSTAIN_to_SILENCE:
                    transition_matrix[i,j] = (1 - prob_stay_note)/(number_of_notes+1)
                case Situation.SUSTAIN_to_ONSET:
                    transition_matrix[i,j] = (1 - prob_stay_note)/(number_of_notes+1)
    return transition_matrix
# debbuging -> print(np.sum(transition_matrix(),axis=1))

"""https://github.com/tiagoft/audio_to_midi/blob/master/sound_to_midi/monophonic.py"""
def prior_probabilities(
        audio_harmonic: np.array,
        audio_percussive: np.array,
        srate: int,
        note_min: str = "E2",
        note_max: str = "E6",
        frame_length: int = 2048,
        hop_length: int = 512,
        pitch_acc: float = 0.9,
        voiced_acc: float = 0.9,
        onset_acc: float = 0.9,
        spread: float = 0.2) -> np.array:
    """
    Estimate prior (observed) probabilities from audio signal

    Parameters
    ----------
    audio_signal : 1-D numpy array
        Array containing audio samples

    note_min : string, 'A#4' format
        Lowest note supported by this estimator
    note_max : string, 'A#4' format
        Highest note supported by this estimator
    srate : int
        Sample rate.
    frame_length : int
    window_length : int
    hop_length : int
        Parameters for FFT estimation
    pitch_acc : float, between 0 and 1
        Probability (estimated) that the pitch estimator is correct.
    voiced_acc : float, between 0 and 1
        Estimated accuracy of the "voiced" parameter.
    onset_acc : float, between 0 and 1
        Estimated accuracy of the onset detector.
    spread : float, between 0 and 1
        Probability that the singer/musician had a one-semitone deviation
        due to vibrato or glissando.

    Returns
    -------
    priors : 2D numpy array.
        priors[j,t] is the prior probability of being in state j at time t.

    """

    fmin = librosa.note_to_hz(note_min)
    fmax = librosa.note_to_hz(note_max)
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi(note_max)
    n_notes = int(midi_max - midi_min + 1)

    # pitch and voicing
    pitch, voiced_flag, voiced_prob = librosa.pyin(
        y=audio_harmonic, fmin=float(fmin * 0.9), fmax=float(fmax * 1.1),
        sr=srate, frame_length=frame_length, win_length=int(frame_length / 2),
        hop_length=hop_length)
    tuning = librosa.pitch_tuning(pitch)
    f0_ = np.round(librosa.hz_to_midi(pitch - tuning)).astype(int)
    onsets = librosa.onset.onset_detect(
        y=audio_percussive, sr=srate,
        hop_length=hop_length, backtrack=True)

    priors = np.zeros((n_notes * 2 + 1, len(pitch)))

    for n_frame in range(len(pitch)):
        if not voiced_flag[n_frame]:
            priors[0, n_frame] = voiced_acc
        else:
            priors[0, n_frame] = 1 - voiced_acc

        for j in range(n_notes):
            if n_frame in onsets:  # detected an onset
                priors[(j * 2) + 1, n_frame] = onset_acc
            else:
                priors[(j * 2) + 1, n_frame] = (1 - onset_acc) / n_notes

            if (j + midi_min) == f0_[n_frame]:  # sustain detected
                priors[(j * 2) + 2, n_frame] = pitch_acc
            elif np.abs(j + midi_min - f0_[n_frame]) == 1:
                priors[(j * 2) + 2, n_frame] = pitch_acc * spread
            else:
                priors[(j * 2) + 2, n_frame] = (1 - pitch_acc) / n_notes

    # Normalize priors for each frame
    for n_frame in range(len(pitch)):
        priors[:, n_frame] /= np.sum(priors[:, n_frame])

    return priors


def find_states(priors, transmat) -> np.array :
    p_init = np.zeros(transmat.shape[0])
    p_init[0] = 1
    states  = librosa.sequence.viterbi(priors, transmat, p_init=p_init)
    return states



def pitches_to_simple_notation(pitch,sr,hop_length=512):
    hop_time = hop_length / sr

    def get_index(some_list):
        for i, item in enumerate(some_list):
            if item != "False":
                yield i, item
    def get_length(indexes):
        # handle last ellement correctly
        return np.diff(indexes)

    def full_process(index:dict):
        i = np.array(list(index.keys()))
        length = get_length(i)
        return list(zip(index.values(),i*hop_time,hop_time*length))

    s = np.insert(np.diff(np.array(pitch[0]).astype(int)),0,1)
    fullon = np.where(s == 1, s, pitch[1]) # add virtual onset representing begining of silence
    np.append(fullon,1)

    # add a virtual onset to the end of the song to handle hanging sustain
    for i in range(len(fullon) -1,0,-1):
        item = fullon[i]
        if item != "False" and item != 1:
            fullon = np.append(fullon,item)
            break

    fu = dict(get_index(fullon))
    return full_process(fu)

def get_closest_duration(duration,tempo):
    quarter_note = 60 / tempo
    half_note = quarter_note * 2
    whole_note = quarter_note * 4
    eighth_note = quarter_note / 2
    sixteenth_note = quarter_note / 4
    thirty_second_note = quarter_note / 8

    dotted_half_note = quarter_note + half_note
    dotted_quarter_note = quarter_note + eighth_note
    dotted_eighth_note = eighth_note + sixteenth_note
    dotted_sixteenth_note = sixteenth_note + thirty_second_note

    full_note = [("1/1" , whole_note), ("1/2" , half_note), ("1/4" , quarter_note), ("1/8" , eighth_note),
        ( "1/16" , sixteenth_note), ("1/32" , thirty_second_note)]
    dotted_note = [ ("3/2"  , dotted_half_note) , ("3/4" , dotted_quarter_note) ,
        ("3/8" , dotted_eighth_note), ("3/16" , dotted_sixteenth_note) ]
    total_note = full_note + dotted_note

    value_of_best_fit = lambda duration:\
        min(total_note, key = lambda x: np.abs(duration - x[1]))
    best_fit = value_of_best_fit(duration)[0]

    return best_fit
