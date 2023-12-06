# library imports
import pandas as pd
import numpy as np
from datetime import datetime 


def invoice_comparison(ups_file, shipstation_file):
    # customer headers for excel sheet to read
    custom_headers = ["Lead Shipment Number", "Shipment Reference Number 1", "Net Amount"]

    ups_df = pd.read_excel(ups_file, sheet_name=0) # add custom headers to read specific columns
    ups_df.info()

    column_indices = [2, 4, 11, 5, 15, 20, 26, 28, 33, 52, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
                      81]
    ups_df = ups_df.iloc[:, column_indices].reset_index(drop=True)

    # open csv file as a dataframe
    ss_df = pd.read_excel(shipstation_file, sheet_name=0)

    # consolidate ups invoice by tracking number
    # sum the net amount pertaining to the same order id
    # unique tracking numbers with total net amount
    tracking_numbers = ups_df.groupby('Tracking Number')['Net Amount'].sum().reset_index()
    tracking_numbers['Net Amount'] = tracking_numbers['Net Amount'].round(2)

    # merge tracking_numbers with ups_df
    merged_df = pd.merge(tracking_numbers, ups_df, on='Tracking Number', how='left')

    merged_df = merged_df[(merged_df['Entered Weight'] != 0.0)]
    merged_df.reset_index(drop=True, inplace=True)

    # convert Shipment Reference Number 1 to string
    merged_df['Shipment Reference Number 1'] = merged_df['Shipment Reference Number 1'].astype(str)
    # sort df by Shipment Reference Number 1
    merged_df = merged_df.sort_values(by=['Shipment Reference Number 1']).reset_index(drop=True)

    # add total Net Amount_x for tracking numbers with identical Shipment Reference Number 1
    merged_df['Net Amount_x'] = merged_df.groupby('Shipment Reference Number 1')['Net Amount_x'].transform('sum')

    # iterate through df and keep only the Net Amount_x on the first row that has multiple Net Amount_x on the same Shipment Reference Number 1
    # place a 0.0 on the rest of the rows that have the same Shipment Reference Number 1

    # consolidate merged_df with shipstation report  by order number
    # on merged_df the column name is Shipment Reference Number 1
    # on shipstation the column name is Order Number
    # extract tge Carrier Fee column value from shipstation report
    # merge Carrier Fee column value with merged_df where Shipment Reference Number 1 == Order Number

    # rename column name from Order Number to Shipment Reference Number 1
    ss_df.rename(columns={'Order Number': 'Shipment Reference Number 1'}, inplace=True)

    # extract only the Shipment Reference Number 1 and Carrier Fee columns
    ss_df = ss_df.loc[:, ['Tracking Number','Shipment Reference Number 1', 'Carrier Fee']].reset_index(drop=True)

    '''Code added by Jonathan to Shipment Reference Number'''

    # List of unique Order ID's with count greater than one
    unique_ids = merged_df['Shipment Reference Number 1'].value_counts()
    # Filter list with count greater than one
    ids_to_update = unique_ids[unique_ids > 1].to_dict()
    # Exclude key-value pairs where the key contains a nan value
    filtered_ids_dict = {key: value for key, value in ids_to_update.items() if "nan"  not in key and "-" not in key and len(key)>6}
    print(filtered_ids_dict)

    # Dictionary to store Tracking Number and Order Number to replace in shipstation Order ID
    orders_to_replace_dict = {}

    # # loop through Order ID column
    for idx, value in merged_df['Shipment Reference Number 1'].items():
        if value in filtered_ids_dict:
            # Update Order ID Number
            new_value = f'{value}-{filtered_ids_dict[value]}'
            merged_df.at[idx, 'Shipment Reference Number 1'] = new_value
            filtered_ids_dict[value] = filtered_ids_dict[value] - 1
            # Store 'Tracking Number' and updated 'Order ID' number in orders_to_replace_dict
            orders_to_replace_dict[f"{merged_df.at[idx, 'Tracking Number']}"] = f"{merged_df.at[idx, 'Shipment Reference Number 1']}"
        
    print('tracking and order ids to replace')
    print(orders_to_replace_dict)

    print('tracking and order ids to replace')
    print(orders_to_replace_dict)

    print('updated ups_consolidated dataframe')
    new_ids = merged_df['Shipment Reference Number 1'].value_counts()
    new_ids_dict = new_ids[new_ids > 1].to_dict()

    print(new_ids_dict)

    print('checking dataframe...')

    print(merged_df['Shipment Reference Number 1'].value_counts())

    # Create a dictionary to map Tracking and Order ID to Order IDs in 
    tracking_order_id_dict = dict(zip(merged_df['Tracking Number'], merged_df['Shipment Reference Number 1']))

    '''left off here'''
    ss_df['Shipment Reference Number 1'] = ss_df['Tracking Number'].map(tracking_order_id_dict).fillna(ss_df['Shipment Reference Number 1'])
    print(ss_df['Shipment Reference Number 1'].value_counts())

    #drop Tracking Number column on ss_df
    ss_df = ss_df[['Shipment Reference Number 1', 'Carrier Fee']]
    # merge ss_df with merged_df
    merged_df = pd.merge(merged_df, ss_df, on='Shipment Reference Number 1', how='left')

    for i in range(1, len(merged_df)):
        if merged_df.loc[i, 'Shipment Reference Number 1'] == merged_df.loc[i - 1, 'Shipment Reference Number 1']:
            merged_df.loc[i, 'Net Amount_x'] = 0.0
            merged_df.loc[i, 'Carrier Fee'] = 0.0
    merged_df['Net Amount_x'] = merged_df['Net Amount_x'].round(2)

    # reorganize columns
    # drop Net Amount_y
    merged_df.drop(columns=['Net Amount_y'], inplace=True)

    # rename Net Amount_x to Net Amount
    merged_df.rename(columns={'Net Amount_x': 'Net Amount'}, inplace=True)

    # move Tracking Number column to index 4
    tracking_number = merged_df.pop('Tracking Number')
    merged_df.insert(4, 'Tracking Number', tracking_number)

    # move Net Amount to column index 9
    net_amount = merged_df.pop('Net Amount')
    merged_df.insert(9, 'Net Amount', net_amount)

    # rename Net Amount to Carrier Fee(UPS)
    merged_df.rename(columns={'Net Amount': 'Carrier Fee(UPS)'}, inplace=True)

    # move Carrier Fee column to index 10
    carrier_fee = merged_df.pop('Carrier Fee')
    merged_df.insert(10, 'Carrier Fee', carrier_fee)

    # rename Carrier Fee to Carrier Fee(SS)
    merged_df.rename(columns={'Carrier Fee': 'Carrier Fee(SS)'}, inplace=True)

    # move Invoice Number to column index 4
    invoice_number = merged_df.pop('Invoice Number')
    merged_df.insert(3, 'Invoice Number', invoice_number)

    # add new column to compare Carrier Fee(UPS) and Carrier Fee(SS)
    # if Carrier Fee(UPS) == Carrier Fee(SS) then True else False
    # place it after Carrier Fee(SS)
    merged_df['Carrier Fee Match'] = merged_df['Carrier Fee(UPS)'] == merged_df['Carrier Fee(SS)']
    merged_df['Carrier Fee Match'] = merged_df['Carrier Fee Match'].astype(str)
    merged_df['Carrier Fee Match'] = merged_df['Carrier Fee Match'].replace({'True': 'Yes', 'False': 'No'})

    # move Carrier Fee Match column to index 11
    carrier_fee_match = merged_df.pop('Carrier Fee Match')
    merged_df.insert(11, 'Carrier Fee Match', carrier_fee_match)

    # add column Difference between Carrier Fee(UPS) and Carrier Fee(SS)
    # place it after Match
    merged_df['Difference'] =  merged_df['Carrier Fee(SS)'] - merged_df['Carrier Fee(UPS)']
    merged_df['Difference'] = merged_df['Difference'].round(2)

    # move Difference column to index 12
    difference = merged_df.pop('Difference')
    merged_df.insert(12, 'Difference', difference)

    merged_df['Carrier Fee(SS)'] = merged_df['Carrier Fee(SS)'].astype(str)
    merged_df['Carrier Fee(SS)'] = merged_df['Carrier Fee(SS)'].replace({'nan': 'no records found'})
    merged_df.info()

    # Generate a timestamp for the processed file name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Export invoice comparison report to a csv file
    merged_df.to_csv(f'invoice_comparison_report2.csv_{timestamp}', index=False)

    return merged_df
