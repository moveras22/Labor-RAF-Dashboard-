import streamlit as st
import pandas as pd
import sqlite3

# =========================
# DATABASE (PERSISTENCE)
# =========================
conn = sqlite3.connect("data.db", check_same_thread=False)

def load_data():
    try:
        return pd.read_sql("SELECT * FROM labor_data", conn)
    except:
        return pd.DataFrame(columns=["Date", "RAF", "Labor", "OT"])

def save_data(df):
    df.to_sql("labor_data", conn, if_exists="replace", index=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS labor_data (
    Date TEXT,
    RAF INTEGER,
    Labor REAL,
    OT REAL
)
""")

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
# TABS
# =========================
tab1, tab2 = st.tabs(["📊 Labor Tracker", "📈 Predictor"])

# =========================
# TAB 1: LABOR TRACKER
# =========================
with tab1:
    st.title("Labor / RAF Tracker")

    st.subheader("Add Daily Entry")

    date = st.text_input("Date")
    raf = st.number_input("RAF", min_value=0)
    labor = st.number_input("Labor Cost", min_value=0.0)
    ot = st.number_input("OT Cost", min_value=0.0)

    if st.button("Add Entry"):
        new_row = pd.DataFrame([{
            "Date": date,
            "RAF": raf,
            "Labor": labor,
            "OT": ot
        }])

        st.session_state.df = pd.concat(
            [st.session_state.df, new_row],
            ignore_index=True
        )

        save_data(st.session_state.df)
        st.success("Saved!")

    st.subheader("Current Data")
    st.dataframe(st.session_state.df)

    # Labor / RAF calc
    if not st.session_state.df.empty:
        total_labor = st.session_state.df["Labor"].sum()
        total_raf = st.session_state.df["RAF"].sum()

        if total_raf > 0:
            labor_per_raf = total_labor / total_raf
            st.metric("Labor / RAF", f"${labor_per_raf:.2f}")

# =========================
# TAB 2: PREDICTOR
# =========================
with tab2:
    st.title("Production Predictor")

    st.subheader("Daily RAF Input")

    for i in range(len(st.session_state.daily_raf)):
        st.session_state.daily_raf[i] = st.number_input(
            f"Day {i+1}",
            value=st.session_state.daily_raf[i],
            key=f"day_{i}"
        )

    total_days = sum(st.session_state.daily_raf)
    avg_daily = total_days / len(st.session_state.daily_raf)

    st.write(f"Total RAF: {total_days}")
    st.write(f"Average Daily RAF: {avg_daily:.2f}")

    st.subheader("Target Analysis")

    target = st.number_input("Target Labor / RAF", value=305.0)

    if not st.session_state.df.empty:
        total_labor = st.session_state.df["Labor"].sum()
        current_raf = st.session_state.df["RAF"].sum()

        if current_raf > 0:
            current_lpr = total_labor / current_raf

            st.write(f"Current Labor / RAF: ${current_lpr:.2f}")

            needed_raf = total_labor / target

            gap = needed_raf - current_raf

            if gap > 0:
                st.error(f"You need {gap:.0f} more RAF to hit target")
            else:
                st.success("You are on target or better")
