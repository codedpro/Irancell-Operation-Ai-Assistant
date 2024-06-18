import pandas as pd

def extract_data_from_excel(file_path, Header):
    df = pd.read_excel(file_path, sheet_name='2GDaily', header=[0])
    
    dates = df.iloc[0, 1:].tolist()

    headers = df.columns[1:].tolist()

    selected_regions = df.loc[df['Region'].isin(['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10']), :]

    header_data = []

    for header, date in zip(headers, dates):
         if date == Header:
            header_name = header.split('.')[0].replace('-', '_') 

            header_values = selected_regions[[header, 'Region']]
            header_values.columns = ['Availability', 'Region']

            availability_values = header_values['Availability'].tolist()
            region_values = header_values['Region'].tolist()

            formatted_date = f"{date}"

            header_dict = {
                header_name: {
                    formatted_date: availability_values,
                    "region": region_values
                }
            }

            header_data.append(header_dict)

    return header_data

