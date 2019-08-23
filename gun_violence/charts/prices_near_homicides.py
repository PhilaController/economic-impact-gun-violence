"""
A line chart showing the sale price per sq. ft. relative to the 
citywide median, as a function of the distance from 
"""
from .. import datasets as gv_data
from ..modeling import get_sale_price_psf_from_homicide
from . import default_style
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
from phila_colors import palette
import matplotlib.transforms as transforms


def _load_data():
    """
    Load the data we will need.
    """
    # Load sales and homicides
    sales = gv_data.ResidentialSales.get()
    homicides = gv_data.PoliceHomicides.get()

    # Remove any null entries
    sales = sales.loc[sales.geometry.notnull()]
    homicides = homicides.loc[homicides.geometry.notnull()]

    return sales, homicides


def plot(fig_num, outfile, xmax=2.25):
    """
    A line chart showing the sale price per sq. ft. relative to the 
    citywide median, as a function of the distance from 
    """
    # Load the data
    sales, homicides = _load_data()

    # Perform the calculation
    space_radius = 2.5  # in miles
    time_window = [90, 90]
    X, Y, N, citywide_median = get_sale_price_psf_from_homicide(
        homicides, sales, space_radius, time_window, nbins=20
    )

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)

        # Initialize
        fig, ax = plt.subplots(
            figsize=(5, 3), gridspec_kw=dict(left=0.1, bottom=0.15, top=0.7)
        )

        # Make the line chart
        color = palette["love-park-red"]
        valid = X < xmax
        ax.plot(
            X[valid],
            Y[valid],
            marker="o",
            color=color,
            mec=color,
            mfc="white",
            mew=3,
            lw=4,
            label="All Homicides",
            zorder=10,
        )

        # Add an x-axis label
        ax.set_xlabel("Distance from a homicide (miles)", fontsize=10, weight="bold")

        # Add a y-axis label
        fig.text(
            0.005,
            1.01,
            "Median sale price\nper square foot",
            fontsize=10,
            weight="bold",
            transform=transforms.blended_transform_factory(
                fig.transFigure, ax.transAxes
            ),
            ha="left",
            va="bottom",
        )

        # Format axes
        ax.set_xlim(-0.05, 2.25)
        ax.set_xticks(np.arange(0, 2.1, 0.5))
        ax.set_yticks([40, 70, 100, 130])
        ax.set_ylim(35, 135)
        ax.set_yticklabels(["$%.0f" % (x) for x in ax.get_yticks()], fontsize=12)
        plt.setp(ax.get_xticklabels(), fontsize=12)
        sns.despine(left=True, bottom=True)
        ax.axhline(y=citywide_median, c=palette["dark-gray"])

        # Label the citywide median
        ax.text(
            1,
            citywide_median + 3,
            "Citywide median: $%.0f per sq. ft." % citywide_median,
            ha="right",
            va="bottom",
            transform=transforms.blended_transform_factory(ax.transAxes, ax.transData),
            bbox=dict(facecolor="white", pad=0, edgecolor="none"),
            fontsize=9,
            weight="bold",
        )

        # Add title
        fig.text(
            0.005,
            0.99,
            f"Figure {fig_num}",
            weight="bold",
            fontsize=9,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.95,
            "Residential Sale Prices Near the Locations of Homicides, 2006 to 2018",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.90,
            "Prices near homicides are significantly depressed relative to the citywide median price",
            fontsize=9,
            ha="left",
            va="top",
            style="italic",
        )

        # Save!
        plt.savefig(outfile, dpi=300)

