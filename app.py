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
# VENUE BUILDER
# -------------------------
st.subheader("🏟️ Add Venues")

venue_options = ["Basketball", "Pool Games", "Soccer", "Tennis", "Volleyball"]

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

# Clear
if st.button("🗑️ Clear Venues"):
    st.session_state.venues = []

# Show venues
st.subheader("📋 Current Plan")
for i, v in enumerate(st.session_state.venues):
    st.write(
        f"{i+1}. {v['name']} | Staff: {v['min_staff']} | "
        f"{v['open'].strftime('%H:%M')} - {v['close'].strftime('%H:%M')}"
    )

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

        # One job per person per time
        for s in range(len(staff)):
            for t in range(len(timeslots)):
                model.Add(
                    sum(x[(s, t, v)] for v in range(len(venues))) <= 1
                )

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            # ✅ CLEAN MANAGER TABLE
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

            # ✅ STAFF VIEW
            st.subheader("🧑‍🤝‍🧑 Staff Schedules")

            for s in range(len(staff)):
                st.write(f"**{staff[s]}**")

                found = False

                for t in range(len(timeslots)):
                    for v in range(len(venues)):
                        if solver.Value(x[(s, t, v)]) == 1:
                            st.write(f"{timeslots[t]} → {venues[v]['name']}")
                            found = True

                if not found:
                    st.write("OFF")

        else:
            st.error("No feasible schedule found.")
