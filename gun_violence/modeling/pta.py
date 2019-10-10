import pandas as pd
import numpy as np
from .causality import FT_PER_MILE, SECONDS_PER_DAY, knn_distance


def get_binned_pta_data(PTA, time_window, bin_size=14):
    """
    Calculate the average sale price per sq. ft., aggregated
    by the sale time relative to the homicide time.

    Parameters
    ----------
    PTA : pandas.DataFrame
        the full data giving sale price and relative time
    time_window : int
        the time window in days
    bin_size : int, optional
        the bin size in days

    Returns
    -------
    result : pandas.DataFrame
        the binned sale price, as well as bin centers and number 
        of sales per bin
    """

    # bin values in days
    bins = np.arange(0, time_window + bin_size, bin_size)
    out = []
    queries = ["time_offset > 0", "time_offset < 0"]
    for i, query in enumerate(queries):

        # Create the bin edges
        if i == 0:
            edges = bins * SECONDS_PER_DAY
        else:
            edges = -1 * bins[::-1] * SECONDS_PER_DAY

        # add the bins
        df = PTA.query(query).copy()
        df["bin"] = pd.cut(df["time_offset"], edges, labels=range(len(edges) - 1))

        # calculations
        grouped = df.groupby("bin")
        sale_price = grouped["sale_price_psf"].mean()
        N = grouped.size()

        r = pd.concat([sale_price, N.rename("N")], axis=1).sort_index()
        r["bin_centers"] = 0.5 * (bins[1:] + bins[:-1])
        if i != 0:
            r["bin_centers"] = -1 * r["bin_centers"].values[::-1]

        out.append(r)

    return pd.concat(out, axis=0).reset_index(drop=True).sort_values("bin_centers")


def test_pta(sales, homicides, time_window, distances):
    """
    Test the parallel trends assumption, calculating the sales within the 
    specified time window and distance limits, and the time relative to the
    homicide time.

    Parameters
    ----------
    sales : pandas.DataFrame
        the sales data
    homicides : pandas.DataFrame
        the homicide data
    time_window : int
        the time window to restrict the sale-homicide overlap to
    distances : list of float
        the list of distance limits to consider

    Returns
    -------
    out : dict
        for each distance group, a data frame of sales occuring within the 
        specified limits 
    """
    if not isinstance(distances, list):
        distances = [distances]

    # Make sure the first distance is 0
    if distances[0] != 0:
        distances = [0] + distances

    # The maximum distance
    max_distance = max(distances)

    # window the sales first
    min_time = sales["sale_date"].min() + pd.Timedelta(
        f"{time_window * SECONDS_PER_DAY} seconds"
    )
    max_time = sales["sale_date"].max() - pd.Timedelta(
        f"{time_window * SECONDS_PER_DAY} seconds"
    )
    valid = (sales["sale_date"] >= min_time) & (sales["sale_date"] <= max_time)
    sales = sales.loc[valid]

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
    dists, indices = knn_distance(homicidesXY, salesXY, max_distance * FT_PER_MILE)

    out = {}
    for distance in distances[1:]:
        out[f"spacetime_flag_within_{distance}"] = []

    # loop
    for i in range(num_homicides):

        # the difference between sale time and homicide time
        dt = sale_times.iloc[indices[i]] - homicide_times.iloc[i]

        # trim by time window
        valid = abs(dt) < time_window * SECONDS_PER_DAY
        sale_price = sales.iloc[indices[i][valid]]["sale_price_psf"]
        dt_valid = dt[valid]

        # distance
        D = dists[i][valid]

        # loop over the distances
        for j in range(0, len(distances) - 1):

            # get the subset that satisfies this distance
            valid = D >= distances[j] * FT_PER_MILE
            valid &= D < distances[j + 1] * FT_PER_MILE

            col = f"spacetime_flag_within_{distances[j+1]}"
            out[col].append(
                pd.concat(
                    [
                        sale_price[valid].reset_index(drop=True),
                        dt_valid[valid].reset_index(drop=True),
                        pd.Series(D[valid], name="dist"),
                    ],
                    axis=1,
                )
            )

    for col in out:
        out[col] = pd.concat(out[col]).reset_index(drop=True)
    return out

