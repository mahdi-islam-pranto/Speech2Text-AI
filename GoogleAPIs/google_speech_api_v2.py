from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import cloud_speech
from google.cloud import storage
from pydub import AudioSegment
import json
import os
from urllib.parse import urlparse

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    storage_client = storage.Client.from_service_account_json('service-account.json')
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to GCS as {destination_blob_name}.")

def download_transcription_and_save_to_txt(bucket_name, gcs_json_dir, output_txt_filename):
    """Downloads JSON results from GCS and saves clean transcript to TXT."""
    storage_client = storage.Client.from_service_account_json('service-account.json')
    bucket = storage_client.bucket(bucket_name)
    blobs = sorted(bucket.list_blobs(prefix=gcs_json_dir), key=lambda x: x.name)  # Sort blobs chronologically

    full_transcript = []

    for blob in blobs:
        if blob.name.endswith(".json"):
            json_content = blob.download_as_text()
            data = json.loads(json_content)
            
            # Process results in chronological order
            for result in data.get("results", []):
                # Take only the first (highest-confidence) alternative
                if result.get("alternatives"):
                    transcript = result["alternatives"][0].get("transcript", "")
                    full_transcript.append(transcript.strip())

    # Combine with spaces between segments
    final_transcript = " ".join(full_transcript)
    
    # Add basic punctuation normalization
    final_transcript = final_transcript.replace(" .", ".").replace(" ,", ",")
    final_transcript = final_transcript[0].upper() + final_transcript[1:] + "."

    # Save to file
    with open(output_txt_filename, "w", encoding="utf-8") as txt_file:
        txt_file.write(final_transcript)
    print(f"Clean transcription saved to {output_txt_filename}")

def transcribe_long_audio(gcs_uri, bucket_name):
    # Initialize client
    client = speech.SpeechClient.from_service_account_file('service-account.json')
    
    # Recognizer configuration
    project_id = "woven-century-448009-r7"
    location = "global"
    recognizer_id = "bangla-recognizer-2"
    parent = f"projects/{project_id}/locations/{location}"
    recognizer_name = f"{parent}/recognizers/{recognizer_id}"
    
    try:
        # Create/get recognizer with optimized settings
        try:
            recognizer = client.get_recognizer(name=recognizer_name)
        except:
            recognizer = client.create_recognizer(
                parent=parent,
                recognizer_id=recognizer_id,
                recognizer={
                    "language_codes": ["bn-BD"],
                    "model": "latest_long",
                    "default_recognition_config": {  # Add default config
                        "auto_decoding_config": {},
                        "features": {
                            "enable_automatic_punctuation": True,
                            "enable_word_time_offsets": True
                        }
                    }
                }
            )

        # Output configuration
        output_dir = "transcription_results/"
        output_config = cloud_speech.RecognitionOutputConfig(
            gcs_output_config=cloud_speech.GcsOutputConfig(
                uri=f"gs://{bucket_name}/{output_dir}"
            )
        )

        # Create optimized recognition request
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=recognizer_name,
            config=cloud_speech.RecognitionConfig(
                auto_decoding_config={},
                language_codes=["bn-BD"],
                model="latest_long",
                features=cloud_speech.RecognitionFeatures(
                    # enable_automatic_punctuation=True,
                    enable_word_time_offsets=True,
                    # enable_spoken_punctuation=True,
                    enable_spoken_emojis=False
                )
            ),
            files=[{"uri": gcs_uri}],
            recognition_output_config=output_config
        )

        # Process audio
        print("Processing audio with optimized settings...")
        operation = client.batch_recognize(request=request)
        operation.result(timeout=3600)  # Increased timeout for large files

        # Generate output filename
        parsed_uri = urlparse(gcs_uri)
        base_name = os.path.splitext(os.path.basename(parsed_uri.path))[0]
        output_txt_filename = f"{base_name}_clean_transcript.txt"

        # Process and save transcript
        download_transcription_and_save_to_txt(bucket_name, output_dir, output_txt_filename)

    except Exception as e:
        print(f"Transcription error: {str(e)}")

if __name__ == "__main__":
    input_file = "butterfly_jannat.wav"
    bucket_name = "bangla_audio_files"
    destination_blob_name = "call_files/call_recordings/butterfly_jannat.wav"
    
    # Upload directly (assuming file is already in correct format)
    upload_to_gcs(bucket_name, input_file, destination_blob_name)
    
    # Start transcription
    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    transcribe_long_audio(gcs_uri, bucket_name)