import argparse
import sys

def load_options(argv):
    parser = argparse.ArgumentParser(description='Detect geography in images')

    parser.add_argument("-i", "--image", required=True,
            help="fully-qualified path to the input image")
    parser.add_argument("-o", "--outdir", required=True,
            help="fully-qualified directory for the output")

    args = parser.parse_args(argv)

    return args

def main(argv):
    args = load_options(argv)

if __name__ == "__main__":
    main(sys.argv[1:])

