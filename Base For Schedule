import streamlit as st
from ortools.sat.python import cp_model

st.title("🚢 Cruise Sports Scheduler")

staff = st.text_area(
    "Enter Staff (one per line)",
    "Alice\nBob\nCarlos\nDiana"
).split("\n")

venues_input = st.text_area(
    "Enter Venues (name,min staff)",
    "Basketball,2\nPool Games,2"
)

venues = []
for line in venues_input.split("\n"):
    name, min_staff = line.split(",")
    venues.append({"name": name, "min_staff": int(min_staff)})

timeslots = ["09:00", "13:00", "17:00"]

if st.button("Generate Schedule"):

    model = cp_model.CpModel()

    x = {}
    for s in range(len(staff)):
        for t in range(len(timeslots)):
            for v in range(len(venues)):
                x[s, t, v] = model.NewBoolVar(f"x_{s}_{t}_{v}")

    for t in range(len(timeslots)):
        for v in range(len(venues)):
            model.Add(sum(x[s, t, v] for s in range(len(staff))) >= venues[v]["min_staff"])

    for s in range(len(staff)):
        for t in range(len(timeslots)):
            model.Add(sum(x[s, t, v] for v in range(len(venues))) <= 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

        st.subheader("📊 Schedule")

        for t in range(len(timeslots)):
            st.write(f"### {timeslots[t]}")
            for v in range(len(venues)):
                assigned = [
                    staff[s]
                    for s in range(len(staff))
                    if solver.Value(x[s, t, v]) == 1
                ]
                st.write(f"{venues[v]['name']}: {assigned}")
    else:
        st.error("No schedule possible")
