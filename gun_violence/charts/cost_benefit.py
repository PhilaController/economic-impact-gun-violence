"""
A two-panel chart showing a bar chart of the number of lives saved 
and the cost / added revenue of the plan over 5 years.
"""
from .. import datasets as gv_data
from . import default_style
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from phila_colors import palette


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

    return df


def plot(fig_num, outfile):
    """
    A two-panel chart showing a bar chart of the number of lives saved 
    and the cost / added revenue of the plan over 5 years.
    """

    # Perform the calculation
    data = _calculate()

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)

        # Initialize
        fig, axs = plt.subplots(
            nrows=2,
            ncols=1,
            figsize=(4.25, 5),
            gridspec_kw=dict(left=0.15, bottom=0.12, right=0.95, top=0.85, hspace=1.0),
        )

        ax = axs[0]
        sns.despine(ax=ax)

        # Top panel: cumulative lives saved
        color = palette["dark-ben-franklin"]
        sns.barplot(
            x=data["plan_year"],
            y=data["lives_saved"],
            color=color,
            ax=ax,
            saturation=1.0,
            zorder=100,
        )

        # Total
        ax.text(
            2,
            155,
            "Total Lives Saved: %.0f" % data["lives_saved"].sum(),
            fontsize=9,
            ha="center",
            va="bottom",
            weight="bold",
            bbox=dict(facecolor="white", pad=0),
        )

        # Format
        ax.set_ylim(-10, 160)
        ax.set_yticks([0, 50, 100, 150])
        plt.setp(ax.get_yticklabels(), fontsize=11)
        plt.setp(ax.get_xticklabels(), fontsize=11)
        ax.set_ylabel("")
        ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
        ax.xaxis.labelpad = 0

        for i, row in data.iterrows():
            ax.text(
                i,
                row["lives_saved"] + 2,
                "%.0f" % row["lives_saved"],
                va="bottom",
                ha="center",
                weight="bold",
                fontsize=10,
                bbox=dict(facecolor="white", pad=0),
            )

        # Bottom panel: cost/benefit
        ax = axs[1]
        sns.despine(ax=ax)

        # Cumulative Plan Cost
        color = palette["love-park-red"]
        ax.plot(
            data["plan_year"],
            data["plan_cost"] / 1e6,
            marker="o",
            color=color,
            mec=color,
            mfc="white",
            mew=3,
            lw=4,
            label="Plan Costs",
            zorder=10,
            clip_on=False,
        )

        # Cumulative Added Revenue
        color = "#666666"
        ax.plot(
            data["plan_year"],
            data["compounded_revenue"] / 1e6,
            marker="o",
            color=color,
            mec=color,
            mfc="white",
            mew=3,
            lw=4,
            label="Potential Revenue",
            zorder=10,
            clip_on=False,
        )

        # fill between!
        ax.fill_between(
            data["plan_year"],
            data["compounded_revenue"] / 1e6,
            data["plan_cost"] / 1e6,
            color=palette["sidewalk"],
        )

        ax.set_ylim(-5, 55)
        ax.set_yticks([0, 25, 50])
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(["$%.0fM" % x for x in ax.get_yticks()], fontsize=11)
        plt.setp(ax.get_xticklabels(), fontsize=11)
        ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
        ax.xaxis.labelpad = 0

        # Add a legend
        ax.legend(
            loc="lower center",
            edgecolor="none",
            framealpha=1,
            ncol=2,
            fontsize=9,
            bbox_to_anchor=(0.5, 0.97),
        )

        # Add the net benefit
        net = (data["compounded_revenue"].sum() - data["plan_cost"].sum()) / 1e6
        ax.annotate(
            "Total Net Benefit: +$%.0fM" % net,
            xy=(3.5, 20),
            xycoords="data",
            xytext=(2.1, 48),
            textcoords="data",
            fontsize=9,
            ha="left",
            va="top",
            weight="bold",
            arrowprops=dict(
                arrowstyle="->", color="black", lw=2, connectionstyle="arc3,rad=0.2"
            ),
            bbox=dict(facecolor="white", pad=0),
            zorder=1000,
        )

        # Add title
        fig.text(
            0.005,
            0.99,
            f"Figure {fig_num}A",
            weight="bold",
            fontsize=9,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.96,
            "Potential Lives Saved from a Plan that Reduces Homicides\nby 10 Percent Annually for Five Years",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )

        fig.text(
            0.005,
            0.52,
            f"Figure {fig_num}B",
            weight="bold",
            fontsize=9,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.52,
            "\nComparing Annual Plan Costs With Potential Tax Revenue\nfrom Increased Housing Prices",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )

        # Add the footnote
        footnote = (
            r"$\bf{Notes}$: Annual plan costs estimated to be \$30K per homicide (see Bleeding Out by Thomas Abt);"
            "\n"
            + " " * 15
            + "Revenue estimate compounds annually, assuming a 2.5% increase in housing prices for every reduction in homicides."
        )
        fig.text(
            0.005,
            0.002,
            footnote,
            fontsize=5,
            color=palette["dark-gray"],
            ha="left",
            va="bottom",
        )

        # Save!
        plt.savefig(outfile, dpi=300)

