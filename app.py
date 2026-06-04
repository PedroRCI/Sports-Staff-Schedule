import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import pandas as pd

st.title("🚢 Cruise Sports Scheduler")

# -------------------------
# STAFF INPUT
# -------------------------
staff = [
    s.strip() for s in st.text_area(
        "Enter Staff (one per line)",
        "Alice\nBob\nCarlos\nDiana"
    ).split("\n") if s.strip()
]

# -------------------------
# CUSTOM VENUE OPTIONS ✅
# -------------------------
st.subheader("⚙️ Manage Venue Types")

venue_list_input = st.text_area(
    "Edit Available Venues (one per line)",
    "Basketball\nPool Games\nSoccer\nTennis\nVolleyball"
)

venue_options = [v.strip() for v in venue_list_input.split("\n") if v.strip()]

# -------------------------
# VENUE BUILDER
# -------------------------
st.subheader("🏟️ Add Venues")

col1, col2 = st.columns(2)

with col1:
    selected_venue = st.selectbox("Venue", venue_options)
    min_staff = st.number_input("Min Staff", 1, 10, 2)

with col2:
    open_time = st.time_input("Open")
    close_time = st.time_input("Close")

# Storage
if "venues" not in st.session_state:
    st.session_state.venues = []

# Add venue
if st.button("➕ Add Venue"):
    if open_time < close_time:
        st.session_state.venues.append({
            "name": selected_venue,
            "min_staff": min_staff,
            "open": open_time,
            "close": close_time
        })
        st.success(f"{selected_venue} added")
    else:
        st.error("Close time must be after open time")

# -------------------------
# EDIT / DELETE VENUES ✅
# -------------------------
st.subheader("📋 Current Plan")

for i, v in enumerate(st.session_state.venues):

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.write(
            f"{v['name']} | Staff: {v['min_staff']} | "
            f"{v['open'].strftime('%H:%M')} - {v['close'].strftime('%H:%M')}"
        )

    with col2:
        if st.button(f"✏️ Edit {i}"):
            st.session_state.edit_index = i

    with col3:
        if st.button(f"❌ Delete {i}"):
            st.session_state.venues.pop(i)
            st.experimental_rerun()

# -------------------------
# EDIT MODE ✅
# -------------------------
if "edit_index" in st.session_state:

    idx = st.session_state.edit_index
    v = st.session_state.venues[idx]

    st.subheader("✏️ Edit Venue")

    new_name = st.selectbox("Venue Name", venue_options, index=venue_options.index(v["name"]))
    new_staff = st.number_input("Min Staff", 1, 10, v["min_staff"])
    new_open = st.time_input("Open Time", v["open"])
    new_close = st.time_input("Close Time", v["close"])

    if st.button("💾 Save Changes"):
        st.session_state.venues[idx] = {
            "name": new_name,
            "min_staff": new_staff,
            "open": new_open,
            "close": new_close
        }
        del st.session_state.edit_index
        st.success("Updated!")
        st.experimental_rerun()

# -------------------------
# GENERATE SCHEDULE
# -------------------------
if st.button("🚀 Generate Schedule"):

    venues = st.session_state.venues

    if not venues:
        st.error("Please add at least one venue.")
    else:

        # Create hourly slots
        all_times = set()

        for v in venues:
            current = datetime.combine(datetime.today(), v["open"])
            end = datetime.combine(datetime.today(), v["close"])

            while current <= end:
                all_times.add(current.strftime("%H:%M"))
                current += timedelta(hours=1)

        timeslots = sorted(all_times)

        # Model
        model = cp_model.CpModel()
        x = {}

        for s in range(len(staff)):
            for t in range(len(timeslots)):
                for v in range(len(venues)):
                    x[(s, t, v)] = model.NewBoolVar(f"x_{s}_{t}_{v}")

        # Constraints
        for t in range(len(timeslots)):
            for v in range(len(venues)):
                time_obj = datetime.strptime(timeslots[t], "%H:%M").time()

                if venues[v]["open"] <= time_obj <= venues[v]["close"]:
                    model.Add(
                        sum(x[(s, t, v)] for s in range(len(staff)))
                        >= venues[v]["min_staff"]
                    )
                else:
                    for s in range(len(staff)):
                        model.Add(x[(s, t, v)] == 0)

        for s in range(len(staff)):
            for t in range(len(timeslots)):
                model.Add(sum(x[(s, t, v)] for v in range(len(venues))) <= 1)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            st.subheader("📊 Manager Dashboard")

            data = []

            for t in range(len(timeslots)):
                row = {"Time": timeslots[t]}

                for v in range(len(venues)):
                    assigned = [
                        staff[s]
                        for s in range(len(staff))
                        if solver.Value(x[(s, t, v)]) == 1
                    ]

                    if len(assigned) >= venues[v]["min_staff"]:
                        row[venues[v]["name"]] = ", ".join(assigned)
                    else:
                        row[venues[v]["name"]] = "❌"

                data.append(row)

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

        else:
            st.error("No feasible schedule found.")
``
