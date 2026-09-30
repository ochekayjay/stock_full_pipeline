import boto3
import json
import pandas as pd
import time
import os
import psycopg2 as pg
import yaml
import yfinance as yf
from curl_cffi import requests
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta,date
#from dotenv import load_dotenv

local_csv_path = os.path.join('/tmp', 'stock_temp_data.csv')
#load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

client = boto3.client('redshift-data')

sql_query = """
    CREATE TABLE IF NOT EXISTS hungryThree (id varchar(256), name varchar(256));
"""

TICKERS = config["tickers"]["values"]
DB_SCHEMA = config["DB"]["SCHEMA"]
STAGING_TABLE = config["DB"]["STAGING_TABLE"]

redshift_data_client = boto3.client('redshift-data')
s3_client = boto3.client('s3')

# Configuration values (store these in Lambda Environment Variables)

DB_NAME = os.environ.get('Database')
DB_USER = os.environ.get('DB_USER')
REDSHIFT_ROLE_ARN = os.environ.get('REDSHIFT_ROLE_ARN')
S3_BUCKET = os.environ.get('STAGING_S3_BUCKET')
WORK_GROUP_NAME = os.environ.get('WorkgroupName')



def create_table() :
    """One-time-safe DDL. Ideally this lives in a separate migration script,
    but kept here as a guarded fallback so the Lambda never hard-fails on re-run."""
    ddl_query_schema = f"""
    CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};"""

    ddl_query_table = f"""CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.{STAGING_TABLE} (          
        "date"          TEXT NOT NULL,
        "close_aapl"    TEXT NOT NULL,
        "close_nvda"    TEXT NOT NULL,
        "high_aapl"     TEXT NOT NULL,
        "high_nvda"     TEXT NOT NULL,
        "low_aapl"      TEXT NOT NULL,
        "low_nvda"      TEXT NOT NULL,
        "open_aapl"     TEXT NOT NULL,
        "open_nvda"     TEXT NOT NULL,
        "volume_aapl"   TEXT NOT NULL,
        "volume_nvda"   TEXT NOT NULL,
        PRIMARY KEY (date)
    )
    SORTKEY (date);"""

    try:
            # 1. Fire off the query to Redshift
            response = redshift_data_client.batch_execute_statement(
                WorkgroupName=WORK_GROUP_NAME,
                Database=DB_NAME,
                Sqls=[ddl_query_schema,ddl_query_table]
            )
            
            # 2. Capture the tracking ID immediately from the response
            statement_id = response['Id']
            print(f"Query submitted. Tracking ID: {statement_id}")
            
            # 3. Keep checking the status until it stops running
            while True:
                # The 'statement_id' from above is fully accessible here
                get_status = redshift_data_client.describe_statement(Id=statement_id)
                status = get_status['Status']
                
                if status == 'FINISHED':
                    print("Table created successfully!")
                    break
                elif status in ['FAILED', 'ABORTED']:
                    error_msg = get_status.get('Error', 'Unknown database error')
                    raise Exception(f"Redshift Query Failed with status {status}: {error_msg}")
                
                # If status is still 'SUBMITTED' or 'PICKED' or 'STARTED', wait and retry
                print(f"Current status is {status}. Waiting 3 seconds...")
                time.sleep(3)
                
            return {
                'statusCode': 200,
                'body': json.dumps('Table creation completed successfully!')
            }
            
    except Exception as e:
        print(f"Execution Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Lambda failed: {str(e)}")
        }
    




def fetch_data(start: str, end: str) -> pd.DataFrame:
    """Pulls OHLCV data for TICKERS between start and end (end exclusive, per yfinance)."""
    session = requests.Session(impersonate="chrome")
    print(f'f5 {start} {end}')
    try:
        dataset = yf.download(
            tickers=TICKERS,
            start=start,
            end=end,
            interval='1d',
            session=session
        )
        if dataset is None or dataset.empty :
            raise ValueError(
                f"No data returned. Ticker '{TICKERS}' may be invalid,delisted or no record for target day."
            )

        # Flatten MultiIndex columns -> underscore, matching SQL column names
        dataset.columns = ['_'.join(col).strip() for col in dataset.columns]
        dataset.to_csv(local_csv_path,index=True)


        # Bring the Date index out as a real column so it lands in the DB
        #dataset = dataset.reset_index()

        return dataset
    except ValueError as val_err:
        # Catches our custom empty data validation rule
        print(f"⚠️ Validation Error: {val_err}")
        return None

    except Exception as general_err:
        # Fallback catch-all for unexpected library bugs or system interruptions
        print(f"💥 An unexpected error occurred: {general_err}")
        return None



def one_full_call() -> pd.DataFrame:
    return fetch_data(start='2005-08-01', end='2026-08-01')


def incremental_call() -> pd.DataFrame:
    # Dynamic window: yesterday -> today, so this works on every scheduled run
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    return fetch_data(start=yesterday.isoformat(), end=today.isoformat())


