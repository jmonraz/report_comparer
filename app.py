import pandas as pd
import numpy as np
import math
from flask import Flask, render_template, request, send_file
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']

        if file1.filename.endswith('.xlsx'):
            df1 = pd.read_excel(file1)
        elif file1.filename.endswith('.csv'):
            df1 = pd.read_csv(file1, encoding='latin-1')
        if file2.filename.endswith('.xlsx'):
            df2 = pd.read_excel(file2)
        elif file2.filename.endswith('csv'):
            df2 = pd.read_csv(file2, encoding='latin-1')

        df2 = df2.dropna(subset=[df2.columns[0]])
        df2 = df2.reset_index(drop=True)

        merged_df = pd.merge(df1, df2, how='left',
                             left_on='SHIPPER REFERENCE', right_on='Order Number')

        df1.insert(40, 'Shipstation Total', merged_df['Carrier Fee'])

        df1.insert(40, 'Combined Total', df1.groupby(
            'SHIPPER REFERENCE')['SHIPMENT TOTAL'].transform('sum'))

        df1.insert(40, 'Shipstation Total (Updated)', df1['Shipstation Total'].mask(
            df1.duplicated(subset='SHIPPER REFERENCE')))
        df1.insert(40, 'Combined Total (Updated)', df1['Combined Total'].mask(
            df1.duplicated(subset='SHIPPER REFERENCE')))

        df1.drop(columns=['Combined Total', 'Shipstation Total'], inplace=True)

        output_path = 'output.csv'
        df1.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)
    return render_template('index.html')


@app.route('/3plwinner', methods=['GET', 'POST'])
def second_page():
    if request.method == 'POST':

        rates_path = './static/data'

        file1 = request.files['file1']
        file2 = request.files['file2']

        dhl_rates1 = os.path.join(rates_path, 'DHL_expedited_max_1lbover.csv')
        dhl_rates2 = os.path.join(rates_path, 'DHL_expedited_max_1lbless.csv')

        dhl_less_lb = pd.read_csv(dhl_rates2, encoding='utf-8-sig')
        dhl_over_lb = pd.read_csv(dhl_rates1, encoding='utf-8-sig')

        df_orders = pd.read_csv(file1, encoding='utf-8-sig')
        df_orders = df_orders.loc[:, ['Order Id', 'Zone']]

        df_invoice = pd.read_csv(file2, encoding='utf-8-sig')

        df_invoice = df_invoice.merge(
            df_orders[['Order Id', 'Zone']], on='Order Id', how='left')

        df_invoice = df_invoice.rename(columns={'Zone': 'Zone'})

        df_invoice['Zone'] = df_invoice['Zone'].str.replace(
            r'^[A-Za-z]+', '', regex=True)

        df_invoice['Zone'] = df_invoice['Zone'].fillna(0)
        df_invoice['Zone'] = df_invoice['Zone'].astype(int)

        df_invoice['Package Weight'] = pd.to_numeric(
            df_invoice['Package Weight'], errors='coerce')

        df_invoice['Package Weight OZ'] = df_invoice['Package Weight'].apply(
            lambda x: math.ceil(x * 16) if x < 1 else 0)

        df_invoice['Package Weight LB'] = df_invoice['Package Weight'].apply(
            lambda x: math.ceil(x) if x >= 1 else 0)

        print(dhl_less_lb.columns)
        print(dhl_over_lb.columns)

        rates1_mapping = dhl_less_lb.set_index(['Zone', 'Package Weight OZ'])[
            'Price'].to_dict()

        rates2_mapping = dhl_over_lb.set_index(
            ['Zone', 'LBS'])['Price'].to_dict()

        def get_package_price_oz(row):
            key = (row['Zone'], row['Package Weight OZ'])
            return rates1_mapping.get(key, 0)

        def get_package_price_lb(row):
            key = (row['Zone'], row['Package Weight LB'])
            return rates2_mapping.get(key, 0)

        df_invoice['Package Price OZ'] = df_invoice.apply(
            get_package_price_oz, axis=1)

        df_invoice['Package Price LB'] = df_invoice.apply(
            get_package_price_lb, axis=1)

        # Remove the '$' symbol and then convert currency strings to numeric values
        df_invoice['Package Price OZ'] = df_invoice['Package Price OZ'].str.replace(
            '[^\d.]', '', regex=True).astype(float)
        df_invoice['Package Price LB'] = df_invoice['Package Price LB'].str.replace(
            '[^\d.]', '', regex=True).astype(float)

        df_invoice['Package Price LB'] = df_invoice['Package Price LB'].replace(
            '', '0.00')
        df_invoice['Package Price OZ'] = df_invoice['Package Price OZ'].replace(
            '', '0.00')

        # Convert columns to numeric
        df_invoice['Package Price OZ'] = pd.to_numeric(
            df_invoice['Package Price OZ'])
        df_invoice['Package Price LB'] = pd.to_numeric(
            df_invoice['Package Price LB'])

        df_invoice['Package Price'] = df_invoice['Package Price OZ'] + \
            df_invoice['Package Price LB']

        df_invoice['Package Price'] = df_invoice['Package Price'].round(2)

        df_invoice['Package Price'] = df_invoice['Package Price'].apply(
            lambda x: '${:,.2f}'.format(x))

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

        merged_df = usps_report.merge(dsx_report[[
                                      'MarketOrderId', 'NegotiatedCost', 'MarkupCost']], on='MarketOrderId', how='left')

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
        dsx_report = pd.read_csv(dsx_data, encoding='utf-8-sig')

        merged_df = freight_report.merge(dsx_report[[
            'MarketOrderId', 'NegotiatedCost', 'MarkupCost']], on='MarketOrderId', how='left')

        output_path = 'updated_freight_report.csv'
        merged_df.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template('freight-innovations-3pl.html')


