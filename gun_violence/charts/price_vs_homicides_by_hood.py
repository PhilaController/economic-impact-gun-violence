"""
A multi-panel chart showing the trends in residential sale prices
and number of homicides from 2006 to 2018.
"""
from .. import datasets as gv_data
from . import default_style
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from phila_colors import palette

YEAR_LIMIT = 2018


def _format_neighborhood_name(x):
    """
    Internal function to format neighborhood names nicely.
    """
    x = x.replace("-", "")
    fields = x.split()
    if x == "East Oak Lane":
        return "East\nOak Lane"
    if x == "West Oak Lane":
        return "West\nOak Lane"
    if x == "East Mount Airy":
        return "East\nMount Airy"
    if x == "West Mount Airy":
        return "West\nMount Airy"
    if x == "West Central Germantown":
        return "West Central\nGermantown"
    if x == "Washington Square West":
        return "Washington\nSquare West"
    if x == "Melrose Park Gardens":
        return "Melrose\nPark Gardens"
    if x.startswith("Fishtown"):
        return "Fishtown/Lower\nKensington"
    return "\n".join([field.strip() for field in fields])


def _plot_sales(ax, df, col, **kws):
    """
    Plot a line chart showing the median residential sale price over time.
    """

    ax.plot(df["sale_year"], df[col], **kws)
    sns.despine(left=True)
    ax.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)


def _plot_homicides(ax, df, **kws):
    """
    Plot a bar graph showing the total number of annual homicides.
    """

    df2 = df.query("year <= @YEAR_LIMIT")
    ax.bar(
        x=df2["year"].values,
        height=df2["count"].values,
        zorder=20,
        clip_on=False,
        **kws,
    )
    sns.despine(left=True, right=True)
    ax.tick_params(
        labelleft=False,
        left=False,
        labelbottom=False,
        bottom=False,
        right=False,
        labelright=False,
    )


def plot(fig_num, outfile):
    """
    Plot a multi-panel chart showing the trends in residential sale prices
    and number of homicides from 2006 to 2018.
    """
    # Load the data
    sales = gv_data.ResidentialSales.get()
    homicides = gv_data.PoliceHomicides.get()

    # Drop condos, since they can include multiple properties
    sales = sales.loc[~sales["parcel_number"].astype(str).str.startswith("888")]

    # Median sale price
    median_sale_price = (
        sales.groupby(["neighborhood", "sale_year"])["sale_price"]
        .median()
        .reset_index()
    )

    # Homicide totals
    homicide_count = (
        homicides.groupby(["neighborhood", "year"])
        .size()
        .unstack()
        .fillna(0)
        .stack()
        .reset_index(name="count")
    )

    # Determine neighborhood order based on 2018 value
    groups = sales.query("sale_year == 2018").groupby(["neighborhood"])
    neighborhoods = (
        pd.merge(
            groups["sale_price"].median().reset_index(),
            groups.size().reset_index(name="N"),
        )
        .query("N > 20")
        .sort_values("sale_price", ascending=False)["neighborhood"]
        .tolist()
    )

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)
        plt.rcParams["axes.edgecolor"] = "black"
        plt.rcParams["patch.edgecolor"] = "black"
        plt.rcParams["axes.linewidth"] = 1.0

        # Create the figure
        nrows = 14
        ncols = 9
        fig, axs = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(6.45, 10),
            gridspec_kw=dict(
                left=0.025, right=0.95, bottom=0.045, top=0.88, hspace=0.9, wspace=0.3
            ),
        )

        # Trim to top neighborhoods
        df = median_sale_price.query("neighborhood in @neighborhoods")

        # Plot each panel
        panel = 0
        for i in range(nrows):
            for j in range(ncols):

                # The axes for this panel
                ax = axs[i, j]  # sale price
                ax2 = ax.twinx()  # homicides

                # Blank panel
                if panel >= len(neighborhoods):
                    ax.set_axis_off()
                    continue

                # The neighborhood we are plotting
                hood = neighborhoods[panel]

                # Plot the homicides
                _plot_homicides(
                    ax2,
                    homicide_count.query("neighborhood == @hood"),
                    color=palette["love-park-red"],
                )

                # Plot the sales
                _plot_sales(
                    ax,
                    median_sale_price.query("neighborhood == @hood"),
                    "sale_price",
                    linewidth=2,
                    clip_on=False,
                    zorder=19,
                    color=palette["ben-franklin-blue"],
                )

                # Add a legend
                if i == 0 and j == ncols - 1:
                    legend_elements = [
                        Line2D(
                            [0],
                            [0],
                            color="#2176d2",
                            lw=2,
                            label="Median Residential Sale Price",
                        ),
                        Patch(facecolor="#cc3000", label="Number of Homicides"),
                    ]
                    ax.legend(
                        handles=legend_elements,
                        loc="lower center",
                        bbox_transform=fig.transFigure,
                        bbox_to_anchor=(0.5, 0.9),
                        ncol=2,
                        fontsize=10,
                        frameon=False,
                    )

                # x ticks
                ax.set_xticks(range(2006, 2019, 3))
                ax2.set_xticks(range(2006, 2019, 3))

                # Put original axes on top
                ax.set_zorder(ax2.get_zorder() + 1)
                ax.patch.set_visible(False)

                # Grid for original axes
                for xtick in ax2.get_xticks():
                    ax2.axvline(
                        x=xtick, color="#a1a1a1", lw=0.5, ls="dashed", zorder=10
                    )

                # Subplot title
                ax.text(
                    0.5,
                    1.1,
                    _format_neighborhood_name(hood),
                    fontsize=6,
                    transform=ax.transAxes,
                    ha="center",
                    va="bottom",
                    bbox=dict(facecolor="white", edgecolor="none", pad=0),
                )

                # Format axes
                ax.set_ylim(bottom=1e3)
                ax.grid(b=False, axis="both")

                ax2.set_ylim(0, 20)
                ax2.grid(b=False, axis="both")

                # More formatting
                if i == nrows - 1:
                    ax.tick_params(labelbottom=True)
                    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=7)
                if j == ncols - 1:
                    ax2.set_yticks([0, 5, 10, 15, 20])
                    ax2.tick_params(labelright=True, right=True, width=1, length=3)
                    plt.setp(ax2.get_yticklabels(), fontsize=7)

                panel += 1

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
            0.975,
            "Trends in Residential Sale Prices & Total Homicides in Philadelphia's Neighborhoods",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.955,
            "Neighborhoods are sorted by median sale price in 2018, starting with the most expensive (top left)",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )
        fig.text(
            0.9575,
            0.895,
            "Total\nHomicides",
            weight="bold",
            ha="left",
            rotation=90,
            fontsize=8,
        )

        # Add the footnote
        footnote = r"$\bf{Sources}$: Office of Property Assessment, Police Department"
        fig.text(
            0.005,
            0.002,
            footnote,
            fontsize=6,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

        # Save!
        plt.savefig(outfile, dpi=300)
