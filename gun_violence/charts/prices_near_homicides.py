from .. import datasets as gv_data
from ..modeling import get_sale_price_psf_from_homicide
from . import default_style
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
from phila_colors import palette
import matplotlib.transforms as transforms


def _load_data():
    sales = gv_data.ResidentialSales.get()
    homicides = gv_data.PoliceHomicides.get()

    sales = sales.loc[sales.geometry.notnull()]
    homicides = homicides.loc[homicides.geometry.notnull()]

    return sales, homicides


def plot(fig_num, outfile):

    # load the data
    sales, homicides = _load_data()

    # perform the calculation
    space_radius = 2.5
    time_window = [90, 90]
    X, Y, N, citywide_median = get_sale_price_psf_from_homicide(
        homicides, sales, space_radius, time_window, nbins=20
    )

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)

        # initialize
        grid_kws = dict(left=0.1, bottom=0.15, top=0.7)
        fig, ax = plt.subplots(figsize=(5, 3), gridspec_kw=grid_kws)

        # plot
        color = palette["love-park-red"]
        ax.plot(
            X,
            Y / citywide_median,
            marker="o",
            color=color,
            mec=color,
            mfc="white",
            mew=3,
            lw=4,
            label="All Homicides",
            zorder=10,
        )

        ax.set_xlabel("Distance from a homicide (miles)", fontsize=10, weight="bold")

        fig.text(
            0.005,
            1.01,
            "Median sale price\nrelative to the citywide median",
            fontsize=10,
            weight="bold",
            transform=transforms.blended_transform_factory(
                fig.transFigure, ax.transAxes
            ),
            ha="left",
            va="bottom",
        )

        ax.set_xlim(-0.05, 2.25)
        ax.set_xticks(np.arange(0, 2.1, 0.5))
        ax.set_yticklabels(["%.0f%%" % (100 * x) for x in ax.get_yticks()], fontsize=12)
        plt.setp(ax.get_xticklabels(), fontsize=12)
        sns.despine(left=True, bottom=True)
        ax.axhline(y=1, c=palette["dark-gray"])
        ax.set_ylim(top=1.1)

        ax.text(
            1,
            1.015,
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

        plt.savefig(outfile, dpi=300)

