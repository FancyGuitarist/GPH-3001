from MusicRetrieval import AudioSignal, Mono
import numpy as np
import sys
import os
from anotation import Partition
import argparse


class CapitalizedHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
            if not action.option_strings:
                return self._metavar_formatter(action, action.dest)(1)[0]
            else:
                parts = []
                if action.nargs == 0:
                    parts.extend(action.option_strings)
                else:
                    default = action.dest
                    args_string = self._format_args(action, default)
                    for option_string in action.option_strings:
                        parts.append(f'{option_string} {args_string}')
                return ', '.join(parts)

    def _get_help_string(self, action):
        help_string = action.help
        if help_string and help_string[0].islower():
            help_string = help_string.capitalize()
        return help_string


# Create the CustomArgumentParser
def create_parser():
    parser = argparse.ArgumentParser(prog="mir", description="Automatic Music transcription & Identification for musicians.", epilog="Music is the arithmetic of sounds as optics is the geometry of light. -Claude Debussy", formatter_class=CapitalizedHelpFormatter)

    analysis_parser = parser.add_subparsers(title='Analysis modes', dest='Modes')
    mono = analysis_parser.add_parser('monophonic', help='Monophonic mode',formatter_class=CapitalizedHelpFormatter )
    poly = analysis_parser.add_parser('polyphonic', help='Polyphonic mode',formatter_class=CapitalizedHelpFormatter )
    chord = analysis_parser.add_parser('chord-only', help='Chord-only mode',formatter_class=CapitalizedHelpFormatter)

    for p in [mono, poly, chord]:
        piano_debug_group = p.add_mutually_exclusive_group(required=False)
        piano_debug_group.add_argument('-pr', '--piano-roll', action='store_true', help='Show piano roll visualization')

        input_group = p.add_mutually_exclusive_group(required=True)

        if p == poly:
            input_group.add_argument('-b','--benchmark', type=str, help='compare against ground truth from midi file', metavar='<path/to/midi/file.midi>')
            p.add_argument('-t','--threshold', type=float, help='Threshold for the detection of note in with respect to the highest correlation value in a frame', metavar='[0-1]')
            p.add_argument('-g','--gamma', type=int, help='Gamma factor used in logarithmic compression, higher values increase the sensitivity', metavar='[1-inf]')
            p.add_argument('-std','--standard-deviation', type=float, help='''
                Standard deviation threshold used to determine if a frame is silenced or not,
                1e-8 work best for polyphonic piano while 1e-2 work best for noisy guitar recording
                ''', metavar='<float>')
            piano_debug_group.add_argument('-d', '--debug', type=float, help='debug a certain time frame, will show the cross-correlation with the template matrix and pseudo2D spectrum', metavar='<time in seconds>')
            p.set_defaults(gamma=50, standard_deviation=1e-2, threshold=0.55)

        input_group.add_argument("-u", '--url', type=str, help='URL to the music file')
        input_group.add_argument('-r', '--recording', action='store_true', help='Record audio from microphone')
        input_group.add_argument('-f', '--file', type=str, help='Path to the music file with .wav extension')
        p.add_argument('-o', '--output', type=str, help='Output file name')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    #print(args)

    if args.Modes == "polyphonic":
        if args.benchmark:
            from Validation.Validator import benchmark
            if not os.path.exists(args.benchmark):
                print(f"File {args.benchmark} not found")
                sys.exit(1)
            # if args.benchmark is in validation folder print the credit to maestro dataset
            if args.benchmark.startswith("Validation"):
                print("Benchmarking against MAESTRO dataset:\n -----------------------------------\n")
                print("""Curtis Hawthorne, Andriy Stasyuk, Adam Roberts, Ian Simon, Cheng-Zhi Anna Huang,
                Sander Dieleman, Erich Elsen, Jesse Engel, and Douglas Eck. 'Enabling
                Factorized Piano Music Modeling and Generation with the MAESTRO Dataset.'
                In International Conference on Learning Representations, 2019.\n""")
            score = benchmark(args.benchmark, show_piano=args.piano_roll)
            import pprint
            pprint.pprint(dict(score.items()))
            sys.exit(0)

    if args.file:
        audio_path = args.file
        audio = AudioSignal(audio_path)
        partition = Partition(audio.tempo)
    elif args.recording:
        from rec_unlimited import record
        audio_path = record()
        audio = AudioSignal(audio_path)
        partition = Partition(audio.tempo)

    elif args.url:
        import yt_dlp
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]}) as ydl:
            info_dict = ydl.extract_info(args.url, download=True)
            audio_path = ydl.prepare_filename(info_dict).replace('.webm', '.wav').replace('.m4a', '.wav')
        import time
        audio = AudioSignal(audio_path)
        partition = Partition(audio.tempo)
    else:
        print("No input provided")
        sys.exit(1)


    if args.Modes == "polyphonic":
        print("Polyphonic mode enabled")
        from Pseudo2D import Pseudo2D
        pseudo2d = Pseudo2D(audio)
        pseudo2d.gamma = args.gamma
        pseudo2d.threshold = args.threshold
        pseudo2d.std_threshold = args.standard_deviation
        _, piano = pseudo2d.multipitch_estimate()
        if args.piano_roll:
            pseudo2d.show_multipitch_estimate(piano)
            sys.exit(0)
        elif args.debug:
            pseudo2d.show(args.debug)
            sys.exit(0)



        simple_notation = pseudo2d.to_simple_notation_v2(piano)
        #print(simple_notation)


    elif args.Modes == "chord-only":
        print("chord-Only mode enabled")
        from Chord import ChordIdentifier
        chord = ChordIdentifier(audio)
        if args.piano_roll:
            chord.show()
            sys.exit(0)
        print(chord.simple_notation())
        sys.exit(0)
        #simple_notation = chord.simple_notation()



    else:
        if args.piano_roll:
            print("Monophonic mode does not support piano roll visualization")
            sys.exit(1)
        if args.debug:
            print("Monophonic mode does not support debug")
            sys.exit(1)
        print("Monophonic mode enabled")
        mono = Mono(audio)
        result = mono.decoded_states
        simple_notation = mono.simple_notation(result)

    if args.output:
        partition.save_score(partition.score(simple_notation, polyphonic=(args.Modes == "polyphonic")), args.output)
    if args.recording:
        # delete audio file after processing
        if args.output:
            import shutil
            shutil.copy(audio_path,  args.output + ".wav")
        else:
            is_keep = input("Do you want to keep the audio file? [y/n]")
            if is_keep.lower() == "n":
                os.remove(audio_path)
    elif args.url:
        if args.output:
            import shutil
            shutil.copy(audio_path,  args.output + ".wav")
        else:
            is_keep = input("Do you want to keep the audio file? [y/n]")
            if is_keep.lower() == "n":
                os.remove(audio_path)

    partition.show(simple_notation,polyphonic=(args.Modes == "polyphonic"))


if __name__ == '__main__':
    main()
