import librosa
from matplotlib.colors import Colormap, Normalize
from MusicRetrieval import AudioSignal
import numpy as np
import matplotlib.pyplot as plt

from Test.testBasic import AUDIO_PATH

"""
This package uses chord templates with harmonics, where the chroma patterns also account for the harmonics of the chord notes.
"""
def get_dummy_chroma(hop_length=512,sr=22050):
    AUDIO_PATH = "./song&samples/polyphonic.wav"
    y, _ = librosa.load(AUDIO_PATH,sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    return chroma




class ChordIdentifier(AudioSignal):
    def __init__(self, AUDIO_PATH):
        super(ChordIdentifier,self).__init__(AUDIO_PATH)
        self.chroma = get_dummy_chroma(hop_length=self.hop_length, sr=self.sampling_rate) # chroma matrix

    @property
    def chord_transition_matrix(self):
        """
        Transition matrix between chords
        ------------------------------
        p: probability of staying in the same chord
        N: number of chords
        A: transition matrix
        transition matrix A is a N x N matrix where A[i,j] is the probability of transitioning from chord i to chord j
        """
        p=0.9
        p_stay_silent = 0.5
        N=self.chord_labels.shape[0]
        """compute a uniform transition matrix between chords"""
        A = np.ones((N,N)) * (1-p)/(N-1)
        np.fill_diagonal(A,p)
        A[0,0] = p_stay_silent
        A[0,1:] = (1-p_stay_silent)/(N-1)
        return A
    @property
    def chord_labels(self):
        label = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        minor_label = [label[i] + "m" for i in range(12)]
        dominant_label = [label[i] + "7" for i in range(12)]
        total_label = ["S"] + label + minor_label + dominant_label
        return np.array(total_label)


    @property
    def chord_template(self):
        "Chroma going from C (0 index) to B (11 index)"
        # TODO potentially add 7th template, 9th, 11th, 13th and sus4, sus2, dim, aug
        # could also do an interval template to observe certain relations between notes like presence of fitfh, third, etc
        # such interval template could be more efficient than the chroma template
        N = 12
        major_template = np.array([1,0,0,0,1,0,0,1,0,0,0,0])/np.sqrt(3)  # major third
        minor_template = np.array([1,0,0,1,0,0,0,1,0,0,0,0])/np.sqrt(3)  # minor third
        dominant_7th_template = np.array([1,0,0,0,1,0,0,0,0,0,1,0])/np.sqrt(3) # dominant 7th
        silence_template = np.ones(N)/np.sqrt(N) # ajdusted by hand to make the silence template more probable in case of homogeneous chroma

        templates = [major_template, minor_template, dominant_7th_template]

        chord_template = np.zeros((N, len(templates) * N + 1))
        for index, some_template in enumerate(templates): # stack template one after another
            for shift in range(N):
                chord_template[:,1 + shift + index*N] = np.roll(some_template, shift)
        chord_template[:,0] = silence_template

        return chord_template

    @property
    def observation_matrix(self):
        """
        Returns the chord observation matrix, where each column is the correlation of the chroma with the chord template.

        Parameters:
        -----------
        chroma: np.array((12, Any)), length of the second dimension is the number of frames
        chord_template: np.array((12, 24))

        Results:
        --------
        chords_observation: np.array((24,Any))
        """

        #chords_observation = np.zeros((chord_template.shape[1],chroma.shape[1]))

        chords_observation = self.chord_template.T @ self.chroma # dot product for every element in the chroma with the chord template

        chords_observation /= np.sum(chords_observation, axis=0, keepdims=True) # normalise the columns to get a usable probability distribution
        max_index = np.argmax(chords_observation, axis=0, keepdims=True)
        filter = np.zeros_like(chords_observation)
        filter[max_index, np.arange(chords_observation.shape[1])] = 1
        return filter != 0, chords_observation


    def solve(self):
        """
        Returns the most probable chord at each frame of the chroma matrix using the Viterbi algorithm.
        """
        transmat=self.chord_transition_matrix
        _, obs_mat = self.observation_matrix
        p_init = np.ones(obs_mat.shape[0]) / obs_mat.shape[0] # uniform initial distribution
        sequence = librosa.sequence.viterbi(obs_mat, transmat, p_init=p_init)
        # named_sequence = self.chord_labels[sequence]
        return sequence

    def show(self, this="result"):
        # librosa.display.specshow(self.observation_matrix, y_axis='chroma', x_ axis='time')
        if this == "result":
            seq = self.solve()
            im = np.zeros_like(self.observation_matrix[1])
            im[seq,np.arange(im.shape[1])] = 1
        elif this == "observation":
            im = self.observation_matrix[1]
        elif this == "observation_mask":
            filter, obs = self.observation_matrix
            obs[~filter] = 0
            im = obs
        elif this == "transition":
            im = self.chord_transition_matrix
        else:
            raise ValueError("Type must be either result, observation or transition")

        plt.imshow(im,aspect="auto",cmap="Reds")

        if type(self.chord_labels) == np.ndarray:
            labels = self.chord_labels.tolist()
            plt.yticks(range(len(self.chord_labels)),labels=labels)
            # Generate time values for the x-axis
            time_values = librosa.times_like(im, sr=self.sampling_rate,hop_length=self.hop_length)

            # Set the x-ticks to time values in seconds
            # Reduce the number of x-ticks for better readability
            num_ticks = 10  # Adjust this number to change the number of x-ticks
            tick_indices = np.linspace(0, len(time_values) - 1, num_ticks, dtype=int)
            tick_labels = np.round(time_values[tick_indices], 2).astype(str).tolist()

            # Set the x-ticks to the reduced set of time values
            plt.xticks(tick_indices, labels=tick_labels, rotation=45)

        plt.show()

    def simple_notation(self):
        """
        Returns [(Chord: str, onset_time: float, duration: float),...]
        """
        seq = self.solve()
        change_index = np.insert(np.where(seq[:-1] != seq[1:])[0] + 1,0,0)
        onset_time = change_index * self.hop_time
        duration = np.append(onset_time[1:], self.chroma.shape[1] * self.hop_time) - onset_time
        chord = seq[change_index]

        return list(zip(self.chord_labels[chord], onset_time, duration))


if __name__ == "__main__":
    c = ChordIdentifier(AUDIO_PATH)
    mask, obs = c.observation_matrix
    #librosa.display.specshow(obs, y_axis='off', x_axis='time')
    #plt.show()
    s = c.simple_notation()
    c.show("result")
