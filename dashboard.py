import streamlit as st
import pandas as pd
import base64
import json
import os

st.set_page_config(page_title="Labor / RAF Dashboard", layout="wide")

SAVE_FILE = "saved_data.json"

# =============================
# LOAD DATA
# =============================
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {}

# =============================
# SAVE DATA
# =============================
def save_data():
    data = {
        "daily_raf": st.session_state.daily_raf,
        "weekly_raf": st.session_state.weekly_raf,
        "weekly_labor": st.session_state.weekly_labor
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

# =============================
# SESSION INIT
# =============================
def init_state():
    saved = load_data()

    st.session_state.daily_raf = saved.get("daily_raf", [0]*14)
    st.session_state.weekly_raf = saved.get("weekly_raf", [0]*5)
    st.session_state.weekly_labor = saved.get("weekly_labor", [0]*5)

init_state()

# =============================
# IMAGE
# =============================
def get_base64(img):
    with open(img, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    img = get_base64("transmissions.png")
    st.markdown(f"""
    <img src="data:image/png;base64,{img}" 
    style="width:100%; height:220px; object-fit:cover; border-radius:10px;">
    """, unsafe_allow_html=True)
except:
    pass

st.title("📊 Labor / RAF Control Dashboard")

menu = st.radio("", ["📊 Daily Dashboard", "📅 Weekly Tracker"], horizontal=True)

# =====================================================
# DAILY DASHBOARD
# =====================================================
if menu == "📊 Daily Dashboard":

    st.subheader("⚙️ Daily Inputs")

    col1, col2, col3 = st.columns(3)

    total_labor = col1.number_input("Total Daily Labor ($)", value=23000)
    ot = col2.number_input("Planned OT ($)", value=800)
    target = col3.number_input("Target RAF", value=71)

    total_cost = total_labor + ot

    st.divider()

    st.subheader("✏️ RAF Per Hour (14 Hours)")

    hours = [f"Hr{i+1}" for i in range(14)]
    cols = st.columns(7)

    raf = []

    for i in range(14):
        with cols[i % 7]:
            val = st.number_input(
                label=hours[i],
                value=st.session_state.daily_raf[i],
                key=f"daily_{i}"
            )
            st.session_state.daily_raf[i] = val
            raf.append(val)

    df = pd.DataFrame({"Hour": hours, "RAF": raf})

    df["Cumulative RAF"] = df["RAF"].cumsum()
    df["Target"] = [(i+1)*(target/14) for i in range(14)]

    total_raf = sum(raf)
    lpr = total_cost / total_raf if total_raf > 0 else 0

    first_shift = sum(raf[:7])
    second_shift = sum(raf[7:])

    hours_entered = sum(1 for x in raf if x > 0)
    projected = (total_raf / hours_entered)*14 if hours_entered > 0 else 0

    st.divider()

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Total RAF", int(total_raf))
    c2.metric("Labor/RAF", f"{lpr:.2f}")
    c3.metric("1st Shift RAF", int(first_shift))
    c4.metric("2nd Shift RAF", int(second_shift))
    c5.metric("Projected RAF", f"{projected:.0f}")

    st.divider()

    # 2nd SHIFT PREDICTOR
    if first_shift > 0:

        second_needed = target - first_shift
        remaining_hours = max(1, 7 - sum(1 for x in raf[7:] if x > 0))

        full_rate = second_needed / 7 if second_needed > 0 else 0
        live_rate = second_needed / remaining_hours if remaining_hours > 0 else 0

        if second_needed > 0:
            st.info(f"""
🔹 1st Shift Output: {int(first_shift)}

🔹 2nd Shift Needs {int(second_needed)} units to hit {target}
- {full_rate:.1f}/hr full pace
- {live_rate:.1f}/hr live pace
""")
        else:
            st.success("1st shift hit target")

    st.divider()

    if total_raf > 0:
        if lpr > 305:
            st.error("Labor/RAF HIGH")
        else:
            st.success("Labor OK")

    st.divider()

    st.subheader("📈 Trend vs Target")
    st.line_chart(df.set_index("Hour")[["Cumulative RAF","Target"]])

    st.dataframe(df)

# =====================================================
# WEEKLY TRACKER
# =====================================================
elif menu == "📅 Weekly Tracker":

    st.subheader("📅 Weekly Labor / RAF")

    target_daily = st.number_input("Daily Target RAF", value=71)
    target_lpr = st.number_input("Target Labor/RAF", value=305)

    days = ["Mon","Tue","Wed","Thu","Fri"]

    raf_data = []
    labor_data = []

    for i, d in enumerate(days):

        c1, c2 = st.columns(2)

        raf = c1.number_input(d+" RAF", value=st.session_state.weekly_raf[i], key=f"wraf_{i}")
        labor = c2.number_input(d+" Labor", value=st.session_state.weekly_labor[i], key=f"wlab_{i}")

        st.session_state.weekly_raf[i] = raf
        st.session_state.weekly_labor[i] = labor

        raf_data.append(raf)
        labor_data.append(labor)

    total_raf = sum(raf_data)
    total_labor = sum(labor_data)

    week_lpr = total_labor / total_raf if total_raf > 0 else 0

    days_entered = sum(1 for x in raf_data if x > 0)
    remaining_days = max(1, 5 - days_entered)

    weekly_target = target_daily * 5

    required_total_raf = total_labor / target_lpr if target_lpr > 0 else 0
    remaining_raf_needed = required_total_raf - total_raf
    needed = remaining_raf_needed / remaining_days

    st.divider()

    c1,c2,c3 = st.columns(3)

    c1.metric("Week RAF", int(total_raf))
    c2.metric("Labor/RAF", f"{week_lpr:.2f}")
    c3.metric("Recovery Needed", f"{needed:.1f}/day")

    if week_lpr > target_lpr:
        st.error("Labor trending HIGH")

# =============================
# SAVE BUTTON
# =============================
st.divider()

if st.button("💾 Save Data"):
    save_data()
    st.success("Data saved successfully!")
