#!/usr/bin/env python3

from datetime import timedelta
import numpy as np
import pandas as pd

startday= pd.to_datetime("1/1/2021")
endday = pd.to_datetime("1/14/2021")

# generate arrival dates. 10**9 is to convert between ns and s
arrival= pd.DatetimeIndex(
        (10**9*np.random.randint(startday.value//10**9, endday.value//10**9, 2000))
    ).sort_values()
treatment = pd.DatetimeIndex(
    [s + timedelta(minutes=np.random.randint(5, 55)) for s in arrival]
)
finish = pd.DatetimeIndex(
    [s + timedelta(minutes=np.random.randint(15, 60)) for s in treatment]
)

waiting = treatment - arrival
df = pd.DataFrame(
    data={
        "arrival": arrival,
        "treatment": treatment,
        "finish": finish,
        "waiting": waiting,
    },
    index=arrival,
)

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
    df["waiting"].groupby([(idx := df["arrival"].dt).weekday, idx.hour]).mean()
)


arrival = [10.00, 10.15, 10,45, 11.30, 11.45, 12.15]
finish =  [10.30, 10.59, 11.45, 12.30, 12.45, 13.00]

load = {"10": 3+0, "11": 2+1, "12":1+2}
