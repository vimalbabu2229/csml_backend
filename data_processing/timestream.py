import boto3
from botocore.exceptions import NoCredentialsError
import os
# Define AWS credentials
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY")
aws_secret_access_key = os.environ.get("AWS_SECRET_KEY")
region_name = 'ap-northeast-1'

# Initialize a Timestream write client
try:
    timestream_write = boto3.client('timestream-write', 
                                    aws_access_key_id=aws_access_key_id,
                                    aws_secret_access_key=aws_secret_access_key,
                                    region_name=region_name)
    print("Successfully initialized Timestream write client.")
except NoCredentialsError:
    print("Credentials not available")

# Define the database and table name
database_name = 'demoNoiseDB'
table_name = 'demoNoise'

# Define a function to write records to Timestream
def write_records_to_timestream(host, timestamp, value):
    host = 'DEV' + str(host)
    records = [
    {
        'Dimensions': [
            {'Name': 'host', 'Value': host},
        ],
        'MeasureName': 'value',
        'MeasureValue': str(value),
        'MeasureValueType': 'BIGINT',
        'Time': str(timestamp)
    }
]
    try:
        result = timestream_write.write_records(DatabaseName=database_name,
                                                TableName=table_name,
                                                Records=records)
        print(result)
        print("Successfully wrote records to Timestream.")
    except Exception as e:
        print(f"Failed to write records to Timestream: {e}")