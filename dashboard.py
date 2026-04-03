import pandas as pd
import os
import streamlit as st

DATA_FILE = "saved_data.csv"

# =========================
# LOAD / SAVE (CSV)
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Date", "RAF", "Labor", "OT"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# =========================
# SESSION STATE INIT
# =========================
if "df" not in st.session_state:
    st.session_state.df = load_data()

if "daily_raf" not in st.session_state:
    st.session_state.daily_raf = [0]*14

if "weekly_raf" not in st.session_state:
    st.session_state.weekly_raf = [0]*5

# =========================
# APP
# =========================
st.title("Labor / RAF Dashboard")

df = st.session_state.df

st.write("### Current Data")
st.dataframe(df)

# =========================
# INPUTS
# =========================
date_input = st.text_input("Date")
raf_input = st.number_input("RAF", value=0)
labor_input = st.number_input("Labor", value=0.0)
ot_input = st.number_input("OT", value=0.0)

# =========================
# ADD ENTRY
# =========================
if st.button("Add Entry"):
    new_row = pd.DataFrame([{
        "Date": date_input,
        "RAF": raf_input,
        "Labor": labor_input,
        "OT": ot_input
    }])

    st.session_state.df = pd.concat(
        [st.session_state.df, new_row],
        ignore_index=True
    )

    save_data(st.session_state.df)

    st.success("Saved!")

# =========================
# DISPLAY UPDATED DATA
# =========================
st.write("### Updated Data")
st.dataframe(st.session_state.df)