@app.route('/format-dsx-file', methods=['GET', 'POST'])
def fifth_page():
    if request.method == 'POST':

        file1 = request.files['file1']

        dsx_report = pd.read_csv(file1, encoding='utf-8-sig')

        dsx_report['TrackingNumber'] = dsx_report['TrackingNumber'].apply(
            lambda x: f'`{x}')

        # split TrackingNumber, MarkupCost, and NegotiatedCost cells into lists
        dsx_report['TrackingNumber'] = dsx_report['TrackingNumber'].apply(
            lambda x: x.split(', ') if isinstance(x, str) else [])
        dsx_report['MarkupCost'] = dsx_report['MarkupCost'].apply(
            lambda x: x.split(', ') if isinstance(x, str) else [])
        dsx_report['NegotiatedCost'] = dsx_report['NegotiatedCost'].apply(
            lambda x: x.split(', ') if isinstance(x, str) else [])

        # create a list to store new rows
        new_rows = []

        # iterate through each row in the dataframe
        for index, row in dsx_report.iterrows():
            tracking_numbers = row['TrackingNumber']
            markup_costs = row['MarkupCost']
            negotiated_costs = row['NegotiatedCost']

            if markup_costs:
                non_zero_mc = [
                    value for value in markup_costs if value.strip() != '0.00']

                non_zero_nc = [
                    value for value in negotiated_costs if value.strip() != '0.00']

                if non_zero_mc:
                    for tn in tracking_numbers:
                        new_row = row.copy()
                        new_row['TrackingNumber'] = tn
                        new_row['MarkupCost'] = ', '.join(non_zero_mc)
                        new_row['NegotiatedCost'] = ', '.join(non_zero_nc)
                        new_rows.append(new_row)

        # function to filter non-zero values and join them back as string
        def filter_non_zero(value_str):
            values = value_str.split(', ')
            non_zero_values = [
                value for value in values if value.strip() != '0.00']
            return ', '.join(non_zero_values)

        # create a new dataframe from the list of new rows
        new_df = pd.DataFrame(new_rows)

        # apply the function to the 'markup cost' column
        new_df['MarkupCost'] = new_df['MarkupCost'].apply(filter_non_zero)
        new_df['NegotiatedCost'] = new_df['NegotiatedCost'].apply(
            filter_non_zero)

        new_df.to_csv('updated_dsx_report.csv', index=False)

        return send_file('updated_dsx_report.csv', as_attachment=True)

    return render_template('format-dsx-file.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
