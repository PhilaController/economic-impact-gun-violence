"""
A 3 x 3 panel chart showing concentrated disadvantage maps with homicides 
overlaid from 2010 to 2017.
"""
from .. import datasets as gv_data
from . import default_style, palette
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

YEARS = list(range(2010, 2018))
PAD = 1500


def _load_data():
    """
    Internal function to get the data to plot.
    """
    # Load homicides
    homicides = gv_data.PoliceHomicides.get()

    # Calculate concentrated disadvantage
    sub_data = []
    for cls in [
        "PublicAssistance",
        "FemaleHouseholders",
        "PercentInPoverty",
        "PercentUnder18",
    ]:
        subset = []
        for year in YEARS:
            df = getattr(gv_data, cls).get(year=year)
            df["year"] = year
            subset.append(df)

        sub_data.append(pd.concat(subset).set_index(["census_tract_id", "year"]))

    data = sub_data[0]
    for df in sub_data[1:]:
        data = data.join(df.drop(labels=["geometry"], axis=1))

    # Do min/max normalization on each
    for col in [
        "percent_public_assistance",
        "percent_female_householder",
        "percent_in_poverty",
        "percent_under_18",
    ]:
        data[col + "_normed"] = (data[col] - data[col].min()) / (
            data[col].max() - data[col].min()
        )

    # Normalize sum to 0 to 1
    data["index"] = data.filter(regex="_normed").sum(axis=1) / 5.0

    return homicides, data


def plot(fig_num, outfile):
    """
    Plot a 3 x 3 panel chart showing concentrated disadvantage maps of 
    Philadelphia with homicides overlaid from 2010 to 2017.
    """
    # Get the data
    homicides, poverty = _load_data()

    # Use city limits as background
    limits = gv_data.CityLimits.get()

    with plt.style.context(default_style):

        # Initialize
        fig, axs = plt.subplots(
            nrows=3,
            ncols=3,
            figsize=(6, 5.5),
            gridspec_kw=dict(
                left=0.02, bottom=0.07, top=0.9, right=0.98, wspace=0, hspace=0.1
            ),
        )

        axs = np.ravel(axs)
        for i, year in enumerate(YEARS):

            ax = axs[i]

            # Get data for this year
            H = homicides.query("year == @year")
            P = poverty.query("year == @year")

            # Add city limits as background
            limits.buffer(1500).plot(
                ax=ax, facecolor=palette["sidewalk"], edgecolor=palette["sidewalk"]
            )

            # Plot choropleth of concentrated disadvantage
            P.plot(ax=ax, column="index", cmap="Blues", edgecolor="none", vmin=0)

            # Plot homicides as markers
            H.plot(
                ax=ax,
                marker=".",
                markersize=10,
                alpha=0.8,
                edgecolor="none",
                color=palette["red"],
            )

            # Add title
            ax.text(
                0.5,
                1.0,
                str(year),
                weight="bold",
                fontsize=12,
                ha="center",
                va="top",
                transform=ax.transAxes,
            )

            # Format
            ax.set_axis_off()
            xmin, ymin, xmax, ymax = P.total_bounds
            ax.set_xlim(xmin - PAD, xmax + PAD)
            ax.set_ylim(ymin - PAD, ymax + PAD)

        ax = axs[-1]
        ax.set_axis_off()

        # Make the colorbar
        cax = inset_axes(
            ax,
            width="90%",  # width = 50% of parent_bbox width
            height="10%",  # height : 5%
            loc="lower left",
            bbox_to_anchor=(-0.05, 0.4, 1.0, 1.0),
            bbox_transform=ax.transAxes,
            borderpad=0,
        )
        cbar = fig.colorbar(
            plt.cm.ScalarMappable(cmap="Blues"),
            cax=cax,
            orientation="horizontal",
            ticks=[],
        )
        cax.text(
            0.5,
            1.4,
            "Level of Disadvantage",
            transform=cax.transAxes,
            fontsize=10,
            ha="center",
        )

        cbar.outline.set_edgecolor(palette["almost-black"])
        cbar.outline.set_linewidth(1)

        cax.text(
            0,
            -0.1,
            "Least\nDisadvantaged",
            ha="center",
            va="top",
            transform=cax.transAxes,
            fontsize=8,
        )
        cax.text(
            1,
            -0.1,
            "Most\nDisadvantaged",
            ha="center",
            va="top",
            transform=cax.transAxes,
            fontsize=8,
        )

        # Add the legend
        legend_elements = [
            Line2D(
                [0],
                [0],
                color=palette["red"],
                ls="",
                marker="o",
                label="Homicide Locations",
            )
        ]
        ax.legend(
            loc="lower left",
            handles=legend_elements,
            fontsize=10,
            frameon=False,
            bbox_to_anchor=(-0.1, 0.6),
            handletextpad=0.1,
        )
        ax.text(0.4, 1.0, "Legend", weight="bold", ha="center", va="top", fontsize=11)

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
            0.965,
            "The Historical Correlation between Disadvantage and Homicides in Philadelphia",
            weight="bold",
            fontsize=10.5,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.935,
            "Homicides are most likely to occur in the most disadvantaged areas of the city",
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
            fontsize=6,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

        footnote = (
            r"$\bf{Notes}$: The level of disadvantage is calculated from"
            " public assistance rates, poverty rates, female-headed households, and population under 18 years old"
        )
        fig.text(
            0.005,
            0.02,
            footnote,
            fontsize=6,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

        # Save!
        plt.savefig(outfile, dpi=300)

