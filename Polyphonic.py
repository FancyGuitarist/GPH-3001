import librosa
from MusicRetrieval import find_states, prior_probabilities, transition_matrix, pitches_to_simple_notation, get_closest_duration
import abjad
import numpy as np
import matplotlib.pyplot as plt
import sys
# le problème en ce moment c'est qu'on n'a pas l'information rythmique sur les notes jouées
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
    channnels =
    states = find_states(priors=prior, transmat=transmat)
    decoded_output = decode_pitch(states, midi_min=librosa.note_to_midi(note_min))
    return decoded_output





def convert_notes_to_abjad(data,tempo):
    """Convertit les tuples de notes en objets Abjad."""
    abjad_notes = []
    for note_name, start_time, duration in data:
        # Convert the duration from float to a rational number
        a = get_closest_duration(duration, tempo)
        treble_staff = abjad.Staff(lilypond_type='Staff')
        bass_staff = abjad.Staff(lilypond_type='Staff')
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
            if octave_adjustment >= 0:
                octave_str = '\'' * octave_adjustment
            else:
                octave_str = ',' * abs(octave_adjustment)
            abjad_note = abjad.Note(f"{note}{octave_str}", duration_rational)

        abjad_notes.append(abjad_note)
    return abjad_notes

def save_score(score, output_path):
    """Exporte la partition en format LilyPond."""
    abjad.persist.as_ly(score, output_path)

def audio_to_score(audio_path, output_path):
    """Pipeline complet pour convertir un fichier audio en partition."""
    y_harm, y_perc, sr = load_audio(audio_path)
    pitches = estimate_pitches(y_harm, y_perc, sr)
    tempo = librosa.feature.tempo(y= y_perc, sr=sr)
    simple_notation = pitches_to_simple_notation(pitches, sr, hop_length=512)

    abjad_notes = convert_notes_to_abjad(simple_notation,tempo)
    staff = abjad.Staff(abjad_notes)
    mark = abjad.MetronomeMark(abjad.Duration(1, 4), int(tempo[0]))
    abjad.attach(mark, staff[0])
    score = abjad.Score([staff])
    save_score(score, output_path)


    #remove all false ellement of the on list

# Exemple d'utilisation de la fonction
if __name__ == '__main__':
    name = sys.argv[1].split("/")[-1].split(".")[0]
    print(name)
    audio_to_score(sys.argv[1], f'{name}.ly')
