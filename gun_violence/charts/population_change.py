"""
A swarm plot showing the population change from 2010 to 2017 as a
function of the number of homicides over that period.
"""
from .. import datasets as gv_data
from . import default_style, palette
import pandas as pd
import geopandas as gpd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns


def _load_data():
    """
    Load the data and calculate the population change.
    """
    # Load homicides and census tracts
    homicides = gv_data.PoliceHomicides.get()
    tracts = gv_data.CensusTracts2010.get()

    # Total number of homicides by census tract
    N_homicides = (
        gpd.sjoin(homicides, tracts, op="within", how="left")
        .groupby(["census_tract_id"])
        .size()
        .rename("num_homicides")
    )

    # Population numbers
    pop = []
    for year in range(2010, 2018):
        df = gv_data.Population.get(year=year)
        df["year"] = year
        pop.append(df)

    Y = pd.concat(pop).set_index(["census_tract_id"])

    # Calculate population change
    pop_change = (
        Y.query("year == 2017")["total_population"]
        - Y.query("year == 2010")["total_population"]
    )

    # Merge tracts with population change and
    Y = pd.merge(
        tracts,
        pd.concat([pop_change, N_homicides], axis=1).reset_index(),
        on="census_tract_id",
        how="left",
    )
    Y["num_homicides"] = Y["num_homicides"].fillna(0)

    # Calculate the homicide bin
    Y["bins"] = pd.cut(Y["num_homicides"], [-1, 7, 15, 24, 36, 64])

    # Sign of the population change
    Y["Sign"] = np.where(
        Y["total_population"] > 0, "Population Growth", "Population Loss"
    )

    return Y


def plot(fig_num, outfile):
    """
    A swarm plot showing the population change from 2010 to 2017 as a
    function of the number of homicides over that period.
    """

    # Load the data
    data = _load_data()

    def get_ylabel(x):
        sign = ""
        if x > 0:
            sign = "+"
        if x < 0:
            sign = "\u2212"
        return sign + "{:,.0f}".format(abs(x))

    with plt.style.context(default_style):

        # Initialize
        fig, ax = plt.subplots(
            figsize=(6.4, 4.5),
            gridspec_kw=dict(left=0.13, bottom=0.15, top=0.82, right=0.98),
        )
        ax.set_ylim(-3100, 3100)

        # Plot the swarm plot
        colors = sns.color_palette("RdYlGn", 7, desat=0.8).as_hex()
        sns.swarmplot(
            x="bins",
            y="total_population",
            data=data,
            hue="Sign",
            palette=[colors[-1], colors[0]],
            alpha=1.0,
            ax=ax,
            size=4,
            edgecolor="none",
        )

        # Add a line at y = 0
        ax.axhline(y=0, c=palette["sidewalk"], lw=2, zorder=1)

        # Format y axis
        ax.set_ylabel("Population Change Since 2010", weight="bold", fontsize=11)
        ax.set_yticklabels([get_ylabel(x) for x in ax.get_yticks()], fontsize=11)

        # Format the x axis
        ax.set_xlabel("Total Homicides Since 2010", weight="bold", fontsize=11)
        ax.set_xticklabels(
            ["Less than 7", "7 to 15", "15 to 24", "24 to 36", "More than 36"],
            fontsize=11,
        )

        # Add the legend
        leg = ax.legend(
            title="Census Tracts With:",
            fontsize=10,
            frameon=True,
            facecolor="white",
            framealpha=1,
            edgecolor="none",
            loc="upper right",
            bbox_to_anchor=(1, 1.05),
            bbox_transform=ax.transAxes,
        )
        title = leg.get_title()
        title.set_weight("bold")
        title.set_fontsize(11)

        # Add title
        fig.text(
            0.005,
            0.99,
            f"Figure {fig_num}",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.96,
            "Population Change and Number of Homicides since 2010 by Census Tract",
            weight="bold",
            fontsize=12,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.92,
            "Areas that experienced the most homicides were more likely to have seen a population decline",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )

        # Add the footnote
        footnote = r"$\bf{Sources}$: American Community Survey 5-Year estimates, Police Department"
        fig.text(
            0.005,
            0.002,
            footnote,
            fontsize=8,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

        # Save!
        plt.savefig(outfile, dpi=300)

