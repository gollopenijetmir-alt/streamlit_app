"""
pipeline/validate.py  (P1)

Kontrollon nëse file-i i ngarkuar (xlsx) ka kolonat dhe tipet e pritura.
S'bën asnjë pastrim këtu — vetëm thotë PO/JO dhe pse.
"""

import pandas as pd

# Skema e pritur (emri i kolonës)
KOLONAT_E_PRITURA = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]

# Kolonat që duhen me qenë numerike
KOLONAT_NUMERIKE = ["Quantity", "Price"]


def validate_workbook(sheets: dict[str, pd.DataFrame]) -> list[str]:
    """
    Kontrollon çdo sheet të workbook-ut.

    Parametra:
        sheets: dict {emri_i_sheet: DataFrame} — siç kthen pd.read_excel(..., sheet_name=None)

    Kthen:
        list[str] — listë gabimesh në shqip. Listë BOSHE = file valid.
    """
    gabimet: list[str] = []

    if not sheets:
        gabimet.append("File-i nuk ka asnjë sheet (fletë) të lexueshme.")
        return gabimet

    for emri_sheet, df in sheets.items():
        gabimet.extend(_validate_sheet(emri_sheet, df))

    return gabimet


def _validate_sheet(emri_sheet: str, df: pd.DataFrame) -> list[str]:
    gabimet: list[str] = []

    # 1) A ekzistojnë të gjitha kolonat e pritura?
    kolonat_ekzistuese = set(df.columns)
    kolonat_mungese = [k for k in KOLONAT_E_PRITURA if k not in kolonat_ekzistuese]

    if kolonat_mungese:
        gabimet.append(
            f"Sheet '{emri_sheet}': mungojnë kolonat {kolonat_mungese}. "
            f"Ky file nuk përputhet me kolonat / skemën e pritur."
        )
        # Nëse mungojnë kolona, s'ka kuptim me kontrollu tipet e tyre
        return gabimet

    # 2) A janë Quantity dhe Price numerike?
    for kolona in KOLONAT_NUMERIKE:
        if not pd.api.types.is_numeric_dtype(df[kolona]):
            # Provo me e konvertu — nëse dështon shumica e vlerave, është gabim
            konvertuar = pd.to_numeric(df[kolona], errors="coerce")
            perqindja_gabim = konvertuar.isna().mean()
            if perqindja_gabim > 0.05:  # >5% vlera jo-numerike = problem real
                gabimet.append(
                    f"Sheet '{emri_sheet}': kolona '{kolona}' duhet me qenë numerike, "
                    f"por {perqindja_gabim:.0%} e vlerave s'janë numra."
                )

    # 3) A është InvoiceDate datë?
    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        konvertuar = pd.to_datetime(df["InvoiceDate"], errors="coerce")
        perqindja_gabim = konvertuar.isna().mean()
        if perqindja_gabim > 0.05:
            gabimet.append(
                f"Sheet '{emri_sheet}': kolona 'InvoiceDate' duhet me qenë datë, "
                f"por {perqindja_gabim:.0%} e vlerave s'janë datë e vlefshme."
            )

    # 4) Sheet bosh?
    if len(df) == 0:
        gabimet.append(f"Sheet '{emri_sheet}': s'ka asnjë rresht të dhënash.")

    return gabimet
