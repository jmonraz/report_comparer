import pandas as pd
import numpy as np
import math
from flask import Flask, render_template, request, send_file
import os
from invoice_comparison_report2 import invoice_comparison
from datetime import datetime 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route('/test-home', methods=['GET', 'POST'])
def test_page():
    return render_template('home2.html')


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         file1 = request.files['file1']
#         file2 = request.files['file2']
#
#         if file1.filename.endswith('.xlsx'):
#             df1 = pd.read_excel(file1)
#         elif file1.filename.endswith('.csv'):
#             df1 = pd.read_csv(file1, encoding='latin-1')
#         if file2.filename.endswith('.xlsx'):
#             df2 = pd.read_excel(file2)
#         elif file2.filename.endswith('csv'):
#             df2 = pd.read_csv(file2, encoding='latin-1')
#
#         df2 = df2.dropna(subset=[df2.columns[0]])
#
#         df2 = df2.reset_index(drop=True)
#
#         merged_df = pd.merge(df1, df2, how='left',
#                              left_on='SHIPPER REFERENCE', right_on='Order Number')
#
#         df1.insert(40, 'Shipstation Total', merged_df['Carrier Fee'])
#
#         df1.insert(40, 'Combined Total', df1.groupby(
#             'SHIPPER REFERENCE')['SHIPMENT TOTAL'].transform('sum'))
#
#         df1.insert(40, 'Shipstation Total (Updated)', df1['Shipstation Total'].mask(
#             df1.duplicated(subset='SHIPPER REFERENCE')))
#
#         df1.insert(40, 'Combined Total (Updated)', df1['Combined Total'].mask(
#             df1.duplicated(subset='SHIPPER REFERENCE')))
# # This code inserts a new column called 'Combined Total (Updated)' into the DataFrame df1.
# # The values in this column are determined by the 'Combined Total' column of df1, but with some values masked.
# # The mask is applied using the mask() function, which takes a boolean condition as an argument.
# # The condition checks for duplicated values in the 'SHIPPER REFERENCE' column of df1.
# # If a value in the 'SHIPPER REFERENCE' column is duplicated, the corresponding value in the 'Combined Total (Updated)' column is masked (set to NaN).
# # If a value in the 'SHIPPER REFERENCE' column is unique, the corresponding value in the 'Combined Total (Updated)' column remains unchanged.
#
#         df1.drop(columns=['Combined Total', 'Shipstation Total'], inplace=True)
#
#         output_path = 'output.csv'
#         df1.to_csv(output_path, index=False)
#
#         return send_file(output_path, as_attachment=True)
#     return render_template('index.html')


@app.route('/luxe-dhl-3pl', methods=['GET', 'POST'])
def second_page():
    if request.method == 'POST':
        rates_path = './static/data'

        file1 = request.files['file1']
        file2 = request.files['file2']

        dhl_rates = os.path.join(rates_path, 'DHL_prices.csv')
        dhl_prices = pd.read_csv(dhl_rates, encoding='utf-8-sig')

        df_orders = pd.read_csv(file1, encoding='utf-8-sig')
        df_orders = df_orders.rename(
            columns={'Billing_Ref2': 'Order Id', 'Service Type ': 'Service Type'})

        df_orders = df_orders.loc[:, [
                                         'Order Id', 'Pricing_Zone', 'Service Type', 'Weight']]

        df_invoice = pd.read_csv(file2, encoding='utf-8-sig')
        df_invoice = df_invoice.rename(columns={'ORDER ID': 'Order Id'})

        df_invoice = df_invoice.merge(
            df_orders[['Order Id', 'Pricing_Zone', 'Service Type', 'Weight']], on='Order Id', how='left')

        # df_invoice = df_invoice.rename(columns={'Zone': 'Zone'})

        df_invoice['Pricing_Zone'] = df_invoice['Pricing_Zone'].str.replace(
            r'^[A-Za-z]+', '', regex=True)

        df_invoice['Pricing_Zone'] = df_invoice['Pricing_Zone'].fillna(0)
        df_invoice['Pricing_Zone'] = df_invoice['Pricing_Zone'].astype(int)

        df_invoice['Package Weight'] = pd.to_numeric(
            df_invoice['Package Weight'], errors='coerce')

        df_invoice['Weight'] = pd.to_numeric(
            df_invoice['Weight'], errors='coerce')

        df_invoice['Weight'] = df_invoice['Weight'].fillna(0)

        df_orders.info()
        df_invoice.info()

        df_invoice['Package_Weight_Converted'] = df_invoice['Weight'].apply(
            lambda x: f"{math.ceil(x * 16):.0f}oz" if x < 1 else f"{math.ceil(x)}lb")

        df_invoice['Package_Weight_Converted2'] = df_invoice['Package Weight'].apply(
            lambda x: f"{math.ceil(x * 16):.0f}oz" if x < 1 else f"{math.ceil(x)}lb")

        price_mapping = dhl_prices.set_index(
            ['Pricing_Zone', 'Weight', 'Service Type'])['Price'].to_dict()
        print(price_mapping)

        def get_package_price(row):
            key = (row['Pricing_Zone'],
                   row['Package_Weight_Converted'], row['Service Type'])
            return price_mapping.get(key, 0)

        df_invoice['Total Price'] = df_invoice.apply(
            get_package_price, axis=1)

        df_invoice['TRACKING NUMBER'] = df_invoice['TRACKING NUMBER'].apply(
            lambda x: f'`{x}')

        output_path = 'updated_invoice.csv'
        df_invoice.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template('3plwinner.html')


