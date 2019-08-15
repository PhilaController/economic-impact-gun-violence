import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

FT_PER_MILE = 5280
SECONDS_PER_DAY = 60 * 60 * 24

__all__ = ["knn_distance", "add_spacetime_flags", "FT_PER_MILE", "SECONDS_PER_DAY"]


def knn_distance(homicides, sales, radius):
    """
    Find all neighbors within a given distance.

    Parameters
    ----------
    homicides : GeoDataFrame
        the homicide data
    sales : GeoDataFrame
        the sale data
    radius : float
        the distance (in feet) to search within

    Returns
    -------
    dist : list of arrays, shape is (n_homicides,)
        for every homicide, the distances to all neighboring sales
    ind : array
        for every homicide, the index of the neighboring sales
    """
    nbrs = NearestNeighbors(radius=radius, algorithm="ball_tree").fit(sales)
    return nbrs.radius_neighbors(homicides)


def _get_sale_groups_by_homicide(homicides, sales, space_radius, time_window):
    """
    Internal function to do the sales that satisfy the distance/time constraints
    for every homicide.

    Yields the homicide number, array of time offsets, and 
    before/after indices and distances.

    Returns
    -------
    i : int
        the integer index specifying the homicide number
    dt : array_like
        the difference in times: sale times - homicide time
    indices : tuple
        tuple of (before, after) specifying indices in sale data frame for those sales
        occurring before/after homicide
    dists : tuple
        tuple of (before, after) specifying distances for those sales
        occurring before/after homicide
    """
    # check for missing geometries
    assert sales.geometry.isnull().sum() == 0
    assert homicides.geometry.isnull().sum() == 0

    # check for columns
    assert "time_offset" in sales.columns
    assert "time_offset" in homicides.columns

    # extract out x and y coordinates
    salesXY = np.vstack([sales.geometry.x, sales.geometry.y]).T
    homicidesXY = np.vstack([homicides.geometry.x, homicides.geometry.y]).T

    # total number of homicides
    num_homicides = len(homicidesXY)

    # time offsets
    sale_times = sales.time_offset
    homicide_times = homicides.time_offset

    # find the neighbors of every sale
    # for every homicide, the distances to all neighboring sales and indices
    dists, indices = knn_distance(homicidesXY, salesXY, space_radius * FT_PER_MILE)

    # loop over every homicide
    for i in range(num_homicides):

        # the difference between sale time and homicide time
        dt = sale_times.iloc[indices[i]] - homicide_times.iloc[i]

        # positive value: sale is after homicide
        after = np.where((dt > 0) & (dt < time_window[1] * SECONDS_PER_DAY))[0]

        # negative value: sale is before homicide
        before = np.where((dt < 0) & (dt > -time_window[0] * SECONDS_PER_DAY))[0]

        indices_before_after = (indices[i][before], indices[i][after])
        dists_before_after = (dists[i][before], dists[i][after])

        yield i, dt, indices_before_after, dists_before_after


def add_spacetime_flags(homicides, sales, distances, windows, window_sales=True):
    """
    Add flags to the input sales if a homicide occurs within a given time window 
    and a given spatial radius from the sale. 

    Notes
    -----
    The added columns are "spacetime_before_X.X" and "spacetime_after_X.X".

    Parameters
    ----------
    homicides : GeoDataFrame
        the homicide data
    sales : GeoDataFrame
        the sale data
    distances : float, or list of float
        a list of the distance (in miles) to search within
    windows : list of float
        the time frame (in days) to search within; this should be a tuple 
        giving the window before and after the sale date to search
    window_sales : bool, optional
        whether to remove invalid sales based on the time window given

    Returns
    -------
    salesWithFlags : GeoDataFrame
        a copy of the input sales data with the added flag columns
    """
    if not isinstance(distances, list):
        distances = [distances]
    max_distance = max(distances)

    # return a copy of the sales
    salesWithFlags = sales.copy()

    # set flags to zero by default
    for distance in distances:
        for tag in ["before", "after"]:
            salesWithFlags[f"spacetime_flag_{tag}_{distance}"] = 0

    # get the groups
    groups = _get_sale_groups_by_homicide(homicides, sales, max_distance, windows)

    # run the calculation
    for i, dt, indices, dists in groups:

        # do each distance flag
        for distance in distances:
            for I, D, tag in zip(indices, dists, ["before", "after"]):

                # get the subset that satisfies this distance
                valid = D < distance * FT_PER_MILE

                # the index values of before/after sales
                subset = sales.index[I[valid]]
                salesWithFlags.loc[subset, f"spacetime_flag_{tag}_{distance}"] = 1

    if window_sales:
        min_time = salesWithFlags["sale_date"].min() + pd.Timedelta(
            f"{windows[0] * SECONDS_PER_DAY} seconds"
        )
        max_time = salesWithFlags["sale_date"].max() - pd.Timedelta(
            f"{windows[1] * SECONDS_PER_DAY} seconds"
        )

        valid = (salesWithFlags["sale_date"] >= min_time) & (
            salesWithFlags["sale_date"] <= max_time
        )
        salesWithFlags = salesWithFlags.loc[valid]

    return salesWithFlags

