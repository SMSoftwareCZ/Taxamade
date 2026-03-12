
""" TAXAMADE"""
import os
import numpy as np
import pandas as pd


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
    cols = ["Quantity","Price","Gross Amount","Commission","Net Amount","Exchange Rate"]

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
    data["Gross Amount"] = data["Gross Amount"] / data["Exchange Rate"]
    data["Commission"] = data["Commission"] / data["Exchange Rate"]
    data["Net Amount"] = data["Net Amount"] / data["Exchange Rate"]

    print("PARSE ERRORS = ",error)
    return data
################ FORMAT XLS ######################
def format_sheet_columns(ws, df, cols_fmt, fmt):
    # mapa jména -> excel sloupec
    index_map = {name: idx for idx, name in enumerate(df.columns)}

    for col in cols_fmt:
        if col in index_map:
            c = index_map[col]
            ws.set_column(c, c, 12, fmt)

if not os.path.exists("Obchody.csv"):
    raise FileNotFoundError("Soubor Obchody.csv nebyl nalezen!")
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


cols_to_sum = ["Počet","Objem v CZK", "Poplatky v CZK","Objem v USD","Poplatky v USD","Objem v EUR","Poplatky v EUR"]
# groupby nad 2. sloupcem a součet sloupce v def poli
#out = sell.groupby(["Symbol","Měna"], as_index=False)[cols_to_sum].sum()
sell=column_sum(sell)

#out = buy.groupby(["Symbol","Měna"], as_index=False)[cols_to_sum].sum()
buy=column_sum(buy)
sell = sell.sort_values(by="Datum obchodu")
buy = buy.sort_values(by="Datum obchodu")

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
    format_sheet_columns(worksheet, sell, cols_to_sum, fmt_default)

    # Druhá tabulka pod první (např.  df1 má 100 řádků)
    start2 = len(sell) + 6
    worksheet.write(start2, 0, "Výpis nákup - informativní - aktuální rok")
    buy.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)
    format_sheet_columns(worksheet, buy, cols_to_sum, fmt_default)

    start2 = start2 + len(buy) + 4
    worksheet.write(start2, 0, "DIVIDENDY ")
    divi.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)
    format_sheet_columns(worksheet, divi, cols_to_sum, fmt_default)

    start2 = start2 + len(divi)+3
    worksheet.write(start2, 0, "SUMA to CZK (bez CZ dividendy) ")
    divi_sum.to_excel(writer, sheet_name="Report", index=False, startrow=start2+1)
    format_sheet_columns(worksheet, divi_sum, cols_to_sum, fmt_default)

######################  IBKR USD #################################

found=0         # pylint: disable=invalid-name
if not os.path.exists("IB.csv"):
    raise FileNotFoundError("Soubor IB.csv nebyl nalezen!")
else:
    with open("IB.csv", "r",encoding="utf-8-sig", newline="") as fin, open("IB_tmp.csv", "w",encoding="utf-8-sig", newline="") as fout:
        for line in fin:
            if not found and line.lstrip().startswith("Transaction History"):
                found = True

            if found:
            #line = line.replace(";", ",")          #not needed
                fout.write(line)

oo = pd.read_csv('IB_tmp.csv',sep=',',encoding='utf-8-sig') # with semicolon,
oo.columns = oo.columns.str.strip() # uprava nazvu sloupců
sell=parse_column_ib("Sell")
buy =parse_column_ib("Buy")
assign = parse_column_ib("Assignment")
# Filtry (bez nul) - z assigment riztřídím dle znaménka BUY/SELL 
sell_new = assign.loc[assign["Quantity"] < 0].copy()
buy_new  = assign.loc[assign["Quantity"] > 0].copy()
# Přidání (append) do existujících tabulek
sell = pd.concat([sell, sell_new], ignore_index=True)
buy  = pd.concat([buy,  buy_new],  ignore_index=True)
divi=parse_column_ib("Dividend")
divi_t=parse_column_ib("Foreign Tax Withholding")

#debug=buy


