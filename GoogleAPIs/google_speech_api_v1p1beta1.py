from google.cloud import speech_v1p1beta1 as speech
import os
from pydub import AudioSegment

def transcribe_audio(file_path):
    # Initialize client
    client = speech.SpeechClient.from_service_account_file('service-account.json')
    
    try:
        # Read audio file
        with open(file_path, "rb") as audio_file:
            content = audio_file.read()

        # Create recognition request for long-running operation
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,  # Specify the audio encoding
            sample_rate_hertz=16000,  # Adjust based on your audio file's sample rate
            language_code="bn-BD",  # Bangla language code
            enable_word_time_offsets=True,  # Enable word-level timestamps
            enable_automatic_punctuation=True,  # Enable automatic punctuation
            model="default"  # Use the default model
        )

        # Perform transcription (long-running operation)
        print("Processing audio... (This may take a while for long files)")
        operation = client.long_running_recognize(config=config, audio=audio)
        
        # Wait for the operation to complete
        response = operation.result(timeout=600)  # Increase timeout if needed
        
        # Process results
        # Collect the transcription results
        transcript_builder = []
        for result in response.results:
            transcript_builder.append(f",: {result.alternatives[0].transcript}")
            """ transcript_builder.append(f"\nConfidence: {result.alternatives[0].confidence}") """

    # Combine and print the full transcript
        transcript = "".join(transcript_builder)
        print(transcript)

        # save the transcription in a text file
        # with open("transcription.txt", "w") as text_file:
        #     text_file.write(transcript)
        
            

        # Print the timestamps of each word
        
                # if hasattr(alternative, 'words'):
                #     for word in alternative.words:
                #         start_time = word.start_time.total_seconds()
                #         end_time = word.end_time.total_seconds()
                #         print(f"Word: {word.word}, Start: {start_time:.2f}s, End: {end_time:.2f}s")

        print("Transcription completed.")

       

    except Exception as e:
        print(f"Error during transcription: {str(e)}")

def convert_to_mono(input_file, output_file):
    sound = AudioSegment.from_mp3(input_file)
    sound = sound.set_channels(1)
    sound.export(output_file, format="mp3")
    print("File converted to mono")

if __name__ == "__main__":
    input_file = "butter.mp3"  # Replace with your audio file name
    mono_file = "converted_mono.mp3"
    convert_to_mono(input_file, mono_file)
    transcribe_audio(mono_file)