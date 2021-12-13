import os
import random
import requests
import numpy as np
import pandas as pd
import streamlit as st
import seaborn as sns

# streamlit config
# st.set_page_config(layout="wide")

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
    ["bLUNA-LUNA", "terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p", 17250000, 0],
    ["LUNA-UST", "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6", 21750000, 0],
    ["ANC-UST", "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3", 14250000, 0.8474],
    ["MIR-UST", "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux", 6750000, 0.2023],
    ["ORION-UST", "terra1z6tp0ruxvynsx5r9mmcc2wcezz9ey9pmrw5r8g", 1500000, 0.7904],
    ["STT-UST", "terra19pg6d7rrndg4z4t0jhcd7z9nhl3p5ygqttxjll", 3750000, 0.7230],
    ["VKR-UST", "terra1e59utusv5rspqsu8t37h5w887d9rdykljedxw0", 2250000, 2.703],
    ["MINE-UST", "terra178jydtjvj4gw8earkgnqc80c3hrmqj4kw2welz", 3000000, 0.8577],
    ["PSI-UST", "terra163pkeeuwxzr0yhndf8xd2jprm9hrtk59xf7nqf", 2250000, 0.97],
    ["APOLLO-UST", "terra1xj2w7w8mx6m2nueczgsxy2gnmujwejjeu2xf78", 2250000, 0],
]

# convert to dataframe
astro_pairs = pd.DataFrame(
    astro_pairs, columns=["pair", "address", "astro_tokens", "lp_rewards"]
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
df["liq"] = df["asset1_poolAmount"] // 1_000_000 * 2

# columns of interest
df_liq = df[
    [
        "pair",
        # "address",
        "astro_tokens",
        "liq",
        "lp_rewards",
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

# sort by astro_tokens
df_liq = df_liq.sort_values("astro_tokens", ascending=False).reset_index(drop=True)

# current LP rewards
with st.sidebar.expander("LP Staking Rewards"):

    st.write("LP incentives on top of $ASTRO")

    for i, row in df_liq.iterrows():
        df_liq.loc[i, "lp_rewards"] = st.number_input(
            f'{row["pair"]}', value=row["lp_rewards"]
        )

# slider bars for predcitions
with st.sidebar.expander("Liquidity Predictions"):
    for i, row in df_liq.iterrows():

        df_liq.loc[i, "adj"] = (
            st.slider(
                f'{row["pair"]}',
                format="%d%%",
                max_value=200,
                value=int(df_liq["liq"].sum() / row["liq"]),
            )
            / 100
        )

        df_liq.loc[i, "adj_liq"] = df_liq.loc[i, "liq"] * (1 + df_liq.loc[i, "adj"])


# value of lockdrop
df_liq["astro_value"] = df_liq["astro_tokens"] * astro_price

# ratios
df_liq["ratio"] = df_liq["astro_value"] / df_liq["liq"]
df_liq["adj_ratio"] = df_liq["astro_value"] / df_liq["adj_liq"]

# separate tables
df_adj = df_liq.drop(columns=["adj", "liq", "ratio"])
df_liq = df_liq.drop(columns=["adj", "adj_liq", "adj_ratio"])

# user lp positions
with st.sidebar.expander("AstroChad LP Positions"):

    # user input
    for i, row in df_adj.iterrows():
        df_adj.loc[i, "chad_lp"] = st.number_input(
            f'{row["pair"]}', value=0, step=100, format="%d"
        )

        # add to adj liquidity
        df_adj.loc[i, "adj_liq"] += df_adj.loc[i, "chad_lp"]

    # recalculate lp_rewards
    df_adj["lp_rewards"] = df_liq["liq"] / df_adj["adj_liq"] * df_adj["lp_rewards"]

    # recalculate ratio
    df_adj["adj_ratio"] = df_adj["astro_value"] / df_adj["adj_liq"]


# chad positions
df_chad = df_adj[["pair", "chad_lp"]]
df_adj.drop(columns=["chad_lp"], inplace=True)

# lockdrop weights
df_weights = pd.read_csv("lockdrop_weights.csv")

# chad weights
with st.sidebar.expander("AstroChad Lockup Duration"):

    for i, row in df_chad.iterrows():
        df_chad.loc[i, "chad_lock"] = st.number_input(
            f"{row['pair']}",
            min_value=2,
            max_value=52,
            value=26,
            help="Lockup in weeks",
        )

        df_chad.loc[i, "chad_weight"] = (
            row["chad_lp"]
            * df_weights.iloc[int(df_chad.loc[i, "chad_lock"]) - 1]["adjusted_weight"]
        )

# avg weights
with st.sidebar.expander("Average Lockup Duration"):

    for i, row in df_chad.iterrows():
        df_chad.loc[i, "avg_lock"] = st.number_input(
            f"{row['pair']}",
            min_value=2,
            max_value=52,
            value=4,
            help="Lockup in weeks",
        )

        df_chad.loc[i, "avg_weight"] = (
            df_adj.loc[i, "adj_liq"] - row["chad_lp"]
        ) * df_weights.iloc[int(df_chad.loc[i, "avg_lock"]) - 1]["adjusted_weight"]

# chad rewards
df_chad["astro_tokens"] = (
    df_chad["chad_weight"]
    / (df_chad["avg_weight"] + df_chad["chad_weight"])
    * df_adj["astro_tokens"]
)

# chad token value
df_chad["astro_value"] = df_chad["astro_tokens"] * astro_price

# lp reward value
df_chad["lp_rewards"] = df_chad["chad_lp"] * df_adj["lp_rewards"]

# total rewards
df_chad["total_rewards"] = df_chad["lp_rewards"] + df_chad["astro_value"]

# main body
st.header("Astroport Lockdrop Dashboard")

st.markdown("### Original Allocation")

cm = sns.light_palette("green", as_cmap=True)

# reorder table
df_liq = df_liq[["pair", "astro_tokens", "astro_value", "liq", "ratio", "lp_rewards"]]

st.dataframe(
    df_liq.style.background_gradient(cmap=cm, subset=["lp_rewards", "ratio"]).format(
        {
            "astro_value": "${:,.0f}",
            "liq": "${:,.0f}",
            "astro_tokens": "{:,}",
            "ratio": "{:.2%}",
            "lp_rewards": "{:.2%}",
        }
    ),
    height=500,
)

st.markdown("### Predicted Allocation")

# reorder table
df_adj = df_adj[
    ["pair", "astro_tokens", "astro_value", "adj_liq", "adj_ratio", "lp_rewards"]
]

st.dataframe(
    df_adj.style.background_gradient(
        cmap=cm, subset=["lp_rewards", "adj_ratio"]
    ).format(
        {
            "astro_value": "${:,.0f}",
            "adj_liq": "${:,.0f}",
            "astro_tokens": "{:,}",
            "adj_ratio": "{:.2%}",
            "lp_rewards": "{:.2%}",
        }
    ),
    height=500,
)

st.markdown("### AstroChad Projections")

# reorder table
df_chad = df_chad[
    ["pair", "chad_lp", "astro_tokens", "astro_value", "lp_rewards", "total_rewards"]
]

st.dataframe(
    df_chad.style.format(
        {
            "chad_lp": "${:,.0f}",
            "astro_tokens": "{:,.0f}",
            "astro_value": "${:,.0f}",
            "lp_rewards": "${:,.0f}",
            "total_rewards": "${:,.0f}",
        }
    ),
    height=500,
)

# disclaimer
st.info("This tool was created for educational purposes only, not financial advice.")
