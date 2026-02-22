import re
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt

print("----INFO----")
print(f"numpy - ",np.__version__) 
print(f"pandas -",pd.__version__) 
pd.set_option("display.max_rows",20)
pd.set_option("display.width",None)
pd.set_option("display.max_columns",30)
print("----TAXAMADE----")

found = False

def parse_column(col):
    error = 0
    data=oo.dropna(subset=["Směr"],axis=0,how="any")    # only valid column
    data=data.dropna(axis=1,how="all")                  # drop empty column
    data=data.drop("Text FIO",axis=1)                   # drop unused column
    data=data.loc[data["Směr"]==col]               # use only for SELL

    data["Datum obchodu"] = pd.to_datetime(
        data["Datum obchodu"],
        # format="%d.%m.%Y %H:%M",  # přesný formát "24.11.2025 17:24"
        errors="coerce"           # neparsovatelné hodnoty -> NaT (něco jako NaN pro datum)
    )
    #conversion to number
    cols = ["Cena", "Počet", "Objem v CZK","Poplatky v CZK","Objem v USD","Poplatky v USD","Objem v EUR","Poplatky v EUR"]                # columns

    for cmn in cols:
        data[cmn] = (
            data[cmn]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace("\u00A0", "", regex=False)  # NBSP
            .str.replace("\u202F", "", regex=False)  # thin NBSP
            .str.replace(" ", "", regex=False)       # běžná mezera
            .astype(float)
        )
        data[cmn] = data[cmn].fillna(0)                 # NaN to 0
        if (data[cmn].isna().sum())>0:
            print(data[cmn].isna().sum(), "non parsed values") # 0 = OK
            error=error+1

    print("PARSE ERRORS = ",error)
    return data

with open("Obchody.csv", "r") as fin, open("fio.csv", "w") as fout:
    for line in fin:
        if not found and line.lstrip().startswith("Datum obchodu"):
            found = True

        if found:
            # Nahradit středníky čárkami
            #line = line.replace(";", ",")          #not needed
            fout.write(line)

oo = pd.read_csv('fio.csv',sep=';',encoding='ANSI') # with semicolon

sell=parse_column("Prodej")
sell.info()
buy=parse_column("Nákup")
buy.info()

cols_to_sum = ["Objem v CZK", "Poplatky v CZK","Objem v USD","Poplatky v USD","Objem v EUR","Poplatky v EUR"] 
# groupby nad 2. sloupcem a součet 3. sloupce
out = sell.groupby("Symbol", as_index=False)[cols_to_sum].sum()
print(out)           # tabulka (col2, col3_sum)
out = buy.groupby("Symbol", as_index=False)[cols_to_sum].sum()
print(out)           # tabulka (col2, col3_sum)

# Nebo vypsat po řádcích:
#for _, r in out.iterrows():
#    print(r["Symbol"], r[cols_to_sum])



pole = sell.to_numpy()
pole2=buy.to_numpy()
with open('output.txt', 'w') as outfile:
    outfile.write(str(pole)) 

uniq, inv = np.unique(pole[:,2], return_inverse=True)   
# 3) Sečteme 3. sloupec podle skupin v 2. sloupci
sums = np.zeros(len(uniq), dtype=float)
np.add.at(sums, inv, pole[:, 3])

#print(uniq,inv,sums)

print("__________________________")
# Výsledek: dvojice (unikátní_hodnota, součet)
for u, s in zip(uniq, sums):
    print(u, s)




