import librosa
import numpy as np
import matplotlib.pyplot as plt

"""
This package uses chord templates with harmonics, where the chroma patterns also account for the harmonics of the chord notes.
"""
def get_dummy_chroma():
    AUDIO_PATH = "./song&samples/polyphonic.wav"
    y, sr = librosa.load(AUDIO_PATH)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    return chroma




class ChordIdentifier:
    def __init__(self, chroma):
        self.chroma = chroma # chroma matrix

    @property
    def chord_labels(self):
        label = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        minor_label = [label[i] + "m" for i in range(12)]
        dominant_label = [label[i] + "7" for i in range(12)]
        total_label = label + minor_label + dominant_label
        return np.array(total_label)


    @property
    def chord_template(self):
        "Chroma going from C (0 index) to B (11 index)"
        # TODO potentially add 7th template, 9th, 11th, 13th and sus4, sus2, dim, aug
        # could also do an interval template to observe certain relations between notes like presence of fitfh, third, etc
        # such interval template could be more efficient than the chroma template
        N = 12
        major_template = np.array([1,0,0,0,1,0,0,1,0,0,0,0]) # major third
        minor_template = np.array([1,0,0,1,0,0,0,1,0,0,0,0]) # minor third
        dominant_7th_template = np.array([1,0,0,0,1,0,0,0,0,0,1,0]) # dominant 7th

        templates = [major_template, minor_template, dominant_7th_template]

        chord_template = np.zeros((N, len(templates) * N))
        for index, some_template in enumerate(templates): # stack template one after another
            for shift in range(N):
                chord_template[:,shift + index*N] = np.roll(some_template, shift)

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
        chroma = self.chroma
        chord_template = self.chord_template
        chords_observation = np.zeros((chord_template.shape[1],chroma.shape[1]))

        chords_observation = chord_template.T @ chroma # dot product for every element in the chroma with the chord template

        chords_observation /= np.sum(chords_observation, axis=0, keepdims=True) # normalise the columns to get a usable probability distribution
        max_index = np.argmax(chords_observation, axis=0,keepdims=True)
        filter = np.zeros_like(chords_observation)
        filter[max_index, np.arange(chords_observation.shape[1])] = 1
        return filter, chords_observation

    def show(self):
        #librosa.display.specshow(self.observation_matrix, y_axis='chroma', x_axis='time')
        plt.imshow(self.observation_matrix[0],aspect="auto")
        if type(self.chord_labels) == np.ndarray:
            labels = self.chord_labels.tolist()
            plt.yticks(range(len(self.chord_labels)),labels=labels)
        plt.show()

if __name__ == "__main__":
    chroma = get_dummy_chroma()


    c = ChordIdentifier(chroma)
    mask, obs = c.observation_matrix
    c.show()
