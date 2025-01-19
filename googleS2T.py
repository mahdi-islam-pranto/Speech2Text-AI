import os
from google.cloud import speech_v1p1beta1 as speech



    # Create a Speech-to-Text client

client = speech.SpeechClient() 



    # Set the audio file path or Cloud Storage URI

    # Get path to Downloads folder
downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')

audio_file_path = os.path.join(downloads_path, 'sobuj3.mp3')

    
    # Read the audio file into memory

with open(audio_file_path, "rb") as audio_file:

    audio_content = audio_file.read()



    # Create the recognition request

audio = speech.RecognitionAudio(content=audio_content)

config = speech.RecognitionConfig( 

    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,

    sample_rate_hertz=16000, 

    language_code="en-US"  # Set your desired language

    )



    # Send the asynchronous request

operation = client.long_running_recognize(config=config, audio=audio)

    

    # Poll for the transcription results

response = operation.result()

    

    # Access the transcribed text

for result in response.results:

    print(result.alternatives[0].transcript) 