@app.route('/usps-3pl', methods=['GET', 'POST'])
def third_page():
    if request.method == 'POST':
        data_path = './static/data'

        file1 = request.files['file1']

        dsx_data = os.path.join(data_path, 'dsx_data.csv')

        usps_report = pd.read_csv(file1, encoding='latin-1')
        dsx_report = pd.read_csv(dsx_data, encoding='latin-1')

        # rename column names for usps_report 'customMessage1' to 'MarketOrderId'
        usps_report = usps_report.rename(
            columns={'customMessage1': 'MarketOrderId'})

        merged_df = usps_report.merge(dsx_report[[
            'MarketOrderId', 'NegotiatedCost', 'MarkupCost', 'CartonWeight']], on='MarketOrderId', how='left')

        merged_df['CartonWeight'] = merged_df['CartonWeight'].fillna(0)
        merged_df['CartonWeight'] = merged_df['CartonWeight'].astype(float)
        merged_df['CartonWeight'] = merged_df['CartonWeight'].apply(
            lambda x: f"{math.ceil(x * 16):.0f}oz" if x < 1 else f"{math.ceil(x)}lb")

        output_path = 'updated_usps_report.csv'
        merged_df.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template('usps-3pl.html')


@app.route('/freight-innovations-3pl', methods=['GET', 'POST'])
def fourth_page():
    if request.method == 'POST':
        data_path = './static/data'

        file1 = request.files['file1']

        dsx_data = os.path.join(data_path, 'dsx_data.csv')

        freight_report = pd.read_csv(file1, encoding='utf-8-sig')
        freight_report = freight_report.rename(
            columns={'Billing_Ref2': 'MarketOrderId', 'Service Type ': 'Service Type'})
        dsx_report = pd.read_csv(dsx_data, encoding='utf-8-sig')

        dsx_report.info()
        freight_report.info()

        print("Before merging:", len(freight_report))
        print('merging')

        merged_df = freight_report.merge(dsx_report[[
            'MarketOrderId', 'NegotiatedCost', 'MarkupCost']], on='MarketOrderId', how='left')

        merged_df = merged_df.drop_duplicates(
            subset=['MarketOrderId', 'MarkupCost'], keep='first')

        print('merge done')

        output_path = 'updated_freight_report.csv'
        merged_df.to_csv(output_path, index=False)

        print("After merging:", len(merged_df))
        print('done')

        return send_file(output_path, as_attachment=True)

    return render_template('freight-innovations-3pl.html')


