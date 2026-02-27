
""" TAXAMADE"""
import os
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

print("----INFO----")
print("numpy - ",np.__version__)
print("pandas -",pd.__version__)
pd.set_option("display.max_rows",20)
pd.set_option("display.width",None)
pd.set_option("display.max_columns",30)
np.set_printoptions(threshold=np.inf, linewidth=np.inf) #switch off linewidth
print("----TAXAMADE----")

found = False       # pylint: disable=invalid-name
kurz_USD = 21.84    # pylint: disable=invalid-name
kurz_EUR = 24.66    # pylint: disable=invalid-name
print(f"Jednotný kurz: USD {kurz_USD} , EUR {kurz_EUR}")

####    parsing CSV do PD tab  ####
def parse_column(col):
    """ CSV FIO parse """
    error = 0
    data=oo.dropna(subset=["Symbol"],axis=0,how="any")    # only valid line
    data=data.dropna(axis=1,how="all")                  # drop empty column
    #data=data.drop("Text FIO",axis=1)                   # drop unused column
    #print(f"[DEBUG] col = {repr(col)} type={type(col)}")
    if col=="":
        data = data.loc[(data["Směr"].isna()) | (data["Směr"] == "")] # use only for col
    # ~ je negace / str.contains("ADR") najde všchny obsahující "ADR"/ na=False - NaN = "neobsahuje ADR"
        data = data[~data["Text FIO"].str.contains("ADR", na=False)]
    else:
        data=data.loc[data["Směr"]==col]

    data["Datum obchodu"] = pd.to_datetime(
        data["Datum obchodu"],
        format="%d.%m.%Y %H:%M",  # přesný formát "24.11.2025 17:24"
        errors="coerce"           # neparsovatelné hodnoty -> NaT (něco jako NaN pro datum)
    )
    #conversion to number
    cols = ["Cena","Počet","Objem v CZK","Poplatky v CZK","Objem v USD","Poplatky v USD","Objem v EUR","Poplatky v EUR"]

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

####  Přepočet na CZK pro Sumarizaci pozic ####
def column_sum(pdt):
    """přepočet do CZK"""
    pdt.loc[pdt["Měna"] == "USD", "Objem v CZK"] = pdt["Objem v USD"].abs() * kurz_USD
    pdt.loc[pdt["Měna"] == "USD", "Poplatky v CZK"] = pdt["Poplatky v USD"].abs() * kurz_USD
    pdt.loc[pdt["Měna"] == "EUR", "Objem v CZK"] = pdt["Objem v EUR"].abs() * kurz_EUR
    pdt.loc[pdt["Měna"] == "EUR", "Poplatky v CZK"] = pdt["Poplatky v EUR"].abs() * kurz_EUR
    return pdt
###########################

####    parsing CSV do PD tab  ####
def parse_column_ib(col):
    """ CSV IBKR parse """
    error = 0
    data=oo.dropna(subset=["Symbol"],axis=0,how="any")    # only valid line
    data=data.dropna(axis=1,how="all")                  # drop empty column
    data=data.drop(["Transaction History","Header","Transaction Fees"],axis=1) # drop unused column
    #print(f"[DEBUG] col = {repr(col)} type={type(col)}")
    #data = data[~data["Description"].str.contains("ADR", na=False)]
    data=data.loc[data["Transaction Type"]==col]

    data["Date"] = pd.to_datetime(
        data["Date"],
        #format="%d.%m.%Y %H:%M",  # přesný formát "24.11.2025 17:24"
        errors="coerce"           # neparsovatelné hodnoty -> NaT (něco jako NaN pro datum)
    )
    #conversion to number
    cols = ["Quantity","Price","Gross Amount ","Commission","Net Amount","Exchange Rate"]

    for cmn in cols:
        data[cmn] = data[cmn].replace("-", np.nan)  # remove - before convert to float
        data[cmn] = (
            data[cmn]
            .astype(str)
            #.str.replace("-", "", regex=False)
            .str.replace("\u00A0", "", regex=False)  # NBSP
            .str.replace("\u202F", "", regex=False)  # thin NBSP
            .str.replace(" ", "", regex=False)       # běžná mezera
            .astype(float)
        )
        data[cmn] = data[cmn].fillna(0)                 # NaN to 0

        if (data[cmn].isna().sum())>0:
            print(data[cmn].isna().sum(), "non parsed values") # 0 = OK
            error=error+1
        # Převod na EUR
        #vytvoř sloupec s hodnocením kladné / záporné složky pro grouping
    data["Currency"] = data["Exchange Rate"].astype(float).gt(1).map({True: "EUR", False: "USD"})    

    data["Gross Amount "] = data["Gross Amount "] / data["Exchange Rate"]
    data["Commission"] = data["Commission"] / data["Exchange Rate"]
    data["Net Amount"] = data["Net Amount"] / data["Exchange Rate"]

    print("PARSE ERRORS = ",error)
    return data
