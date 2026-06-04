import streamlit as st
from ortools.sat.python import cp_model

st.title("🚢 Cruise Sports Scheduler")

# -------------------------
# STAFF INPUT
# -------------------------
staff = st.text_area(
    "Enter Staff (one per line)",
    "Alice\nBob\nCarlos\nDiana"
).split("\n")

# -------------------------
# VENUE BUILDER UI
# -------------------------
st.subheader("🏟️ Add Venues")

venue_options = ["Basketball", "Pool Games", "Soccer", "Tennis", "Volleyball"]

selected_venue = st.selectbox("Select Venue", venue_options)
min_staff = st.number_input("Minimum Staff Needed", min_value=1, max_value=10, value=2)

open_time = st.time_input("Open Time")
close_time = st.time_input("Close Time")

# Store venues
if "venues" not in st.session_state:
    st.session_state.venues = []

# Add venue button
if st.button("➕ Add Venue"):
    st.session_state.venues.append({
        "name": selected_venue,
        "min_staff": min_staff,
        "open": open_time.strftime("%H:%M"),
        "close": close_time.strftime("%H:%M")
    })

# Show current venues
st.subheader("📋 Current Venues")
for v in st.session_state.venues:
    st.write(v)

# -------------------------
# GENERATE SCHEDULE
# -------------------------
if st.button("🚀 Generate Schedule"):

    venues = st.session_state.venues

    if len(venues) == 0:
        st.error("Please add at least one venue.")
    else:

        # Collect times
        all_times = set()
        for v in venues:
            all_times.add(v["open"])
            all_times.add(v["close"])

        timeslots = sorted(all_times)

        model = cp_model.CpModel()

        # Variables
        x = {}
        for s in range(len(staff)):
            for t in range(len(timeslots)):
                for v in range(len(venues)):
                    x[s, t, v] = model.NewBoolVar(f"x_{s}_{t}_{v}")

        # Constraints
        for t in range(len(timeslots)):
            for v in range(len(venues)):
                time = timeslots[t]

                if venues[v]["open"] <= time <= venues[v]["close"]:
                    model.Add(
                        sum(x[s, t, v] for s in range(len(staff)))
                        >= venues[v]["min_staff"]
                    )
                else:
                    for s in range(len(staff)):
                        model.Add(x[s, t, v] == 0)

        # One job per person per time
        for s in range(len(staff)):
            for t in range(len(timeslots)):
                model.Add(sum(x[s, t, v] for v in range(len(venues))) <= 1)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # -------------------------
        # OUTPUT
        # -------------------------
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            st.subheader("📊 Manager View")

            for t in range(len(timeslots)):
                st.write(f"### {timeslots[t]}")
                for v in range(len(venues)):
                    assigned = [
                        staff[s]
                        for s in range(len(staff))
                        if solver.Value(x[s, t, v]) == 1
                    ]
                    st.write(f"{venues[v]['name']}: {assigned}")

            st.subheader("🧑‍🤝‍🧑 Staff Schedules")

            for s in range(len(staff)):
                st.write(f"### {staff[s]}")
                for t in range(len(timeslots)):
                    for v in range(len(venues)):
                        if solver.Value(x[s, t, v]) == 1:
                            st.write(f"{timeslots[t]} → {venues[v]['name']}")

        else:
            st.error("No feasible schedule found.")
