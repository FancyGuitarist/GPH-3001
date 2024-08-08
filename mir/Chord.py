import librosa
from MusicRetrieval import AudioSignal
import numpy as np
import matplotlib.pyplot as plt

AUDIO_PATH = "./song&samples/polyphonic.wav"

"""
This package uses chord templates with harmonics, where the chroma patterns also account for the harmonics of the chord notes.
"""


def get_dummy_chroma(path,hop_length=512, sr=22050):
    path= "./song&samples/polyphonic.wav"
    y, _ = librosa.load(AUDIO_PATH, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    return chroma


class ChordIdentifier(AudioSignal):
    def __init__(self, AUDIO: AudioSignal):
        super(ChordIdentifier, self)
        self.audio = AUDIO
        self.chroma = librosa.feature.chroma_cqt(y=AUDIO.y, sr=AUDIO.sampling_rate, hop_length=AUDIO.hop_length)

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
        p = 0.1
        p_stay_silent = 0.1
        N = self.chord_labels.shape[0]
        """compute a uniform transition matrix between chords"""
        A = np.ones((N, N)) * (1 - p) / (N - 1)
        np.fill_diagonal(A, p)
        if p_stay_silent != p:
            A[0, 0] = p_stay_silent
            A[0, 1:] = (1 - p_stay_silent) / (N - 1)
        return A

    @property
    def chord_labels(self):
        label = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B"]
        minor_label = [label[i] + "m" for i in range(12)]
        dominant_label = [label[i] + "7" for i in range(12)]
        total_label = ["S"] + label + minor_label + dominant_label
        return np.array(total_label)

    @property
    def chord_template(self):
        "Chroma going from C (0 index) to B (11 index)"
        # TODO potentially add 7th template, 9th, 11th, 13th and sus4, sus2, dim, aug
        # could also do an interval template to observe certain relations between notes like presence of fitfh, third, etc
        # such interval template could be more efficient than the chroma
        # template
        N = 12
        major_template = np.array(
            [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]) / np.sqrt(3)  # major third
        minor_template = np.array(
            [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]) / np.sqrt(3)  # minor third
        dominant_7th_template = np.array(
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0]) / np.sqrt(3)  # dominant 7th
        # ajdusted by hand to make the silence template more probable in case
        # of homogeneous chroma
        silence_template = np.ones(N) / np.sqrt(N)

        templates = [major_template, minor_template, dominant_7th_template]

        chord_template = np.zeros((N, len(templates) * N + 1))
        for index, some_template in enumerate(
                templates):  # stack template one after another
            for shift in range(N):
                chord_template[:, 1 + shift + index *
                               N] = np.roll(some_template, shift)
        chord_template[:, 0] = silence_template

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
        argmax_mask: np.array((24,Any)) most probable chord at each fram is True else False,
        chords_observation: np.array((24,Any)) contains the probability of each chord at each frame
        """
        chords_observation = self.chord_template.T @ self.chroma  # dot product for every element in the chroma with the chord template

        # normalise the columns to get a usable probability distribution
        chords_observation /= np.sum(chords_observation, axis=0, keepdims=True)
        max_index = np.argmax(chords_observation, axis=0, keepdims=True)
        filter = np.zeros_like(chords_observation, dtype=bool)
        filter[max_index, np.arange(chords_observation.shape[1])] = True
        return filter, chords_observation

    def solve(self):
        """
        Returns the most probable chord at each frame of the chroma matrix using the Viterbi algorithm.
        """
        transmat = self.chord_transition_matrix
        _, obs_mat = self.observation_matrix
        # uniform initial distribution
        p_init = np.ones(obs_mat.shape[0]) / obs_mat.shape[0]
        sequence = librosa.sequence.viterbi(obs_mat, transmat, p_init=p_init)
        # named_sequence = self.chord_labels[sequence]
        return sequence

    def show(self, this="result"):
        """
        Display the result, observation, observation mask or transition matrix
        """
        def result():
            sequence = self.solve()
            im = np.zeros_like(self.observation_matrix[1])
            im[sequence, np.arange(im.shape[1])] = 1
            return im

        def observation():
            return self.observation_matrix[1]

        def observation_mask():
            argmax_mask, obs = self.observation_matrix
            obs[~argmax_mask] = 0
            return obs

        def x_ticks(im):
            # returns a list of xticks for the plot
            time_values = librosa.times_like(
                im, sr=self.audio.sampling_rate, hop_length=self.audio.hop_length)
            # Set the x-ticks to time values in seconds
            # Reduce the number of x-ticks for better readability
            num_ticks = 10  # Adjust this number to change the number of x-ticks
            tick_indices = np.linspace(
                0, len(time_values) - 1, num_ticks, dtype=int)
            tick_labels = np.round(
                time_values[tick_indices],
                2).astype(str).tolist()
            return tick_indices, tick_labels
        if this == "result":
            im = result()
        elif this == "observation":
            im = observation()
        elif this == "observation_mask":
            im = observation_mask()
        elif this == "transition":
            im = self.chord_transition_matrix
        else:
            if this == "compare":
                im = np.vstack((observation_mask(), result()))
            else:
                raise ValueError(
                    "Type must be either result, observation, observation_mask, compare or transition")

        if isinstance(self.chord_labels, np.ndarray) and this != "compare":
            labels = self.chord_labels.tolist()
            plt.yticks(range(len(self.chord_labels)), labels=labels)
            # Generate time values for the x-axis
            tick_indices, tick_labels = x_ticks(im)

            # Set the x-ticks to the reduced set of time values
            plt.xticks(tick_indices, labels=tick_labels, rotation=45)

        if this == "compare":
            images = [observation(), observation_mask(), result()]
            labels = [
                "Matrice de similarité",
                "Probabilité maximale",
                "Résultat de l'algorithme de Viterbi"]
            N = len(images)
            fig, axs = plt.subplots(N, 1, figsize=(10, 10))
            for i in range(N):
                axs[i].imshow(images[i], aspect="auto", cmap="Reds")
                axs[i].set_title(labels[i], fontsize=16)
                axs[i].set_yticks(range(len(self.chord_labels)))
                axs[i].set_yticklabels(
                    labels=self.chord_labels.tolist(), fontsize=6)
                tick_indices, tick_labels = x_ticks(images[0])
                axs[i].set_xticks(tick_indices)
                axs[i].set_xticklabels(tick_labels, rotation=45)
                if i < N - 1:
                    axs[i].set_xticklabels([])
                else:
                    axs[i].set_xlabel("Temps (s)", fontsize=16)

        else:
            plt.imshow(im, aspect="auto", cmap="Reds")

        plt.tight_layout()
        plt.show()

    def simple_notation(self):
        """
        Returns [(Chord: str, onset_time: float, duration: float),...]
        """
        seq = self.solve()
        change_index = np.insert(np.where(seq[:-1] != seq[1:])[0] + 1, 0, 0)
        onset_time = change_index * self.audio.hop_time
        duration = np.append(
            onset_time[1:], self.chroma.shape[1] * self.audio.hop_time) - onset_time
        chord = seq[change_index]

        return list(zip(self.chord_labels[chord], onset_time, duration))


if __name__ == "__main__":
    aud = AudioSignal(AUDIO_PATH)
    c = ChordIdentifier(aud)
    mask, obs = c.observation_matrix
    #librosa.display.specshow(obs, y_axis='off', x_axis='time')
    # plt.show()
    s = c.simple_notation()
    c.show("compare")
