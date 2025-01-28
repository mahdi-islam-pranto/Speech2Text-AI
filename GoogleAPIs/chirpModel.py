from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import cloud_speech
from google.cloud import storage
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
    blobs = sorted(bucket.list_blobs(prefix=gcs_json_dir), key=lambda x: x.name)

    full_transcript = []

    for blob in blobs:
        if blob.name.endswith(".json"):
            json_content = blob.download_as_text()
            data = json.loads(json_content)
            
            for result in data.get("results", []):
                if result.get("alternatives"):
                    transcript = result["alternatives"][0].get("transcript", "")
                    full_transcript.append(transcript.strip())

    final_transcript = " ".join(full_transcript)
    final_transcript = final_transcript.replace(" .", ".").replace(" ,", ",")
    final_transcript = final_transcript[0].upper() + final_transcript[1:] + "."

    with open(output_txt_filename, "w", encoding="utf-8") as txt_file:
        txt_file.write(final_transcript)
    print(f"Clean transcription saved to {output_txt_filename}")

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
        output_config = cloud_speech.RecognitionOutputConfig(
            gcs_output_config=cloud_speech.GcsOutputConfig(
                uri=f"gs://{bucket_name}/{output_dir}"
            )
        )

        # Configure the request
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
        output_txt_filename = f"{base_name}_chirp_transcript.txt"

        download_transcription_and_save_to_txt(bucket_name, output_dir, output_txt_filename)

    except Exception as e:
        print(f"Transcription error: {str(e)}")

if __name__ == "__main__":
    input_file = "go_zayan_anika.mp3"
    bucket_name = "bangla_audio_files"
    destination_blob_name = "call_files/call_recordings/go_zayan_anika.mp3"
    
    upload_to_gcs(bucket_name, input_file, destination_blob_name)
    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    transcribe_long_audio(gcs_uri, bucket_name)
    