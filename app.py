import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime, timedelta

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

selected_venue = st.selectbox("Select Venue", venue_options)
min_staff = st.number_input("Minimum Staff Needed", 1, 10, 2)

open_time = st.time_input("Open Time")
close_time = st.time_input("Close Time")

if "venues" not in st.session_state:
    st.session_state.venues = []

if st.button("➕ Add Venue"):
    st.session_state.venues.append({
        "name": selected_venue,
        "min_staff": min_staff,
        "open": open_time,
        "close": close_time
    })

st.subheader("📋 Current Venues")
for v in st.session_state.venues:
    st.write(
        f"{v['name']} | Staff: {v['min_staff']} | "
        f"{v['open'].strftime('%H:%M')} - {v['close'].strftime('%H:%M')}"
    )

# -------------------------
# GENERATE SCHEDULE
# -------------------------
if st.button("🚀 Generate Schedule"):

    venues = st.session_state.venues

    if len(venues) == 0:
        st.error("Please add at least one venue.")
    else:

        # -------------------------
        # CREATE HOURLY TIMESLOTS
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

        # -------------------------
        # CONSTRAINTS
        # -------------------------
        for t in range(len(timeslots)):
            for v in range(len(venues)):

                time_str = timeslots[t]
                time_obj = datetime.strptime(time_str, "%H:%M").time()

                if venues[v]["open"] <= time_obj <= venues[v]["close"]:
                    model.Add(
                        sum(x[s, t, v] for s in range(len(staff)))
                        >= venues[v]["min_staff"]
                    )
                else:
                    for s in range(len(staff)):
                        model.Add(x[s, t, v] == 0)

        # One job per time
        for s in range(len(staff)):
            for t in range(len(timeslots)):
                model.Add(sum(x[s, t, v] for v in range(len(venues))) <= 1)

        # -------------------------
        # SOLVE
        # -------------------------
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # -------------------------
        # OUTPUT: MANAGER TABLE
        # -------------------------
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            st.subheader("📊 Manager Schedule")

            # Table header
            header = ["Time"] + [v["name"] for v in venues]
            st.write(header)

            for t in range(len(timeslots)):
                row = [timeslots[t]]

                for v in range(len(venues)):
                    assigned = [
                        staff[s]
                        for s in range(len(staff))
                        if solver.Value(x[s, t, v]) == 1
                    ]

                    if len(assigned) >= venues[v]["min_staff"]:
                        cell = "✅ " + ", ".join(assigned)
                    else:
                        cell = "❌"

                    row.append(cell)

                st.write(row)

            # -------------------------
            # STAFF VIEW
            # -------------------------
            st.subheader("🧑‍🤝‍🧑 Staff Schedules")

            for s in range(len(staff)):
                st.write(f"### {staff[s]}")

                for t in range(len(timeslots)):
                    for v in range(len(venues)):
                        if solver.Value(x[s, t, v]) == 1:
                            st.write(f"{timeslots[t]} → {venues[v]['name']}")

        else:
            st.error("No feasible schedule found.")
