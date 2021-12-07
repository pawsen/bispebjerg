#!/usr/bin/env python3

from datetime import timedelta, datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md


"""
Example of load calculation
arrival = [10.00, 10.15, 10,45, 11.30, 11.45, 12.15]
finish =  [10.30, 10.59, 11.45, 12.30, 12.45, 13.00]

load = {"10": 3+0, "11": 2+1, "12":1+2}
"""

startday = pd.to_datetime("1/1/2021")
endday = pd.to_datetime("1/14/2021")

# generate arrival dates. 10**9 is to convert between ns and s
arrival = pd.DatetimeIndex(
    (
        10 ** 9
        * np.random.randint(startday.value // 10 ** 9, endday.value // 10 ** 9, 2000)
    )
).sort_values()
treatment = pd.DatetimeIndex(
    [s + timedelta(minutes=np.random.randint(5, 55)) for s in arrival]
)
finish = pd.DatetimeIndex(
    [s + timedelta(minutes=np.random.randint(15, 60)) for s in treatment]
)

waiting = (treatment - arrival).round("S")
df = pd.DataFrame(
    data={
        "arrival": arrival,
        "treatment": treatment,
        "finish": finish,
        "waiting": waiting,
    },
    index=arrival,
)

df["arrival_date_hour"] = df.arrival.apply(lambda x: x.strftime("%y-%m-%d %H"))
df["finish_date_hour"] = df.finish.apply(lambda x: x.strftime("%y-%m-%d %H"))

# group into hourly bins over one week
df2 = pd.DataFrame(
    data={
        "arrival": df["arrival"]
        .groupby([(idx := df["arrival"].dt).weekday, idx.hour])
        .count(),
        "treatment": df["treatment"]
        .groupby([(idx := df["treatment"].dt).weekday, idx.hour])
        .count(),
        "finish": df["finish"]
        .groupby([(idx := df["finish"].dt).weekday, idx.hour])
        .count(),
    },
).fillna(0)
# fillna fails if waiting is added
df2["waiting"] = (
    df["waiting"]
    .groupby([(idx := df["arrival"].dt).weekday, idx.hour])
    .mean()
    .round("S")
)

# calculate load
df["arrival_date_hour"] = df.arrival.apply(lambda x: x.strftime("%y-%m-%d %H"))
df["finish_date_hour"] = df.finish.apply(lambda x: x.strftime("%y-%m-%d %H"))

result_df = pd.DataFrame(
    {"arrival_date_hour": df.arrival_date_hour.unique(), "load": None}
).set_index("arrival_date_hour")

for datehour in df.arrival_date_hour.unique():
    load = df[
        (df.finish_date_hour >= datehour) & (df.arrival_date_hour <= datehour)
    ].shape[0]
    result_df.loc[datehour] = load

# mean of load based on weekday and hour
result_df.reset_index(inplace=True)
result_df["arrival_date_hour"] = result_df.arrival_date_hour.apply(
    datetime.strptime, args=["%y-%m-%d %H"]
)
result_df["hour"] = result_df.arrival_date_hour.apply(lambda x: x.hour)
result_df["weekday"] = result_df.arrival_date_hour.apply(datetime.weekday)

df2["load"] = result_df.groupby(["weekday", "hour"]).load.mean()

print("\nData averaged over weeks per hour:")
print(df2.head(25))

# Note we take the statistics of Waiting before it ois averaged over weeks
print(f"\nStatistik for waiting i minutter")
print((df["waiting"] / pd.Timedelta(minutes=1)).describe())
# The difference between dividing with pd.Timedelta(minutes=1) and
# .astype("timedelta64[m]") is that the latter just uses floor() on the numbers
# print(df["waiting"].astype("timedelta64[m]").describe())

## histogram of waitinger
plt.figure()
(df["waiting"] / pd.Timedelta(minutes=1)).hist(bins=range(5, 45))
# alternative way
# waiting_mean.astype("timedelta64[m]").hist()
plt.xlabel("waiting (min)")
plt.ylabel("frekvens")
plt.title("Histogram over ventetid")
plt.tight_layout()
plt.savefig("fig/waiting_hist.png")

## waitinger during the week
plt.figure()

# two ways of plotting -- either just show minutes on the y-axis
# (df["waiting"] / pd.Timedelta(minutes=1)).plot()

# OR convert timedelta to datetime. This gives all waitinger a date of
# 1/1/1970 but we only care about the %H:%M:%S so it doesn't matter
pd.to_datetime((df["waiting"] / pd.Timedelta(minutes=1)), unit="m").plot()
plt.xlabel("dato")
plt.ylabel("waiting (min)")
plt.title("Ventetid i gennemsnit over hver time")

xfmt = md.DateFormatter("%H:%M:%S")
ax = plt.gca()
ax.yaxis.set_major_formatter(xfmt)
ax.set_ylim(bottom=0)
plt.tight_layout()
plt.savefig("fig/waiting_average_hourly.png")

# plot hourly average waiting per weekday
plt.figure()

for day in range(7):
    pd.to_datetime((df2["waiting"].xs(day) / pd.Timedelta(minutes=1)), unit="m").plot()

plt.xlabel("Time på dagen")
plt.ylabel("waiting (min)")
plt.title("Waiting i gennemsnit over hver time")
plt.legend(["mon", "tue", "wed", "thur", "fri", "sat", "sun"])

ax = plt.gca()
ax.yaxis.set_major_formatter(xfmt)
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("fig/waiting_average_week.png")


plt.show()
# plt.show(block=False)

# print(df[df.index.day == 1])
