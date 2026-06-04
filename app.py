import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------------------
# ✅ READ VOY FILE
# -----------------------------------------
def read_voy_excel(file):
    xls = pd.ExcelFile(file, engine="openpyxl")

    voy_sheets = [s for s in xls.sheet_names if "voy" in s.lower()]

    frames = []
    for sheet in voy_sheets:
        df = pd.read_excel(xls, sheet_name=sheet, header=None, engine="openpyxl")
        df["sheet"] = sheet
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


# -----------------------------------------
# ✅ CONVERT TIME
# -----------------------------------------
def convert_decimal_time(decimal):
    try:
        seconds = float(decimal) * 24 * 3600
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h:02}:{m:02}"
    except:
        return None


# -----------------------------------------
# ✅ EXTRACT ACTIVITIES
# -----------------------------------------
def extract_schedule(df):
    rows = []

    for i in range(len(df)):
        for j in range(len(df.columns)):
            val = df.iat[i, j]

            if isinstance(val, float) and 0 < val < 1.1:
                time = convert_decimal_time(val)

                activities = []
                for k in range(1, 6):
                    if i + k < len(df):
                        nxt = df.iloc[i + k].dropna().values
                        activities.extend(nxt)

                for act in activities:
                    if isinstance(act, str) and len(act.strip()) > 2:
                        rows.append({
                            "time": time,
                            "activity": act.strip()
                        })

    return pd.DataFrame(rows)


# -----------------------------------------
# ✅ DETECT VENUES (FIXED VERSION ✅)
# -----------------------------------------
KNOWN_VENUES = [
    "FLOWRIDER", "SKYPAD", "ROCKWALL",
    "SPORTS COURT", "STUDIO B", "ZIPLINE",
    "LASER", "MINI GOLF"
]

def detect_venues(df):
    venues = set()
    flat = df.values.flatten()

    for val in flat:
        if isinstance(val, str):
            val_str = val.lower()

            for v in KNOWN_VENUES:
                if v.lower() in val_str:
                    venues.add(v.title())

    return list(venues)


# -----------------------------------------
# ✅ ASSIGN VENUES
# -----------------------------------------
def assign_venues(schedule, venues):
    schedule = schedule.copy()

    if len(venues) == 0:
        schedule["venue"] = "Unknown"
        return schedule

    schedule["venue"] = [venues[i % len(venues)] for i in range(len(schedule))]
    return schedule


# -----------------------------------------
# ✅ STAFF ASSIGNMENT
# -----------------------------------------
def assign_staff(schedule, staff_list, venue_requirements):
    staff_load = {s: 0 for s in staff_list}
    results = []

    for _, row in schedule.iterrows():
        venue = row["venue"]
        needed = venue_requirements.get(venue, 1)

        assigned = []

        for _ in range(needed):
            staff = sorted(staff_load, key=staff_load.get)[0]
            staff_load[staff] += 1
            assigned.append(staff)

        results.append({
            "time": row["time"],
            "venue": venue,
            "activity": row["activity"],
            "staff": ", ".join(assigned)
        })

    return pd.DataFrame(results)


# -----------------------------------------
# ✅ BUILD TIME GRID (7AM → MIDNIGHT)
# -----------------------------------------
def build_time_grid():
    times = []
    current = datetime.strptime("07:00", "%H:%M")
    end_time = datetime.strptime("23:59", "%H:%M")

    while current <= end_time:
        times.append(current.strftime("%H:%M"))
        current += timedelta(minutes=15)

    return times


# -----------------------------------------
# ✅ BUILD MATRIX VIEW
# -----------------------------------------
def build_schedule_matrix(schedule_df, staff_list):
    time_slots = build_time_grid()

    matrix = pd.DataFrame(index=time_slots, columns=staff_list)

    for _, row in schedule_df.iterrows():
        time = row["time"]
        venue = row["venue"]
        staff_members = row["staff"].split(",")

        for s in staff_members:
            s = s.strip()
            if s in matrix.columns and time in matrix.index:
                matrix.loc[time, s] = venue

    return matrix


# -----------------------------------------
# ✅ COLOR BY VENUE
# -----------------------------------------
def color_cells(val):
    colors = {
        "Flowrider": "#00BFFF",
        "Skypad": "#32CD32",
        "Rockwall": "#FFA500",
        "Sports Court": "#FF69B4",
        "Studio B": "#9370DB",
        "Zipline": "#FFD700",
        "Laser": "#FF4500"
    }

    if isinstance(val, str):
        for k in colors:
            if k in val:
                return f"background-color: {colors[k]}; color: black"

    return ""


# -----------------------------------------
# ✅ UI
# -----------------------------------------
st.set_page_config(layout="wide")
st.title("🚢 VOY Planner → Smart Staff Scheduler")

tabs = st.tabs(["1️⃣ Upload VOY", "2️⃣ Staff Setup", "3️⃣ Schedule"])

# -----------------------------------------
# TAB 1
# -----------------------------------------
with tabs[0]:
    uploaded_file = st.file_uploader("Upload VOY file", type=["xlsx", "xlsm"])

    if uploaded_file:
        df = read_voy_excel(uploaded_file)
        st.session_state["raw_df"] = df

        venues = detect_venues(df)
        st.session_state["venues"] = venues

        st.success("✅ File loaded")
        st.write("Detected Venues:", venues)


# -----------------------------------------
# TAB 2
# -----------------------------------------
with tabs[1]:
    if "venues" not in st.session_state:
        st.warning("Upload VOY first")
    else:
        staff_input = st.text_input(
            "Staff names (comma separated)",
            "John, Maria, Alex, Sam"
        )

        staff_list = [s.strip() for s in staff_input.split(",")]
        st.session_state["staff"] = staff_list

        st.subheader("Staff per Venue")

        venue_requirements = {}

        for v in st.session_state["venues"]:
            venue_requirements[v] = st.number_input(
                f"{v}",
                1, 10, 2, key=v
            )

        st.session_state["venue_requirements"] = venue_requirements


# -----------------------------------------
# TAB 3
# -----------------------------------------
with tabs[2]:
    if "raw_df" not in st.session_state:
        st.warning("Upload VOY first")
    elif "staff" not in st.session_state:
        st.warning("Set staff first")
    else:
        if st.button("Generate Schedule"):
            schedule = extract_schedule(st.session_state["raw_df"])
            schedule = assign_venues(schedule, st.session_state["venues"])

            final = assign_staff(
                schedule,
                st.session_state["staff"],
                st.session_state["venue_requirements"]
            )

            matrix = build_schedule_matrix(final, st.session_state["staff"])

            st.subheader("📅 Schedule Grid")

            styled = matrix.style.map(color_cells)
            st.dataframe(styled, use_container_width=True)
