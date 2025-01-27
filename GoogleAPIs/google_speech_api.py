import os
from google.cloud import speech
from google.oauth2 import service_account

# Path to your local audio file and service account JSON key
audio_path = "butter.mp3"  
credentials_path = "woven-century-448009-r7-01f84d62a35c.json" 

# Initialize credentials
credentials = service_account.Credentials.from_service_account_file(credentials_path)

def transcribe_local_audio(audio_path: str) -> str:
    """Transcribes a local audio file using the Google Cloud Speech-to-Text API."""
    # Instantiate the Speech client with provided credentials
    client = speech.SpeechClient(credentials=credentials)

    # Read the local audio file into memory
    with open(audio_path, "rb") as audio_file:
        audio_content = audio_file.read()

    # Prepare the audio content for the request
    audio = speech.RecognitionAudio(content=audio_content)

    # Configure the transcription request
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3, 
        sample_rate_hertz=44100,  
        language_code="bn-BD",   
    )

    # Perform the transcription
    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=600)

    # Collect the transcription results
    transcript_builder = []
    for result in response.results:
        transcript_builder.append(f",: {result.alternatives[0].transcript}")
        """ transcript_builder.append(f"\nConfidence: {result.alternatives[0].confidence}") """

    # Combine and print the full transcript
    transcript = "".join(transcript_builder)
    print(transcript)

    return transcript

# Call the function with the local audio file path
transcribe_local_audio(audio_path)
