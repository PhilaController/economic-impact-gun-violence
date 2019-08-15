from .. import datasets as gv_data
from ..modeling import get_sale_price_psf_from_homicide
from . import default_style
import pandas as pd
import geopandas as gpd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
from phila_colors import palette


def _load_data():
    """
    Load the data
    """

    # load homicides and census tracts
    homicides = gv_data.PoliceHomicides.get()
    tracts = gv_data.CensusTracts2010.get()

    N = (
        gpd.sjoin(homicides, tracts, op="within", how="left")
        .groupby(["census_tract_id", "year"])
        .size()
    )

    # number of homicides
    num_homicides = pd.merge(
        tracts, N.reset_index(name="num_homicides"), on="census_tract_id"
    )

    # population numbers
    pop = []
    for year in range(2010, 2018):
        df = gv_data.Population.get(year=year)
        df["year"] = year
        pop.append(df)

    Y = pd.concat(pop).set_index(["census_tract_id"])
    pop_change = (
        Y.query("year == 2017")["total_population"]
        - Y.query("year == 2010")["total_population"]
    )
    N_homicides = num_homicides.groupby("census_tract_id")["num_homicides"].sum()
    Y = pd.merge(
        tracts,
        pd.concat([pop_change, N_homicides], axis=1).reset_index(),
        on="census_tract_id",
    )
    Y["bins"] = pd.cut(Y["num_homicides"], [0, 7, 15, 24, 36, 64])
    Y["Sign"] = np.where(
        Y["total_population"] > 0, "Population Growth", "Population Loss"
    )

    return Y


def plot(fig_num, outfile):

    # load the data
    data = _load_data()

    def get_ylabel(x):
        sign = ""
        if x > 0:
            sign = "+"
        if x < 0:
            sign = "\u2212"
        return sign + "{:,.0f}".format(abs(x))

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)

        # initialize
        grid_kws = dict(left=0.15, bottom=0.15, top=0.85, right=0.98)
        fig, ax = plt.subplots(figsize=(6, 4), gridspec_kw=grid_kws)

        # plot
        sns.swarmplot(
            x="bins",
            y="total_population",
            data=data,
            hue="Sign",
            palette=["#d6604d", "#4393c3"],
            alpha=1.0,
            ax=ax,
            size=3.75,
            edgecolor="none",
        )

        # add a line at y = 0
        ax.axhline(y=0, c=palette["medium-gray"], lw=2, zorder=1)

        # format y axis
        ax.set_ylim(-3100, 3100)
        ax.set_ylabel("Population Change Since 2010", weight="bold", fontsize=11)
        ax.set_yticklabels([get_ylabel(x) for x in ax.get_yticks()], fontsize=11)

        # format the x axis
        ax.set_xlabel("Total Homicides Since 2010", weight="bold", fontsize=11)
        ax.set_xticklabels(
            ["Less than 7", "7 to 15", "15 to 24", "24 to 36", "More than 36"],
            fontsize=11,
        )

        # add the legend
        leg = ax.legend(
            title="Census Tracts With:",
            fontsize=10,
            frameon=True,
            facecolor="white",
            framealpha=1,
            edgecolor="none",
        )
        title = leg.get_title()
        title.set_weight("bold")
        title.set_fontsize(10)

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
            "Population Change and Number of Homicides since 2010 by Census Tract",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.91,
            "Areas that experienced the most homicides were more likely to have seen a population decline",
            fontsize=9,
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
            fontsize=7,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

        plt.savefig(outfile, dpi=300)

