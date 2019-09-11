"""
A two panel chart: 

    Top panel:  A grouped bar chart showing the annual plan costs and 
                added revenue associated with a plan that reduces 
                homicides 10% annually.
    Bottom panel:   A line chart showing the cumulative return on investment
                    of such a plan.
"""
from .. import datasets as gv_data
from . import default_style, palette, light_palette
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns


def simulate_violence_reduction_plan():
    """
    Simulate the violence reduction plan over five years, assuming 
    a 10% annual reduction in homicides. This calculates:
    
    1. The number of lives saved.
    2. The annual plan costs, assuming a funding level of $30K per homicide.
    3. The added tax revenue from property tax revenues.
    """
    NUM_YEARS = 5  # Run analysis for 5 years
    START_YEAR = 2018  # First year of plan
    COST_PER_HOMICIDE = 30e3  # Per Thomas Abt's estimate in Bleeding Out
    TOTAL_REVENUE = 129.9e6  # From analysis of property assessments near homicides

    # Calculte the number of lives saved
    homicides = [351]
    for i in range(1, NUM_YEARS):
        homicides.append(homicides[i - 1] - np.round(homicides[i - 1] * 0.1))

    # Make into a DataFrame
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
    Plot a line chart showing the annual net gain.
    """
    # Net gain is the difference between cumulative revenue added and cost
    net_gain = (data["cumulative_revenue"] - data["cumulative_cost"]) / 1e6

    # Make the bar plot
    color = palette["almost-black"]
    ax.plot(
        data["plan_year"],
        net_gain,
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

    # Add the dollar amounts
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

    # Format the x-axis
    ax.set_xlim(left=-0.75)
    ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels([1, 2, 3, 4, 5], fontsize=11)
    ax.xaxis.labelpad = 0

    # Format the y-axis
    ax.set_ylabel("")
    ax.set_ylim(-30)
    ax.set_yticks([0, 40, 80])
    ax.set_yticklabels([format_currency(x) for x in ax.get_yticks()], fontsize=11)
    plt.setp(ax.get_yticklabels(), ha="center")

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
    Plot a grouped bar chart showing the annual cost/revenue numbers.
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

    # Format the x-axis
    ax.set_xlim(left=-0.75)
    plt.setp(ax.get_xticklabels(), fontsize=11)
    ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
    ax.xaxis.labelpad = 0

    # Format the y-axis
    ax.set_ylabel("")
    ax.set_yticklabels(["$%.0fM" % x for x in ax.get_yticks()], fontsize=11)
    plt.setp(ax.get_yticklabels(), ha="center")

    # Add a grid
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

    # Add the total dollar amount above the bars
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
    A two panel chart: 

        Top panel:  A grouped bar chart showing the annual plan costs and 
                    added revenue associated with a plan that reduces 
                    homicides 10% annually.
        Bottom panel:   A line chart showing the cumulative return on investment
                        of such a plan.
    """
    # Perform the calculation
    data = simulate_violence_reduction_plan()

    # Melt the data into the right format
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

    # Plot
    with plt.style.context(default_style):

        # Initialize the axes/figure
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

        # Add a figure title
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

        # The sub title
        net_gain = ((data["cumulative_revenue"] - data["cumulative_cost"]) / 1e6).iloc[
            -1
        ]
        fig.text(
            0.005,
            0.89,
            "Over five years, the return on investment would be $%.0fM" % net_gain,
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

