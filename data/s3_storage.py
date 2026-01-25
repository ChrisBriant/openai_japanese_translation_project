import boto3, os, uuid, dotenv
from botocore.exceptions import ClientError
from urllib.parse import urlparse
from typing import Optional
import asyncio
import argparse
from pathlib import Path
#from ai.ai import get_image_description_name_category

dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

LINODE_BUCKET = os.environ.get('LINODE_BUCKET')
LINODE_BUCKET_ACCESS_KEY = os.environ.get('LINODE_BUCKET_ACCESS_KEY') 
LINODE_BUCKET_SECRET_KEY = os.environ.get('LINODE_BUCKET_SECRET_KEY') 
LINODE_CLUSTER_URL = 'https://japanese-translations.nl-ams-1.linodeobjects.com' # Your specific Linode cluster URL


async def upload_to_s3(upload_file_data, upload_file_name):
    AWS_ACCESS_KEY_ID=LINODE_BUCKET_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY=LINODE_BUCKET_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME=LINODE_BUCKET

    print(AWS_STORAGE_BUCKET_NAME)
    print(AWS_SECRET_ACCESS_KEY)
    print(AWS_ACCESS_KEY_ID)

    storage_url = "This will be a storage url"
    #TRANSFER TO STORAGE
    linode_obj_config = {
        "aws_access_key_id":AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
        "endpoint_url": LINODE_CLUSTER_URL,
    }

    client = boto3.client("s3", **linode_obj_config)
    try:
      response = client.put_object(Body=upload_file_data,  
                                Bucket=AWS_STORAGE_BUCKET_NAME,
                                Key=upload_file_name,
                                ContentType="audio/mpeg",  # Set Content-Type for PNG images
                                ACL="public-read"  # Set ACL to public-read
                            )
      print("S3 Upload Response", response)
    except Exception as e:
      print('File upload failed', e)
    storage_url = f"{LINODE_CLUSTER_URL}/{AWS_STORAGE_BUCKET_NAME}/{upload_file_name}"
    return storage_url

# # Changed to a synchronous function as requested.
# def retrieve_from_s3(storage_url: str) -> Optional[bytes]:
#     """
#     Retrieves a file from an S3-compatible Linode bucket given its full storage URL.
#     This is a synchronous function.

#     Args:
#         storage_url: The full URL of the object in the S3-compatible storage
#                      (e.g., "https://midjourneyart.nl-ams-1.linodeobjects.com/midjourneyart/some-key.gpx").

#     Returns:
#         The content of the file as bytes if successful, None otherwise.

#     Raises:
#         Exception: If there's an error during retrieval.
#     """

#     AWS_ACCESS_KEY_ID = LINODE_BUCKET_ACCESS_KEY
#     AWS_SECRET_ACCESS_KEY = LINODE_BUCKET_SECRET_KEY
#     AWS_STORAGE_BUCKET_NAME = LINODE_BUCKET # This environment variable should hold 'gpxfiles' from your example
#     LINODE_CLUSTER_URL='https://midjourneyart.nl-ams-1.linodeobjects.com'

#     linode_obj_config = {
#         "aws_access_key_id": AWS_ACCESS_KEY_ID,
#         "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
#         "endpoint_url": LINODE_CLUSTER_URL,
#     }

#     try:
#         # Parse the URL to get the object key (path within the bucket)
#         parsed_url = urlparse(storage_url)
#         # The path will be like /bucket_name/key. We need just the key.
#         # Assuming the URL format is LINODE_CLUSTER_URL/BUCKET_NAME/KEY
#         path_parts = parsed_url.path.split('/')
#         if len(path_parts) < 3 or path_parts[1] != AWS_STORAGE_BUCKET_NAME:
#             print(f"Error: Invalid storage URL format or bucket name mismatch. Expected format: {LINODE_CLUSTER_URL}/{AWS_STORAGE_BUCKET_NAME}/key")
#             return None
        
#         # The actual key is everything after the bucket name in the path
#         object_key = '/'.join(path_parts[2:])
        
#         print(f"Attempting to retrieve object '{object_key}' from bucket '{AWS_STORAGE_BUCKET_NAME}'")

#         client = boto3.client("s3", **linode_obj_config)
        
#         response = client.get_object(
#             Bucket=AWS_STORAGE_BUCKET_NAME,
#             Key=object_key
#         )

#         file_content = response['Body'].read()
#         print(f"Successfully retrieved {len(file_content)} bytes for object '{object_key}'.")
#         return file_content

#     except ClientError as e:
#         error_code = e.response.get("Error", {}).get("Code")
#         if error_code == "NoSuchKey":
#             print(f"Error: Object '{object_key}' not found in bucket '{AWS_STORAGE_BUCKET_NAME}'.")
#         else:
#             print(f"S3 Client Error retrieving file: {error_code} - {e}")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred during S3 retrieval: {e}")
#         return None
    

async def list_bucket_contents():
    AWS_ACCESS_KEY_ID = LINODE_BUCKET_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = LINODE_BUCKET_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME = LINODE_BUCKET
    LINODE_CLUSTER_URL = 'https://nl-ams-1.linodeobjects.com'
    LINODE_BASE_URL = "https://pocketportalimages.nl-ams-1.linodeobjects.com"

    linode_obj_config = {
        "aws_access_key_id": AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
        "endpoint_url": LINODE_CLUSTER_URL,
    }

    client = boto3.client("s3", **linode_obj_config)

    try:
        response = client.list_objects_v2(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            #Prefix="/"
        )
        print("S3 Response", response)
    except ClientError as e:
        print(f"Error listing objects: {e}")
        return

    if 'Contents' not in response:
        print("No objects found.")
        return

    for obj in response["Contents"]:
        key = obj["Key"]
        size = obj["Size"]

        acl = client.get_object_acl(
            Bucket = AWS_STORAGE_BUCKET_NAME,
            Key = obj["Key"]
        )

        print(f"{obj['Key']} - ACL = {acl}")

        print("IMAGE FROM BUCKET", obj)



async def main(filename: str):
    # get project root (parent of current file)
    BASE_DIR = Path(__file__).resolve().parent.parent

    file_path = BASE_DIR / "audio" / filename

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        #Get the file data required for transferring to S3
        audio_data = f.read()

    # Move to storage
    storage_url = await upload_to_s3(audio_data,filename)
    print("UPLOADED: ", storage_url)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON output file")
    parser.add_argument(
        "filename",
        help="Name of the JSON file inside the output directory"
    )

    args = parser.parse_args()

    asyncio.run(main(args.filename))