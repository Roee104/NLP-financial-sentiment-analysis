# scripts/build_company_dict.py
import json
import yfinance as yf
import pandas as pd
import tqdm
d = {}
for sym in tqdm.tqdm(pd.read_csv('data/ticker_master.csv').symbol):
    try:
        info = yf.Ticker(sym).info
        name = info.get('shortName')
        if name:
            d[name.lower()] = sym
    except:
        pass
json.dump(d, open('data/company_dict.json', 'w'))
