import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from ..datasets import CityLimits, EPSG

__all__ = ["shuffle_locations", "shuffle_times", "get_random_data"]


def shuffle_times(data):
    """
    Return a copy of the input data with shuffled times.

    Notes
    -----
    Shuffle the `time_offset` column.

    Parameters
    ----------
    data : pandas.DataFrame
        the sales/homicides data

    Returns
    -------
    pandas.DataFrame :
        a copy of the input data with the shuffled `time_offset` column
    """
    return data.copy().assign(
        time_offset=np.random.permutation(data.time_offset.values)
    )


def shuffle_locations(data):
    """
    Return a copy of the input data with shuffled locations.

    Notes
    -----
    Shuffle the `geometry` column.

    Parameters
    ----------
    data : pandas.DataFrame
        the sales/homicides data

    Returns
    -------
    pandas.DataFrame :
        a copy of the input data with the shuffled `geometry` column
    """
    return data.copy().assign(geometry=np.random.permutation(data.geometry.values))


def get_random_data(data, location=True, time=True):
    """
    Randomize the input data, both the times and locations.

    Notes
    -----
    This randomizes the `geometry` and `time_offset` columns.

    Parameters
    ----------
    data : pandas.DataFrame
        the sales/homicides data

    Returns
    -------
    pandas.DataFrame :
        a copy of the input data with the `time_offset` and `geometry` columns 
    """
    out = data.copy()

    # the number to generate
    total = len(data)

    if location:

        # city limits
        limits = CityLimits.get().iloc[0].geometry
        min_x, min_y, max_x, max_y = limits.bounds

        A = (max_x - min_x) * (max_y - min_y)
        N = total * (1 + (A - limits.area) / A + 1.0)

        x = np.random.uniform(min_x, max_x, int(N))
        y = np.random.uniform(min_y, max_y, int(N))

        points = gpd.GeoDataFrame(
            {"geometry": [Point(x, y) for x, y in zip(x, y)]}, crs=data.crs
        )

        geo = gpd.sjoin(points, CityLimits.get(), op="within")
        assert len(geo) > total
        geo = geo["geometry"].sample(n=total)

        out["geometry"] = geo.values

    if time:

        # get random time
        min_time = data.time_offset.min()
        max_time = data.time_offset.max()
        time_offset = np.random.uniform(min_time, max_time, total)

        out["time_offset"] = np.random.uniform(min_time, max_time, total)

    return out
