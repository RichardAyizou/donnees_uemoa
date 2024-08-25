import pandas as pd
import re
from io import StringIO


class Data:
    def __init__(self, file_path, file_type='xls'):
        self.file_path = file_path
        self.file_type = file_type
        
        if self.file_type=='xls':
            self.content, self.content_str, self.country_pattern, self.country_list = self.read_file()
        elif self.file_type=='csv':
            self.data, self.country_list, self.content_str = self.read_file()
            
        self.merged = self.get_header()
        
        
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
        df1.columns = [col.replace('.', '').strip() for col in list(columns1)]
        df1 = df1.reset_index().rename(columns={'index':'Annee'})
        # create country column
        df1['Country'] = self.country_list[0]
        
        # initialize a merged dataframe with columns names only
        merged = pd.DataFrame(columns=df1.columns)
        return merged
    
    
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
            df = df[2:]
            df.columns = [col.replace('.', '').strip() for col in list(columns)]
            df = df.reset_index().rename(columns={'index':'Annee'})
            df['Country'] = c
            self.merged = pd.concat([self.merged, df])

        return self.merged
        