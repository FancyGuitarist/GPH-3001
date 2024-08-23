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
from Pseudo2D import Pseudo2D


params = AudioParams()
#first_10_midi_files = glob('/Users/antoine/Desktop/GPH/E2024/PFE/Validation/maestro-v1.0.0/2017/*.midi')[:10]
#mid = pm.PrettyMIDI(first_10_midi_files[0])

test_1_path = "/Users/antoine/Desktop/GPH/E2024/PFE/mir/Validation/polyphonic_piano_test.midi"



#mr.piano_roll_to_note_sequence()

def convert_midi_to_wav(midi_path):
    """create a temporary file to save the audio generated from the midi file and delete it afterwards"""
    name = midi_path.split("/")[-1].split(".")[0]+".wav"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(current_dir + "/" + name):
        return current_dir + "/" + name
    sig = os.system(f"fluidsynth -ni {current_dir}/TimGM6mb.sf2 {midi_path} -F {name} -r 44100  2> /dev/null")
    if sig != 0:
        raise Exception("Error while converting the midi file to wav, is fluidsynth installed ?")
    return name

def benchmark(midi_path, show_piano=None, clean=False,gamma=500,std_threshold=1e-6,min_length=3,threshold=0.54,template_matrix=None):
    name = convert_midi_to_wav(midi_path)
    audio = AudioSignal(name)
    pseudo = Pseudo2D(audio)

    # optimize the parameters for polyphonic piano
    pseudo.gamma = gamma
    pseudo.std_threshold = std_threshold
    pseudo.min_length = min_length
    pseudo.threshold = threshold
    if template_matrix is not None:
        pseudo.template_matrix = pseudo.generate_template_from_audio_file("/Users/antoine/Desktop/GPH/E2024/PFE/mir/single-piano-note-a3_60bpm_A_major.wav")
    #pseudo.show(1)
    #plt.show()
    #test_result, piano = pseudo.multipitch_estimate()
    # piano = np.roll(piano, -3, axis=1)
#
    score = compare(midi_path, pseudo, sampling_rate=audio.sampling_rate, show_piano=show_piano)
    f_measure = f(score['Precision'], score["Recall"])
    score['F-measure'] = f_measure
    if clean:
        os.system(f"rm {name}")
    return score


def compare(midi_file_path, pseudo: Pseudo2D ,hop_length = params.hop_length, sampling_rate = params.sampling_rate,show_piano=None):
    mid = pm.PrettyMIDI(midi_file_path)

    # shift the piano roll by 2 frame to match the midi file
    test_result, piano = pseudo.multipitch_estimate()
    #piano = np.roll(piano, -2, axis=1)
    #test_result = test_result[2:] + test_result[:2]


    hop_time = (hop_length/sampling_rate)
    s = len(test_result)
    estimate_time = np.linspace(0,s*hop_time,s)

    midi_roll = np.zeros((128, mid.instruments[0].get_piano_roll(times=estimate_time).shape[1]))
    for instrument in mid.instruments:
        midi_roll = np.ceil(instrument.get_piano_roll(times=estimate_time))

    ground_truth = [librosa.midi_to_hz(np.argwhere(midi_roll[:,i]).flatten()) for i in np.arange(len(midi_roll[1,:])) ]

    if show_piano:
        fig, (ax)= plt.subplots()
        #ax1.imshow(midi_roll, aspect='auto', origin='lower', interpolation='nearest')
        #librosa.display.specshow(midi_roll, y_axis='cqt_note', x_axis='time', sr=sampling_rate, hop_length=hop_length, ax=ax1, fmin=librosa.midi_to_hz(0))
        ax.title.set_text('Vérité Absolue (rose) et Estimation (bleu))')
        #ax.legend(labels=['Ground Truth', 'Estimate'], loc='upper right')
        librosa.display.specshow(midi_roll, y_axis='cqt_note', x_axis='time', sr=sampling_rate, hop_length=hop_length, ax=ax, cmap='Reds', alpha=0.5)
        librosa.display.specshow(piano, y_axis='cqt_note', x_axis='time', sr=sampling_rate, hop_length=hop_length, ax=ax, fmin=librosa.midi_to_hz(pseudo.note_min.midi + 24.0) , cmap='Blues', alpha=0.5)
        fig.tight_layout()
        ax.set_xlabel('Temps (minutes : secondes)')

        fig.set_size_inches(12, 6)

        plt.show()
    scores = evaluate(estimate_time,ground_truth,estimate_time,test_result)
    return scores




if __name__ == "__main__":
    score = benchmark(test_1_path,show_piano=True)
    print(score)
