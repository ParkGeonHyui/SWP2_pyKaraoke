import sys
import threading
import urllib
from time import sleep

import qtmodern.styles
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from spleeter.separator import Separator
from spleeter.audio.adapter import get_default_audio_adapter
import qtmodern.windows
import os
from PyQt5.QtWidgets import *
from bs4 import *
import requests
from librosa import load
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pysndfx import AudioEffectsChain

t=0

def getLyrics(name):
    h = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    url = 'https://www.genie.co.kr/search/searchMain?query=' + name
    html = requests.get(url, headers=h)
    soup = BeautifulSoup(html.content, "html.parser")
    a = soup.findAll("tr", {"songid": lambda L: L})
    songid = a[0]['songid']
    html = requests.get("https://www.genie.co.kr/detail/songInfo?xgnm=" + songid, headers=h)
    soup = BeautifulSoup(html.content, "html.parser")
    a = soup.findAll("pre", {"id": "pLyrics"})

    lyriclines = a[0].text.splitlines()[1:]
    lyric = ""
    for line in lyriclines:
        line = line.lstrip()
        lyric += (line+"\n\n")
    return lyric


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.player = QMediaPlayer()

    def initUI(self):
        self.setWindowTitle("pyKaraoke")

        self.setGeometry(600, 100, 500, 700)
        self.filebutton = QPushButton("불러오기")
        self.playButton = QPushButton("▶")
        self.pauseButton = QPushButton("❚❚")
        self.prevButton = QPushButton("◀◀")
        self.nextButton = QPushButton("▶▶")
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setValue(100)

        self.lyricbox = QTextEdit()
        self.lyricbox.setReadOnly(True)

        self.filebutton.clicked.connect(self.fileButtonClicked)
        self.playButton.clicked.connect(self.playButtonClicked)
        self.pauseButton.clicked.connect(self.pauseButtonClicked)
        self.prevButton.clicked.connect(self.prevButtonClicked)
        self.nextButton.clicked.connect(self.nextButtonClicked)

        self.volumeSlider.valueChanged.connect(self.volumeChanged)

        self.vb = QHBoxLayout()


        self.vb.addWidget(self.playButton)

        self.vb.addWidget(self.pauseButton)
        self.vb.addWidget(self.prevButton)
        self.vb.addWidget(self.nextButton)

        self.layout = QGridLayout()

        self.layout.addWidget(self.lyricbox, 0, 0)
        self.layout.addWidget(self.filebutton, 1, 0)
        self.layout.addLayout(self.vb,2,0)
        self.layout.addWidget(self.volumeSlider, 3, 0)

        self.setLayout(self.layout)


    def playButtonClicked(self):
        self.player.play()

    def pauseButtonClicked(self):
        self.player.pause()

    def prevButtonClicked(self):
        self.player.setPosition(self.player.position()-5000)

    def nextButtonClicked(self):
        self.player.setPosition(self.player.position()+5000)

    def volumeChanged(self):
        self.player.setVolume(self.volumeSlider.value())

    def fileButtonClicked(self):
        global t

        strFilter = "음악 파일 (*.mp3)";
        fname = QFileDialog.getOpenFileName(self,filter=strFilter)
        if fname[0] == "": return
        a = os.path.split(fname[0])[1]
        songname = os.path.splitext(a)[0]

        #p1.join()
        t=0

        if (os.path.exists("C:/pyKaraoke/"+songname+"/accompaniment.wav")):
            loaded = "C:/pyKaraoke/"+songname+"/accompaniment.wav"

        else:
            sep = Separator('spleeter:2stems')
            # spleeter:2stems 보컬/반주
            # spleeter:4stems 목소리 피아노 베이스 드럼
            sep.separate_to_file(fname[0], "C:/pyKaraoke/")
            loaded = "C:/pyKaraoke/"+songname+"/accompaniment.wav"

        p1 = threading.Thread(target=echo, args="")
        p1.daemon = True
        p1.start()
        self.lyricbox.clear()
        self.lyricbox.setAlignment(Qt.AlignCenter)
        self.lyricbox.append(getLyrics(songname))

        url = QUrl.fromLocalFile(loaded)
        self.player.setMedia(QMediaContent(url))




def callback(indata, outdata, frames, time, status):

    if status:
        print(status)

    outdata[:] = indata

def echo():
    global t
    fs=44100
    with sd.Stream(device=(1, 5), samplerate=fs, dtype='float32', latency=None, channels=2, callback=callback):
        input()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    window = MyWindow()
    window.show()
    mw = qtmodern.windows.ModernWindow(window)
    mw.show()


    app.exec_()
