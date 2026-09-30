import json
import boto3
import time
import urllib.request

redshift_data_client = boto3.client('redshift-data')



def get_daily_stock_deposits():

    call_last_stocks = f"""
        SELECT stock,
               highest_lowest_valuation_key,
               start_date,
               end_date,
               day_length
        FROM 
        (SELECT stock,
               highest_lowest_valuation_key,
               start_date,
               end_date,
               day_length,
               ROW_NUMBER() OVER( PARTITION BY stock ORDER BY start_date DESC) AS rn
            FROM stock_pipeline.highest_lowest_stock_metric)
            WHERE rn = 1
    """
    
    response = redshift_data_client.execute_statement(
        Database="dev",
        Sql=call_last_stocks,
        StatementName="stock_tracking",
        WorkgroupName="redshift-stock-project-workgroup"
    )
    print(f"tracking call initiated. StatementId: {response['Id']}")
    statement_id = response['Id']
    #return response['Id']

    while True:

        status_response = redshift_data_client.describe_statement(
            Id=statement_id
        )

        status = status_response["Status"]

        print(f"COPY status: {status}")

        if status == "FINISHED":
            print("tracking successfully completed successfully.")

            tracking_call_response = redshift_data_client.get_statement_result(
            Id=statement_id
            )
            return tracking_call_response
          

        if status in ["FAILED", "ABORTED"]:
            error = status_response.get(
                "Error",
                "Unknown Redshift error"
            )

            raise Exception(
                f"COPY failed: {error}"
            )
        time.sleep(3)
  




def tracker_func(val):
    url = "google_webhook_url"
    data = json.dumps(val).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return response.read()


def lambda_handler(event, context):
    data  = get_daily_stock_deposits()
    obj_list = []
    #print(data)
    for el in data['Records']:
        stock = None
        valuation_key = None
        start_date = None
        end_date = None
        day_length = None
        for index,element in enumerate(el):
            new_val = list(element.values())
            if index == 0:
                stock = new_val[0]
            if index == 1:
                valuation_key = new_val[0]
            if index == 2:
                start_date = new_val[0]
            if index == 3:
                end_date = new_val[0]
            if index == 4:
                day_length = new_val[0]
            print(new_val)
        data = {"stock": stock,
                "valuation_key": valuation_key,
                "start_date": start_date,
                "end_date": end_date,
                "day_length": day_length
        }
        tracker_func(data)