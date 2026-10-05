import pandas as pd
import json
import boto3
import time
from sql_script_call import back_test_query


redshift_data_client = boto3.client('redshift-data')

stock_purchase_table_nvda = pd.DataFrame({'stock':[],'purchased_date':[],'purchased_price':[],'min_window_price':[],'min_price_date':[],'max_window_price':[],'max_price_date':[]})

stock_sale_table_nvda = pd.DataFrame({'stock':[],'sale_date':[],'sale_price':[],'min_window_sale':[],'min_sale_date':[],'max_window_sale':[],'max_sale_date':[]})

stock_purchase_table_aapl = pd.DataFrame({'stock':[],'purchased_date':[],'purchased_price':[],'min_window_price':[],'min_price_date':[],'max_window_price':[],'max_price_date':[]})

stock_sale_table_aapl = pd.DataFrame({'stock':[],'sale_date':[],'sale_price':[],'min_window_sale':[],'min_sale_date':[],'max_window_sale':[],'max_sale_date':[]})


start_value = 10000
running_cost_price = None
running_shares = None
running_investment_in_cash = None
holding_shares = False
running_sold_at_cost = None
max_value = None
min_value = None
window_min_date = None
window_max_date = None
window_sale_date = None
share_window_max_value = None
share_window_min_value = None
share_window_min_date = None
share_window_max_date = None
share_window_purchase_date = None


