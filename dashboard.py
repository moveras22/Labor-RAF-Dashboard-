import streamlit as st
import pandas as pd
import base64

st.set_page_config(page_title="Labor / RAF Dashboard", layout="wide")

# =============================
# SESSION STATE INIT
# =============================
def init_state():
    if "daily_raf" not in st.session_state:
        st.session_state.daily_raf = [0]*14
    if "weekly_raf" not in st.session_state:
        st.session_state.weekly_raf = [0]*5
    if "weekly_labor" not in st.session_state:
        st.session_state.weekly_labor = [0]*5

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

    # SHIFT SPLIT
    first_shift = sum(raf[:7])
    second_shift = sum(raf[7:])

    # HOURS TRACKING
    hours_entered = sum(1 for x in raf if x > 0)
    remaining_hours = max(1, 14 - hours_entered)

    remaining_units = target - total_raf
    projected = (total_raf / hours_entered)*14 if hours_entered > 0 else 0

    st.divider()

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Total RAF", int(total_raf))
    c2.metric("Labor/RAF", f"{lpr:.2f}")
    c3.metric("1st Shift RAF", int(first_shift))
    c4.metric("2nd Shift RAF", int(second_shift))
    c5.metric("Projected RAF", f"{projected:.0f}")

    st.divider()

    # =============================
    # 🔥 2ND SHIFT PREDICTOR
    # =============================
    if first_shift > 0:

        second_needed = target - first_shift

        second_hours_entered = sum(1 for x in raf[7:] if x > 0)
        remaining_second_hours = max(1, 7 - second_hours_entered)

        full_shift_rate = second_needed / 7 if second_needed > 0 else 0
        live_rate = second_needed / remaining_second_hours if remaining_second_hours > 0 else 0

        if second_needed > 0:
            st.info(f"""
🔹 1st Shift Output: {int(first_shift)}

🔹 2nd Shift Requirements:
- {int(second_needed)} units TOTAL to hit {target}
- {full_shift_rate:.1f}/hr (full shift pace)
- {live_rate:.1f}/hr (based on remaining hours)
""")
        else:
            st.success("1st shift already hit or exceeded target")

    st.divider()

    # ALERTS
    st.subheader("🚨 Alerts")

    if total_raf > 0:
        if lpr > 305:
            st.error("Labor/RAF HIGH")
        else:
            st.success("Labor OK")

        if projected < target:
            st.error(f"Off pace → projected {int(projected)} vs {target}")
        else:
            st.success("On pace")

    st.divider()

    # CHART
    st.subheader("📈 Trend vs Target")
    chart_df = df[["Hour","Cumulative RAF","Target"]].set_index("Hour")
    st.line_chart(chart_df)

    st.divider()
    st.dataframe(df, use_container_width=True)

# =====================================================
# WEEKLY TRACKER
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

    avg_raf = total_raf / days_entered if days_entered > 0 else 0
    avg_labor = total_labor / days_entered if days_entered > 0 else 0

    projected_raf = avg_raf * 5 if days_entered > 0 else 0
    projected_labor = avg_labor * 5 if days_entered > 0 else 0

    projected_lpr = projected_labor / projected_raf if projected_raf > 0 else 0

    weekly_target = target_daily * 5

   remaining_days = max(1, 5 - days_entered)

    # TARGET TOTAL LABOR BASED ON TARGET LPR
    target_total_labor = target_lpr * (target_daily * 5)

    # HOW MUCH LABOR YOU'VE ALREADY SPENT
    labor_used = total_labor

    # REMAINING LABOR BUDGET
    remaining_labor_budget = target_total_labor - labor_used

    # RAF NEEDED TO HIT TARGET LPR
    required_total_raf = total_labor / target_lpr if target_lpr > 0 else 0

    remaining_raf_needed = required_total_raf - total_raf

    needed = remaining_raf_needed / remaining_days if remaining_days > 0 else 0
    st.divider()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Week RAF", int(total_raf))
    c2.metric("Week Labor/RAF", f"{week_lpr:.2f}")
    c3.metric("Projected RAF", f"{projected_raf:.0f}")
    c4.metric("Projected Labor/RAF", f"{projected_lpr:.2f}")

    st.divider()

    if total_raf > 0:

        if projected_lpr > target_lpr:
            st.error("Labor trending HIGH")
        else:
            st.success("Labor OK")

        if projected_raf < weekly_target:
            st.error(f"Need {needed:.1f}/day to recover")
        else:
            st.success("On pace")

    df_week = pd.DataFrame({
        "Day": days,
        "RAF": raf_data,
        "Labor": labor_data,
        "Labor/RAF": daily_lpr
    })

    st.dataframe(df_week, use_container_width=True)
