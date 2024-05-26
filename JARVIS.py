import argparse
import queue
import sys
import sounddevice as sd
import requests
import json
# from gtts import gTTS
import os
import playsound
import pyttsx3

from vosk import Model, KaldiRecognizer
engine = pyttsx3.init()
engine.setProperty('voice', 'english+f4')
engine.setProperty('rate', 150)


def speak(msg):
    engine.say(msg)
    engine.runAndWait()
    engine.stop()

# def speak(text):
#     tts = gTTS(text=text, lang='en', tld='co.in')

#     filename = "abc.mp3"
#     tts.save(filename)
#     playsound.playsound(filename)
#     os.remove(filename)

history = []

def init_history():
    global history
    history = [
        {
            'role': 'system',
            'content': 'you are a personal assistant named JARVIS. keep your answer precise and short not more than 50 words. give detailed answer only if asked for.'
        }
    ]

def append(msg):
    history.append(msg)

def chat(msg):
    messages = {'role': 'user', 'content': msg}
    append(messages)
    url = 'http://localhost:11434/api/chat'
    data = {'model': 'llama3', 'messages': history, 'stream': False}
    resp = requests.post(url, json.dumps(data))
    resp = resp.json()
    append(resp['message'])                             #history
    _resp = resp['message']['content']
    print(f'J.A.R.V.I.S.:  {_resp}')
    speak(_resp)

q = queue.Queue()

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        pass
        # print(status, file=sys.stderr)
    q.put(bytes(indata))

args = {
    'samplerate': None,
    'model': None,
    'filename': None,
    'device': None
}

init_history()
try:
    if args['samplerate'] is None:
        device_info = sd.query_devices(args['device'], "input")
        # soundfile expects an int, sounddevice provides a float:
        args['samplerate'] = int(device_info["default_samplerate"])
        
    if args['model'] is None:
        model = Model(lang="en-in")
    else:
        model = Model(lang=args['model'])

    if args['filename']:
        dump_fn = open(args['filename'], "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args['samplerate'], blocksize = 4000, device=args['device'],
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args['samplerate'])
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                _input = json.loads(rec.Result())['text']
                if len(_input):
                    print(f'User: {_input}')
                    chat(_input)
            else:
                pass
                # print(rec.PartialResult())
            if dump_fn is not None:
                dump_fn.write(data)

except KeyboardInterrupt:
    print("\nDone")