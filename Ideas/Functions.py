# Functions from other stuff
import json
import os
from datetime import datetime
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import requests


def addAverage(dt: pd.DataFrame) -> pd.DataFrame:
    """Adds a col "average" to the Pandas Dataframe passed in

    Args:
        dt (Dataframe): The Dataframe to be modified

    Returns:
        Dataframe: The modified Dataframe
    """
    # the volumes will still be there to calculate an average
    average = []
    for time in dt.values:
        # averageVal = (time['lowPriceVolume']*time['avgLowPrice'] + time['highPriceVolume']*time['avgHighPrice']) / (time['lowPriceVolume'] + time['highPriceVolume'])
        averageVal = (time[3] * time[1] + time[2] * time[0]) / (time[3] + time[2])
        if np.isnan(averageVal):
            if time[0] == time[1]:
                # uh oh
                continue
            elif np.isnan(time[0]):
                averageVal = time[1]
            elif np.isnan(time[1]):
                averageVal = time[0]
        average.append(averageVal)
    dt["average"] = average
    return dt


def getTimeSeries(name: str, timestep: str) -> pd.Series:
    """Returns a Datetime formated Pandas Series of an item

    Args:
        name (str): The name of the item
        timestep (str): The timestep (e.g. "5m", "1h", "6h")

    Returns:
        pd.Series: A Datetime formated Pandas Series of an item
    """
    data = getDT(name, timestep)
    data.drop(columns=["avgHighPrice", "avgLowPrice"], inplace=True)
    data = data.reset_index()
    ser = pd.Series(data["average"].array, pd.to_datetime(data["timestamp"]))
    return ser


def getDT(name: str, timestep: str) -> pd.DataFrame:
    """Returns a Datetime formated Pandas Dataframe of an item

    Args:
        name (str): The name of the item
        timestep (str): The timestep (e.g. "5m", "1h", "6h")

    Returns:
        pd.DataFrame: A Datetime formated Pandas Dataframe of an item
    """
    url = "https://prices.runescape.wiki/api/v1/osrs"
    # we want the latest data, so lets add that to the url
    url += "/timeseries?timestep="
    url += timestep
    url += "&id="
    # lets add the abyssal whip to the url:
    url += str(NameToID(name))

    headers = {
        # the wiki blocks all common user-agents in order to prevent spam
        # after talking with some of the API maintainers over discord they asked me to include my discord in the user-agent
        "User-Agent": "DateTimeHelper - @Be#9998",
    }
    req = Request(url, headers=headers)
    with urlopen(req) as response:
        latestData = response.read()
    data = json.loads(latestData)

    for date in data["data"]:
        date["timestamp"] = datetime.utcfromtimestamp(date["timestamp"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    data = data["data"]

    dt_pandas = pd.DataFrame(data)
    dt_pandas = dt_pandas.set_index("timestamp")
    # dt_pandas.dropna(inplace=True)
    dt_pandas = addAverage(dt_pandas)
    dt_pandas.drop(columns=["lowPriceVolume", "highPriceVolume"], inplace=True)
    return dt_pandas


def NameToID(name: str) -> int:
    """Returns the ID the Name represents

    Args:
        name (str): The name

    Returns:
        int: The id
    """
    return name_dict[name]


def IdToName(id: int) -> str:
    """Returns the Name the ID represents

    Args:
        id (int): The id

    Returns:
        str : The name
    """
    return id_dict[id]


# This function will update the locally stored JSON
def UpdateJson():
    """Updates the locally stored JSON"""
    url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
    # we want the latest data, so lets add that to the url

    headers = {
        # the wiki blocks all common user-agents in order to prevent spam
        # after talking with some of the API maintainers over discord they asked me to include my discord in the user-agent
        "User-Agent": "Item_ID_Helper_Functions - @Be#9998",
    }

    response_json = requests.get(url, headers=headers).text
    try:
        f = open("Data/NameIDMap.json", "w")
    except:
        os.mkdir("Data")
        f = open("Data/NameIDMap.json", "w")
    import json

    mydata = json.loads(response_json)
    f.write(json.dumps(mydata, indent=4))
    f.close()


# Creating df with json data instead of calling the API
# this is to lower the amount of calls needed for this helper function!
try:
    mapping_df = pd.read_json("Data/NameIDMap.json")
    # we are going to drop the useless cols that we wont be needing
    mapping_df = mapping_df.drop(
        columns=["examine", "lowalch", "limit", "value", "highalch", "icon", "members"]
    )
    name_dict = mapping_df.set_index("name")["id"].to_dict()
    id_dict = mapping_df.set_index("id")["name"].to_dict()
except:
    UpdateJson()
