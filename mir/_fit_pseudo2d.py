from sklearn.model_selection import ParameterGrid
from sklearn.base import BaseEstimator
import numpy as np
import os
import sys
from mir_eval.multipitch import evaluate
from mir_eval.util import f_measure as f
import librosa
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mir.MusicRetrieval import AudioParams
from mir.Pseudo2D import Pseudo2D
import pretty_midi as pm
from mir.MusicRetrieval import AudioSignal
import pandas as pd
# Initialize AudioParams
params = AudioParams()

# Load your audio and MIDI files
midi_file_path = 'mir/Validation/polyphonic_piano_test.midi'
X = [AudioSignal('mir/Validation/polyphonic_piano_test.wav')]  # Wrap AudioSignal in a list
def get_midi_roll(midi_file_path=midi_file_path):
    mid = pm.PrettyMIDI(midi_file_path)
    hop_time = (params.hop_length / params.sampling_rate)
    s = len(Pseudo2D(X[0]).cqt.T)
    estimate_time = np.linspace(0, s * hop_time, s)

    midi_roll = np.zeros((128, mid.instruments[0].get_piano_roll(times=estimate_time).shape[1]))
    for instrument in mid.instruments:
        midi_roll = np.ceil(instrument.get_piano_roll(times=estimate_time))
    ground_truth = [librosa.midi_to_hz(np.argwhere(midi_roll[:, i]).flatten()) for i in np.arange(len(midi_roll[1, :]))]
    return estimate_time, ground_truth

est_time, ground_truth = get_midi_roll()

def f_measure_from_song(song, ground_truth=ground_truth, estimate_time=est_time):
    scores = evaluate(estimate_time, ground_truth, estimate_time, song)
    f_measure = f(scores["Precision"], scores["Recall"])
    return f_measure

class Pseudo2DWrapper(BaseEstimator):
    def __init__(self, std_threshold=0.005, n_harmonics=3, gamma=50):
        self.std_threshold = std_threshold
        self.n_harmonics = n_harmonics
        self.gamma = gamma

    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self

    def fit(self, X, y=None):
        self.pseudo2d_instance = Pseudo2D(X[0])  # Unpack the AudioSignal from the list
        self.pseudo2d_instance.std_threshold = self.std_threshold
        self.pseudo2d_instance.n_harmonics = self.n_harmonics
        self.pseudo2d_instance.gamma = self.gamma
        return self

    def score(self, X, y=None):
        song, _ = self.pseudo2d_instance.multipitch_estimate()
        return f_measure_from_song(song)

# Define the parameter grid
param_grid = {
    'std_threshold': [1e-6],
    'threshold' : [0.54],
    'n_harmonics': [3,4],
    'gamma': [550],
    'min_length' : [1]
}
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
# Use ParameterGrid to iterate over all parameter combinations
best_score = -np.inf
best_params = None
pseudo2d_estimator = Pseudo2DWrapper()
tot_item = len(ParameterGrid(param_grid))
i = 0
results = []
print(f"total item : {tot_item}")
import time
start = time.time()
for params in ParameterGrid(param_grid):
    i+=1
    sec_tot = (time.time()-start)*tot_item/i
    print(f"{100*i/tot_item: .2f}% \t {time.time()-start: .2f} sec \t estimated time : {sec_tot//60 : .0f} min {sec_tot%60 : .2f} sec")
    print(LINE_UP, end=LINE_CLEAR)
    pseudo2d_estimator.set_params(**params)
    pseudo2d_estimator.fit(X)
    score = pseudo2d_estimator.score(X)
    results.append({**params, 'score': score})
    if score > best_score:
        best_score = score
        best_params = params
results_df = pd.DataFrame(results)
# Define the path to your CSV file
csv_file_path = 'Notes/pseudo2d_optimization_results.csv'

# Check if the file exists
if os.path.exists(csv_file_path):
    # If the file exists, append the new results without the header
    results_df.to_csv(csv_file_path, mode='a', header=False, index=False)
else:
    # If the file doesn't exist, write the results with the header
    results_df.to_csv(csv_file_path, mode='w', header=True, index=False)
print("Best parameters found:", best_params)
print("Best score:", best_score)
