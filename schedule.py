#!/usr/bin/env python

import os
import csv
import datetime
from volunteers import volunteers

conf_date = datetime.datetime(2021, 2, 20)

f = open("data.csv", "r")
reader = csv.reader(f, delimiter="\t")

headers = ["Staff", "T-0", "Role", "Stage", "Duration", "QA", "Title"]

talks = {}

interactive = []
prerecorded = []

interactive_schedule = []
prerecorded_schedule = []

talk_speakers = []

def get_volunteer(row, duty):
    if duty == "QA Session Chair":
        if row["Stage"] == "Interactive":
            shift = "PM"
        else:
            shift = conf_date + datetime.timedelta(hours=13, minutes=30)
            if row["T-0"] <= shift:
                shift = "AM"
            else:
                shift = "PM"
    else:
        shift = conf_date + datetime.timedelta(hours=13, minutes=45)
        if row["T-0"] <= shift:
            shift = "AM"
        else:
            shift = "PM"
    volunteer = volunteers[duty][row["Stage"]][shift]
    return volunteer

for row in reader:
    row = dict(zip(headers, row))

    if not row["T-0"]:
        continue
    t = datetime.datetime.strptime(row["T-0"], "%I:%M %p")
    row["T-0"] = conf_date + datetime.timedelta(hours=t.hour, minutes=t.minute)
    row["Duration"] = int(row["Duration"])
    row["QA"] = row["QA"] == "TRUE"

    talks[row["Stage"]] = talks.get(row["Stage"], {})
    talks[row["Stage"]][row["T-0"]] = talks[row["Stage"]].get(row["T-0"], {
        "Emcee": None,
    })

    talks[row["Stage"]][row["T-0"]][row["Role"]] = talks[row["Stage"]][row["T-0"]].get(row["Role"], [])

    talks[row["Stage"]][row["T-0"]][row["Role"]].append(
        row["Staff"]
    )
    talks[row["Stage"]][row["T-0"]]["Emcee"] = get_volunteer(row, "Session Chair")

    talk_speakers.append(row["Staff"])

    if row["Stage"] == "Interactive":
        interactive.append(row)
    else:
        prerecorded.append(row)

t_90s = []
t_60s = []