#################################################################

if not os.path.exists("Obchody.csv"):
    print("Soubor Obchody.csv nebyl nalezen! Zpracování bude přeskočeno.")
else:
    with open("Obchody.csv", "r", encoding='ANSI') as fin, open("fio.csv", "w", encoding='ANSI') as fout:
        for line in fin:
            if not found and line.lstrip().startswith("Datum obchodu"):
                found = True

            if found:
            # Nahradit středníky čárkami
            #line = line.replace(";", ",")          #not needed
                fout.write(line)

oo = pd.read_csv('fio.csv',sep=';',encoding='ANSI') # with semicolon

sell=parse_column("Prodej")
#sell.info()
buy=parse_column("Nákup")
#buy.info()
divi=parse_column("")
#debug=divi
#divi.info()


cols_to_sum = ["Počet","Objem v CZK", "Poplatky v CZK","Objem v USD","Poplatky v USD","Objem v EUR","Poplatky v EUR"]
# groupby nad 2. sloupcem a součet sloupce v def poli
out = sell.groupby(["Symbol","Měna"], as_index=False)[cols_to_sum].sum()
sell=column_sum(out)

out = buy.groupby(["Symbol","Měna"], as_index=False)[cols_to_sum].sum()
buy=column_sum(out)

cols_for_divi = ["Objem v CZK", "Objem v USD","Objem v EUR"]
divi=column_sum(divi)
#vytvoř sloupec s hodnocením kladné / záporné složky pro grouping
divi["Typ"] = divi[cols_for_divi].lt(0).any(axis=1).map({True: "-daň-", False: "D"})
divi = divi.groupby(["Symbol","Měna","Typ"], as_index=False)[cols_for_divi].sum()

divi_sum = divi.groupby(["Měna","Typ"], as_index=False)[cols_for_divi].sum()
divi_sum = divi_sum[~divi_sum["Měna"].str.contains("CZK", na=False)]

#print(divi_sum)

with pd.ExcelWriter("fio.xlsx", engine="xlsxwriter") as writer:
    # První tabulka
    sell.to_excel(writer, sheet_name="Report", index=False, startrow=2)

    fmt_default   = writer.book.add_format({"num_format": '#,##0.00'})
    # Nadpis mezi tabulkami
    worksheet = writer.sheets["Report"]
    worksheet.write(0, 0, "Výpis prodej - poplatky prodeje započteny již v sloupcích Objem v XXX")

    # Najdi indexy sloupců a nastav formáty na celý sloupec
    colsx = {name: idx for idx, name in enumerate(sell.columns)}
    for name in cols_to_sum:
        if name in colsx:
            colx = colsx[name]
            worksheet.set_column(colx, colx, 12, fmt_default)

    # Druhá tabulka pod první (např.  df1 má 100 řádků)
    start2 = len(sell) + 6
    worksheet.write(start2, 0, "Výpis nákup - informativní - aktuální rok")
    buy.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)

    start2 = start2 + len(buy) + 4
    worksheet.write(start2, 0, "DIVIDENDY ")
    divi.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)

    start2 = start2 + len(divi)+3
    worksheet.write(start2, 0, "SUMA to CZK (bez CZ dividendy) ")
    divi_sum.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)
