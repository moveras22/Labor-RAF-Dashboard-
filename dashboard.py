import pandas as pd
import os
import streamlit as st
import sqlite3

# =========================
# DATABASE (REPLACES CSV)
# =========================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS labor_data (
    Date TEXT,
    RAF INTEGER,
    Labor REAL,
    OT REAL
)
""")
conn.commit()

def load_data():
    try:
        return pd.read_sql("SELECT * FROM labor_data", conn)
    except:
        return pd.DataFrame()

def save_data(df):
    df.to_sql("labor_data", conn, if_exists="replace", index=False)

# =========================
# SESSION STATE INIT
# =========================
if "df" not in st.session_state:
    st.session_state.df = load_data()

# =========================
# SESSION STATE INIT (DO NOT REMOVE)
# =========================
if "daily_raf" not in st.session_state:
    st.session_state.daily_raf = [0]*14

if "weekly_raf" not in st.session_state:
    st.session_state.weekly_raf = [0]*5

# =========================
# YOUR EXISTING APP CONTINUES BELOW
# (UNCHANGED)
# =========================

st.title("Labor / RAF Dashboard")

df = st.session_state.df

st.write("### Current Data")
st.dataframe(df)

# Example inputs (keep yours if you already have them)
date_input = st.text_input("Date")
raf_input = st.number_input("RAF", value=0)
labor_input = st.number_input("Labor", value=0.0)
ot_input = st.number_input("OT", value=0.0)

if st.button("Add Entry"):
    new_row = pd.DataFrame([{
        "Date": date_input,
        "RAF": raf_input,
        "Labor": labor_input,
        "OT": ot_input
    }])

    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)

    # SAVE DATA (CRITICAL)
    save_data(st.session_state.df)

    st.success("Saved!")

# =========================
# DISPLAY UPDATED DATA
# =========================
st.write("### Updated Data")
st.dataframe(st.session_state.df)
