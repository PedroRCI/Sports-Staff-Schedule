import streamlit as st
from ortools.sat.python import cp_model

st.title("🚢 Cruise Sports Scheduler")

staff = st.text_area(
    "Enter Staff (one per line)",
    "Alice\nBob\nCarlos\nDiana"
).split("\n")

venues_input = st.text_area(
    "Enter Venues (name,min staff,open,close)",
    "Basketball,2,09:00,17:00\nPool Games,2,10:00,18:00"
)
``

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

            # collect times
            all_times.add(open_time)
            all_times.add(close_time)

        except:
            st.warning(f"Invalid line: {line}")

# create sorted timeslots
timeslots = sorted(all_times)

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
``
