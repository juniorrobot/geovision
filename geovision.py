"""
This module demonstrates basic functionality of the OpenCV and GeoJSON packages
in Python 3 by performing rudimentary line detection of roads from an image and
exporting those lines to a GeoJSON file.

Example usage:
    % python geovision.py --image /path/to/satellite/image.jpg --outdir=/tmp

Full usage is available via the -h/--help argument.

Details:
    Road detection uses Canny edge detection to find initial segments. A Hough
    transform is then applied in order to find straight lines and filter out
    paths that are not well-connected to others.

TODO:
    - More tuning of the Hough parameters
    - Expose more parameters via command line
    - Use a neural network with trainable weights for larger context. (fun!)
"""

import argparse
import cv2
import geojson
import math
import numpy as np
import os
import sys

class Debugger:
    """Basic debugging visualization.

    Attributes:
        show_images (bool): Render image data & display to window using cv2.
        show_log (bool): Print log statements to stdout.

    """

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
    """Detect objects within an image.

    Attributes:
        lines (list): Collection of detected lines.

    """

    def __init__(self, debugger=Debugger()):
        self._debug = debugger
        self._hough_rho = 1.0
        self._hough_theta = math.pi / 2
        self._hough_threshold = 80
        self._canny_threshold1 = 200
        self._canny_threshold2 = 255

    @property
    def hough_rho(self):
        return self._hough_rho

    @hough_rho.setter
    def hough_rho(self, rho):
        self._hough_rho = rho

    @property
    def hough_theta(self):
        return self._hough_theta

    @hough_theta.setter
    def hough_theta(self, theta):
        self._hough_theta = theta

    def detect_roads(self, image_path):
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(img_gray,
                self._canny_threshold1, self._canny_threshold2)
        self._debug.image(canny)
        filtered = cv2.HoughLinesP(canny,
                self._hough_rho, self._hough_theta, self._hough_threshold)
        if filtered is None:
            self._debug.log("No lines found")
            return None

        lines = []
        for line in filtered[0]:
            line = ((line[0], line[1]), (line[2], line[3]))
            lines.append(line)
            self._debug.line(img, line)
        self._debug.image(img)
        return lines


class GIS:
    """Collect geographic information for output to GeoJSON.
    """

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
    parser.add_argument("-r", "--rho", type=float,
            help="Hough rho parameter")
    parser.add_argument("-t", "--theta", type=float,
            help="Hough theta parameter")

    args = parser.parse_args(argv)

    return args

def save_json(json, outdir):
    output_path = os.path.join(outdir, "geo.json")
    with open(output_path, "w") as output:
        output.write(json)

def main(argv):
    with Debugger() as debug:
        args = load_options(argv)
        if args.verbosity:
            if args.verbosity > 0:
                debug.show_log = True
            if args.verbosity > 1:
                debug.show_images = True

        detect = Detector(debug)
        if args.rho:
            detect.hough_rho = args.rho
        if args.theta:
            detect.hough_theta = args.theta

        lines = detect.detect_roads(args.image)
        if lines:
            gis = GIS(debug)
            gis.add_lines(lines)
            save_json(gis.to_json(), args.outdir)


if __name__ == "__main__":
    main(sys.argv[1:])

