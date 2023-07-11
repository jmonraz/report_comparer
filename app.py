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
            df1 = pd.read_csv(file1)
        if file2.filename.endswith('.xlsx'):
            df2 = pd.read_excel(file2)
        elif file2.filename.endswith('csv'):
            df2 = pd.read_csv(file2)

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
        file1 = request.files['file1']
        file2 = request.files['file2']

        df_orders = pd.read_csv(file1)
        df_invoice = pd.read_csv(file2)

        df_orders = df_orders.loc[:, ['ORDER ID', 'ZONE']]

        df_invoice = df_invoice.merge(
            df_orders[['ORDER ID', 'ZONE']], on='ORDER ID', how='left')

        df_invoice = df_invoice.rename(columns={'ZONE': 'Zone'})

        df_invoice['Zone'] = df_invoice['Zone'].str.replace(
            r'^[A-Za-z]+', '', regex=True)

        df_invoice['Zone'] = df_invoice['Zone'].fillna(0)

        df_invoice['Package Weight'] = pd.to_numeric(
            df_invoice['Package Weight'], errors='coerce')

        df_invoice['Package Weight OZ'] = df_invoice['Package Weight'].apply(
            lambda x: math.ceil(x * 16) if x < 1 else 0)

        df_invoice['Package Weight LB'] = df_invoice['Package Weight'].apply(
            lambda x: math.ceil(x) if x >= 1 else 0)

        output_path = 'updated_invoice.csv'
        df_invoice.to_csv(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template('3plwinner.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
