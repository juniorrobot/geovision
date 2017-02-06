import argparse
import cv2
import math
import numpy as np
import sys

class Debugger:
    def __init__(self):
        self._show_images = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        cv2.destroyAllWindows()
        if exc_type is not None:
            raise
        return self

    @property
    def show_images(self):
        return self._show_images

    @show_images.setter
    def show_images(self, show):
        self._show_images = show

    def image(self, img, window_name="image"):
        if self._show_images:
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            cv2.imshow(window_name, img)
            cv2.waitKey(0)

    def line(self, img, line):
        if self._show_images:
            cv2.line(img, line[0], line[1], (0, 255, 0))


class Detector:
    def __init__(self, debugger=Debugger()):
        self._debug = debugger
        self._lines = []

    @property
    def lines(self):
        return self._lines

    def detect_roads(self, image_path):
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(img_gray, threshold1=200, threshold2=255)
        self._debug.image(canny)
        filtered = cv2.HoughLinesP(canny, rho=1, theta=math.pi/2, threshold=80)
        for line in filtered[0]:
            line = ((line[0], line[1]), (line[2], line[3]))
            self._lines.append(line)
            self._debug.line(img, line)
        self._debug.image(img)


def load_options(argv):
    parser = argparse.ArgumentParser(description='Detect geography in images')

    parser.add_argument("-i", "--image", required=True,
            help="fully-qualified path to the input image")
    parser.add_argument("-o", "--outdir", required=True,
            help="fully-qualified directory for the output")
    parser.add_argument("-v", "--verbosity", action="count",
            help="increase debug verbosity")

    args = parser.parse_args(argv)

    return args

def main(argv):
    with Debugger() as debug:
        args = load_options(argv)
        if args.verbosity and args.verbosity > 0:
            debug.show_images = True
        detect = Detector(debug)
        detect.detect_roads(args.image)


if __name__ == "__main__":
    main(sys.argv[1:])

