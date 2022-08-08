#!/usr/bin/env python3

import os
import sys
import time
import signal
import subprocess

from goprocam import GoProCamera
from goprocam import constants


class GoProStream:
    def __init__(self):
        self.gopro = GoProCamera.GoPro()
        self.ffmpeg = ""

    def startStream(self):
        print("Start Streaming...")
        self.gopro.livestream("start")

        print("Open FFMPEG process...")
        time.sleep(1)
        self.ffmpeg = subprocess.Popen(
            "ffmpeg -f mpegts -i udp://"
            + self.gopro.ip_addr
            + ":8554 -c copy -an -f flv rtmp://localhost:1935/live/gopro",
            stdout=subprocess.PIPE,
            shell=True,
            preexec_fn=os.setsid,
        )

        time.sleep(10)
        print("Keep alive...")
        self.gopro.KeepAlive()

    def stopStream(self):
        print("Stop Streaming...")
        self.gopro.livestream("stop")

        print("Close FFMPEG process...")
        time.sleep(1)
        os.killpg(os.getpgid(self.ffmpeg.pid), signal.SIGTERM)

        print("Power Off GoPro...")
        time.sleep(1)
        self.gopro.power_off()


if __name__ == "__main__":
    goprostream = GoProStream()
    try:
        goprostream.startStream()
    except KeyboardInterrupt:
        goprostream.stopStream()
        pass
    finally:
        sys.exit(0)

# octopi.local:1935/gopro
