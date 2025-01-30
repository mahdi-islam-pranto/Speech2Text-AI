from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import cloud_speech
from google.cloud import storage
import json
import os
from urllib.parse import urlparse


# upload audio file to Google Storage
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    storage_client = storage.Client.from_service_account_json('service-account.json')
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to GCS as {destination_blob_name}.")


# Exitiong file delete from Google Storage
def delete_files_from_gcs(bucket_name, folder_path):
    """Deletes all files in a folder from Google Cloud Storage."""
    storage_client = storage.Client.from_service_account_json('service-account.json')
    bucket = storage_client.bucket(bucket_name)
    
    # List all files in the folder
    blobs = bucket.list_blobs(prefix=folder_path)
    
    # Delete each file
    for blob in blobs:
        blob.delete()
        print(f"Deleted file from GCS: gs://{bucket_name}/{blob.name}")


# Download specific JSON file from GCS and save clean transcript to TXT locally
def download_transcription_and_save_to_txt(bucket_name, gcs_json_dir, output_txt_filename):
    """Downloads specific JSON result from GCS and saves clean transcript to TXT"""
    storage_client = storage.Client.from_service_account_json('service-account.json')
    bucket = storage_client.bucket(bucket_name)
    
    # Ensure the GCS directory path ends with a slash
    if not gcs_json_dir.endswith("/"):
        gcs_json_dir += "/"
    
    # List all JSON files in the GCS directory
    blobs = list(bucket.list_blobs(prefix=gcs_json_dir))
    if not blobs:
        print(f"No JSON files found in gs://{bucket_name}/{gcs_json_dir}")
        return

    # Find the first JSON file in the directory
    json_blob = None
    for blob in blobs:
        if blob.name.endswith(".json"):
            json_blob = blob
            break
    
    if not json_blob:
        print(f"No JSON files found in gs://{bucket_name}/{gcs_json_dir}")
        return

    # Download the JSON file locally
    local_json_path = os.path.basename(json_blob.name)
    json_blob.download_to_filename(local_json_path)
    print(f"Downloaded JSON file: {local_json_path}")

    full_transcript = []   # final transcriptions
    
    try:
        with open(local_json_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            
            for result in data.get("results", []):
                for alternative in result.get("alternatives", []):
                    transcript = alternative.get("transcript", "").strip()
                    if transcript:
                        full_transcript.append(transcript)
        
        # Join transcripts while maintaining order
        final_transcript = " ".join(full_transcript)
        
        # Clean up punctuation using regex
        import re
        final_transcript = re.sub(r'\s+([.,!?])', r'\1', final_transcript)
        final_transcript = re.sub(r'\s+', ' ', final_transcript)
        
        # Capitalize first letter and add final punctuation
        if final_transcript:
            final_transcript = final_transcript[0].upper() + final_transcript[1:]
            if final_transcript[-1] not in {'.', '!', '?'}:
                final_transcript += '.'
        else:
            final_transcript = "No transcription found."
        
        # Save to text file
        with open(output_txt_filename, "w", encoding="utf-8") as txt_file:
            txt_file.write(final_transcript)
            
        print(f"Clean transcription saved to {output_txt_filename}")

    except Exception as e:
        print(f"Error processing JSON file: {e}")

    finally:
        # Clean up: Delete the downloaded JSON file
        if os.path.exists(local_json_path):
            os.remove(local_json_path)
            print(f"Deleted local JSON file: {local_json_path}")

# Transcribe long audio file using Chirp model
def transcribe_long_audio(gcs_uri, bucket_name):
    # Set the correct region for Chirp_2 (e.g., "us" or "eu")
    location = "us-central1"  # Use "eu" for European Union

    # Initialize the client with the REGIONAL ENDPOINT
    client = speech.SpeechClient.from_service_account_file(
        'service-account.json',
        client_options={"api_endpoint": f"{location}-speech.googleapis.com"}
    )
    
    project_id = "woven-century-448009-r7"
    recognizer_id = "bangla-recognizer-2"
    parent = f"projects/{project_id}/locations/{location}"
    recognizer_name = f"{parent}/recognizers/{recognizer_id}"
    
    try:
        # Create/Get recognizer with Chirp model
        try:
            recognizer = client.get_recognizer(name=recognizer_name)
        except:
            recognizer = client.create_recognizer(
                parent=parent,
                recognizer_id=recognizer_id,
                recognizer={
                    "language_codes": ["bn-BD"],
                    "model": "chirp_2",
                    "default_recognition_config": {
                        "auto_decoding_config": {},
                        "features": {
                            "enable_automatic_punctuation": True,
                            "enable_word_time_offsets": True
                        }
                    }
                }
            )

        output_dir = "transcription_results/"
        # Output configuration
        output_config = cloud_speech.RecognitionOutputConfig(
            gcs_output_config=cloud_speech.GcsOutputConfig(
                uri=f"gs://{bucket_name}/{output_dir}"
            )
        )

        # Configure the request for Chirp model and transcribe
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=recognizer_name,
            config=cloud_speech.RecognitionConfig(
                auto_decoding_config={},
                language_codes=["bn-BD"],
                model="chirp_2",
                features=cloud_speech.RecognitionFeatures(
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=True,
                    # enable_spoken_punctuation=True
                )
            ),
            files=[{"uri": gcs_uri}],
            recognition_output_config=output_config
        )

        print("Processing audio with Chirp model...")
        operation = client.batch_recognize(request=request)
        operation.result(timeout=3600)

        parsed_uri = urlparse(gcs_uri)
        base_name = os.path.splitext(os.path.basename(parsed_uri.path))[0]
        output_txt_filename = f"{base_name}_chirp2_transcript.txt"

        # Download and save the transcription
        download_transcription_and_save_to_txt(bucket_name, output_dir, output_txt_filename)

        # Delete the audio file and all JSON files in the transcription_results folder
        audio_file_path = parsed_uri.path.lstrip("/")  # Remove leading slash
        delete_files_from_gcs(bucket_name, [audio_file_path])  # Delete audio file
        delete_files_from_gcs(bucket_name, [output_dir])  # Delete all JSON files in the folder

    except Exception as e:
        print(f"Transcription error: {str(e)}")


# main function
if __name__ == "__main__":
    input_file = "butter4.mp3"
    bucket_name = "bangla_audio_files"
    destination_blob_name = "call_files/call_recordings/transcripted_output.mp3"
    
    upload_to_gcs(bucket_name, input_file, destination_blob_name)
    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    transcribe_long_audio(gcs_uri, bucket_name)