def get_all_stock_records():
    
    response = redshift_data_client.execute_statement(
        Database="dev",
        Sql=back_test_query,
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

def transform_raw_data_to_df (raw):
    raw_data = get_all_stock_records()
    df = pd.DataFrame({raw_data['Records']})
    return df

def test_data_generator(data,ticker) :
    checker = False
    check_for_stocks = False
    data_under_view = data[data['stock']==ticker]
    for index,el in data_under_view.iterrows():
        #print(running_investment_in_cash)
        if index == len(truncated_personal_data) - 1 :
            break;
        
        if el['highest_lowest_valuation_key'] == 4 :

            if share_window_min_value == None or el['minimum_value'] <  share_window_min_value :
                share_window_min_value = el['minimum_value']
                share_window_min_date = el['stock_valuation_date']
            if share_window_max_value == None or el['maximum_value'] > share_window_max_value :
                share_window_max_value = el['maximum_value']
                share_window_max_date = el['stock_valuation_date']
            
            if running_cost_price == None  and int(truncated_personal_data.iloc[index+1]['highest_lowest_valuation_key']) == 4:
                running_cost_price = float(truncated_personal_data.iloc[index+1]['stock_value'])
                running_shares = round(start_value/running_cost_price,3)
                holding_shares = True
                lowest = el['minimum_value']
                maximum = el['maximum_value']
                min_value = None
                max_value = None
                window_min_date = None
                window_max_date = None
                window_sale_date = None
                share_window_purchase_date = truncated_personal_data.iloc[index+1]['stock_valuation_date']
                check_for_stocks = True
                #print(f'current owned shares : {running_shares}, bought at:{running_cost_price}, lowest possible value: {lowest} , highest possible purchase value : {maximum}')

            if holding_shares == False and int(truncated_personal_data.iloc[index+1]['highest_lowest_valuation_key']) == 4:
                running_cost_price = float(truncated_personal_data.iloc[index+1]['stock_value'])
                running_shares = round(running_investment_in_cash/running_cost_price,3)
                holding_shares = True
                lowest = el['minimum_value']
                maximum = el['maximum_value']
                min_value = None
                max_value = None
                window_min_date = None
                window_max_date = None
                window_sale_date = None
                share_window_purchase_date = truncated_personal_data.iloc[index+1]['stock_valuation_date']
                check_for_stocks = True
                #print(f'current owned shares : {running_shares}, bought at:{running_cost_price}, lowest possible value: {lowest} , highest possible purchase value : {maximum}')


            if int(truncated_personal_data.iloc[index+1]['highest_lowest_valuation_key']) == 5 and check_for_stocks == True:
                temp_df = pd.DataFrame([{'stock':'NVDA','purchased_date':share_window_purchase_date,'purchased_price':running_cost_price,'min_window_price':share_window_min_value,'min_price_date':share_window_min_date,'max_window_price':share_window_max_value,'max_price_date':share_window_max_date}])
                stock_purchase_table_nvda = pd.concat([stock_purchase_table_nvda,temp_df], ignore_index=True)
                #'purchased_date':[],'purchased_price':[],'min_window_price':[],'max_window_price':[],'min_price_date':[],'max_price_date'
                #print(f'current owned shares : {running_cost_price}, lowest possible value: {share_window_min_value} , highest possible purchase value : {share_window_max_value}')
                share_window_min_value = None
                share_window_max_value = None
                share_window_min_date = None
                share_window_max_date = None
                share_window_purchase_date = None
                check_for_stocks = False
            
        if el['highest_lowest_valuation_key'] == 5 and running_shares != None:
            share_window_min_value = None
            share_window_max_value = None
            share_window_min_date = None
            share_window_max_date = None
            share_window_purchase_date = None
            if min_value == None or el['minimum_value'] <  min_value :
                min_value = el['minimum_value']
                window_min_date = el['stock_valuation_date']

            if max_value == None or el['maximum_value'] > max_value :
                max_value = el['maximum_value']
                window_max_date = el['stock_valuation_date']
            
            if float(el['stock_value']) > running_cost_price and holding_shares == True :
                if truncated_personal_data.iloc[index+1]['highest_lowest_valuation_key'] == 5 and truncated_personal_data.iloc[index+1]['stock_value'] > running_cost_price:
                    running_sold_at_cost = float(truncated_personal_data.iloc[index+1]['stock_value'])
                    old_investment_in_cash = running_investment_in_cash
                    running_investment_in_cash = running_shares * running_sold_at_cost
                    window_sale_date = el['stock_valuation_date']
                    lowest_possible_investment = running_shares * el['minimum_value']
                    highest_possible_investment = running_shares * el['maximum_value']
                    holding_shares = False
                    checker = True
            """
                    if truncated_personal_data.iloc[index+1]['highest_lowest_valuation_key'] == 4 and holding_shares == False and running_sold_at_cost != None:
                running_investment_in_cash = running_shares * running_sold_at_cost
                lowest_possible_investment = running_shares * min_value
                highest_possible_investment = running_shares * max_value
                print(f'invetment_takeout_in_cash : {running_investment_in_cash},lowest_possible_takeout: {lowest_possible_investment},  highest_possible_takeout :{highest_possible_investment}')
            """

            if truncated_personal_data.iloc[index+1]['highest_lowest_valuation_key'] == 4 and checker == True :
                running_investment_in_cash = running_shares * running_sold_at_cost
                lowest_possible_investment = running_shares * min_value
                highest_possible_investment = running_shares * max_value
                #print(f'invetment_takeout_in_cash : {running_investment_in_cash},lowest_possible_takeout: {lowest_possible_investment},  highest_possible_takeout :{highest_possible_investment}')
                temp_df = pd.DataFrame([{'stock':'NVDA','sale_date':window_sale_date,'sale_price':running_investment_in_cash,'min_window_sale':lowest_possible_investment,'min_sale_date':window_min_date,'max_window_sale':highest_possible_investment,'max_sale_date':window_max_date}])
                stock_sale_table_nvda = pd.concat([stock_sale_table_nvda,temp_df], ignore_index=True)
                min_value = None
                max_value = None 
                share_window_min_value = None
                share_window_max_value = None
                share_window_min_date = None
                share_window_max_date = None
                share_window_purchase_date = None
                checker = False
                
def lambda_handler(event, context):
    data  = get_all_stock_records()
    all_data_records_df = transform_raw_data_to_df(data['Records'])
    extracted_data = test_data_generator(all_data_records_df,'NVDA')
    return extracted_data