def fetch_for_last_saved_date():
    fetch_last_date_query = f"""
                                SELECT MAX(date::date) AS max_date from {DB_SCHEMA}.{STAGING_TABLE}
                            """
    try:
        response = redshift_data_client.execute_statement(
                        Database=DB_NAME,
                        Sql=fetch_last_date_query,
                        StatementName="fetch_most_recent_date",
                        WorkgroupName=WORK_GROUP_NAME
                    )

        response_id = response['Id']
        while True:
            response_description = redshift_data_client.describe_statement(
                                            Id=response_id,
                                            WaitTimeSeconds=10
                                        )
            response_status = response_description["Status"]
            if response_status == "FINISHED":
                print("Maximum date fetched")
                query_result = redshift_data_client.get_statement_result(
                                                        Id=response_id,
                                                        WaitTimeSeconds = 25
                                                    )
                print(query_result['Records'])
                return query_result['Records'][0][0]['stringValue']

            if response_status in ["ABORTED","FAILED"]:
                 raise Exception('Call for last date encountered a disrupted attempt')

                # return {"copy_id":statement_id,"deduplication_id":pruning_id}
            time.sleep(10)
    except Exception as general_err:
         print(f"💥 An unexpected error occurred: {general_err}")
         return None
         



def fetch_succeeding_day():
    try:
        prev_date = fetch_for_last_saved_date()
        #end_date = start_date
        print(f'1 {prev_date}')
        if prev_date is None:
            raise ValueError('Last Date wasnt fetched')

        previous_day_object = datetime.strptime(
            prev_date,
            "%Y-%m-%d"
        ).date()
        print(f'2 {previous_day_object}')
        if previous_day_object > datetime.now().date():
             raise ValueError ('Date out of bound')
        else :
            weekday = previous_day_object.weekday()

            if weekday == 4:          # Friday
                days_to_add = 3 
            elif weekday == 5:          # Friday
                    days_to_add = 2
            elif weekday == 6:          # Friday
                days_to_add = 1
            else:                     # Monday–Thursday
                days_to_add = 1

            start_date = previous_day_object + timedelta(days=days_to_add)
            end_date = start_date + timedelta(days=1)
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            print(f'this is for fetch succeeding day {start_date} and {end_date}')
            returned_slice_stock =  fetch_data(
                start = start_date,
                end = end_date
            )
            print(returned_slice_stock)

            return returned_slice_stock
    except Exception as error:
        print(f'Error : {error}')






def inceremental_insert_fnc(index,row):
    date_only = index.strftime('%Y-%m-%d')
    incremental_query = f"""
                        INSERT INTO {DB_SCHEMA}.{STAGING_TABLE} (date,close_aapl,close_nvda,high_aapl ,high_nvda ,low_aapl,low_nvda,open_aapl,open_nvda,volume_aapl,volume_nvda )
                        VALUES('{date_only}','{row['Close_AAPL']}','{row['Close_NVDA']}','{row['High_AAPL']}','{row['High_NVDA']}','{row['Low_AAPL']}','{row['Low_NVDA']}','{row['Open_AAPL']}','{row['Open_NVDA']}','{row['Volume_AAPL']}','{row['Volume_NVDA']}' )
                        """
    return incremental_query


def action_inc_function():
    incremental_data = fetch_succeeding_day()
    clear_duplicates = f"""
        CREATE TABLE {DB_SCHEMA}.{STAGING_TABLE}_dedup
          SORTKEY (date) 
          AS
                        SELECT *
                        FROM (
                        SELECT
                            *,
                            ROW_NUMBER() OVER (
                            PARTITION BY date::timestamp
                            ORDER BY date::timestamp
                            ) AS rn
                        FROM {DB_SCHEMA}.{STAGING_TABLE}
                        ) t
                        WHERE rn = 1;
        
                       
                        ALTER TABLE {DB_SCHEMA}.{STAGING_TABLE}_dedup DROP COLUMN rn;
        
                        
                        ALTER TABLE {DB_SCHEMA}.{STAGING_TABLE} RENAME TO {STAGING_TABLE}_old;
                        ALTER TABLE {DB_SCHEMA}.{STAGING_TABLE}_dedup RENAME TO {STAGING_TABLE};
        
                     
                        DROP TABLE {DB_SCHEMA}.{STAGING_TABLE}_old;
            """
    for index,row in incremental_data.iterrows():
        baked_query = inceremental_insert_fnc(index,row)
        response = redshift_data_client.execute_statement(
                Database=DB_NAME,
                Sql=baked_query,
                StatementName="incremental_Load",
                WorkgroupName=WORK_GROUP_NAME
            )
        statement_id = response['Id']
        while True:
        
            status_response = redshift_data_client.describe_statement(
                Id=statement_id
            )
    
            status = status_response["Status"]
    
            print(f"COPY status: {status}")
    
            if status == "FINISHED":
                print("COPY completed successfully.")
                prune_db = redshift_data_client.execute_statement(
                    Database=DB_NAME,
                    Sql=clear_duplicates,
                    StatementName="clear_incremental_dups",
                    WorkgroupName=WORK_GROUP_NAME
                    )
                
                pruning_id = prune_db['Id']
    
                while True: 
                    pruning_status_response = redshift_data_client.describe_statement(
                                Id=pruning_id
                            )
                    pruning_status = pruning_status_response["Status"]
                    if pruning_status == "FINISHED":
                        print("DB deduplicated")
                        return {"copy_id":statement_id,"deduplication_id":pruning_id}
    
                    if pruning_status in ["FAILED", "ABORTED"]:
                                error = pruning_status_response.get(
                                    "Error",
                                    "Unknown Redshift error"
                                )
                    
                                raise Exception(
                                    f"COPY failed: {error}"
                                )
                    time.sleep(3)
    
            if status in ["FAILED", "ABORTED"]:
                error = status_response.get(
                    "Error",
                    "Unknown Redshift error"
                )
    
                raise Exception(
                    f"COPY failed: {error}"
                )
            time.sleep(3)



