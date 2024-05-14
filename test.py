import unittest
# Import the function to be tested


from MusicRetrieval import MRI
class TestIdentifyNotesAndRhythm(unittest.TestCase):
    def test_identify_bpm(self):
        # Test case 1: Audio with known notes and rhythm
        test_path = "./test/80bpm.wav"
        audio_input_1 = MRI(test_path)
        expected_result_1 = 80
        self.assertAlmostEqual(audio_input_1.bpm, expected_result_1,delta=1)
if __name__ == '__main__':
    unittest.main(warnings="ignore")
