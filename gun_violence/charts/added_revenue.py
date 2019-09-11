"""
A chart showing a bar chart of the potential added property tax 
revenue over five years.
"""
from .. import datasets as gv_data
from . import default_style, palette
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from .cost_benefit import simulate_violence_reduction_plan


def plot(fig_num, outfile):
    """
    A chart showing a bar chart of the potential added property tax 
    revenue over five years.
    """
    # Perform the calculation
    data = simulate_violence_reduction_plan()

    with plt.style.context(default_style):

        # Initialize
        fig, ax = plt.subplots(
            nrows=1,
            ncols=1,
            figsize=(5, 3),
            gridspec_kw=dict(left=0.13, bottom=0.17, right=0.95, top=0.75, hspace=1.0),
        )

        # Top panel: cumulative added revenue
        color = palette["blue"]
        sns.barplot(
            x=data["plan_year"],
            y=data["compounded_revenue"] / 1e6,
            color=color,
            ax=ax,
            saturation=1.0,
            zorder=100,
        )

        # Format y-axis
        ax.set_ylabel("")
        ax.set_ylim(0, 55)
        ax.set_yticks([0, 10, 20, 30, 40, 50])
        ax.set_yticklabels(["$%.0fM" % x for x in ax.get_yticks()], fontsize=11)

        # Format x-axis
        ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
        plt.setp(ax.get_xticklabels(), fontsize=11)
        ax.xaxis.labelpad = 0

        # Add a y=0 line
        ax.axhline(y=0, c=palette["light-gray"], lw=4, zorder=101)

        # Add numbers above the bars
        for i, row in data.iterrows():
            ax.text(
                i,
                row["compounded_revenue"] / 1e6,
                "$%.0fM" % (row["compounded_revenue"] / 1e6),
                va="bottom",
                ha="center",
                weight="bold",
                fontsize=10,
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
            0.945,
            "Potential Added Property Tax Revenue from a Plan that Reduces\nHomicides by 10 Percent Annually for Five Years",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )

        # Sub title
        total = (data["compounded_revenue"] / 1e6).sum()
        fig.text(
            0.005,
            0.84,
            "The plan has the potential to add a total of $%.0fM over five years"
            % total,
            style="italic",
            fontsize=9,
            ha="left",
            va="top",
        )

        # Add the footnote
        footnote = r"$\bf{Notes}$: Revenue estimates compound annually, assuming a 2.5% increase in housing prices for every reduction in homicides."
        fig.text(
            0.005, 0.002, footnote, fontsize=6, color="#444444", ha="left", va="bottom"
        )

        # Save!
        plt.savefig(outfile, dpi=300)

