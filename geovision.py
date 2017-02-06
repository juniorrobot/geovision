import argparse
import cv2
import geojson
import math
import numpy as np
import os
import sys

class Debugger:
    def __init__(self):
        self._show_images = False
        self._show_log = False

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

    @property
    def show_log(self):
        return self._show_log

    @show_log.setter
    def show_log(self, show):
        self._show_log = show

    def image(self, img, window_name="image"):
        if self._show_images:
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            cv2.imshow(window_name, img)
            cv2.waitKey(0)

    def line(self, img, line):
        if self._show_images:
            cv2.line(img, line[0], line[1], (0, 255, 0))

    def log(self, message):
        if self._show_log:
            print(message)


class Detector:
    def __init__(self, debugger=Debugger()):
        self._debug = debugger


    def detect_roads(self, image_path):
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(img_gray, threshold1=200, threshold2=255)
        self._debug.image(canny)
        filtered = cv2.HoughLinesP(canny, rho=1, theta=math.pi/2, threshold=80)

        lines = []
        for line in filtered[0]:
            line = ((line[0], line[1]), (line[2], line[3]))
            lines.append(line)
            self._debug.line(img, line)
        self._debug.image(img)
        return lines


class GIS:
    def __init__(self, debugger=Debugger()):
        self._debug = debugger
        self._features = []

    def add_lines(self, lines):
        line_strings = []
        for line in lines:
            self._debug.log(line)
            line_string = geojson.LineString([
                (float(line[0][0]), float(line[0][1])),
                (float(line[1][0]), float(line[1][1])),
                ])
            line_strings.append(line_string)
        col = geojson.GeometryCollection(line_strings)
        self._features.append(col)

    def to_json(self):
        feature_col = geojson.FeatureCollection(self._features)
        self._debug.log(feature_col)
        return str(feature_col)


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
        if args.verbosity:
            if args.verbosity > 0:
                debug.show_log = True
            if args.verbosity > 1:
                debug.show_images = True

        detect = Detector(debug)
        lines = detect.detect_roads(args.image)

        gis = GIS(debug)
        gis.add_lines(lines)
        json = gis.to_json()

        output_path = os.path.join(args.outdir, "geo.json")
        with open(output_path, "w") as output:
            output.write(json)


if __name__ == "__main__":
    main(sys.argv[1:])

