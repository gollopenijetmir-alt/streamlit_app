"""
app.py — UI kryesore. Vetëm orkestron; logjika jeton në pipeline/ dhe slides.py.
"""

import streamlit as st
import pandas as pd

from pipeline.clean import load_and_clean
from pipeline.validate import KOLONAT_E_PRITURA
from slides import slide_puls, slide_motoret, slide_rrjedhjet

st.set_page_config(page_title="Raporti Automatik i Shitjeve", layout="wide")

st.title("📈 Raporti Automatik i Shitjeve")
st.caption("Ngarko file-in xlsx të shitjeve dhe merr automatikisht 3 sllajde vendimmarrëse.")

# ---------------------------------------------------------------------------
# 1) Uploader
# ---------------------------------------------------------------------------

with st.expander("ℹ️ Skema e pritur e file-it (kliko për me pa)"):
    st.write("Çdo sheet i xlsx-it duhet t'i ketë këto kolona:")
    st.code(" · ".join(KOLONAT_E_PRITURA))

file_i_ngarkuar = st.file_uploader("Ngarko file-in e shitjeve (.xlsx)", type=["xlsx"])

if file_i_ngarkuar is None:
    st.info("⬆️ Ngarko një file xlsx për me fillu.")
    st.stop()

# ---------------------------------------------------------------------------
# 2) Validim + pastrim (me cache)
# ---------------------------------------------------------------------------

file_bytes = file_i_ngarkuar.getvalue()
df_sales, df_returns, cleaning_log, validation_errors = load_and_clean(file_bytes)

if validation_errors:
    st.error("❌ Ky file nuk përputhet me kolonat / skemën e pritur:")
    for gabim in validation_errors:
        st.write(f"- {gabim}")
    st.stop()

st.success(
    f"✅ File-i u lexua me sukses: **{len(df_sales):,} rreshta shitje** "
    f"+ **{len(df_returns):,} rreshta kthime**."
)

with st.expander("🧹 Log-u i pastrimit (çka u hoq dhe pse)"):
    for përshkrim, nr in cleaning_log:
        st.write(f"- {përshkrim}: **{nr:,}** rreshta")

# ---------------------------------------------------------------------------
# 3) Dropdown-at (periudha / shteti) — filtrojnë të gjitha sllajdet
# ---------------------------------------------------------------------------

st.divider()
st.subheader("🔧 Filtro raportin")

kol1, kol2 = st.columns(2)

with kol1:
    muajt_disponueshem = sorted(df_sales["InvoiceDate"].dt.to_period("M").astype(str).unique())
    periudha = st.selectbox(
        "Periudha (deri në muajin e zgjedhur)",
        options=["Të gjitha"] + muajt_disponueshem,
        index=0,
    )

with kol2:
    shtetet_disponueshme = sorted(df_sales["Country"].dropna().unique())
    shteti = st.selectbox(
        "Shteti",
        options=["Të gjitha"] + shtetet_disponueshme,
        index=0,
    )

# Apliko filtrat
df_sales_filtruar = df_sales.copy()
df_returns_filtruar = df_returns.copy()

if periudha != "Të gjitha":
    df_sales_filtruar = df_sales_filtruar[
        df_sales_filtruar["InvoiceDate"].dt.to_period("M").astype(str) <= periudha
    ]
    df_returns_filtruar["InvoiceDate"] = pd.to_datetime(
        df_returns_filtruar["InvoiceDate"], errors="coerce"
    )
    df_returns_filtruar = df_returns_filtruar[
        df_returns_filtruar["InvoiceDate"].dt.to_period("M").astype(str) <= periudha
    ]

if shteti != "Të gjitha":
    df_sales_filtruar = df_sales_filtruar[df_sales_filtruar["Country"] == shteti]
    df_returns_filtruar = df_returns_filtruar[df_returns_filtruar["Country"] == shteti]

# ---------------------------------------------------------------------------
# 4) Tre sllajdet
# ---------------------------------------------------------------------------

st.divider()
slide_puls(df_sales_filtruar)

st.divider()
slide_motoret(df_sales_filtruar)

st.divider()
slide_rrjedhjet(df_sales_filtruar, df_returns_filtruar)
