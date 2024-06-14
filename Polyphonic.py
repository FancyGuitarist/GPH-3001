import librosa
from MusicRetrieval import find_states, transition_matrix, pitches_to_simple_notation, get_closest_duration
import abjad
import numpy as np
import sys
# le problème en ce moment c'est qu'on n'a pas l'information rythmique sur les notes jouées
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

    fmin: float = librosa.note_to_hz(note_min)
    fmax: float = librosa.note_to_hz(note_max)
    midi_min: int = librosa.note_to_midi(note_min)
    midi_max: int = librosa.note_to_midi(note_max)
    n_notes: int = int(midi_max - midi_min + 1)
    # preprocessing
    X = librosa.iirt(y=audio_harmonic, sr=srate, win_length=N, hop_length=H, center=True, tuning=0.0)
    gamma = 1
    X = np.log(1.0 + gamma * X)
    X = librosa.cqt(y=X, bins_per_octave=12, n_bins=midi_max-midi_min+1,fmin=librosa.midi_to_hz(24), norm=None)
    # pitch and voicing

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
# Il faut utilisé une matrice de transition pour determiner correctement les notes jouées
# utiliser les onset pour trouver les notes jouées
def load_audio(audio_path):
    """Charge l'audio et renvoie le signal et le taux d'échantillonnage."""
    y, sr = librosa.load(audio_path)
    y_harmonic = librosa.effects.harmonic(y)
    y_percussive = librosa.effects.percussive(y)
    return y_harmonic, y_percussive, sr

def estimate_fmin_fmax():
    """Estime les fréquences minimales et maximales , pour l'instant c'est la note la plus haute et la plus basse jouable sur un guitare standard accordée en E2-E6."""
    return "E2", "E6"

def decode_pitch(encoded_state: np.array, midi_min=librosa.note_to_midi("E2")):
    """Decode the pitch from the encoded state."""
    silence = np.array([i == 0 for i in encoded_state])
    sustain = np.array([librosa.midi_to_note(i // 2 - 1 + midi_min) if i % 2 == 0 and i != 0 else False for i in encoded_state])
    onset = np.array([librosa.midi_to_note(i // 2 + midi_min) if i % 2 != 0 else False for i in encoded_state])
    return (silence, onset, sustain)

def estimate_pitches(y_harm,y_perc, sr):
    """Estime les pitches en utilisant pyin et filtre les pitches non voicés."""
    """On commence pour une guitare accordée en Tuning standard (E2-E6)"""
    note_min, note_max = estimate_fmin_fmax()
    transmat = transition_matrix(note_min=note_min,note_max=note_max)
    prior = prior_probabilities(y_harm,y_perc, sr)

    states = find_states(priors=prior, transmat=transmat)
    decoded_output = decode_pitch(states, midi_min=librosa.note_to_midi(note_min))
    return decoded_output





def convert_notes_to_abjad(data,tempo):
    """Convertit les tuples de notes en objets Abjad."""
    treble_notes = []
    bass_notes = []
    for note_name, start_time, duration in data:
        # Convert the duration from float to a rational number
        a = get_closest_duration(duration, tempo)
        if a == "1/1":
            duration_rational = abjad.Duration(1)
        else:
            duration_rational = abjad.Duration(a)

        if note_name == '1':  # Handle rest
            abjad_note = abjad.Rest(duration_rational)
        else:
            # Convert note name to abjad format
            note = note_name[:-1].lower()
            if '#' in note or "♯" in note:
                note = note.replace('#', 's')
                note = note.replace('♯', 's')
            octave = int(note_name[-1])
            octave_adjustment = octave - 3
            if octave_adjustment >= 1:
                octave_str = '\'' * octave_adjustment
                treble_notes.append(abjad.Note(f"{note}{octave_str}", duration_rational))
                bass_notes.append(abjad.Skip(duration_rational))

            else:
                octave_str = ',' * abs(octave_adjustment)
                bass_notes.append(abjad.Note(f"{note}{octave_str}", duration_rational))
                treble_notes.append(abjad.Skip(duration_rational))

    return treble_notes, bass_notes

def save_score(score, output_path):
    """Exporte la partition en format LilyPond."""
    abjad.persist.as_ly(score, output_path)

def audio_to_score(audio_path, output_path):
    """Pipeline complet pour convertir un fichier audio en partition."""
    y_harm, y_perc, sr = load_audio(audio_path)
    pitches = estimate_pitches(y_harm, y_perc, sr)
    tempo = librosa.feature.tempo(y=y_perc, sr=sr)
    simple_notation = pitches_to_simple_notation(pitches, sr, hop_length=512)
    treble_notes, bass_notes = convert_notes_to_abjad(simple_notation,tempo)

    treble_staff = abjad.Staff(treble_notes,lilypond_type='Staff',name='treble')
    bass_staff = abjad.Staff(bass_notes,lilypond_type='Staff',name='bass')

    if treble_staff:
        abjad.attach(abjad.Clef('treble'), treble_staff[0])
    if bass_staff:
        abjad.attach(abjad.Clef('bass'), bass_staff[0])
    mark = abjad.MetronomeMark(abjad.Duration(1, 4), int(tempo[0]))
    score = abjad.Score([treble_staff,bass_staff])
    abjad.attach(mark, treble_staff[0])
    save_score(score, output_path)

# Exemple d'utilisation de la fonction
if __name__ == '__main__':
    name = sys.argv[1].split("/")[-1].split(".")[0]
    audio_to_score(sys.argv[1], f'{name}.ly')
