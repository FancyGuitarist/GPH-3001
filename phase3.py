import librosa
import abjad

def load_audio(audio_path):
    """Charge l'audio et renvoie le signal et le taux d'échantillonnage."""
    y, sr = librosa.load(audio_path)
    return y, sr

def estimate_pitches(y, sr):
    """Estime les pitches en utilisant pyin et filtre les pitches non voicés."""
    pitches, voiced_flag, voiced_probs = librosa.pyin(y,
                                                      fmin=librosa.note_to_hz('E2'),
                                                      fmax=librosa.note_to_hz('E6'))

    return pitches[voiced_flag]

def convert_pitches_to_notes(pitches):
    """Convertit les pitches en noms de notes."""
    notes = []
    for pitch in pitches:
        if pitch is not None:
            note_name = librosa.hz_to_note(pitch)
            notes.append(note_name)
    return notes



def convert_notes_to_abjad(notes):
    """Convertit les noms de notes en objets Abjad."""
    abjad_notes = []
    for note in notes:
        note_name = note[:-1].lower()
        if '#' in note_name:
            note_name = note_name.replace('#', 's')
        elif 'b' in note_name:
            note_name = note_name.replace('b', 'f')
        octave = int(note[-1])
        """
        Nous ajustons les octaves en utilisant des apostrophes (')
        pour les octaves au-dessus de 4 et des virgules (,)
        pour les octaves en dessous de 4
        """
        octave_adjustment = octave - 4
        if octave_adjustment >= 0:
            octave_str = '\'' * octave_adjustment
        else:
            octave_str = ',' * abs(octave_adjustment)
        abjad_note = abjad.Note(f"{note_name}{octave_str}")
        abjad_notes.append(abjad_note)
    return abjad_notes





def create_score(abjad_notes):
    """Crée une partition avec Abjad."""
    staff = abjad.Staff(abjad_notes)
    score = abjad.Score([staff])
    return score

def save_score(score, output_path):
    """Exporte la partition en format LilyPond."""
    abjad.persist.as_ly(score, output_path)

def audio_to_score(audio_path, output_path):
    """Pipeline complet pour convertir un fichier audio en partition."""
    y, sr = load_audio(audio_path)
    pitches = estimate_pitches(y, sr)
    notes = convert_pitches_to_notes(pitches)
    abjad_notes = convert_notes_to_abjad(notes)
    score = create_score(abjad_notes)
    save_score(score, output_path)

# Exemple d'utilisation de la fonction
audio_to_score('./song&samples/gamme_C.wav', 'output_score.ly')