######################  IBKR #################################

found=0         # pylint: disable=invalid-name
if not os.path.exists("IB.csv"):
    print("Soubor IB.csv nebyl nalezen! Zpracování bude přeskočeno.")
else:
    with open("IB.csv", "r",encoding="utf-8-sig", newline="") as fin, open("IB_tmp.csv", "w",encoding="utf-8-sig", newline="") as fout:
        for line in fin:
            if not found and line.lstrip().startswith("Transaction History"):
                found = True

            if found:
            #line = line.replace(";", ",")          #not needed
                fout.write(line)

oo = pd.read_csv('IB_tmp.csv',sep=',',encoding='utf-8-sig') # with semicolon,
sell=parse_column_ib("Sell")
buy =parse_column_ib("Buy")
assign = parse_column_ib("Assignment")
pro buy je špatně EUR???
debug=buy
# Filtry (bez nul)
sell_new = assign.loc[assign["Quantity"] < 0].copy()
buy_new  = assign.loc[assign["Quantity"] > 0].copy()

# Přidání (append) do existujících tabulek
sell = pd.concat([sell, sell_new], ignore_index=True)
buy  = pd.concat([buy,  buy_new],  ignore_index=True)


divi=parse_column_ib("Dividend")
divi_t=parse_column_ib("Foreign Tax Withholding")

debug=buy


cols_sum = ["Quantity","Price","Gross Amount ","Commission","Net Amount"]
# groupby nad 2. sloupcem a součet sloupce v def poli
options= sell[sell["Symbol"].str.len() >= 6]#.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()
sell = sell[sell["Symbol"].str.len() < 6].groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()
buy =  buy.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()
divi = divi.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()
divi_t = divi_t.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()


with pd.ExcelWriter("IBKR.xlsx", engine="xlsxwriter") as writer:
    
    # První tabulka
 
    sell.to_excel(writer, sheet_name="Report", index=False, startrow=2)
    
    worksheet = writer.sheets["Report"]
    worksheet.write(0, 0, "Výpis prodej         -    (USD)EXCHANGE RATE není celé číslo >> EUR")
    start2 = len(sell)+4
    worksheet.write(start2, 0, "Výpis Assignment - informativní zahrnuto v nákup/prodej")
    assign.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)
    
    # Druhá tabulka pod první (např.  df1 má 100 řádků)
    start2 = start2+len(assign) + 4
    worksheet.write(start2, 0, "Výpis nákup - informativní - aktuální rok")
    buy.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)

    start2 = start2 + len(buy) + 4
    worksheet.write(start2, 0, "OPCE ")
    options.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)

    start2 = start2 + len(options) + 4
    worksheet.write(start2, 0, "DIVIDENDY ")
    divi.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)

    start2 = start2 + len(divi)+3
    worksheet.write(start2, 0, " TAX ")
    divi_t.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)

    fmt_default   = writer.book.add_format({"num_format": '#,##0.00'})
  
    

    # Najdi indexy sloupců a nastav formáty na celý sloupec
    colsx = {name: idx for idx, name in enumerate(sell.columns)}
    for name in cols_to_sum:
        if name in colsx:
            colx = colsx[name]
            worksheet.set_column(colx, colx, 12, fmt_default)

print("_____________NumPy_____________")
######################### DEBUG ###############################
pole = debug.to_numpy()
#pole2=buy.to_numpy()
with open('output.txt', 'w', encoding="utf-8") as outfile:
    outfile.write(str(pole))

#uniq, inv = np.unique(pole[:,2], return_inverse=True)
# 3) Sečteme 3. sloupec podle skupin v 2. sloupci
#sums = np.zeros(len(uniq), dtype=float)
#np.add.at(sums, inv, pole[:, 3])

#print(uniq,inv,sums)

print("_______________________________")
# Výsledek: dvojice (unikátní_hodnota, součet)
#for u, s in zip(uniq, sums):
   # print(u, s)