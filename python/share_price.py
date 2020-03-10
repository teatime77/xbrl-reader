import datetime
import os
import sys
import json
from collections import Counter
from pathlib import Path
import urllib.request
import codecs
import zipfile
import xml.etree.ElementTree as ET
import time
import re
import random
import pickle
from typing import Dict, List, Any
from collections import OrderedDict
import multiprocessing
from multiprocessing import Process, Array
import pandas as pd
from datetime import datetime

start_time = time.time()

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path = root_dir + '/data/share_price'

def kabuka_main():
    kaisha = pd.read_csv("%s/data/EDINET/EdinetcodeDlInfo.csv" % root_dir, encoding='cp932', skiprows=[0], dtype={'証券コード':'object'})
    # kaisha = kaisha.astype({'証券コード': str})
    kaisha = kaisha.set_index('証券コード')   # ('ＥＤＩＮＥＴコード')
    print(kaisha[0:1])

    print(kaisha.dtypes)
    print(kaisha.columns)

    df = pd.DataFrame()

    for zip_idx, zip_path_obj in enumerate(Path(data_path).glob("**/*.zip")):
        zip_path = str(zip_path_obj)

        try:
            with zipfile.ZipFile(zip_path) as zf:
                assert len(zf.namelist()) == 1
                csv_file = zf.namelist()[0]

                with zf.open(csv_file) as f:
                    csv_bin = f.read()
        except zipfile.BadZipFile:
            print("\nBadZipFile : %s\n" % zip_path)
            continue

        csv_text = csv_bin.decode('cp932')
        lines = csv_text.split('\r\n')
        for line in lines:
            items = line.split(',')
            if len(items) != 10:
                continue

            code = items[1].strip()
            if len(code) == 0:
                continue

            code2 = code + "0"
            try:
                data = kaisha.loc[code2]
                # print("[%s][%s]" % (items[3], data['提出者名']))
            except KeyError:
                continue

            date = datetime.strptime(items[0], '%Y/%m/%d')

            try:
                df.at[data['ＥＤＩＮＥＴコード'], date ] = float(items[7])

            except:
                print("error", items)

        # print(df.iloc[:10])
        print(df.shape, zip_path)

    df.sort_index(axis=1, inplace=True)

    with open(root_dir + '/python/data/share_price.pickle', 'wb') as f:
        pickle.dump(df, f)

    print('終了:%d' % int(time.time() - start_time) )

if __name__ == '__main__':
    kabuka_main()