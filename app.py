import streamlit as st
import pandas as pd

# -----------------------------------------
# ✅ 1. READ VOY FILE (ALL VOY TABS)
# -----------------------------------------
def read_voy_excel(file):
    xls = pd.ExcelFile(file)
    
    voy_sheets = [s for s in xls.sheet_names if "voy" in s.lower()]
    
    frames = []
    for sheet in voy_sheets:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        df["source_sheet"] = sheet
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


# -----------------------------------------
# ✅ 2. CONVERT DECIMAL TIME → HH:MM
# -----------------------------------------
def convert_decimal_time(decimal):
    try:
        seconds = float(decimal) * 24 * 3600
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours:02}:{minutes:02}"
    except:
        return None


# -----------------------------------------
# ✅ 3. EXTRACT SCHEDULE GRID FROM VOY
# -----------------------------------------
def extract_schedule_grid(df):
    rows = []

    for i in range(len(df)):
        for j in range(len(df.columns)):
            value = df.iat[i, j]

            # ✅ detect time slot (fractional)
            if isinstance(value, float) and 0 < value < 1.1:
                time = convert_decimal_time(value)

                # look ahead for activities (VOY structure)
                activities = []
                for k in range(1, 6):
                    if i + k < len(df):
                        next_row = df.iloc[i + k].dropna().values
                        activities.extend(next_row)

                for act in activities:
                    if isinstance(act, str) and len(act.strip()) > 2:
                        rows.append({
                            "time": time,
                            "activity": act.strip()
                        })

    return pd.DataFrame(rows)


# -----------------------------------------
# ✅ 4. ASSIGN VENUES (BASED ON VOY PATTERN)
# -----------------------------------------
VENUES = ["Flowrider", "Skypad", "Rockwall", "Sports Court"]

def assign_venues(df):
    df = df.copy()
    df["venue"] = [VENUES[i % len(VENUES)] for i in range(len(df))]
    return df


# -----------------------------------------
# ✅ 5. SMART STAFF ASSIGNMENT
# -----------------------------------------
def assign_staff(schedule_df, staff_list, staff_per_activity):
    staff_load = {s: 0 for s in staff_list}
    result = []

    for _, row in schedule_df.iterrows():
        assigned_staff = []

        for _ in range(staff_per_activity):
            # pick least-busy staff
            staff = sorted(staff_load, key=staff_load.get)[0]
            staff_load[staff] += 1
            assigned_staff.append(staff)

        result.append({
            "time": row["time"],
            "venue": row["venue"],
            "activity": row["activity"],
            "staff": ", ".join(assigned_staff)
        })

    return pd.DataFrame(result)


# -----------------------------------------
# ✅ STREAMLIT UI
# -----------------------------------------
st.title("🚢 VOY Planner → Daily Sports Schedule")

uploaded_file = st.file_uploader("Upload VOY Excel File", type=["xlsx", "xlsm"])

if uploaded_file:
    st.success("File uploaded successfully ✅")

    # Read file
    raw_df = read_voy_excel(uploaded_file)

    # Extract schedule
    schedule = extract_schedule_grid(raw_df)

    if schedule.empty:
        st.error("Could not extract schedule. Try another VOY file.")
    else:
        schedule = assign_venues(schedule)

        # STAFF INPUT
        st.subheader("Staff Setup")

        staff_input = st.text_input(
            "Enter staff (comma-separated)",
            "John, Maria, Alex, Sam, Chris"
        )
        staff_list = [s.strip() for s in staff_input.split(",")]

        staff_per_activity = st.slider(
            "Staff per activity",
            min_value=1,
            max_value=5,
            value=1
        )

        # Generate schedule
        final_schedule = assign_staff(schedule, staff_list, staff_per_activity)

        # Show results
        st.subheader("📅 Generated Schedule")
        st.dataframe(final_schedule, use_container_width=True)

        # Download
        csv = final_schedule.to_csv(index=False)
        st.download_button(
            "⬇️ Download Schedule",
            csv,
            file_name="daily_schedule.csv"
        )
