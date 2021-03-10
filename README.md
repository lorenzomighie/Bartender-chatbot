# Bartender chatbot

A toy vocal assistent, which can receive orders, advice some products, delete an item and reading the final receipt.

Such a chatbot makes use of:
   - automated speech recognition;
   - dependency parsing and answer elaboration;
   - text to speech.

For a detailed explaination on the strategy we used to make it work take a look at ```bartender.pdf```.


# Requirements

```
python -m venv <virtualenv>
source <virtualenv>/bin/activate
pip install -U pip setuptools wheel
pip install spacy
pip install pyaudio
pip install SpeechRecognition
pip install PyQt5
pip install numpy
```
