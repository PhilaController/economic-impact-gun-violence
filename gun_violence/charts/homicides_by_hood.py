"""
A two panel chart showing two choropleth maps: 

1. The total number of homicides in 2018
2. The median residential housing sale price in 2018
"""
from .. import datasets as gv_data
from . import default_style, palette
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable


def _plot_choropleth(
    fig, ax, N, ticks, cmap="Reds", ascending=False, format_prices=False
):
    """
    Internal function to make the choropleth map.
    """
    # Despine the axes
    sns.despine(ax=ax, bottom=True, top=True, left=True, right=True)

    # Split and add the colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad="7%")
    fig.add_axes(cax, label="cax")

    # Plot the city limits as background
    limits = gv_data.CityLimits.get()
    limits.buffer(1500).plot(
        ax=ax, facecolor=palette["sidewalk"], edgecolor=palette["sidewalk"]
    )

    # Plot the choropleth
    N.plot(
        column="N",
        ax=ax,
        cmap=cmap,
        edgecolor=palette["dark-gray"],
        linewidth=0.5,
        legend=False,
        vmin=ticks[0],
        vmax=ticks[-1],
        zorder=10,
    )

    # Set axes limits
    xmin, ymin, xmax, ymax = N.total_bounds
    PAD = 1500
    ax.set_xlim(xmin - PAD, xmax + PAD)
    ax.set_ylim(ymin - PAD, ymax + PAD)

    # Format the colorbar
    cbar = plt.colorbar(ax.collections[-1], cax=cax, orientation="horizontal")
    cbar.set_ticks(ticks)

    # Format axes
    labelsize = 8 if format_prices else 9
    cbar.ax.tick_params(labelsize=labelsize)
    cbar.outline.set_edgecolor("black")
    cbar.outline.set_linewidth(0.5)
    ax.set_axis_off()

    # Format prices
    if format_prices:
        cbar.set_ticklabels(["$%.0fK" % (np.exp(x) / 1e3) for x in ticks])

    return cbar


def plot(fig_num, outfile):
    """
    Plot a two panel chart showing two choropleth maps: 

    1. The total number of homicides in 2018
    2. The median residential housing sale price in 2018
    """
    # Load the data
    homicides = gv_data.PoliceHomicides.get()
    neighborhoods = gv_data.Neighborhoods.get()
    sales = gv_data.ResidentialSales.get()

    with plt.style.context(default_style):

        # Create the figure
        fig, axs = plt.subplots(
            nrows=1,
            ncols=2,
            figsize=(5, 3.5),
            gridspec_kw=dict(
                left=0.01, right=0.95, bottom=0.07, top=0.81, hspace=0.35, wspace=0.45
            ),
        )

        # Homicide totals
        ax = axs[0]
        _plot_choropleth(
            fig,
            ax,
            pd.merge(
                neighborhoods,
                homicides.query("year == 2018")
                .groupby("neighborhood")
                .size()
                .reset_index(name="N"),
                how="left",
            ).fillna(0),
            ticks=[0, 10, 20],
        )

        total = len(homicides.query("year == 2018"))
        ax.text(
            0.75,
            0.2,
            "Citywide Total\n%.0f" % (total),
            transform=ax.transAxes,
            fontsize=9,
            weight="bold",
            ha="center",
        )

        # Add a title
        fig.text(
            0.25,
            0.80,
            "Total Number of Homicides",
            ha="center",
            weight="bold",
            fontsize=10,
        )

        # Median sale price
        ax = axs[1]
        cbar = _plot_choropleth(
            fig,
            ax,
            pd.merge(
                neighborhoods,
                sales.query("sale_year == 2018")
                .groupby("neighborhood")["ln_sale_price"]
                .median()
                .reset_index(name="N"),
                how="inner",
            ),
            ticks=np.log([10e3, 25e3, 60e3, 160e3, 450e3]),
            cmap="Reds_r",
            ascending=True,
            format_prices=True,
        )

        citywide_median = np.exp(
            sales.query("sale_year == 2018")["ln_sale_price"].median()
        )

        with plt.style.context({"lines.solid_capstyle": "butt"}):
            ylim = cbar.ax.get_ylim()
            cbar.ax.vlines(
                x=np.log(citywide_median),
                ymin=ylim[0],
                ymax=ylim[1] * 1.25,
                lw=2,
                color=palette["almost-black"],
                clip_on=False,
            )
        cbar.ax.text(
            np.log(citywide_median),
            ylim[1] * 1.3,
            "Citywide Median",
            fontsize=7,
            ha="center",
            va="bottom",
            clip_on=False,
            weight="bold",
        )

        ax.text(
            0.82,
            0.2,
            "Citywide Median\n$%.0fK" % (citywide_median / 1e3),
            transform=ax.transAxes,
            fontsize=9,
            weight="bold",
            ha="center",
        )

        # Add a title
        fig.text(
            0.75,
            0.80,
            "Median Residential Sale Price",
            ha="center",
            weight="bold",
            fontsize=10,
        )

        # Add the footnote
        footnote = r"$\bf{Sources}$: Office of Property Assessment, Police Department"
        fig.text(
            0.005,
            0.002,
            footnote,
            fontsize=7,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

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
            0.95,
            "Median Sale Price & Homicide Totals across Philadelphia in 2018",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.90,
            "Areas of the city with the most homicides also have the lowest median sale prices",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )

        # Save!
        plt.savefig(outfile, dpi=300)
