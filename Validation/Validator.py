import librosa
from matplotlib import legend
import pretty_midi as pm
from glob import glob
import matplotlib.pyplot as plt
import sys
import os
from mir_eval.multipitch import evaluate
from mir_eval.util import f_measure as f
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from MusicRetrieval import  AudioParams, AudioSignal
from bivariate import Pseudo2D


params = AudioParams()
first_10_midi_files = glob('/Users/antoine/Desktop/GPH/E2024/PFE/Validation/maestro-v1.0.0/2017/*.midi')[:10]
mid = pm.PrettyMIDI(first_10_midi_files[0])

test_1_path = "/Users/antoine/Desktop/GPH/E2024/PFE/Validation/maestro-v1.0.0/2017/MIDI-Unprocessed_041_PIANO041_MID--AUDIO-split_07-06-17_Piano-e_1-01_wav--1.midi"



#mr.piano_roll_to_note_sequence()

def convert_midi_to_wav(midi_path):
    """create a temporary file to save the audio generated from the midi file and delete it afterwards"""
    name = midi_path.split("/")[-1].split(".")[0]+".wav"
    if os.path.exists(name):
        return name
    os.system(f"fluidsynth -ni /Users/antoine/Desktop/GPH/E2024/PFE/Validation/TimGM6mb.sf2 {midi_path} -F {name} -r 44100  2> /dev/null")
    return name

def load_and_clean(midi_path):
    name = convert_midi_to_wav(midi_path)
    audio = AudioSignal(name)
    pseudo = Pseudo2D(audio)
    test_result, piano = pseudo.multipitch_estimate()
    score = benchmark(midi_path, pseudo, hop_length=audio.hop_length, sampling_rate=audio.sampling_rate)
    f_measure = f(score['Precision'], score["Recall"])
    score['F-measure'] = f_measure
    return score


def benchmark(midi_file_path, pseudo: Pseudo2D ,hop_length = params.hop_length, sampling_rate = params.sampling_rate,show_piano=None):
    mid = pm.PrettyMIDI(midi_file_path)
    test_result, piano = pseudo.multipitch_estimate()
    hop_time = (hop_length/sampling_rate)
    s = len(test_result)
    estimate_time = np.linspace(0,s*hop_time,s)

    midi_roll = np.zeros((128, mid.instruments[0].get_piano_roll(times=estimate_time).shape[1]))
    for instrument in mid.instruments:
        midi_roll = np.ceil(instrument.get_piano_roll(times=estimate_time))

    ground_truth = [librosa.midi_to_hz(np.argwhere(midi_roll[:,i]).flatten()) for i in np.arange(len(midi_roll[1,:])) ]

    if (show_piano is not None):
        fig, (ax)= plt.subplots()
        #ax1.imshow(midi_roll, aspect='auto', origin='lower', interpolation='nearest')
        #librosa.display.specshow(midi_roll, y_axis='cqt_note', x_axis='time', sr=sampling_rate, hop_length=hop_length, ax=ax1, fmin=librosa.midi_to_hz(0))
        ax.title.set_text('Ground Truth and Estimate')
        #ax.legend(labels=['Ground Truth', 'Estimate'], loc='upper right')
        librosa.display.specshow(midi_roll, y_axis='cqt_note', x_axis='time', sr=sampling_rate, hop_length=hop_length, ax=ax, cmap='Reds', alpha=0.5)
        librosa.display.specshow(piano, y_axis='cqt_note', x_axis='time', sr=sampling_rate, hop_length=hop_length, ax=ax, fmin=librosa.midi_to_hz(pseudo.note_min.midi + 24.0) , cmap='Blues', alpha=0.5)
        fig.tight_layout()

        fig.set_size_inches(12, 6)
        plt.legend(['Legend','1;',"dick"],loc='upper right')

        plt.show()
    scores = evaluate(estimate_time,ground_truth,estimate_time,test_result)
    return scores




if __name__ == "__main__":
    score = load_and_clean(test_1_path)
    print(score)
