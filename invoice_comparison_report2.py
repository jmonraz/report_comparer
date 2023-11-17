# library imports
import pandas as pd
import numpy as np


def invoice_comparison(ups_file, shipstation_file):
    # customer headers for excel sheet to read
    custom_headers = ["Lead Shipment Number", "Shipment Reference Number 1", "Net Amount"]

    ups_df = pd.read_excel(ups_file, sheet_name=0,
                           usecols=custom_headers)
    ship_stations_df = pd.read_csv(shipstation_file,
                                   usecols=['Order Number', 'Tracking Number', 'Carrier Fee', 'Store Name']).iloc[1:, :]

    # Rename columns in ups_df
    ups_df.rename(columns={'Lead Shipment Number': 'Tracking Number', 'Shipment Reference Number 1': 'Order Number',
                           'Net Amount': 'Charge'}, inplace=True)

    # Consolidates ups data based on Tracking Number and Order Number
    '''
    TRACKING NUMBER 1 - ORDER NUMBER 1
    TRACKING NUMBER 2 - ORDER NUMBER 1
    TRACKING NUMBER 3 - ORDER NUMBER 2
    TRACKING NUMBER 4 - ORDER NUMBER 2
    '''

    # Clean Tracking and Order Number columns for whitespace
    ups_df['Tracking Number'] = ups_df['Tracking Number'].str.strip()
    ups_df['Order Number'] = ups_df['Order Number'].astype(str).str.strip()

    # Group by Tracking and Order Number
    ups_consolidated = ups_df.groupby(['Tracking Number', 'Order Number']).agg({'Charge': 'sum'}).reset_index()
    print(ups_consolidated['Order Number'].value_counts())
    print(ups_consolidated.head())

    # Consolidate ups data on Order ID once it's grouped by Tracking Number and Order Number
    ups_order_consolidated = ups_consolidated.groupby(['Order Number']).agg({'Charge': 'sum'}).reset_index()

    print(ups_order_consolidated.describe())

    # Join dataframes based on Order ID Field
    invoice_comparison = pd.merge(ups_order_consolidated, ship_stations_df, left_on=['Order Number'],
                                  right_on=['Order Number'], suffixes=('_ups', '_ss'), how='left')

    # convert numeric numbers to numeric and round to two decimal values
    invoice_comparison['Charge'] = pd.to_numeric(invoice_comparison['Charge']).round(2)
    invoice_comparison['Carrier Fee'] = pd.to_numeric(invoice_comparison['Carrier Fee']).round(2)

    # Rearrange order of columns Order ID, Tracking Number, Charge, Carrier Fee
    new_order = ['Order Number', 'Tracking Number', 'Charge', 'Carrier Fee']
    invoice_comparison = invoice_comparison[new_order]

    # Add Column to see difference between ups-ss
    invoice_comparison['Invoice Difference(ups-ss)'] = (
                invoice_comparison['Charge'] - invoice_comparison['Carrier Fee']).round(2)

    # Add Column to compare invoice
    invoice_comparison['Invoice Match'] = np.where(invoice_comparison['Charge'] == invoice_comparison['Carrier Fee'],
                                                   'Yes', 'No')

    # Export invoice comparison report to a csv file
    invoice_comparison.to_csv('invoice_comparison_report2.csv', index=False)

    return invoice_comparison
