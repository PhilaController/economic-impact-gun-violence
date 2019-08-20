import numpy as np
import pandas as pd
from .causality import _get_sale_groups_by_homicide, FT_PER_MILE, SECONDS_PER_DAY


def get_sale_price_psf_from_homicide(
    homicides,
    sales,
    space_radius,
    time_window,
    nbins=30,
    window_sales=True,
    split_results=False,
):
    """
    Calculate the sale price per square foot as a function of the distance 
    from the location of a homicide.

    Parameters
    ----------
    homicides : GeoDataFrame
        the homicide data
    sales : GeoDataFrame
        the sale data
    space_radius : float
        the distance (in feet) to search within
    time_window : list of float
        the time frame (in seconds) to search within; this should be a tuple 
        giving the window before and after the sale date to search
    nbins : int, optional
        the number of bins to use
    window_sales : bool, optional
        whether to remove invalid sales based on the time window given
    split_results : bool, optional
        whether to return separate results for sales that 
        occur before and after the homicide
    """
    if window_sales:
        min_time = sales["sale_date"].min() + pd.Timedelta(
            f"{time_window[0] * SECONDS_PER_DAY} seconds"
        )
        max_time = sales["sale_date"].max() - pd.Timedelta(
            f"{time_window[1] * SECONDS_PER_DAY} seconds"
        )

        valid = (sales["sale_date"] >= min_time) & (sales["sale_date"] <= max_time)
        sales = sales.loc[valid]

    # get sale price PSF
    sale_price_psf = sales["sale_price_indexed"] / sales["total_livable_area"]

    # get the groups
    groups = _get_sale_groups_by_homicide(homicides, sales, space_radius, time_window)

    # run the calculation
    D = {"before": [], "after": []}
    Y = {"before": [], "after": []}
    for i, dt, indices, dists in groups:

        # the index values of before/after sales
        for i, tag in enumerate(["before", "after"]):

            idx = sales.index[indices[i]]
            D[tag].append(dists[i])
            Y[tag].append(sale_price_psf.loc[idx])

    for tag in ["before", "after"]:
        D[tag] = np.concatenate(D[tag])
        Y[tag] = np.concatenate(Y[tag])

    # bin
    def get_binned_distance(D, Y, nbins):
        edges = np.linspace(0, space_radius * FT_PER_MILE, nbins + 1)
        dig = np.digitize(D, edges)
        r = pd.DataFrame({"dig": dig, "C": Y, "R": D})

        X = r.groupby("dig")["R"].mean() / FT_PER_MILE
        C = r.groupby("dig")["C"].median()
        N = r.groupby("dig").size()

        X = X[:-1]
        C = C[:-1]
        N = N[:-1]
        return X, C, N

    if split_results:
        out = {}
        for tag in ["before", "after"]:
            out[tag] = get_binned_distance(D[tag], Y[tag], nbins)

        return out["before"], out["after"], sale_price_psf.median()

    else:

        D = np.concatenate([D["before"], D["after"]])
        Y = np.concatenate([Y["before"], Y["after"]])

        return get_binned_distance(D, Y, nbins) + (sale_price_psf.median(),)

