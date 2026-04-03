import streamlit as st
import pandas as pd
import base64

st.set_page_config(page_title="Labor / RAF Dashboard", layout="wide")

# ===== BANNER IMAGE (FULL WIDTH, FIXED) =====
def get_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64("transmissions.png")

st.markdown(f"""
<style>
.banner-img {{
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 10px;
}}
</style>

<img src="data:image/png;base64,{img}" class="banner-img">
""", unsafe_allow_html=True)

# ===== SETTINGS =====
HOURS = [
    "7-8","8-9","9-10","10-11","11-12","12-1","1-2",
    "2-3","3-4","4-5","5-6","6-7","7-8","8-9"
]

TOTAL_HOURS = len(HOURS)  # 14
FIRST_SHIFT_HOURS = 7
TARGET_LPR = 305

st.title("📊 Labor / RAF Control Dashboard")

# ===== INPUTS =====
st.subheader("🔧 Daily Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    daily_labor = st.number_input("Total Daily Labor ($)", value=23000, step=500)

with col2:
    planned_ot = st.number_input("Planned OT ($)", value=800, step=50)

with col3:
    target_raf = st.number_input("Target RAF", value=71)

total_labor_budget = daily_labor + planned_ot

# ===== INPUT TABLE =====
st.subheader("✏️ Enter RAF Per Hour")

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "Hour": HOURS,
        "RAF": [0]*TOTAL_HOURS
    })

df = st.data_editor(
    st.session_state.data,
    num_rows="fixed",
    use_container_width=True,
    key="raf_editor",
    column_config={
        "RAF": st.column_config.NumberColumn("RAF", step=1)
    }
)

st.session_state.data = df.copy()

# ===== CALCULATIONS =====
df["Cumulative RAF"] = df["RAF"].cumsum()

hours_worked = (df["RAF"] > 0).sum()
total_raf = df["RAF"].sum()

current_lpr = total_labor_budget / total_raf if total_raf > 0 else 0

df["Target RAF"] = [(i+1)*(target_raf/TOTAL_HOURS) for i in range(TOTAL_HOURS)]
df["Variance"] = df["Cumulative RAF"] - df["Target RAF"]

current_variance = df["Variance"].iloc[hours_worked-1] if hours_worked > 0 else 0
projected_raf = (total_raf / hours_worked) * TOTAL_HOURS if hours_worked > 0 else 0

# ===== METRICS =====
st.subheader("📈 Current Performance")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total RAF", int(total_raf))
col2.metric("Total Labor ($)", f"${int(total_labor_budget)}")
col3.metric("Labor / RAF", f"{current_lpr:.2f}")
col4.metric("Pace Variance", f"{current_variance:.1f}")
col5.metric("Projected RAF", f"{projected_raf:.1f}")

# ===== STATUS =====
st.subheader("🚨 Status")

if current_variance >= 0 and current_lpr <= TARGET_LPR:
    st.success("✅ On pace AND efficient")

elif current_variance >= 0 and current_lpr > TARGET_LPR:
    st.warning("⚠️ On pace BUT inefficient → push more units")

elif current_variance < 0 and current_lpr <= TARGET_LPR:
    st.warning("⚠️ Efficient BUT behind pace → need production")

else:
    st.error("❌ Behind pace AND inefficient")

# ===== LIVE PACE =====
st.subheader("⏱️ Live Pace Control")

if hours_worked > 0:
    expected_by_now = (target_raf / TOTAL_HOURS) * hours_worked
    remaining_hours = TOTAL_HOURS - hours_worked
    remaining_units = target_raf - total_raf
    current_pace = total_raf / hours_worked

    col1, col2, col3 = st.columns(3)
    col1.metric("Expected By Now", f"{expected_by_now:.1f}")
    col2.metric("Actual RAF", int(total_raf))
    col3.metric("Current Pace/hr", f"{current_pace:.1f}")

    if remaining_hours > 0:
        required_per_hour = remaining_units / remaining_hours

        st.markdown(f"""
**To recover:**
- Remaining Hours: {remaining_hours}
- Units Needed: {int(remaining_units)}
- Required Pace: {required_per_hour:.1f} / hr
""")

        if total_raf >= expected_by_now:
            st.success("On/Ahead of pace")
        else:
            st.error("Behind pace")

# ===== SHIFT BREAKDOWN =====
st.subheader("🔄 Shift Breakdown")

first_shift_raf = df["RAF"].iloc[:FIRST_SHIFT_HOURS].sum()
remaining_after_first = target_raf - first_shift_raf
second_shift_hours = TOTAL_HOURS - FIRST_SHIFT_HOURS

st.markdown("### 🟦 1st Shift")

st.metric("1st Shift RAF", int(first_shift_raf))

st.markdown("### 🟨 2nd Shift Requirements")

if remaining_after_first > 0:

    required_per_hour_2nd = remaining_after_first / second_shift_hours

    st.markdown(f"""
**1st shift ended with:** {int(first_shift_raf)} units  

2nd shift must produce:
- {int(remaining_after_first)} units
- {required_per_hour_2nd:.1f} per hour
""")

    if required_per_hour_2nd <= (target_raf / TOTAL_HOURS):
        st.success("2nd shift in good position")
    elif required_per_hour_2nd <= 8:
        st.warning("2nd shift needs to push")
    else:
        st.error("2nd shift in recovery mode")

else:
    st.success("Target already achieved in 1st shift")

# ===== WHAT IF =====
st.subheader("🔮 What If")

extra_units = st.number_input("Add Units:", value=20)
what_if_lpr = total_labor_budget / (total_raf + extra_units)

st.info(f"If +{extra_units} units → Labor/RAF = {what_if_lpr:.2f}")

# ===== TABLE =====
st.subheader("📋 Hourly Breakdown")

st.dataframe(df[["Hour","RAF","Cumulative RAF","Target RAF","Variance"]], use_container_width=True)

# ===== CHART =====
st.subheader("📊 Pace vs Target")

st.line_chart(df[["Cumulative RAF","Target RAF"]])