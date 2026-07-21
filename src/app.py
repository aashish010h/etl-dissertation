import os
import time
import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import boto3
import polars as pl


def _upload_to_s3(local_path, s3_uri):
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"Unsupported S3 URI: {s3_uri}")

    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-north-1"

    s3_client = boto3.client("s3", region_name=region)
    s3_client.upload_file(str(local_path), bucket, key)
    return s3_uri


def _download_from_s3(s3_uri, destination_path):
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"Unsupported S3 URI: {s3_uri}")

    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-north-1"

    s3_client = boto3.client("s3", region_name=region)
    s3_client.download_file(bucket, key, str(destination_path))
    return destination_path


def execute_etl_pipeline():
    """
    The core data processing logic. This remains 100% identical 
    regardless of whether it runs on Lambda or Fargate.
    """
    # Read S3 paths from environment variables provisioned in the cloud
    input_uri = os.environ.get("INPUT_S3_URI", "s3://aashish-etl-dissertation-2026/input/yellow_tripdata_2015-01.csv")
    output_uri = os.environ.get("OUTPUT_S3_URI", "s3://aashish-etl-dissertation-2026/output/processed_data.parquet")
    
    print(f"Starting ETL execution.")
    print(f"Extracting from: {input_uri}")
    
    # Start the monotonic benchmarking clock
    start_time = time.monotonic()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        input_path = temp_dir_path / "input.csv"
        output_path = temp_dir_path / "output.parquet"

        parsed_input = urlparse(input_uri)
        if parsed_input.scheme == "s3":
            print(f"Downloading input file from S3 to local temp storage")
            _download_from_s3(input_uri, input_path)
        else:
            input_path = Path(input_uri)

        # 1. EXTRACT & TRANSFORM (Utilising Polars LazyFrames for optimization)
        lazy_df = (
            pl.scan_csv(input_path, low_memory=True)
            # Drop rows containing any null values
            .drop_nulls()
            # GroupBy categorical configurations specified in dissertation scope
            .group_by(["VendorID", "payment_type", "passenger_count"])
            # Aggregate required operational metrics
            .agg([
                pl.len().alias("trip_count"),
                pl.col("fare_amount").mean().alias("avg_fare"),
                pl.col("trip_distance").mean().alias("avg_distance"),
                pl.col("tip_amount").mean().alias("avg_tip")
            ])
        )

        # 2. LOAD
        print(f"Writing temporary Parquet locally before uploading to: {output_uri}")
        # collect(streaming=True) forces Polars to process data in chunks, minimizing RAM spikes
        lazy_df.collect(streaming=True).write_parquet(output_path)

        print(f"Uploading Parquet to S3: {output_uri}")
        _upload_to_s3(output_path, output_uri)
    
    end_time = time.monotonic()
    execution_duration = end_time - start_time
    
    print(f"ETL Execution successful. Duration: {execution_duration:.4f} seconds.")
    return {
        "statusCode": 200,
        "execution_time_seconds": execution_duration,
        "platform": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "AWS_Fargate")
    }


def lambda_handler(event, context):
    """
    AWS Lambda Execution Entrypoint
    """
    print("Execution Context: AWS Lambda")
    try:
        metrics = execute_etl_pipeline()
        return {
            "statusCode": 200,
            "body": json.dumps(metrics)
        }
    except Exception as e:
        print(f"Lambda Execution Failure: {str(e)}")
        raise e


if __name__ == "__main__":
    """
    AWS Fargate (CLI/Container) Execution Entrypoint
    """
    # AWS Lambda sets AWS_LAMBDA_FUNCTION_NAME automatically. 
    # If it's missing, we are running inside the Fargate container.
    if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
        print("Execution Context: AWS Fargate Task")
        try:
            execute_etl_pipeline()
        except Exception as e:
            print(f"Fargate Execution Failure: {str(e)}")
            exit(1)
