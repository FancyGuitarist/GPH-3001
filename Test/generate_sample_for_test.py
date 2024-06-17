import numpy as np
import librosa
import soundfile as sf

def generate_simple_note_progression():
    sr = 22050  # Sample rate
    duration = 0.5  # Duration of each note in seconds
    note_names = ['C4', 'E4', 'G4', 'C5']  # Note names for the progression
    audio = np.array([])

    for note in note_names:
        hz = librosa.note_to_hz(note)
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        sine_wave = 0.5 * np.sin(2 * np.pi * hz * t)
        audio = np.concatenate([audio, sine_wave])

    # Save the generated audio to a file for testing purposes
    sf.write('simple_note_progression.wav', audio, sr)

    return audio, sr

# Generate and save the note progression
generate_simple_note_progression()

