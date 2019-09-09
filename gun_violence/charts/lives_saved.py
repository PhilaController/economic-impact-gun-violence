"""
A bar chart showing the total number of lives saved associated 
with a plan that reduces homicides 10% annually.
"""
from .. import datasets as gv_data
from . import default_style, palette
from .cost_benefit import _calculate
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns


def plot(fig_num, outfile):
    """
    A bar chart showing the total number of lives saved associated 
    with a plan that reduces homicides 10% annually.
    """

    # Perform the calculation
    data = _calculate()
    data["cumulative_lives_saved"] = data["lives_saved"].cumsum()

    with plt.style.context(default_style):

        # Initialize
        fig, ax = plt.subplots(
            figsize=(4.5, 3),
            gridspec_kw=dict(left=0.12, bottom=0.18, right=0.95, top=0.72),
        )

        # Top panel: cumulative lives saved
        color = palette["blue"]
        sns.barplot(
            x=data["plan_year"],
            y=data["cumulative_lives_saved"],
            color=color,
            ax=ax,
            saturation=1.0,
            zorder=100,
        )

        # Total
        total = data["lives_saved"].sum()

        # Format
        # ax.set_ylim(0, 160)
        # ax.set_yticks([0, 50, 100, 150])
        plt.setp(ax.get_yticklabels(), fontsize=11)
        plt.setp(ax.get_xticklabels(), fontsize=11)
        ax.set_ylabel("")
        ax.set_xlabel("Plan Year", fontsize=10, weight="bold")
        ax.xaxis.labelpad = 0

        ax.axhline(y=0, c=palette["light-gray"], lw=4, zorder=101)

        for i, row in data.iterrows():
            ax.text(
                i,
                row["cumulative_lives_saved"] + 2,
                "%.0f" % row["cumulative_lives_saved"],
                va="bottom",
                ha="center",
                weight="bold",
                fontsize=10,
                # bbox=dict(facecolor="white", pad=0),
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
            "Cumulative Lives Saved from a Plan that Reduces Homicides\nby 10% Annually for Five Years",
            weight="bold",
            fontsize=10,
            ha="left",
            va="top",
        )

        fig.text(
            0.005,
            0.845,
            "Over five years, the plan would save a total of %d lives" % total,
            fontsize=9,
            ha="left",
            va="top",
            style="italic",
        )

        # Add the footnote
        footnote = r"$\bf{Note}$: The calculation compares to a baseline scenario where the homicide total remains at its 2018 level"
        fig.text(
            0.005, 0.002, footnote, fontsize=6, color="#444444", ha="left", va="bottom"
        )

        # Save!
        plt.savefig(outfile, dpi=300)