cols_sum = ["Quantity","Price","Gross Amount","Commission","Net Amount"]
# groupby nad 2. sloupcem a součet sloupce v def poli
options_s = sell[sell["Symbol"].str.len() >= 6]
options_b = buy[buy["Symbol"].str.len() >= 6]
options_s = options_s.sort_values(by=["Currency","Date"])
options_b = options_b.sort_values(by=["Currency","Date"])
#options = options.groupby(["Date","Currency","Symbol"], as_index=False)[cols_sum].sum()
sell = sell[sell["Symbol"].str.len() < 6]##.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()
sell = sell.sort_values(by="Date")
buy = buy.sort_values(by="Date")
##buy.groupby(["Currency","Symbol","Price"], as_index=False)[cols_sum].sum()
divi = divi.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()
# zaplacená daň
divi_t = divi_t.groupby(["Currency","Symbol"], as_index=False)[cols_sum].sum()


with pd.ExcelWriter("IBKR.xlsx", engine="xlsxwriter") as writer_2:

    # Formát (pokud chceš aplikovat)
    fmt_default2 = writer_2.book.add_format({"num_format": '#,##0.00'})
    # --- LIST: PRODEJ ---
    sell.to_excel(writer_2, sheet_name="Prodej", index=False, startrow=2,float_format="%.2f")
    ws_prodej = writer_2.sheets["Prodej"]
    # Nadpis 1
    ws_prodej.write(0, 0, "Výpis prodej - (USD)EXCHANGE RATE není celé číslo >> EUR")

    # Druhá tabulka – Assignment
    start = len(sell) + 4
    ws_prodej.write(start, 0, "Výpis Assignment - informativní zahrnuto v nákup/prodej")
    assign.to_excel(writer_2, sheet_name="Prodej", index=False, startrow=start + 1,float_format="%.2f")

    # Třetí tabulka – Buy
    start = start + len(assign) + 4
    ws_prodej.write(start, 0, "Výpis nákup - informativní - aktuální rok")
    buy.to_excel(writer_2, sheet_name="Prodej", index=False, startrow=start + 1,float_format="%.2f")

    format_sheet_columns(ws_prodej, sell, cols_sum, fmt_default2)
    format_sheet_columns(ws_prodej, assign, cols_sum, fmt_default2)
    format_sheet_columns(ws_prodej, buy, cols_sum, fmt_default2)

    # --- LIST: OPCE ---
  
    start = 0
    options_b.to_excel(writer_2, sheet_name="Opce", index=False, startrow=start + 1,float_format="%.2f")
    ws_opce = writer_2.sheets["Opce"]
    ws_opce.write(start, 0, "OPCE - BUY")

    start = start + len(options_b) + 3
    ws_opce.write(start, 0, "OPCE - SELL")
    options_s.to_excel(writer_2, sheet_name="Opce", index=False, startrow=start + 1,float_format="%.2f")

    format_sheet_columns(ws_opce, options_b, cols_sum, fmt_default2)
    format_sheet_columns(ws_opce, options_s, cols_sum, fmt_default2)
    # --- LIST: DIVIDENDY ---
  
    start = 0
    divi.to_excel(writer_2, sheet_name="Divi", index=False, startrow=start + 1,float_format="%.2f")
    ws_divi = writer_2.sheets["Divi"]
    ws_divi.write(start, 0, "DIVIDENDY")

    start = start + len(divi) + 3
    ws_divi.write(start, 0, "TAX")
    divi_t.to_excel(writer_2, sheet_name="Divi", index=False, startrow=start + 1,float_format="%.2f")

    format_sheet_columns(ws_divi, divi, cols_sum, fmt_default2)
    format_sheet_columns(ws_divi, divi_t, cols_sum, fmt_default2)



print("_____________NumPy_____________")
######################### DEBUG ###############################
if 'debug' in locals() or 'debug' in globals():
    pole = debug.to_numpy()
    with open('output.txt', 'w', encoding="utf-8") as outfile:
        outfile.write(str(pole))
