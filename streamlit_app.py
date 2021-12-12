import os
import random
import requests
import numpy as np
import pandas as pd
import streamlit as st

# streamlit config
# st.set_page_config(layout="wide")

# requests headers
headers = {
    "authority": "api.coinhall.org",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
    "accept": "*/*",
    "sec-gpc": "1",
    "origin": "https://coinhall.org",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://coinhall.org/",
    "accept-language": "en-US,en;q=0.9",
}

# coinhall api
response = requests.get(
    "https://api.coinhall.org/api/v1/charts/terra/pairs", headers=headers
).json()

# convert to dataframe
df = (
    pd.DataFrame.from_dict(response, orient="index")
    .reset_index(drop=False)
    .rename(columns={"index": "address"})
    .drop(labels=["timestamp", "unofficial", "startAt", "endAt"], axis=1)
)

# astroport lockdrop pairs
astro_pairs = [
    ["bLUNA-LUNA", "terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p", 17250000],
    ["LUNA-UST", "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6", 21750000],
    ["ANC-UST", "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3", 14250000],
    ["MIR-UST", "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux", 6750000],
    ["ORION-UST", "terra1z6tp0ruxvynsx5r9mmcc2wcezz9ey9pmrw5r8g", 1500000],
    ["STT-UST", "terra19pg6d7rrndg4z4t0jhcd7z9nhl3p5ygqttxjll", 3750000],
    ["VKR-UST", "terra1e59utusv5rspqsu8t37h5w887d9rdykljedxw0", 2250000],
    ["MINE-UST", "terra178jydtjvj4gw8earkgnqc80c3hrmqj4kw2welz", 3000000],
    ["PSI-UST", "terra163pkeeuwxzr0yhndf8xd2jprm9hrtk59xf7nqf", 2250000],
    ["APOLLO-UST", "terra1xj2w7w8mx6m2nueczgsxy2gnmujwejjeu2xf78", 2250000],
]

# convert to dataframe
astro_pairs = pd.DataFrame(astro_pairs, columns=["pair", "address", "astro_tokens"])

# filter for astroport pairs
df = df[df["address"].isin(astro_pairs["address"])]

# parse json data
df = pd.concat(
    [
        df,
        df["asset0"].apply(pd.Series).add_prefix("asset0_"),
        df["asset1"].apply(pd.Series).add_prefix("asset1_"),
    ],
    axis=1,
)

# merge data
df = df.merge(astro_pairs, on="address")

# liquidity in usd
df["liq"] = df["asset1_poolAmount"] // 1_000_000 * 2

# columns of interest
df_liq = df[
    [
        "pair",
        # "address",
        "astro_tokens",
        "liq",
    ]
]

# luna price
luna_ust = df[df["pair"] == "LUNA-UST"]
luna_price = (luna_ust["asset0_poolAmount"] / luna_ust["asset1_poolAmount"])[0]

# fix mirror liquidity
mir_ust = df[df["pair"] == "MIR-UST"]
df_liq.loc[mir_ust.index, "liq"] = (
    df.loc[mir_ust.index, "asset0_poolAmount"] // 1_000_000 * 2
)

# fix luna liquidity
luna_ust = df[df["pair"] == "LUNA-UST"]
df_liq.loc[luna_ust.index, "liq"] = (
    df.loc[luna_ust.index, "asset0_poolAmount"] // 1_000_000 * 2
)

# fix bluna liquidity
bluna_luna = df[df["pair"] == "bLUNA-LUNA"]
df_liq.loc[bluna_luna.index, "liq"] = int(
    df.loc[bluna_luna.index, "asset1_poolAmount"] // 1_000_000 * 2 * luna_price
)

# sidebar
st.sidebar.markdown(
    f"""
    # Assumptions
    """
)

# astro price prediction
astro_price = st.sidebar.number_input(
    "$ASTRO Price", min_value=0.01, value=2.5, help="Price of $ASTRO"
)

st.sidebar.header("Liquidity Predictions")

# slider bars for predcitions
for i, row in df_liq.iterrows():
    df_liq.loc[i, "adj"] = (
        st.sidebar.slider(
            f'{row["pair"]} Percent Increase',
            format="%d%%",
            max_value=500,
            value=int(df_liq["liq"].sum() / row["liq"]),
        )
        / 100
    )

    df_liq.loc[i, "adj_liq"] = df_liq.loc[i, "liq"] * (1 + df_liq.loc[i, "adj"])

# value of lockdrop
df_liq["value_of_lockdrop"] = df_liq["astro_tokens"] * astro_price

# ratio
df_liq["ratio"] = df_liq["value_of_lockdrop"] / df_liq["liq"]
df_liq["adj_ratio"] = df_liq["value_of_lockdrop"] / df_liq["adj_liq"]

# separate tables
df_adj = df_liq.drop(columns=["adj", "liq", "ratio"])
df_liq = df_liq.drop(columns=["adj", "adj_liq", "adj_ratio"])

# main body
st.header("Astroport Lockdrop Dashboard")

st.markdown("### Original Allocation")

st.dataframe(
    df_liq.style.format(
        {
            "value_of_lockdrop": "${:,.0f}",
            "liq": "${:,.0f}",
            "astro_tokens": "{:,}",
            "ratio": "{:.2%}",
        }
    ),
    height=500,
)

st.markdown("### Predicted Allocation")

st.dataframe(
    df_adj.style.format(
        {
            "value_of_lockdrop": "${:,.0f}",
            "adj_liq": "${:,.0f}",
            "astro_tokens": "{:,}",
            "adj_ratio": "{:.2%}",
        }
    ),
    height=500,
)
