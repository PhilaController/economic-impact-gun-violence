"""
A grouped bar chart showing the cumulative cost and added
revenue associated with a plan that reduces homicides 10% annually.
"""
from .. import datasets as gv_data
from . import default_style, palette, light_palette
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns


def _calculate():
    """
    Calculate the number of lives saved, plan costs, and added tax 
    revenue associated with a plan that reduces homicides 10% annually.
    """

    NUM_YEARS = 5
    START_YEAR = 2018
    COST_PER_HOMICIDE = 30e3
    TOTAL_REVENUE = 134.2e6

    # Lives Saved
    homicides = [351]
    for i in range(1, NUM_YEARS):
        homicides.append(homicides[i - 1] - np.round(homicides[i - 1] * 0.1))

    # Make the DataFrame
    df = pd.DataFrame(
        {
            "year": list(range(START_YEAR, START_YEAR + NUM_YEARS)),
            "homicides": homicides,
        }
    ).assign(
        homicide_change=lambda df: abs(df["homicides"].diff()).fillna(0),
        lives_saved=lambda df: homicides[0] - df["homicides"],
        plan_cost=lambda df: df["homicides"] * COST_PER_HOMICIDE,
        added_tax_revenue=lambda df: df["homicide_change"]
        / homicides[0]
        * TOTAL_REVENUE,
        cumulative_cost=lambda df: df["plan_cost"].cumsum(),
        plan_year=lambda df: range(1, len(df) + 1),
    )

    # Add cumulative revenue
    R = [0]
    for i in range(1, NUM_YEARS):
        r = df.iloc[: i + 1]["added_tax_revenue"].sum()
        R.append(r)
    df["compounded_revenue"] = R
    df["cumulative_revenue"] = df["compounded_revenue"].cumsum()

    return df


def _plot_net_gain(ax, data):
    """
    Plot a bar chart showing the annual net gain
    """
    X = range(5)
    Y = (data["cumulative_revenue"] - data["cumulative_cost"]) / 1e6

    color = palette["almost-black"]
    ax.plot(
        X,
        Y,
        zorder=1000,
        color=color,
        mfc="white",
        mec=color,
        marker="o",
        mew=2,
        label="Cumulative Return on Investment",
    )

    def format_currency(y):
        if y < 0:
            fmt = "\u2212" + "$%.0fM"
        else:
            fmt = "+$%.0fM"
        return fmt % (abs(y))

    for i in X:
        yval = Y.iloc[i]
        if yval < 0:
            yval -= 5
        else:
            yval += 7
        ax.text(
            i + 0.1,
            yval,
            format_currency(Y.iloc[i]),
            ha="left" if yval < 0 else "right",
            va="top" if yval < 0 else "bottom",
            fontsize=9,
            weight="bold",
            zorder=102,
            bbox=dict(facecolor="white", pad=0),
        )

    # Add a y=0 line
    ax.axhline(y=0, c=palette["light-gray"], lw=2, zorder=101)

    # Format the axes
    ax.set_xlim(left=-0.75)
    ax.set_ylim(-30)
    ax.set_yticks([0, 40, 80])
    ax.set_yticklabels([format_currency(x) for x in ax.get_yticks()], fontsize=11)
    plt.setp(ax.get_yticklabels(), ha="center")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels([1, 2, 3, 4, 5], fontsize=11)

    ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
    ax.set_ylabel("")
    ax.xaxis.labelpad = 0

    # Add a legend
    ax.legend(
        loc="lower center",
        edgecolor="none",
        framealpha=1,
        ncol=2,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.95),
    )


def _plot_annual_costs(ax, data):
    """
    Plot a grouped bar chart showing the annual cost/revenue numbers
    """
    # Plot
    sns.barplot(
        x="plan_year",
        y="value",
        hue="variable",
        palette=[light_palette[color] for color in ["blue", "green"]],
        ax=ax,
        saturation=1.0,
        zorder=100,
        data=data,
    )

    # Add a y=0 line
    ax.axhline(y=0, c=palette["light-gray"], lw=4, zorder=101)

    # Format the axes
    ax.set_xlim(left=-0.75)
    ax.set_yticklabels(["$%.0fM" % x for x in ax.get_yticks()], fontsize=11)
    plt.setp(ax.get_yticklabels(), ha="center")
    plt.setp(ax.get_xticklabels(), fontsize=11)
    ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
    ax.set_ylabel("")
    ax.xaxis.labelpad = 0
    ax.grid(b=True, axis="x")

    # Add a legend
    ax.legend(
        loc="lower center",
        edgecolor="none",
        framealpha=1,
        ncol=2,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.95),
    )

    # Add the total dollar amount above the chart
    for p in ax.patches:
        height = p.get_height()
        if height == 0:
            y = 3
        else:
            y = height + 2
        ax.text(
            p.get_x() + p.get_width() / 2.0,
            y,
            "$%.0fM" % height,
            ha="center",
            fontsize=8,
            va="center",
            bbox=dict(facecolor="white", pad=0),
        )


def plot(fig_num, outfile):
    """
    A grouped bar chart showing the cumulative cost and added
    revenue associated with a plan that reduces homicides 10% annually.
    """

    # Perform the calculation
    data = _calculate()

    # Melt the data
    melted = (
        data[["plan_year", "plan_cost", "compounded_revenue"]]
        .assign(
            plan_cost=lambda df: df.plan_cost / 1e6,
            compounded_revenue=lambda df: df.compounded_revenue / 1e6,
        )
        .rename(
            columns={
                "plan_cost": "Annual Costs",
                "compounded_revenue": "Revenue Added Each Year",
            }
        )
        .melt(id_vars=["plan_year"])
    )

    with plt.style.context(default_style):

        # Initialize
        fig, axs = plt.subplots(
            figsize=(5, 5),
            nrows=2,
            ncols=1,
            gridspec_kw=dict(
                left=0.1,
                bottom=0.12,
                right=0.95,
                top=0.77,
                hspace=0.6,
                height_ratios=[1.25, 1],
            ),
        )

        # Make the plots
        _plot_annual_costs(axs[0], melted)
        _plot_net_gain(axs[1], data)

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
            0.96,
            "Annual Costs and Added Property Tax Revenue from a Plan that\nReduces Homicides by 10% Annually for Five Years",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )

        fig.text(
            0.005,
            0.89,
            "Over five years, the return on investment would be $78M",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )

        # Add the footnote
        footnote = (
            r"$\bf{Notes}$: Annual plan costs estimated to be \$30K per homicide per Thomas Abt's $\it{Bleeding \ Out}$;"
            "\n"
            + " " * 15
            + "Revenue estimate compounds annually, assuming a 2.5% increase in housing prices for every reduction in homicide."
        )
        fig.text(
            0.005, 0.002, footnote, fontsize=6, color="#444444", ha="left", va="bottom"
        )

        # Save!
        plt.savefig(outfile, dpi=300)