def load_and_deduplicate_stock_data():
        
    s3_key = "staging/initial_stock_load.csv"
    
    # Upload your local CSV file to S3
    s3_client.upload_file(local_csv_path, S3_BUCKET, s3_key)
    
    # Format the COPY statement for Redshift Data API
    copy_sql = f"""
        COPY {DB_SCHEMA}.{STAGING_TABLE}
        FROM 's3://{S3_BUCKET}/{s3_key}'
        IAM_ROLE '{REDSHIFT_ROLE_ARN}'
        CSV
        IGNOREHEADER 1;
    """

    clear_duplicates = f"""
                CREATE TABLE {DB_SCHEMA}.{STAGING_TABLE}_dedup
                SORTKEY (date) 
                AS
                SELECT *
                FROM (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                    PARTITION BY date::timestamp
                    ORDER BY date::timestamp
                    ) AS rn
                FROM {DB_SCHEMA}.{STAGING_TABLE}
                ) t
                WHERE rn = 1;

               
                ALTER TABLE {DB_SCHEMA}.{STAGING_TABLE}_dedup DROP COLUMN rn;

                
                ALTER TABLE {DB_SCHEMA}.{STAGING_TABLE} RENAME TO {STAGING_TABLE}_old;
                ALTER TABLE {DB_SCHEMA}.{STAGING_TABLE}_dedup RENAME TO {STAGING_TABLE};

             
                DROP TABLE {DB_SCHEMA}.{STAGING_TABLE}_old;
        """
    
    response = redshift_data_client.execute_statement(
        Database=DB_NAME,
        Sql=copy_sql,
        StatementName="Bulk_Initial_Load",
        WorkgroupName=WORK_GROUP_NAME
    )
    print(f"Bulk load triggered successfully. StatementId: {response['Id']}")
    statement_id = response['Id']
    #return response['Id']

    while True:

        status_response = redshift_data_client.describe_statement(
            Id=statement_id
        )

        status = status_response["Status"]

        print(f"COPY status: {status}")

        if status == "FINISHED":
            print("COPY completed successfully.")
            prune_db = redshift_data_client.execute_statement(
                Database=DB_NAME,
                Sql=clear_duplicates,
                StatementName="Bulk_Initial_Load",
                WorkgroupName=WORK_GROUP_NAME
               )
            
            pruning_id = prune_db['Id']

            while True: 
                pruning_status_response = redshift_data_client.describe_statement(
                            Id=pruning_id
                        )
                pruning_status = pruning_status_response["Status"]
                if pruning_status == "FINISHED":
                    print("DB deduplicated")
                    return {"copy_id":statement_id,"deduplication_id":pruning_id}

                if status in ["FAILED", "ABORTED"]:
                            error = pruning_status_response.get(
                                "Error",
                                "Unknown Redshift error"
                            )
                
                            raise Exception(
                                f"COPY failed: {error}"
                            )
                time.sleep(3)

        if status in ["FAILED", "ABORTED"]:
            error = status_response.get(
                "Error",
                "Unknown Redshift error"
            )

            raise Exception(
                f"COPY failed: {error}"
            )
        time.sleep(3)
  

   


def handler(event,context):
   
    mode = event.get("mode")
    if mode == 'incremental':
        action_inc_function()
        if os.path.exists(local_csv_path):
            os.remove(local_csv_path)
            print(f"Deleted: {local_csv_path}")
        else:
            print("File does not exist.")
    if mode == 'full':
        try:
                create_table()
                print(event)
            
        except Exception as e:
                print(f"Execution Error: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f"Lambda failed: {str(e)}")
                }
        
        try:
            df = one_full_call()
            if df is None or df.empty:
                raise ValueError("Stock download returned no data.")
    
        except Exception as e:
                    print(f"Execution Error: {str(e)}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps(f"Lambda failed: {str(e)}")
                    }
    
        try:
            load_and_deduplicate_stock_data()
    
        except Exception as e:
                        print(f"Execution Error: {str(e)}")
                        return {
                            'statusCode': 500,
                            'body': json.dumps(f"Lambda failed: {str(e)}")
                        }
        if os.path.exists(local_csv_path):
            os.remove(local_csv_path)
            print(f"Deleted: {local_csv_path}")
        else:
            print("File does not exist.")

    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn='arn:aws:states:us-east-1:828311095616:stateMachine:stock_ecs_task_coordinator'
    )