def gen_schedule(row):
    entries = []

    speakers = talks[row["Stage"]][row["T-0"]].get("Speaker", [])
    panelists = talks[row["Stage"]][row["T-0"]].get("Panelist", [])
    chairs = talks[row["Stage"]][row["T-0"]].get("Chair", [])

    # Anyone who doesn't require a T-90 or T-60 check
    no_t_90 = []
    no_t_60 = []

    if row["Duration"] == 30:
        t_15_delta = datetime.timedelta(minutes=10)
    else:
        t_15_delta = datetime.timedelta(minutes=15)

    # Speaker Wrangler - T-90
    if row["Staff"] not in no_t_90 and row["Staff"] not in t_90s:
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=90),
            get_volunteer(row, "Speaker Wrangler"),
            "(T-90) Verify {staff} is online".format(
                volunteer=get_volunteer(row, "Speaker Wrangler"),
                staff=row["Staff"],
            ),
            row["Stage"],
        ])

        # Speaker - T-90
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=90),
            row["Staff"],
            "(T-90) Make sure you are online in the PyCascades Slack",
            row["Stage"],
        ])

        t_90s.append(row["Staff"])

    if row["Staff"] not in no_t_90 and row["Staff"] not in t_90s:
        if len(panelists + chairs) == 0:
            entries.append([
                row["T-0"] - datetime.timedelta(minutes=90),
                get_volunteer(row, "Speaker Wrangler"),
                "(T-90) Verify {staff} is online".format(
                    volunteer=get_volunteer(row, "Speaker Wrangler"),
                    staff=get_volunteer(row, "QA Session Chair"),
                ),
                row["Stage"],
            ])

        # Session Chair - T-90
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=90),
            get_volunteer(row, "QA Session Chair"),
            "(T-90) Make sure you are online in the PyCascades Slack",
            row["Stage"],
        ])

        t_90s.append(get_volunteer(row, "QA Session Chair"))

    # Tech Check - T-60
    if row["Staff"] not in no_t_60 and row["Staff"] not in t_60s:
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=60),
            get_volunteer(row, "T-60"),
            "Run T-60 for {staff}".format(
                staff=row["Staff"],
            ),
            row["Stage"],
        ])

        # Speaker Wrangler - T-60
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=60),
            get_volunteer(row, "Speaker Wrangler"),
            "(T-60) {staff} Tech Check".format(
                volunteer=get_volunteer(row, "Speaker Wrangler"),
                staff=row["Staff"],
            ),
            row["Stage"],
        ])

        t_60s.append(row["Staff"])

    if len(panelists + chairs) == 0 and get_volunteer(row, "Session Chair") not in t_60s:
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=60),
            get_volunteer(row, "T-60"),
            "Run T-60 for {staff}".format(
                staff=get_volunteer(row, "Session Chair"),
            ),
            row["Stage"],
        ])

        entries.append([
            row["T-0"] - datetime.timedelta(minutes=60),
            get_volunteer(row, "Speaker Wrangler"),
            "(T-60) {staff} Tech Check".format(
                volunteer=get_volunteer(row, "Speaker Wrangler"),
                staff=get_volunteer(row, "Session Chair"),
            ),
            row["Stage"],
        ])

        t_60s.append(get_volunteer(row, "Session Chair"))

    # Speaker - T-60
    if row["Staff"] not in no_t_60:
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=60),
            row["Staff"],
            "(T-60) Head to Tech Check".format(
                staff=row["Staff"],
            ),
            row["Stage"],
        ])

    # Session Chair - T-60
    if len(panelists + chairs) == 0:
        entries.append([
            row["T-0"] - datetime.timedelta(minutes=60),
            get_volunteer(row, "Session Chair"),
            "(T-60) Head to Tech Check".format(
                staff=get_volunteer(row, "Session Chair"),
            ),
            row["Stage"],
        ])

    # Speaker Wrangler - T-15
    entries.append([
        row["T-0"] - t_15_delta,
        get_volunteer(row, "Speaker Wrangler"),
        "(T-15) {staff} to Streamyard".format(
            volunteer=get_volunteer(row, "Speaker Wrangler"),
            staff=row["Staff"],
            stage=row["Stage"],
        ),
        row["Stage"],
    ])

    if len(panelists + chairs) == 0:
        entries.append([
            row["T-0"] - t_15_delta,
            get_volunteer(row, "Speaker Wrangler"),
            "(T-15) {staff} to Streamyard".format(
                volunteer=get_volunteer(row, "Speaker Wrangler"),
                staff=get_volunteer(row, "Session Chair"),
                stage=row["Stage"],
            ),
            row["Stage"],
        ])

    # Speaker - T-15
    entries.append([
        row["T-0"] - t_15_delta,
        row["Staff"],
        "(T-15) Join Streamyard".format(
            staff=row["Staff"],
            stage=row["Stage"],
        ),
        row["Stage"],
    ])

    # Session Chair - T-15
    if len(panelists + chairs) == 0:
        entries.append([
            row["T-0"] - t_15_delta,
            get_volunteer(row, "Session Chair"),
            "(T-15) Join Streamyard".format(
                staff=get_volunteer(row, "Session Chair"),
                stage=row["Stage"],
            ),
            row["Stage"],
        ])

    # Speaker - T-0
    t_0 = row["T-0"]
    if row["Title"] == "Core Python Devs on how COVID has changed core Python development":
        t_0 += datetime.timedelta(minutes=15)
    if row["Staff"] in panelists:
        entries.append([
            t_0,
            row["Staff"],
            "(T-0) Live on {stage} stage as panelist for {speakers}.".format(
                staff=row["Staff"],
                stage=row["Stage"],
                speakers=", ".join(speakers)
            ),
            row["Stage"],
        ])
    else:
        entries.append([
            t_0,
            row["Staff"],
            "(T-0) Live on {stage} stage for '{talk}'.".format(
                staff=row["Staff"],
                stage=row["Stage"],
                speakers=", ".join(speakers),
                talk=row["Title"],
            ),
            row["Stage"],
        ])

    # Session Chair - T-0
    if len(panelists + chairs) == 0:
        entries.append([
            t_0,
            get_volunteer(row, "Session Chair"),
            "(T-0) Live on {stage} Stage to Introduce {speakers}".format(
                staff=get_volunteer(row, "Session Chair"),
                stage=row["Stage"],
                speakers=", ".join(speakers)
            ),
            row["Stage"],
        ])

    # Session Chair - T+<duration - 10>
    if len(panelists + chairs) == 0:
        entries.append([
            t_0 + datetime.timedelta(minutes=row["Duration"] - 10),
            get_volunteer(row, "Session Chair"),
            "Reminder to be ready to go Live for Outro".format(
                staff=get_volunteer(row, "Session Chair"),
                stage=row["Stage"],
                speakers=", ".join(speakers)
            ),
            row["Stage"],
        ])

    # Speaker Wrangler - T+<duration> (Q/A)
    if row["QA"]:
        entries.append([
            row["T-0"] + datetime.timedelta(minutes=row["Duration"] - 15),
            get_volunteer(row, "Speaker Wrangler"),
            "Make sure {staff} is in {track} Track Discussions".format(
                duration=row["Duration"] - 15,
                staff=get_volunteer(row, "QA Session Chair"),
                track=row["Stage"],
            ),
            "{track} Track Discussions".format(track=row["Stage"]),
        ])

    # Speaker - T+<duration> (Q/A)
    if row["QA"]:
        entries.append([
            row["T-0"] + datetime.timedelta(minutes=row["Duration"]),
            row["Staff"],
            "Join \"{track} Track Discussions\" room for Q/A".format(
                duration=row["Duration"],
                staff=row["Staff"],
                track=row["Stage"],
            ),
            "{track} Track Discussions".format(track=row["Stage"]),
        ])

    # Session Chair - T+<duration> (Q/A)
    if len(panelists + chairs) == 0:
        if row["QA"]:
            entries.append([
                row["T-0"] + datetime.timedelta(minutes=row["Duration"] - 5),
                get_volunteer(row, "QA Session Chair"),
                "Join \"{track} Track Discussions\" room for Q/A".format(
                    duration=row["Duration"],
                    staff=get_volunteer(row, "QA Session Chair"),
                    track=row["Stage"],
                ),
                "{track} Track Discussions".format(track=row["Stage"]),
            ])

    for entry in entries:
        headers = ["time", "staff", "message", "stage"]
        entry = dict(zip(headers, entry))
        {
            "Interactive": interactive_schedule,
            "Prerecorded": prerecorded_schedule,
        }.get(row["Stage"], []).append(entry)

