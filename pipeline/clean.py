"""
pipeline/clean.py  (P2 + P3)

P2: strip kolonat, drop duplikatet, ndarja e C-invoices (kthimet) -> split_returns()
P3: filtri StockCode, Price>0 & Qty>0, kolona Revenue         -> clean_sales()

load_and_clean() i bashkon të dyja dhe është pika që e thërret app.py.
"""

import re
import io
import pandas as pd
import streamlit as st

from pipeline.validate import validate_workbook

STOCKCODE_PATTERN = re.compile(r"^\d{5}")


# ---------------------------------------------------------------------------
# P2 — pjesa 1: strip + duplikate + ndarja e kthimeve
# ---------------------------------------------------------------------------

def split_returns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ndan rreshtat në (sales_raw, returns).

    Një rresht është "kthim" (return) nëse Invoice fillon me 'C' (cancellation).
    Këta rreshta NUK fshihen — ruhen veç e veç për Sllajdin 3.
    """
    df = df.copy()

    # Strip kolonat e tipit tekst (hapësira në fillim/fund shkaktojnë bugs të fshehta)
    for kolona in df.select_dtypes(include="object").columns:
        df[kolona] = df[kolona].astype(str).str.strip()

    # Drop duplikatet (rreshta identikë 100%)
    para = len(df)
    df = df.drop_duplicates()
    nr_duplikate = para - len(df)

    invoice_str = df["Invoice"].astype(str)
    eshte_kthim = invoice_str.str.startswith("C")

    returns = df[eshte_kthim].copy()
    sales_raw = df[~eshte_kthim].copy()

    return sales_raw, returns, nr_duplikate


# ---------------------------------------------------------------------------
# P3 — pjesa 2: StockCode, Price/Qty, Revenue
# ---------------------------------------------------------------------------

def clean_sales(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    """
    Pastron rreshtat e shitjeve (jo-kthime) dhe llogarit Revenue.

    Kthen:
        (df_sales, cleaning_log)
        cleaning_log: listë tuplesh (përshkrimi_i_hapit, sa_rreshta_u_hoqën)
    """
    log: list[tuple[str, int]] = []
    df = df.copy()

    # 1) Vetëm StockCode që fillon me 5 shifra (produkte reale, jo POSTAGE/DOT/etj.)
    para = len(df)
    df = df[df["StockCode"].astype(str).str.match(STOCKCODE_PATTERN)]
    log.append(("StockCode jo-standard (jo 5 shifra në fillim)", para - len(df)))

    # 2) Price > 0
    para = len(df)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df[df["Price"] > 0]
    log.append(("Price <= 0 ose jo-numerik", para - len(df)))

    # 3) Quantity > 0
    para = len(df)
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df = df[df["Quantity"] > 0]
    log.append(("Quantity <= 0 ose jo-numerik", para - len(df)))

    # 4) InvoiceDate -> datetime
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    para = len(df)
    df = df.dropna(subset=["InvoiceDate"])
    log.append(("InvoiceDate e pavlefshme", para - len(df)))

    # 5) Revenue
    df["Revenue"] = df["Quantity"] * df["Price"]

    return df, log


# ---------------------------------------------------------------------------
# Funksioni kryesor që e thërret app.py — me cache që file 45MB të mos rilexohet
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Duke lexuar dhe pastruar file-in...")
def load_and_clean(file_bytes: bytes):
    """
    Merr bytes e xlsx-it, kthen:
        df_sales, df_returns, cleaning_log, validation_errors

    Nëse validation_errors s'është bosh, df_sales/df_returns kthehen bosh
    dhe app.py duhet me e ndalu (me shfaq mesazhin e gabimit, jo crash).
    """
    # engine="calamine" -> shumë më i shpejtë se openpyxl për file të mëdhenj
    try:
        sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, engine="calamine")
    except Exception:
        # fallback nëse calamine s'është i instaluar / dështon
        sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, engine="openpyxl")

    errors = validate_workbook(sheets)
    if errors:
        return pd.DataFrame(), pd.DataFrame(), [], errors

    # Bashko të gjitha sheets në një DataFrame të vetëm
    df_raw = pd.concat(sheets.values(), ignore_index=True)

    sales_raw, returns_raw, nr_duplikate = split_returns(df_raw)
    df_sales, cleaning_log = clean_sales(sales_raw)

    cleaning_log = [("Rreshta duplikatë (të hequr)", nr_duplikate)] + cleaning_log

    return df_sales, returns_raw, cleaning_log, []
