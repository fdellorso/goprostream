#!/usr/bin/env python3

from operator import concat
import sys

from goprocam import GoProCamera
from goprocam import constants


class GoProPhoto:
    def __init__(self):
        self.gopro = GoProCamera.GoPro()

    def takePhoto(self):
        print("Setting Photo...")
        self.gopro.mode(constants.Mode.PhotoMode, constants.Mode.SubMode.Photo.Single)
        self.gopro.gpControlSet(
            constants.Photo.RESOLUTION, constants.Photo.Resolution.R5M
        )

        print("Take Photo and Download")
        self.gopro.downloadLastMedia(self.gopro.take_photo(0))


if __name__ == "__main__":
    goprostream = GoProPhoto()
    try:
        goprostream.takePhoto()
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(0)
