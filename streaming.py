#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample application using the streaming API.

NOTE: This module requires the additional dependency `pyaudio`. To install
using pip:

    pip install pyaudio

Example usage:
    python transcribe_streaming_mic.py

"""


# [START import_libraries]
from __future__ import division

#내가 추가한 부분
import wave
import pygame
import time
import threading


import re
import sys
import os
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
# [END import_libraries]

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)
# [END audio_stream]

##global check
##def execute(): # 쓰레드 객체 선언
##    if check == 1 :
##        # 녹음부분
##        FORMAT = pyaudio.paInt16
##        CHANNELS=1
##        RATE = 16000
##        CHUNK= int(RATE/10)
##        RECORD_SECONDS= 10
##        WAVE_OUTPUT_FILENAME="file.wav"
##
##        audio = pyaudio.PyAudio()
##        stream = audio.open(format=pyaudio.paInt16,
##                        channels=CHANNELS,
##                        rate = RATE,
##                        input = True,
##                        input_device_index=1,
##                        frames_per_buffer=CHUNK)
##    
##        print("녹음중")
##        frames=[]
##        while True:
##            data = stream.read(CHUNK)
##            frames.append(data)
##            if check == 2:
##                break
##        
##    elif check == 2:
##        # 녹음끝
##            stream.stop_stream()
##            stream.close()
##            audio.terminate()
##
##            waveFile = wave.open(WAVE_OUTPUT_FILENAME,'wb')
##            waveFile.setnchannels(CHANNELS)
##            waveFile.setsampwidth(audio.get_sample_size(FORMAT))
##            waveFile.setframerate(RATE)
##            waveFile.writeframes(b''.join(frames))
##
##            waveFile.close()

def listen_print_loop(responses,s):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0

    
   
    check = 1
    for response in responses:
        

        
        #녹음 시작
       
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.

        
        result = response.results[0]
        if not result.alternatives:
            continue
        
        
        

        
        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))
        
        if not result.is_final:
            #sys.stdout.write(transcript + overwrite_chars + '\r')
            #sys.stdout.flush()

            num_chars_printed = len(transcript)
            

        else:
            check = 2
            #녹음 끝 저장 파일 실행
##            pygame.mixer.init()
##            bang = pygame.mixer.Sound(WAVE_OUTPUT_FILENAME)
##            while True:
##                bang.play()
##                time.sleep(2.0)
##            
##            os.remove(WAVE_OUTPUT_FILENAME)
            
            
            print(str(transcript + overwrite_chars).strip().lower())
            if(s.strip() == str(transcript + overwrite_chars).strip().lower()):
                print("Perfect!!", end ="\n\n\n")
                break
                
            else:
                print("NOOOOOOO!!", end="\n\n")
            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0
            
def prints():
    print("en-AU(오스트레일리아)")
    print("en-CA(케나다)")
    print("en-GB(영국)")
    print("en-US(미국)")
    print("es-ES(스페인어)")
    print("fr-FR(프랑스어)")
    print("ja-JP(일본어)")
    print("ko-KR(한국어)")
    print("exit(프로그램종료)")
    
    return input()

language = ['en-AU','en-CA','en-GB', 'en-US', 'es-ES', 'fr-FR', 'ja-JP','ko-KR']
def main():
    check = 0
    # See http://g.cㅇo/cloud/speech/docs/languages
    # for a list of supported languages.
    while(True):
        language_code = prints()  # a BCP-47 language tag
        if language_code == "exit":
            break;
        if language_code not in language:
            print("잘못 입력했습니다.\n 다시입력해주세요.")
            continue
        s = input("원하는 문장을 입력하세요 : ")
        
        client = speech.SpeechClient()
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code)
        streaming_config = types.StreamingRecognitionConfig(
            config=config,
            interim_results=True)

        with MicrophoneStream(RATE, CHUNK) as stream:
            
            audio_generator = stream.generator()
            requests = (types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)
            # Now, put the transcription responses to use.
            listen_print_loop(responses,s)

if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'pivotal-purpose-232707-5fd75ba680f5.json'
    main()