for speaker in interactive:
    gen_schedule(speaker)

for speaker in prerecorded:
    gen_schedule(speaker)

full_schedule = interactive_schedule + prerecorded_schedule
staff = list(set([x["staff"] for x in full_schedule]))


def render_schedule(schedule, initial_tech_check_only=True, names=False):
    tech_checked = False
    individual_schedule = []
    for entry in sorted(schedule, key=lambda x: x['time']):
        is_tech_check = False
        if "T-60" in entry["message"]:
            is_tech_check = True

        if is_tech_check and tech_checked and initial_tech_check_only:
            continue

        if names:
            individual_schedule.append("{time}\t{staff}: {message}\n".format(
                staff=entry["staff"],
                time=entry["time"].strftime("%I:%M %p"),
                message=entry["message"],
            ))
        else:
            individual_schedule.append("{time}\t{message}\n".format(
                time=entry["time"].strftime("%I:%M %p"),
                message=entry["message"],
            ))
        tech_checked = tech_checked or is_tech_check

    # Deduplicate talks with multiple speakers
    individual_schedule = list(set(individual_schedule))
    return individual_schedule


def final_sort(entries):
    return sorted([
        x for x in entries],
        key=lambda x: datetime.datetime.strptime(x.split("\t")[0], "%I:%M %p")
    )

def write_header(f, header):
    f.write("PyCascades 2021 - {date}\n{header}\n\n".format(
        date=conf_date.strftime("%A %B %d, %Y"),
        header=header,
    ))
    f.write("ALL TIMES ARE US/PACIFIC\n\n")

dirs = [
    "schedules",
    "schedules/speakers",
    "schedules/volunteers",
]
for directory in dirs:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Individual Schedules
t_60 = [
    volunteers["T-60"]["Interactive"]["AM"],
    volunteers["Speaker Wrangler"]["Interactive"]["AM"],
    volunteers["Speaker Wrangler"]["Prerecorded"]["AM"],
]
tech_checked = []
for person in staff:
    print("Generating schedule for {person}".format(person=person))
    filtered_schedule = [x for x in full_schedule if x["staff"] == person]

    individual_schedule = render_schedule(filtered_schedule, person not in t_60)

    folder_name = "volunteers"
    if person in talk_speakers:
        folder_name = "speakers"
    with open("schedules/{folder}/{staff}.txt".format(folder=folder_name, staff=person), "w+") as f:
        write_header(f, "Schedule for {person}".format(person=person))
        for entry in final_sort(individual_schedule):
            if person in t_60:
                f.write("* " + entry)
            elif "T-60" in entry and person in tech_checked:
                continue
            else:
                f.write("* " + entry)
            if "T-60" in entry:
                tech_checked.append(person)

# Stage Schedules
stages = list(set([x["stage"] for x in full_schedule]))
for stage in stages:
    print("Generating schedule for {stage} Track".format(stage=stage))
    filtered_schedule = [x for x in full_schedule if x["stage"] == stage]

    individual_schedule = render_schedule(filtered_schedule, False, True)

    with open("schedules/{stage}.txt".format(stage=stage), "w+") as f:
        write_header(f, "Full schedule for {stage} Track".format(stage=stage))
        for entry in final_sort(individual_schedule):
            f.write("* " + entry)

# Master Schedule
print("Generating Master Schedule")

individual_schedule = render_schedule(full_schedule, False, True)

with open("schedules/Final.txt", "w+") as f:
    write_header(f, "Full conference schedule")
    for entry in final_sort(individual_schedule):
        f.write("* " + entry)
