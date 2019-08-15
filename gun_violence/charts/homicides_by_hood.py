from .. import datasets as gv_data
from . import default_style
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
from phila_colors import palette
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable


def _plot(fig, axs, N, ticks, cmap="Reds", ascending=False, format_prices=False):

    # the left plot: choropleth
    ax = axs[0]
    sns.despine(ax=ax, bottom=True, top=True, left=True, right=True)

    # add the colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad="7%")
    fig.add_axes(cax, label="cax")

    # plot the city limits as background
    limits = gv_data.CityLimits.get()
    limits.buffer(1500).plot(
        ax=ax, facecolor=palette["sidewalk"], edgecolor=palette["sidewalk"]
    )

    # plot the total
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

    # set axes limits
    xmin, ymin, xmax, ymax = N.total_bounds
    PAD = 1500
    ax.set_xlim(xmin - PAD, xmax + PAD)
    ax.set_ylim(ymin - PAD, ymax + PAD)

    # format the colorbar
    cbar = plt.colorbar(ax.collections[-1], cax=cax, orientation="horizontal")
    cbar.set_ticks(ticks)

    labelsize = 8 if format_prices else 9
    cbar.ax.tick_params(labelsize=labelsize)
    cbar.outline.set_edgecolor("black")
    cbar.outline.set_linewidth(0.5)
    ax.set_axis_off()

    # format price
    if format_prices:
        cbar.set_ticklabels(["$%.0fK" % (np.exp(x) / 1e3) for x in ticks])

    # the right plot: top 20 bar graph
    top20 = N.sort_values("N", ascending=ascending).iloc[:20]
    ax = axs[1]

    # make the bar plot
    sns.barplot(
        y=top20.neighborhood, x=top20.N, ax=axs[1], color=palette["dark-ben-franklin"]
    )

    # add the title
    title = "Top 20 Neighborhoods" if not ascending else "Bottom 20 Neighborhoods"
    ax.text(
        0.2, 1.03, title, fontsize=8, ha="center", transform=ax.transAxes, weight="bold"
    )

    # format labels
    if format_prices:
        ax.set_xticks(ticks[:3])
        ax.set_xticklabels(["$%.0fK" % (np.exp(x) / 1e3) for x in ax.get_xticks()])
    else:
        ax.set_xticks(ticks)

    plt.setp(ax.get_xticklabels(), fontsize=9)
    plt.setp(ax.get_yticklabels(), fontsize=6)

    if not format_prices:
        ax.set_xlim(ticks[0], ticks[-1] + int(0.1 * ticks[-1]))
    else:
        ax.set_xlim(ticks[0], ticks[2] + 0.1)
    ax.set_ylabel("")
    ax.set_xlabel("")


def plot(fig_num, outfile):

    # load the data
    homicides = gv_data.PoliceHomicides.get()
    neighborhoods = gv_data.Neighborhoods.get()
    sales = gv_data.ResidentialSales.get()

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)

        # create the figure
        grid_kws = dict(
            left=0.01,
            right=0.95,
            bottom=0.07,
            top=0.825,
            hspace=0.35,
            wspace=0.45,
            width_ratios=[2, 1],
        )
        nrows = 2
        ncols = 2
        fig, axs = plt.subplots(
            nrows=nrows, ncols=ncols, figsize=(5, 5.25), gridspec_kw=grid_kws
        )

        # Homicide totals
        _plot(
            fig,
            axs[0],
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

        fig.text(
            0.5,
            0.865,
            "Total Number of Homicides",
            ha="center",
            weight="bold",
            fontsize=10,
        )

        # Median sale price
        _plot(
            fig,
            axs[1],
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

        fig.text(
            0.5,
            0.43,
            "Median Residential Sale Prices",
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
            0.965,
            "Median Sale Prices & Homicide Totals across Philadelphia in 2018",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.93,
            "Areas of the city with the most homicides also have the lowest median sale prices",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )

        plt.savefig(outfile, dpi=300)
