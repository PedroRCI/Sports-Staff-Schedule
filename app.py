import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import pandas as pd

st.title("🚢 Cruise Sports Scheduler")

# -------------------------
# STAFF INPUT
# -------------------------
staff = st.text_area(
    "Enter Staff (one per line)",
    "Alice\nBob\nCarlos\nDiana"
).split("\n")

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

# Session state
if "venues" not in st.session_state:
    st.session_state.venues = []

# Add venue button
if st.button("➕ Add Venue"):
    st.session_state.venues.append({
        "name": selected_venue,
        "min_staff": min_staff,
        "open": open_time,
        "close": close_time
    })
    st.success(f"{selected_venue} added")

# Clear button (VERY useful)
if st.button("🗑️ Clear Venues"):
    st.session_state.venues = []

# Show venues nicely
st.subheader("📋 Current Plan")
for i, v in enumerate(st.session_state.venues):
    st.write(
        f"{i+1}. {v['name']} | Staff: {v['min_staff']} | "
        f"{v['open'].strftime('%H:%M')} - {v['close'].strftime('%H:%M')}"
    )

# -------------------------
# GENERATE
# -------------------------
if st.button("🚀 Generate Schedule"):

    venues = st.session_state.venues

    if len(venues) == 0:
        st.error("Please add at least one venue.")
    else:

        # -------------------------
        # CREATE HOURLY TIMES
        # -------------------------
        all_times = set()

        for v in venues:
            current = datetime.combine(datetime.today(), v["open"])
            end = datetime.combine(datetime.today(), v["close"])

            while current <= end:
                all_times.add(current.strftime("%H:%M"))
                current += timedelta(hours=1)

        timeslots = sorted(all_times)

        # -------------------------
        # MODEL
        # -------------------------
        model = cp_model.CpModel()

        x = {}
        for s in range(len(staff)):
            for t in range(len(timeslots)):
                for v in range(len(venues)):
                    x[s, t, v] = model.NewBoolVar(f"x_{s}_{t}_{v}")

        # Constraints
        for t in range(len(timeslots)):
            for v in range(len(venues)):
                time_obj = datetime.strptime(timeslots[t], "%H:%M").time()

                if venues[v]["open"] <= time_obj <= venues[v]["close"]:
                    model.Add(
                        sum(x[s, t, v] for s in range(len(staff)))
                        >= venues[v]["min_staff"]
                    )
                else:
                    for s in range(len(staff)):
                        model.Add(x[s, t, v] == 0)

        for s in range(len(staff)):
            for t in range(len(timeslots)):
                model.Add(sum(x[s, t, v] for v in range(len(venues))) <= 1)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # -------------------------
        # CLEAN MANAGER TABLE ✅
        # -------------------------
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            st.subheader("📊 Manager Dashboard")

            table_data = []

            for t in range(len(timeslots)):
                row = {"Time": timeslots[t]}

                for v in range(len(venues)):
                    assigned = [
                        staff[s]
                        for s in range(len(staff))
                        if solver.Value(x[s, t, v]) == 1
                    ]

                    if len(assigned) >= venues[v]["min_staff"]:
                        row[venues[v]["name"]] = ", ".join(assigned)
                    else:
                        row[venues[v]["name"]] = "❌"

                table_data.append(row)

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)

            # -------------------------
            # STAFF VIEW
            # -------------------------
            st.subheader("🧑‍🤝‍🧑 Staff Schedules")

            for s in range(len(staff)):
                schedule_lines = []

                for t in range(len(timeslots)):
                    for v in range(len(venues)):
                        if solver.Value(x[s, t, v]) == 1:
                            schedule_lines.append(f"{timeslots[t]} → {venues[v]['name']}")

                st.write(f"**{staff[s]}**")
                if schedule_lines:
                    for line in schedule_lines:
                        st.write(line)
                else:
                    st.write("OFF")

        else:
            st.error("No feasible schedule found.")

        else:
            st.error("No feasible schedule found.")
