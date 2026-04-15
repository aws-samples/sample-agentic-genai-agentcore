"""
Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.

This is AWS Content subject to the terms of the Customer Agreement
----------------------------------------------------------------------
File content:
    S3 utilities
"""

import json
import logging
from pathlib import Path

import boto3

# content type [enables opening file in browser]
CONTENT_TYPES = {
    "bmp": "image/bmp",
    "csv": "text/csv",
    "gif": "image/gif",
    "htm": "text/html",
    "html": "text/html",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "json": "application/json",
    "png": "image/png",
    "pdf": "application/pdf",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "txt": "text/plain",
}


#########################
#   S3
#########################

S3_CLIENT = boto3.client("s3")
S3_RESOURCE = boto3.resource("s3")
S3_WAITER = S3_CLIENT.get_waiter("object_exists")


def file_existing_s3(bucket_name, key):
    try:
        S3_WAITER.wait(Bucket=bucket_name, Key=key, WaiterConfig={"Delay": 1, "MaxAttempts": 1})
        return True
    except:  # TODO: specify exception type  # noqa: E722
        return False


def read_json_from_s3(
    bucket_name: str,
    key: str,
) -> dict:
    """
    Read a JSON file into memory from S3

    Parameters
    ----------
    bucket_name : str
        S3 bucket name
    key : str
        S3 object key

    Returns
    -------
    dict
        JSON data from S3 object
    """
    try:
        data = S3_RESOURCE.Object(bucket_name, key)
        file_content = data.get()["Body"].read().decode("utf-8")
        json_data = json.loads(file_content)
    except Exception as err:
        if hasattr(err, 'response') and err.response.get("Error", {}).get("Code") == "NoSuchKey":
            json_data = None
        else:
            logging.error(f"Error reading {bucket_name}/{key}: {err}")
            json_data = None

    return json_data


def write_json_to_s3(
    bucket_name: str,
    key: str,
    json_data: dict,
):
    """
    Write a JSON file from memory to S3

    Parameters
    ----------
    bucket_name : str
        S3 bucket name
    key : str
        S3 object key

    Returns
    -------
    dict
        JSON data from S3 object
    """
    try:
        json_data = json.dumps(json_data, indent=2).encode("utf-8")
        S3_CLIENT.put_object(Bucket=bucket_name, Key=key, Body=json_data)
    except Exception as err:
        logging.error(err)


def write_text_to_s3(
    bucket_name: str,
    key: str,
    text_content: str,
    content_type: str = "text/plain",
):
    """
    Write text content from memory to S3

    Parameters
    ----------
    bucket_name : str
        S3 bucket name
    key : str
        S3 object key
    text_content : str
        Text content to write
    content_type : str, optional
        Content type for the S3 object, by default "text/plain"
    """
    try:
        S3_CLIENT.put_object(Bucket=bucket_name, Key=key, Body=text_content.encode("utf-8"), ContentType=content_type)
    except Exception as err:
        logging.error(err)
        raise


def read_text_from_s3(
    bucket_name: str,
    key: str,
) -> str:
    """
    Read a text file into memory from S3

    Parameters
    ----------
    bucket_name : str
        S3 bucket name
    key : str
        S3 object key

    Returns
    -------
    str
        Text content from S3 object
    """
    try:
        data = S3_RESOURCE.Object(bucket_name, key)
        return data.get()["Body"].read().decode("utf-8")
    except Exception as err:
        if hasattr(err, 'response') and err.response.get("Error", {}).get("Code") == "NoSuchKey":
            return None
        logging.error(err)
        raise


def create_presigned_url(s3_path, expiration=3600):
    """
    Generate a presigned URL to share an S3 object.

    Parameters
    ----------
    s3_path : string
        Full path to the file in S3 (including bucket and key).
    expiration: int
        Time in seconds for the URL to remain valid. By default, 3600.

    Returns
    -------
    str
        Presigned URL as string. If error, returns None.
    """
    # Return the URL if it is not an S3 path
    if not s3_path.startswith("s3://"):
        return s3_path

    # Generate a presigned URL for the S3 object
    s3_bucket, s3_name = split_s3_path(s3_path)
    file_params = {"Bucket": s3_bucket, "Key": s3_name}

    file_format = Path(s3_name).suffix[1:]
    if file_format in CONTENT_TYPES:
        file_params["ResponseContentType"] = CONTENT_TYPES[file_format]

    try:
        response = S3_CLIENT.generate_presigned_url(
            "get_object",
            Params=file_params,
            ExpiresIn=expiration,
        )
    except Exception as error:
        logging.error(error)
        return None

    # The response contains the presigned URL
    return response


def split_s3_path(s3_path: str):
    """
    Splits an S3 path into bucket and key.

    Parameters
    ----------
    s3_path : str
        S3 path (including bucket and key)

    Returns
    -------
    bucket : str
        S3 bucket
    key : str
        S3 key
    """

    # split into parts
    path_parts = s3_path.replace("s3://", "").split("/")

    # extract bucket and key
    bucket = path_parts.pop(0)
    key = "/".join(path_parts)

    return bucket, key


def download_from_s3(s3_path: str, local_path: str):
    """
    Downloads a file from S3.

    Parameters
    ----------
    s3_path : str
        S3 path (including bucket and key)
    local_path : str
        Local path to save the file
    """

    s3_bucket, s3_key = split_s3_path(s3_path)
    S3_CLIENT.download_file(s3_bucket, s3_key, local_path)


def upload_to_s3(s3_bucket, s3_key, local_path: str):
    """
    Uploads a file from S3.

    Parameters
    ----------
    s3_bucket : str
        S3 destination bucket
    s3_key : str
        S3 destination key
    local_path : str
        Local path to the file
    """
    file_format = Path(s3_key).suffix[1:]
    if file_format in CONTENT_TYPES:
        ExtraArgs = {
            "ContentType": CONTENT_TYPES[file_format],
        }
    else:
        ExtraArgs = None

    # upload the file
    S3_CLIENT.upload_file(
        local_path,
        s3_bucket,
        s3_key,
        ExtraArgs=ExtraArgs,
    )


def list_bucket_items(bucket: str, prefix=None) -> list:
    """
    List items in the S3 bucket

    Parameters
    ----------
    bucket : str
        S3 bucket name
    prefix : _type_, optional
        S3 bucket prefix, by default None

    Returns
    -------
    list
        List with the file paths
    """

    # set up paginator
    paginator = S3_CLIENT.get_paginator("list_objects_v2")
    params = {"Bucket": bucket, "Prefix": prefix}
    page_iterator = paginator.paginate(**params)

    # add file from all pages
    all_files = []
    for page in page_iterator:
        if "Contents" in page:
            all_files.extend(page["Contents"])

    return [file for file in all_files if file["Key"][-1] != "/"]  # removing folder
