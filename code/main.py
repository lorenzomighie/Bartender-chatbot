import json
import spacy
import os
import subprocess
import speech_recognition as sr
import sys
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

from bar import Bar, Drink
from bartender import Bartender

# init tools
nlp = spacy.load('en_core_web_lg')
r = sr.Recognizer()

if sys.platform == 'win32':
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
    engine.setProperty('rate', 125)


def get_query():
    # filtering the audio --> takes 0.5 seconds of preprocessing
    # r.adjust_for_ambient_noise(source)
    # timeout = max number of second waited for a phrase to start

    with sr.Microphone() as source:
        try:
            audio = r.listen(source, timeout=5)
            text = r.recognize_google(audio)
            doc = nlp(text)
            answer = bartender.respond(doc)
        except sr.UnknownValueError:
            answer = bartender.not_understood(None)
        except sr.WaitTimeoutError:
            answer = bartender.not_understood(None)
        except sr.RequestError as e:
            print(e)
            answer = "I'm offline at the moment. I'm sorry."
        synthesize_speech(answer)


def synthesize_speech(text):
    if sys.platform == 'linux':
        from gtts import gTTS
        tts = gTTS(text=text, lang='en')
        filename = '/tmp/tmp.mp3'
        tts.save(filename)
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call(['mpg321', filename], stdout=devnull, stderr=subprocess.STDOUT)
        os.remove(filename)
    elif sys.platform == 'win32':
        engine.say(text)
        engine.runAndWait()
    else:
        raise RuntimeError("Your operating system is obsolete!")


def create_bartender():
    bar = Bar()
    bar.add_drink(Drink("ipa", "beer", 5.))
    bar.add_drink(Drink("blanche", "beer", 5.))
    bar.add_drink(Drink("heineken", "beer", 3.))
    bar.add_drink(Drink("moretti", "beer", 3.))
    bar.add_drink(Drink("peroni", "beer", 2.5))
    bar.add_drink(Drink("budweiser", "beer", 3.))
    bar.add_drink(Drink("tuborg", "beer", 2.5))
    bar.add_drink(Drink("bavaria", "beer", 1.))
    bar.add_drink(Drink("franziskaner", "beer", 3.5))
    bar.add_drink(Drink("leffe", "beer", 4.))
    bar.add_drink(Drink("ceres", "beer", 5.))
    bar.add_drink(Drink("prosecco dop", "wine", 20.))
    bar.add_drink(Drink("don perignon", "wine", 100.))
    bar.add_drink(Drink("chianti", "wine", 15.))
    bar.add_drink(Drink("cristal", "wine", 100.))
    bar.add_drink(Drink("cartizze", "wine", 50.))

    return Bartender(bar)


class Thread(QtCore.QThread):
    def run(self):
        # import lucene
        # vm_env = lucene.getVMEnv()
        # vm_env.attachCurrentThread()
        get_query()


class Application(QWidget):
    def __init__(self):
        super(Application, self).__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.button = QPushButton('Talk')
        self.button.clicked.connect(self.click)
        icon = QIcon('../res/baseline_mic_black_24.png')
        self.button.setIcon(icon)
        layout.addWidget(self.button)
        self.thread = Thread()
        self.thread.finished.connect(lambda: self.button.setEnabled(True))
        self.setLayout(layout)
        self.setFixedSize(500, 500)
        self.show()

    def click(self):
        if not self.thread.isRunning():
            self.button.setEnabled(False)
            self.thread.start()


def debug_compound():
    # parte utile per debug
    # synthesize_speech("Screaming Eagle Cabernet Sauvignon")
    nlp = spacy.load('en_core_web_lg')
    doc = nlp("Could you suggest me a beer?")

    print(list(doc.noun_chunks))
    for i in doc.noun_chunks:
        print("noun_chunks rooot: " + i.root.text)
    for token in doc:
        print('text: ' + token.text, 'lemma: ' + token.lemma_, 'tag: ' + token.tag_,
             'pos: ' + token.pos_, 'head.lemma: ' + token.head.lemma_, 'dep_:' + token.dep_, sep=' ' * 4)
        print([t.text for t in token.children])
        print('\n')
    # for nc in doc.noun_chunks:
    #     for token in nc:
    #         print('text: ' + token.text, 'lemma: ' + token.lemma_, 'tag: ' + token.tag_,
    #               'pos: ' + token.pos_, 'head.lemma: ' + token.head.lemma_,
    #               'dep_:' + token.dep_, 'children: ' + str(list(children.lemma_ for children in token.children))
    #               , sep=' ' * 4)


if __name__ == '__main__':
    bartender = create_bartender()
    app = QApplication(['Bender the Bartender'])
    ex = Application()
    sys.exit(app.exec_())
    # debug_compound()
