"""
A grouped bar chart showing the cumulative cost and added
revenue associated with a plan that reduces homicides 10% annually.
"""
from .. import datasets as gv_data
from . import default_style, palette
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


def plot(fig_num, outfile):
    """
    A grouped bar chart showing the cumulative cost and added
    revenue associated with a plan that reduces homicides 10% annually.
    """

    # Perform the calculation
    data = _calculate()

    # Melt the data
    data = (
        data[["plan_year", "cumulative_cost", "cumulative_revenue"]]
        .assign(
            cumulative_cost=lambda df: df.cumulative_cost / 1e6,
            cumulative_revenue=lambda df: df.cumulative_revenue / 1e6,
        )
        .rename(
            columns={
                "cumulative_cost": "Plan Costs",
                "cumulative_revenue": "Potential Revenue",
            }
        )
        .melt(id_vars=["plan_year"])
    )

    with plt.style.context(default_style):

        # Initialize
        fig, ax = plt.subplots(
            figsize=(4.5, 3),
            gridspec_kw=dict(left=0.12, bottom=0.18, right=0.95, top=0.7),
        )

        # Grouped bar chart
        sns.barplot(
            x="plan_year",
            y="value",
            hue="variable",
            palette=["#cc3000", "#0f4d90"],
            ax=ax,
            saturation=1.0,
            zorder=100,
            data=data,
        )
        ax.axhline(y=0, c=palette["light-gray"], lw=4, zorder=101)

        ax.set_yticklabels(["$%.0fM" % x for x in ax.get_yticks()], fontsize=11)
        plt.setp(ax.get_xticklabels(), fontsize=11)
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
                fontsize=7,
                bbox=dict(facecolor="white", pad=0),
            )

        # Add title
        fig.text(
            0.005,
            0.99,
            f"Figure {fig_num}",
            weight="bold",
            fontsize=8,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.95,
            "Cumulative Cost and Property Tax Revenue from a Plan that\nReduces Homicides by 10% Annually for Five Years",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )

        fig.text(
            0.005,
            0.845,
            "Over five years, the return on investment would be $79M",
            fontsize=9,
            ha="left",
            va="top",
            style="italic",
        )

        # Add the footnote
        footnote = (
            r"$\bf{Notes}$: Annual plan costs estimated to be \$30K per homicide (see Bleeding Out by Thomas Abt);"
            "\n"
            + " " * 15
            + "Revenue estimate compounds annually, assuming a 2.5% increase in housing prices for every reduction in homicides."
        )
        fig.text(
            0.005, 0.002, footnote, fontsize=5, color="#444444", ha="left", va="bottom"
        )

        # Save!
        plt.savefig(outfile, dpi=300)

