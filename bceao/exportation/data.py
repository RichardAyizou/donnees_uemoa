import pandas as pd
import numpy as np

import re
from io import StringIO

import plotly.express as px

class Data:
    def __init__(self, file_path, file_type='xls'):
        self.file_path = file_path
        self.file_type = file_type
        
        if self.file_type=='xls':
            self.content, self.content_str, self.country_pattern, self.country_list = self.read_file()
        elif self.file_type=='csv':
            self.data, self.country_list, self.content_str = self.read_file()
        
        self.patern_mois = r'^[A-Z]{3}[0-9]{4}$'
        self.dict_mois = {
            'JAN': '01', 'FEV': '02', 'MAR': '03', 'AVR': '04',
            'MAI': '05', 'JUN': '06', 'JUL': '07', 'AOU': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        self.merged, self.dict_columns = self.get_header()
        
        
    def read_file(self):
        if self.file_type=='xls':
            with open(self.file_path, 'rb') as file:
                content = file.read()
            content_str = content.decode('utf-8')
            country_pattern = re.compile(r'\n\n(.*?)\s*;', re.DOTALL)
            country_list = country_pattern.findall(content_str)
            return content, content_str, country_pattern, country_list
        elif self.file_type=='csv':
            data = pd.read_csv(self.file_path, sep=';')
            content_str = data.reset_index().to_string()
            country_pattern = ["COTE D'IVOIRE", 'BENIN', 'BURKINA FASO', 'MALI', 'NIGER',
       'SENEGAL', 'GUINEE BISSAU', 'TOGO', 'ENSEMBLE UMOA']
            country_list = [c for c in country_pattern if c in re.findall(rf'{re.escape(c)}', content_str)]
            
            return data, country_list, content_str
    
    
    def get_header(self):
        if self.file_type=='xls':
            # get country pattern
            pattern = re.compile(rf'\n\n{re.escape(self.country_list[0])}(.*?)(?=\n\n|$)', re.DOTALL)
            data_list = pattern.findall(self.content_str)

            # transform the data to read in csv
            data_str = ''.join(data_list)
            data_io = StringIO(data_str)

            # read as csv
            df1 = pd.read_csv(data_io, sep=';')
            df1.reset_index(inplace=True)
        elif self.file_type=='csv':
            df1 = pd.read_csv(self.file_path, sep=';')
            df1.reset_index(inplace=True)
        
        # set first row as header
        columns1 = df1.iloc[0]
        df1 = df1[1:]
        df1.columns = list(columns1)
        
        # the last column is empty, remove it
        df1 = df1.iloc[:, :-1]
        
        # transpose to have years in rows
        df1 = df1.transpose()
        
        # set indicators as columns names
        columns1 = df1.iloc[1] 
        code1 = df1.iloc[0].str[3:]
        zip_code_columns1 = list(zip(code1, columns1))
        dict_columns = dict(zip_code_columns1)
        df1.columns = [col.replace('.', '').strip() for col in list(columns1)]
        df1 = df1.reset_index().rename(columns={'index':'Date'})
        if df1['Date'].apply(lambda x: bool(re.match(self.patern_mois, x))).all():
            df1['Mois'] = df1['Date'].str[:3]
            df1['Annee'] = df1['Date'].str[3:]
        
        # create country column
        df1['Country'] = self.country_list[0]
        
        # initialize a merged dataframe with columns names only
        merged = pd.DataFrame(columns=df1.columns)
        return merged, dict_columns
    
    
    def load_data(self):
        # Isoler chaque pays
        for c in self.country_list:
            if self.file_type=='xls':
                pattern = re.compile(rf'\n\n{re.escape(c)}(.*?)(?=\n\n|$)', re.DOTALL)
                data_list = pattern.findall(self.content_str)
                data_str = ''.join(data_list)
                data_io = StringIO(data_str)
                df = pd.read_csv(data_io, sep=';')
                df.reset_index(inplace=True)
            elif self.file_type=='csv':
                df = pd.read_csv(self.file_path, sep=';').reset_index()
            columns = df.iloc[0] 
            df = df[1:]
            df.columns = list(columns)
            df = df.iloc[:, :-1]
            df = df.transpose()
            columns = df.iloc[1]
            code = df.iloc[0]
            zip_code_columns = list(zip(code, columns))
            df = df[2:]
            l_columns = [code_indicateur[3:] if pd.isnull(libelle_indicateur) else libelle_indicateur for code_indicateur, libelle_indicateur in zip_code_columns]
            df.columns = [col.replace('.', '').strip() for col in l_columns]
            df.rename(columns=self.dict_columns, inplace=True)
            
            df = df.reset_index().rename(columns={'index':'Date'})
            df['Country'] = c
            self.merged = pd.concat([self.merged, df])
            self.merged = self.merged.replace('-', np.nan)
            col_sans_country = [col for col in df.columns.to_list() if ((col!='Country') & (col!='Date'))]
#             self.merged.loc[:, col_sans_country] = self.merged.loc[:, col_sans_country].replace(',', '', regex=True).astype(float)
            print(col_sans_country)
            self.merged.loc[:, col_sans_country] = self.merged.loc[:, col_sans_country].replace(',', '.', regex=True).astype(float)
            if self.merged['Date'].astype(str).apply(lambda x: bool(re.match(self.patern_mois, x))).all():
                self.merged['Mois'] = self.merged['Date'].str[:3].map(self.dict_mois)
                self.merged['Annee'] = self.merged['Date'].str[3:]
                self.merged = self.merged.sort_values(by=['Annee', 'Mois', 'Country'])
            else:
                self.merged['Date'] = pd.to_datetime(self.merged['Date'])
                self.merged = self.merged.sort_values(by=['Date', 'Country'])
            

        return self.merged
        