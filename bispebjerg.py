#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt
import matplotlib.dates as md


def pp(start: str, end: str, n: int):
    """Generate random datetime"""

    start: pd.Timestamp = pd.to_datetime(start)
    end: pd.Timestamp = pd.to_datetime(end)

    # convert to unix time. 10**9 is for datetimes default unit=ns
    start_u = start.value // 10 ** 9
    end_u = end.value // 10 ** 9

    # view-cast datetime64 to int64, for speedup.
    # datetime64 is a numpy type based on int64 so nothing is lost here
    return pd.DatetimeIndex(
        (10 ** 9 * np.random.randint(start_u, end_u, n, dtype=np.int64)).view("M8[ns]")
    ).sort_values()


# lets make some fake data during two weeks
# behandling is `ind + random amount of minutes between [5, 45[`
# ud is `behandling + random amount of minutes between [15, 60[`
start = "1/1/2021"
end = "1/14/2021"
ind = pp(start=start, end=end, n=2000)
behandling = pd.DatetimeIndex(
    [start + timedelta(minutes=random.randint(5, 55)) for start in ind]
)
ud = pd.DatetimeIndex(
    [start + timedelta(minutes=random.randint(15, 60)) for start in behandling]
)

# OR use the excel data. Remember to rename columns to "ind", "ud", "behandling"
bb = pd.read_excel("x.xlsx")

ventetid = behandling - ind
orig_df = pd.DataFrame(
    data={
        "ind": ind,
        "behandling": behandling,
        "ud": ud,
        "ventetid": ventetid,
    },
    index=ind,
)

print("\n\nthe untreated data looks like")
print(orig_df.head())

# create dataframes for each column
ind_df = pd.Series(range(len(ind)), index=ind)
behandling_df = pd.Series(range(len(ind)), index=behandling)
ud_df = pd.Series(range(len(ind)), index=ud)
ventetid_df = pd.DataFrame(data={"ventetid": ventetid}, index=ind)
ventetid_mean = ventetid_df.resample("1h").mean()


# create bins, start: first day of ind. end: last day of out + 1day
date_rng = pd.date_range(
    start=ind.min().date(), end=(ud.max().date() + timedelta(days=1)), freq="H"
)


# resample all data to 1h intervals and use the bins as index
df = pd.DataFrame(
    data={
        "ind": ind_df.resample("1h").count(),
        "behandling": behandling_df.resample("1h").count(),
        "ud": ud_df.resample("1h").count(),
    },
    index=date_rng,
).fillna(0)
df["ventetid"] = ventetid_mean

print(
    "\n\nthe data grouped by hourly bins (but not averaged over weekd) looks like this ",
)
print("\n", df.head())

# group all data into weekdays and then hours, get the hourly average during a week
df2 = pd.DataFrame(
    data={
        "ind": ind_df.groupby([(idx := ind_df.index).weekday, idx.hour]).count(),
        "ud": ud_df.groupby([(idx := ud_df.index).weekday, idx.hour]).count(),
        "behandling": behandling_df.groupby(
            [(idx := behandling_df.index).weekday, idx.hour]
        ).count(),
    },
).fillna(0)
df2["ventetid"] = ventetid_df.groupby(
    [(idx := ventetid_df.index).weekday, idx.hour]
).mean()

print(
    "\n\nthe data averaged over weeks and gruped by hourly bins looks like this ",
)
print("for the first hours of the first day")
print("\n", df2.head())


# Note we take the statistics of Ventetid before it ois averaged over weeks
print(f"\nStatistik for ventetid i minutter")
print((df["ventetid"] / pd.Timedelta(minutes=1)).describe())
# The difference between dividing with pd.Timedelta(minutes=1) and
# .astype("timedelta64[m]") is that the latter just uses floor() on the numbers
# print(df["ventetid"].astype("timedelta64[m]").describe())

## histogram of ventetider
plt.figure()
(df["ventetid"] / pd.Timedelta(minutes=1)).hist(bins=range(5, 45))
# alternative way
# ventetid_mean.astype("timedelta64[m]").hist()
plt.xlabel("ventetid (min)")
plt.ylabel("frekvens")
plt.title("Histogram over ventetider")
plt.tight_layout()
plt.savefig("fig/ventetid_hist.png")

## ventetider during the week
plt.figure()

# two ways of plotting -- either just show minutes on the y-axis
# (df["ventetid"] / pd.Timedelta(minutes=1)).plot()

# OR convert timedelta to datetime. This gives all ventetider a date of
# 1/1/1970 but we only care about the %H:%M:%S so it doesn't matter
pd.to_datetime((df["ventetid"] / pd.Timedelta(minutes=1)), unit="m").plot()
plt.xlabel("dato")
plt.ylabel("ventetid (min)")
plt.title("Ventetid i gennemsnit over hver time")

xfmt = md.DateFormatter("%H:%M:%S")
ax = plt.gca()
ax.yaxis.set_major_formatter(xfmt)
plt.tight_layout()
plt.savefig("fig/ventetid_average_hourly.png")

# plot hourly average ventetid per weekday
plt.figure()

for day in range(7):
    pd.to_datetime((df2["ventetid"].xs(day) / pd.Timedelta(minutes=1)), unit="m").plot()

plt.xlabel("Time på dagen")
plt.ylabel("ventetid (min)")
plt.title("Ventetid i gennemsnit over hver time")
plt.legend(["mon", "tue", "wed", "thur", "fri", "sat", "sun"])

ax = plt.gca()
ax.yaxis.set_major_formatter(xfmt)

plt.tight_layout()
plt.savefig("fig/ventetid_average_week.png")


plt.show()
# plt.show(block=False)

# print(df[df.index.day == 1])
