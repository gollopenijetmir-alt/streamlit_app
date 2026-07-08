"""
slides.py  (P3, P4, P5 — secili sllajdin e vet)

Çdo funksion: titull -> KPI (st.metric) -> grafik (plotly) -> insight (tekst
i llogaritur nga vetë të dhënat, jo i shkruar dorazi).
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from pipeline.aggregate import (
    monthly_revenue, top_products, markets_summary, movers,
    returns_summary, top_customers, concentration,
)


# ---------------------------------------------------------------------------
# SLLAJDI 1 — Pulsi i biznesit  (P3)
# ---------------------------------------------------------------------------

def slide_puls(df_sales: pd.DataFrame):
    st.header("📊 Sllajdi 1 — Pulsi i biznesit: si shkuam dhe çfarë na pret?")

    mujor = monthly_revenue(df_sales)
    if mujor.empty:
        st.warning("S'ka të dhëna të mjaftueshme për këtë sllajd.")
        return

    i_fundit = mujor.iloc[-1]

    kol1, kol2, kol3 = st.columns(3)
    kol1.metric("Revenue (muaji i fundit)", f"£{i_fundit['Revenue']:,.0f}")
    kol2.metric(
        "MoM % (vs muaji para)",
        f"{i_fundit['mom_pct']:.1f}%" if pd.notna(i_fundit["mom_pct"]) else "N/A",
        delta=f"{i_fundit['mom_pct']:.1f}%" if pd.notna(i_fundit["mom_pct"]) else None,
    )
    kol3.metric(
        "YoY % (vs viti para)",
        f"{i_fundit['yoy_pct']:.1f}%" if pd.notna(i_fundit["yoy_pct"]) else "N/A",
        delta=f"{i_fundit['yoy_pct']:.1f}%" if pd.notna(i_fundit["yoy_pct"]) else None,
    )

    fig = px.line(
        mujor, x=mujor["muaji"].astype(str), y="Revenue",
        title="Revenue mujor", markers=True,
    )
    fig.update_layout(xaxis_title="Muaji", yaxis_title="Revenue (£)")
    st.plotly_chart(fig, use_container_width=True)

    # Insight automatik
    if pd.notna(i_fundit["mom_pct"]):
        drejtimi = "u rrit" if i_fundit["mom_pct"] > 0 else "ra"
        st.info(
            f"💡 Revenue {drejtimi} me **{abs(i_fundit['mom_pct']):.1f}%** krahasuar "
            f"me muajin paraprak. "
            + (
                f"Krahasuar me të njëjtin muaj vitin e kaluar, ndryshimi është "
                f"**{i_fundit['yoy_pct']:.1f}%**."
                if pd.notna(i_fundit["yoy_pct"]) else ""
            )
        )


# ---------------------------------------------------------------------------
# SLLAJDI 2 — Motorët e revenue  (P4)
# ---------------------------------------------------------------------------

def slide_motoret(df_sales: pd.DataFrame):
    st.header("🚀 Sllajdi 2 — Motorët e revenue: cilat produkte e tregje po e bëjnë muajin?")

    produktet = top_products(df_sales, n=10)
    tregjet = markets_summary(df_sales, n=10)

    kol1, kol2 = st.columns(2)
    with kol1:
        fig1 = px.bar(
            produktet, x="Revenue", y="Description", orientation="h",
            title="Top 10 produktet sipas Revenue",
        )
        fig1.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig1, use_container_width=True)

    with kol2:
        fig2 = px.bar(
            tregjet, x="revenue_mesatare_porosi", y="Country", orientation="h",
            title="Top tregjet — Revenue mesatare për porosi",
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)

    # Insight automatik
    if not produktet.empty:
        top1 = produktet.iloc[0]
        st.info(
            f"💡 Produkti me revenue më të lartë këtë periudhë është "
            f"**{top1['Description']}** (£{top1['Revenue']:,.0f})."
        )
    if not tregjet.empty:
        tregu_wholesale = tregjet.sort_values("revenue_mesatare_porosi", ascending=False).iloc[0]
        st.info(
            f"💡 **{tregu_wholesale['Country']}** ka revenue mesatare më të lartë "
            f"për porosi (£{tregu_wholesale['revenue_mesatare_porosi']:,.0f}) — "
            f"mundësi për trajtim si klient wholesale/VIP."
        )

    # BONUS: movers
    lëvizësit = movers(df_sales, n=5)
    if not lëvizësit.empty:
        with st.expander("📈 Movers — produktet me ndryshimin më të madh vs muajin paraprak"):
            st.dataframe(lëvizësit)


# ---------------------------------------------------------------------------
# SLLAJDI 3 — Rrjedhjet & klientët kyç  (P5)
# ---------------------------------------------------------------------------

def slide_rrjedhjet(df_sales: pd.DataFrame, df_returns: pd.DataFrame):
    st.header("🔍 Sllajdi 3 — Rrjedhjet & klientët kyç: kthimet dhe koncentrimi")

    kthimet = returns_summary(df_sales, df_returns)
    klientet = top_customers(df_sales, n=10)
    koncentrimi_pct = concentration(df_sales, top_pct=0.05)

    kol1, kol2 = st.columns(2)
    kol1.metric("Shkalla e kthimit", f"{kthimet['shkalla_kthimit_pct']:.1f}%")
    kol2.metric("Top 5% e porosive = % e revenue", f"{koncentrimi_pct:.1f}%")

    if not kthimet["mujor"].empty:
        fig = px.bar(
            kthimet["mujor"], x=kthimet["mujor"]["muaji"].astype(str), y="vlera_kthyer",
            title="Vlera e kthyer për muaj",
        )
        fig.update_layout(xaxis_title="Muaji", yaxis_title="Vlera e kthyer (£)")
        st.plotly_chart(fig, use_container_width=True)

    kol3, kol4 = st.columns(2)
    with kol3:
        st.subheader("Top 5 produktet më të kthyera")
        st.dataframe(kthimet["top_produktet"])
    with kol4:
        st.subheader("Top 10 klientët sipas revenue")
        st.dataframe(klientet)

    # Insight automatik
    if not kthimet["top_produktet"].empty:
        top_kthim = kthimet["top_produktet"].iloc[0]
        st.info(
            f"💡 Produkti më i kthyer është **{top_kthim['Description']}** "
            f"({top_kthim['sasia_kthyer']:,.0f} copë) — vlen me u hetu cilësia."
        )
    st.info(
        f"💡 Top 5% e porosive gjenerojnë **{koncentrimi_pct:.1f}%** të revenue total — "
        f"këta klientë meritojnë vëmendje prioritare."
    )
