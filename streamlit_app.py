import os
import random
import requests
import numpy as np
import pandas as pd
import streamlit as st

# streamlit config
st.set_page_config(layout="wide")

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
astro_pairs = {
    "bLUNA-LUNA": "terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p",
    "LUNA-UST": "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6",
    "ANC-UST": "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3",
    "MIR-UST": "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux",
    "ORION-UST": "terra1z6tp0ruxvynsx5r9mmcc2wcezz9ey9pmrw5r8g",
    "STT-UST": "terra19pg6d7rrndg4z4t0jhcd7z9nhl3p5ygqttxjll",
    "VKR-UST": "terra1e59utusv5rspqsu8t37h5w887d9rdykljedxw0",
    "MINE-UST": "terra178jydtjvj4gw8earkgnqc80c3hrmqj4kw2welz",
    "PSI-UST": "terra163pkeeuwxzr0yhndf8xd2jprm9hrtk59xf7nqf",
    "APOLLO-UST": "terra1xj2w7w8mx6m2nueczgsxy2gnmujwejjeu2xf78",
}

# convert to dataframe
astro_pairs = (
    pd.DataFrame.from_dict(astro_pairs, orient="index")
    .reset_index()
    .rename(columns={"index": "pair", 0: "address"})
)

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
df["liquidity_usd"] = df["asset1_poolAmount"] // 1_000_000 * 2

# columns of interest
df_liq = df[
    [
        "pair",
        "address",
        "liquidity_usd",
    ]
]

# luna price
luna_ust = df[df["pair"] == "LUNA-UST"]
luna_price = (luna_ust["asset0_poolAmount"] / luna_ust["asset1_poolAmount"])[0]

# fix mirror liquidity
mir_ust = df[df["pair"] == "MIR-UST"]
df_liq.loc[mir_ust.index, "liquidity_usd"] = (
    df.loc[mir_ust.index, "asset0_poolAmount"] // 1_000_000 * 2
)

# fix luna liquidity
luna_ust = df[df["pair"] == "LUNA-UST"]
df_liq.loc[luna_ust.index, "liquidity_usd"] = (
    df.loc[luna_ust.index, "asset0_poolAmount"] // 1_000_000 * 2
)

# fix bluna liquidity
bluna_luna = df[df["pair"] == "bLUNA-LUNA"]
df_liq.loc[bluna_luna.index, "liquidity_usd"] = int(
    df.loc[bluna_luna.index, "asset1_poolAmount"] // 1_000_000 * 2 * luna_price
)

# astro tokens

# sensitivity

st.header("Astroport Lockdrop Dashboard")

st.write(df_liq)
