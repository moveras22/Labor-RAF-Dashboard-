import streamlit as st
import pandas as pd
import base64

st.set_page_config(page_title="Labor / RAF Dashboard", layout="wide")

# =============================
# SESSION STATE INIT (DO NOT REMOVE)
# =============================
if "daily_raf" not in st.session_state:
    st.session_state.daily_raf = [0]*14

if "weekly_raf" not in st.session_state:
    st.session_state.weekly_raf = [0]*5

if "weekly_labor" not in st.session_state:
    st.session_state.weekly_labor = [0]*5

# =============================
# HEADER IMAGE
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
# DAILY TAB (UNCHANGED)
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

    # 2ND SHIFT PREDICTOR (UNCHANGED)
    if first_shift > 0:

        second_needed = target - first_shift

        second_hours_entered = sum(1 for x in raf[7:] if x > 0)
        remaining_second_hours = max(1, 7 - second_hours_entered)

        full_shift_rate = second_needed / 7 if second_needed > 0 else 0
        live_rate = second_needed / remaining_second_hours if remaining_second_hours > 0 else 0

        if second_needed > 0:
            st.info(f"""
🔹 1st Shift Output: {int(first_shift)}

🔹 2nd Shift Needs:
- {int(second_needed)} units total to hit {target}
- {full_shift_rate:.1f}/hr (full shift pace)
- {live_rate:.1f}/hr (based on remaining hours)
""")
        else:
            st.success("1st shift already hit target")

    st.divider()

    st.subheader("📈 Trend vs Target")
    chart_df = df[["Hour","Cumulative RAF","Target"]].set_index("Hour")
    st.line_chart(chart_df)

# =====================================================
# WEEKLY TAB (FIXED LOGIC ONLY)
# =====================================================
elif menu == "📅 Weekly Tracker":

    st.subheader("📅 Weekly Labor / RAF")

    target_daily = st.number_input("Daily Target RAF", value=71)
    target_lpr = st.number_input("Target Labor/RAF", value=305)

    st.divider()

    days = ["Mon","Tue","Wed","Thu","Fri"]

    raf_data = []
    labor_data = []
    daily_lpr = []

    for i, d in enumerate(days):

        c1, c2 = st.columns(2)

        raf = c1.number_input(
            f"{d} RAF",
            value=st.session_state.weekly_raf[i],
            key=f"wraf_{i}"
        )

        labor = c2.number_input(
            f"{d} Labor ($)",
            value=st.session_state.weekly_labor[i],
            key=f"wlab_{i}"
        )

        st.session_state.weekly_raf[i] = raf
        st.session_state.weekly_labor[i] = labor

        raf_data.append(raf)
        labor_data.append(labor)

        daily_lpr.append(labor/raf if raf > 0 else 0)

    total_raf = sum(raf_data)
    total_labor = sum(labor_data)

    days_entered = sum(1 for x in raf_data if x > 0)

    week_lpr = total_labor / total_raf if total_raf > 0 else 0

    weekly_target = target_daily * 5

    st.divider()

    c1,c2,c3 = st.columns(3)

    c1.metric("Week RAF", int(total_raf))
    c2.metric("Week Labor/RAF", f"{week_lpr:.2f}")
    c3.metric("RAF Target", weekly_target)

    st.divider()

    # =============================
    # 🔥 FIXED RECOVERY LOGIC (LABOR BASED)
    # =============================
    if total_raf > 0:

        required_raf = total_labor / target_lpr if target_lpr > 0 else 0
        remaining = required_raf - total_raf

        remaining_days = max(1, 5 - days_entered)

        needed = remaining / remaining_days if remaining_days > 0 else 0

        if week_lpr > target_lpr:
            st.error(f"""
To recover Labor/RAF:

Required RAF: {required_raf:.0f}
Current RAF: {total_raf}
Gap: {remaining:.0f}

👉 Need {needed:.1f}/day to recover
""")
        else:
            st.success("Labor/RAF on target")

    df_week = pd.DataFrame({
        "Day": days,
        "RAF": raf_data,
        "Labor": labor_data,
        "Labor/RAF": daily_lpr
    })

    st.dataframe(df_week, use_container_width=True)
