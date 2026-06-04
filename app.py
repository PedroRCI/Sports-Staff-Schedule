import streamlit as st
from ortools.sat.python import cp_model

st.title("🚢 Cruise Sports Scheduler")

# -------------------------
# INPUTS
# -------------------------
staff = st.text_area(
    "Enter Staff (one per line)",
    "Alice\nBob\nCarlos\nDiana"
).split("\n")

venues_input = st.text_area(
    "Enter Venues (name,min staff,open,close)",
    "Basketball,2,09:00,17:00\nPool Games,2,10:00,18:00"
)

# -------------------------
# PARSE VENUES
# -------------------------
venues = []
all_times = set()

for line in venues_input.split("\n"):
    parts = line.split(",")

    if len(parts) == 4:
        name = parts[0].strip()

        try:
            min_staff = int(parts[1].strip())
            open_time = parts[2].strip()
            close_time = parts[3].strip()

            venues.append({
                "name": name,
                "min_staff": min_staff,
                "open": open_time,
                "close": close_time
            })

            all_times.add(open_time)
            all_times.add(close_time)

        except:
            st.warning(f"Invalid line: {line}")

timeslots = sorted(all_times)

# -------------------------
# GENERATE BUTTON
# -------------------------
if st.button("Generate Schedule"):

    # ✅ CREATE MODEL (this fixes your error)
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

            time = timeslots[t]

            if venues[v]["open"] <= time <= venues[v]["close"]:
                model.Add(
                    sum(x[s, t, v] for s in range(len(staff)))
                    >= venues[v]["min_staff"]
                )
            else:
                for s in range(len(staff)):
                    model.Add(x[s, t, v] == 0)

    # Each person only one job at a time
    for s in range(len(staff)):
        for t in range(len(timeslots)):
            model.Add(sum(x[s, t, v] for v in range(len(venues))) <= 1)

    # -------------------------
    # SOLVE
    # -------------------------
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
