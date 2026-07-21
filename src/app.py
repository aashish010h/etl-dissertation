import os
import time
import json
import polars as pl


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
    
    # 1. EXTRACT & TRANSFORM (Utilising Polars LazyFrames for optimization)
    # Specifying storage_options allows Polars to natively use the container/lambda IAM role permissions
    lazy_df = (
        pl.scan_csv(input_uri, low_memory=True)
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
    print(f"Loading and writing Parquet directly to: {output_uri}")
    # collect(streaming=True) forces Polars to process data in chunks, minimizing RAM spikes
    lazy_df.collect(streaming=True).write_parquet(output_uri)
    
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
