"""
pipeline/aggregate.py  (P4 + P5)

P4: monthly_revenue(), top_products(), markets_summary()
P5: returns_summary(), top_customers(), concentration()

Të gjitha funksionet marrin DataFrame (jo file) dhe kthejnë DataFrame/numra
gati për t'u vizualizuar te slides.py — s'kanë asnjë logjikë Streamlit.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# P4 — Sllajdi 2: motorët e revenue
# ---------------------------------------------------------------------------

def monthly_revenue(df_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Revenue total për muaj + MoM% + YoY%.
    Kthen DataFrame me kolonat: muaji, revenue, mom_pct, yoy_pct
    """
    df = df_sales.copy()
    df["muaji"] = df["InvoiceDate"].dt.to_period("M")

    mujor = df.groupby("muaji", as_index=False)["Revenue"].sum()
    mujor = mujor.sort_values("muaji").reset_index(drop=True)

    mujor["mom_pct"] = mujor["Revenue"].pct_change() * 100
    mujor["yoy_pct"] = mujor["Revenue"].pct_change(periods=12) * 100

    return mujor


def top_products(df_sales: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N produktet sipas Revenue total (jo sipas numrit të rreshtave!)."""
    return (
        df_sales.groupby(["StockCode", "Description"], as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(n)
    )


def markets_summary(df_sales: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Top N tregjet (shtetet) sipas revenue, + revenue mesatare për porosi
    (kjo zbulon klientë wholesale me pak porosi por shumë vlerë).
    """
    grup = df_sales.groupby("Country")
    rev_total = grup["Revenue"].sum()
    nr_porosi = grup["Invoice"].nunique()
    rev_mesatare_porosi = rev_total / nr_porosi

    rezultati = pd.DataFrame({
        "Country": rev_total.index,
        "revenue_total": rev_total.values,
        "nr_porosi": nr_porosi.values,
        "revenue_mesatare_porosi": rev_mesatare_porosi.values,
    })

    return rezultati.sort_values("revenue_total", ascending=False).head(n)


def movers(df_sales: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """BONUS: produktet me rritjen/rënien më të madhe vs muajin paraprak."""
    df = df_sales.copy()
    df["muaji"] = df["InvoiceDate"].dt.to_period("M")

    muajt = sorted(df["muaji"].unique())
    if len(muajt) < 2:
        return pd.DataFrame()

    muaji_i_fundit, muaji_paraprak = muajt[-1], muajt[-2]

    def revenue_per_muaj(muaj):
        return df[df["muaji"] == muaj].groupby("Description")["Revenue"].sum()

    aktual = revenue_per_muaj(muaji_i_fundit)
    paraprak = revenue_per_muaj(muaji_paraprak)

    krahasim = pd.DataFrame({"aktual": aktual, "paraprak": paraprak}).fillna(0)
    krahasim["ndryshimi"] = krahasim["aktual"] - krahasim["paraprak"]
    krahasim = krahasim.sort_values("ndryshimi", ascending=False)

    return pd.concat([krahasim.head(n), krahasim.tail(n)])


# ---------------------------------------------------------------------------
# P5 — Sllajdi 3: kthimet & klientët
# ---------------------------------------------------------------------------

def returns_summary(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> dict:
    """
    Kthen dict me:
        mujor: DataFrame (muaji, sasia_kthyer, vlera_kthyer)
        shkalla_kthimit_pct: float (vlera e kthyer / revenue total)
        top_produktet: DataFrame top 5 produktet më të kthyera (sipas sasisë)
    """
    returns = df_returns.copy()
    returns["InvoiceDate"] = pd.to_datetime(returns["InvoiceDate"], errors="coerce")
    returns["Quantity"] = pd.to_numeric(returns["Quantity"], errors="coerce")
    returns["Price"] = pd.to_numeric(returns["Price"], errors="coerce")

    # Në kthimet, Quantity zakonisht është negative -> e bëjmë pozitive për lexueshmëri
    returns["sasia_kthyer"] = returns["Quantity"].abs()
    returns["vlera_kthyer"] = returns["sasia_kthyer"] * returns["Price"]

    returns["muaji"] = returns["InvoiceDate"].dt.to_period("M")
    mujor = returns.groupby("muaji", as_index=False)[["sasia_kthyer", "vlera_kthyer"]].sum()

    vlera_totale_kthyer = returns["vlera_kthyer"].sum()
    revenue_total = df_sales["Revenue"].sum()
    shkalla_kthimit_pct = (
        (vlera_totale_kthyer / revenue_total * 100) if revenue_total > 0 else 0
    )

    top_produktet = (
        returns.groupby("Description", as_index=False)["sasia_kthyer"]
        .sum()
        .sort_values("sasia_kthyer", ascending=False)
        .head(5)
    )

    return {
        "mujor": mujor,
        "shkalla_kthimit_pct": shkalla_kthimit_pct,
        "top_produktet": top_produktet,
    }


def top_customers(df_sales: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N klientët sipas revenue total."""
    return (
        df_sales.dropna(subset=["Customer ID"])
        .groupby("Customer ID", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(n)
    )


def concentration(df_sales: pd.DataFrame, top_pct: float = 0.05) -> float:
    """
    Sa % e revenue vjen nga top X% e porosive (default top 5%).
    Kthen një %  (p.sh. 62.3 do të thotë top 5% e porosive = 62.3% e revenue).
    """
    porosi_revenue = df_sales.groupby("Invoice")["Revenue"].sum().sort_values(ascending=False)

    if len(porosi_revenue) == 0:
        return 0.0

    nr_top = max(1, int(len(porosi_revenue) * top_pct))
    revenue_top = porosi_revenue.head(nr_top).sum()
    revenue_gjithsej = porosi_revenue.sum()

    return (revenue_top / revenue_gjithsej * 100) if revenue_gjithsej > 0 else 0.0


def klientet_per_thirrje(df_sales: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    BONUS: VIP-at (top klientë) me rënie aktiviteti vs muajin paraprak.
    """
    df = df_sales.copy()
    df["muaji"] = df["InvoiceDate"].dt.to_period("M")
    muajt = sorted(df["muaji"].unique())
    if len(muajt) < 2:
        return pd.DataFrame()

    muaji_i_fundit, muaji_paraprak = muajt[-1], muajt[-2]
    vip = top_customers(df_sales, n=n)["Customer ID"]

    def revenue_klienti_per_muaj(muaj):
        return (
            df[(df["muaji"] == muaj) & (df["Customer ID"].isin(vip))]
            .groupby("Customer ID")["Revenue"]
            .sum()
        )

    aktual = revenue_klienti_per_muaj(muaji_i_fundit)
    paraprak = revenue_klienti_per_muaj(muaji_paraprak)

    krahasim = pd.DataFrame({"aktual": aktual, "paraprak": paraprak}).fillna(0)
    krahasim["ndryshimi_pct"] = (
        (krahasim["aktual"] - krahasim["paraprak"]) / krahasim["paraprak"].replace(0, 1) * 100
    )

    return krahasim[krahasim["ndryshimi_pct"] < 0].sort_values("ndryshimi_pct")
