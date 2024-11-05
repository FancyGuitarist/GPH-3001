import sys
import os

from matplotlib.pyplot import imshow
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import pretty_midi as pm

from mir.MusicRetrieval import AudioSignal
from mir.Pseudo2D import Pseudo2D

## Load dataset
# for each song in the dataset, create the pseudo2D representation and associate it with its label
# the label must be 1 where the note is played and 0 where the note isn't
# label vector for a specific time frame will be of N = size midi_max - midi_min + 1
# for each label vector will be associated a 2D matrix[N x N] representing the pseudo2D representation of the time frame
# a song containing T time frame will be a tensor of size (T,N,N)
# with label of size (T,N)
# for a dataset with M songs, we have a Tensor of size (M,T,N,N) associated with label of size (M,T,N)

maestro_dir_path = "../../maestro-v3.0.0/"
pseudo_dir_path = maestro_dir_path + "pseudo2D/"
df = pd.read_csv(maestro_dir_path + "maestro-v3.0.0.csv")

names = df.audio_filename.values

# load first file
audio = AudioSignal(maestro_dir_path + names[0])

pseudo = Pseudo2D(audio)
P2D_generator = pseudo.pseudo_2d
# or
Pseudo2D_array = pseudo.pseudo_as_array()
first = next(P2D_generator)
plt.imshow(np.abs(first),origin="lower")
plt.show()

# from sklearn.decomposition import PCA
