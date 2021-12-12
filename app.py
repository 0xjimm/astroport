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
    .rename(columns={"index": "pair"})
    .drop(labels=["timestamp", "unofficial", "startAt", "endAt"], axis=1)
)

# astroport lockdrop pairs
astro_pairs = [
    "terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p",
    "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6",
    "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3",
    "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux",
    "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux",
    "terra19pg6d7rrndg4z4t0jhcd7z9nhl3p5ygqttxjll",
    "terra1e59utusv5rspqsu8t37h5w887d9rdykljedxw0",
    "terra178jydtjvj4gw8earkgnqc80c3hrmqj4kw2welz",
    "terra163pkeeuwxzr0yhndf8xd2jprm9hrtk59xf7nqf",
    "terra1xj2w7w8mx6m2nueczgsxy2gnmujwejjeu2xf78",
]

# filter for astroport pairs
df = df[df["pair"].isin(astro_pairs)]

# parse json data
df = pd.concat(
    [
        df,
        df["asset0"].apply(pd.Series).add_prefix("asset0_"),
        df["asset1"].apply(pd.Series).add_prefix("asset1_"),
    ],
    axis=1,
)

# liquidity in usd
df["liquidity_usd"] = df["asset1_poolAmount"] // 1_000_000 * 2

# columns of interest
df_liq = df[
    ["asset0_name", "asset0_symbol", "asset1_name", "asset1_symbol", "liquidity_usd"]
]

# luna price
luna_price = df.loc[22, "asset0_poolAmount"] / df.loc[22, "asset1_poolAmount"]

# fix mirror liquidity
df_liq.loc[30, "liquidity_usd"] = df.loc[30, "asset0_poolAmount"] // 1_000_000 * 2

# fix luna liquidity
df_liq.loc[22, "liquidity_usd"] = df.loc[22, "asset0_poolAmount"] // 1_000_000 * 2

# fix bluna liquidity
df_liq.loc[23, "liquidity_usd"] = int(
    df.loc[23, "asset1_poolAmount"] // 1_000_000 * 2 * luna_price
)

# rename columns

# astro tokens

# sensitivity

st.header("Astroport Lockdrop Dashboard")

st.write(df_liq)
