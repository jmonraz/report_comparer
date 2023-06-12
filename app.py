import pandas as pd
from flask import Flask, render_template, request, send_file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']

        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        df2 = df2.dropna(subset=[df2.columns[0]])
        df2 = df2.reset_index(drop=True)

        print(df2.head())

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

# if __name__ == '__main__':
#     root = tk.Tk()
#     root.withdraw()
#     file1 = filedialog.askopenfilenames(
#         title="Select Invoice File", filetypes=[("CSV Files", "*csv")])
#     file1 = list(file1)
#     file2 = filedialog.askopenfilenames(
#         title="Select Shipstation File", filetypes=[("CSV Files", "*csv")])
#     file2 = list(file2)

#     df1 = pd.read_csv(file1[0])
#     df2 = pd.read_csv(file2[0])

#     df2 = df2.dropna(subset=[df2.columns[0]])
#     df2 = df2.reset_index(drop=True)

#     print(df2.head())

#     merged_df = pd.merge(df1, df2, how='left',
#                          left_on='SHIPPER REFERENCE', right_on='Order Number')

#     df1.insert(40, 'Shipstation Total', merged_df['Carrier Fee'])

#     df1.insert(40, 'Combined Total', df1.groupby(
#         'SHIPPER REFERENCE')['SHIPMENT TOTAL'].transform('sum'))

#     df1.insert(40, 'Shipstation Total (Updated)', df1['Shipstation Total'].mask(
#         df1.duplicated(subset='SHIPPER REFERENCE')))
#     df1.insert(40, 'Combined Total (Updated)', df1['Combined Total'].mask(
#         df1.duplicated(subset='SHIPPER REFERENCE')))

#     df1.drop(columns=['Combined Total', 'Shipstation Total'], inplace=True)

#     desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
#     path = os.path.join(desktop_path, 'output.csv')
#     df1.to_csv(path, index=False)