@app.route('/format-dsx-file', methods=['GET', 'POST'])
def fifth_page():
    def add_backtick(cell):
        numbers = [f"`{num.strip()}" if not num.strip().startswith(
            "`") else num.strip() for num in cell.split(',')]
        return ','.join(numbers)

    if request.method == 'POST':

        file1 = request.files['file1']

        dsx_report = pd.read_csv(file1, encoding='utf-8-sig')

        dsx_report.info()

        dsx_report['TrackingNumber'] = dsx_report['TrackingNumber'].apply(
            add_backtick)

        # Split Tracking Number and MarkupCost cells into lists
        dsx_report['TrackingNumber'] = dsx_report['TrackingNumber'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['MarkupCost'] = dsx_report['MarkupCost'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['NegotiatedCost'] = dsx_report['NegotiatedCost'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['CartonWeight'] = dsx_report['CartonWeight'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['Class'] = dsx_report['Class'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['ShippedCarrierCode'] = dsx_report['ShippedCarrierCode'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['Carrier'] = dsx_report['Carrier'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['IsVoid'] = dsx_report['IsVoid'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['DateShipped'] = dsx_report['DateShipped'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])
        dsx_report['ShipUsername'] = dsx_report['ShipUsername'].apply(
            lambda x: x.split(',') if isinstance(x, str) else [])

        # Create a list to store new rows
        new_rows = []

        # Iterate through each row
        for index, row in dsx_report.iterrows():
            tracking_numbers = row['TrackingNumber']
            markup_costs = row['MarkupCost']
            negotiated_costs = row['NegotiatedCost']
            carton_weights = row['CartonWeight']
            classes = row['Class']
            shipped_carrier_codes = row['ShippedCarrierCode']
            carriers = row['Carrier']
            is_voided = row['IsVoid']
            date_shipped = row['DateShipped']
            ship_username = row['ShipUsername']

            if markup_costs:
                non_zero_mc = [
                    value for value in markup_costs if value.strip() != '0.00']

                non_zero_nc = [
                    value for value in negotiated_costs if value.strip() != '0.00']

                if non_zero_mc:
                    for tn in tracking_numbers:
                        new_row = row.copy()
                        new_row['TrackingNumber'] = tn
                        new_row['MarkupCost'] = ','.join(non_zero_mc)
                        new_row['NegotiatedCost'] = ','.join(non_zero_nc)

                    for cw in carton_weights:
                        new_row['CartonWeight'] = cw

                    for c in classes:
                        new_row['Class'] = c

                    for sc in shipped_carrier_codes:
                        new_row['ShippedCarrierCode'] = sc

                    for c in carriers:
                        new_row['Carrier'] = c

                    for v in is_voided:
                        new_row['IsVoid'] = v

                    for ds in date_shipped:
                        new_row['DateShipped'] = ds

                    for su in ship_username:
                        new_row['ShipUsername'] = su

                    new_rows.append(new_row)

        # Function to filter non-zero values and join them back as a string

        def filter_non_zero(value_str):
            values = value_str.split(',')
            non_zero_values = [v for v in values if v != '0.00']
            return ','.join(non_zero_values)

        # Create a new DataFrame from the list of new rows
        new_df = pd.DataFrame(new_rows)

        # Apply the function to the 'markup cost' column
        new_df['MarkupCost'] = new_df['MarkupCost'].apply(filter_non_zero)
        new_df['NegotiatedCost'] = new_df['NegotiatedCost'].apply(
            filter_non_zero)

        output_path = 'updated_dsx_report.csv'
        new_df.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template('format-dsx-file.html')


@app.route('/fedex-3pl', methods=['GET', 'POST'])
def sixth_page():
    if request.method == 'POST':
        data_path = './static/data'

        file1 = request.files['file1']

        dsx_data = os.path.join(data_path, 'dsx_data.csv')

        dsx_report = pd.read_csv(dsx_data, encoding='utf-8-sig')

        fedex_invoice = pd.read_csv(file1, encoding='utf-8-sig')

        fedex_invoice = fedex_invoice.rename(
            columns={'AIRBILL #': 'TrackingNumber'})

        fedex_invoice['TrackingNumber'] = fedex_invoice['TrackingNumber'].apply(
            lambda x: f'`{x}')

        merged_df = fedex_invoice.merge(dsx_report[[
            'TrackingNumber', 'MarketOrderId', 'NegotiatedCost', 'MarkupCost']], on='TrackingNumber', how='left')

        merged_df = merged_df.loc[:, ['INVOICE #', 'INVOICE DATE', 'MarketOrderId', 'TrackingNumber', 'CONSIGNEE NAME',
                                      'CONSIGNEE ATTENTION', 'CONSIGNEE ADDRESS 1', 'CONSIGNEE ADDRESS 2',
                                      'CONSIGNEE CITY', 'CONSIGNEE STATE', 'CONSIGNEE ZIP CODE',
                                      'CONSIGNEE COUNTRY CODE',
                                      'SHIPMENT DATE', 'PRODUCT CODE', 'ZONE', 'BILLED WEIGHT', 'PIECES', 'DIMENSIONS',
                                      'SHIPMENT TOTAL',
                                      'BASE CHARGE AMOUNT', 'MarkupCost', 'NegotiatedCost']]

        output_path = 'updated_freight_report.csv'
        merged_df.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template('fedex-3pl.html')


@app.route('/', methods=['GET', 'POST'])
def seventh_page():
    if request.method == 'POST':
        ups_file = request.files['ups_file']

        shipstation_file = request.files['shipstation_file']

        invoice_comparison_report = invoice_comparison(ups_file=ups_file, shipstation_file=shipstation_file)
        # Generate a timestamp for the processed file name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_name = f'invoice_comparison_report_{timestamp}.csv'
        invoice_comparison_report.to_csv(output_name, index=False)
        return send_file(output_name, as_attachment=True)
    return render_template('logico-ups-invoice-comparison.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
