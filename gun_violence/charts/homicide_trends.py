"""
A 4x4 panel chart showing the following trends in homicides in Philadelphia: 

1. Weapon type
2. Race
3. Gender
4. Age
"""
from .. import datasets as gv_data
from . import default_style, palette
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns


def _age_panel(ax, df):
    """
    Histogram showing the distribution of homicides by victim age.
    """
    # Plot the histogram
    ax.hist(df.age.values, bins="auto", histtype="bar", color=palette["blue"])

    # Format the x-axis
    ax.set_xlim(-5, 95)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90])
    plt.setp(ax.get_xticklabels(), fontsize=11)
    ax.set_xlabel("Victim Age", weight="bold", fontsize=11)

    # Format the y-axis
    ax.set_yticklabels(["{:,.0f}".format(x) for x in ax.get_yticks()], fontsize=11)
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)

    # Sdd a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)

    # Title
    ax.text(
        0.5,
        1.1,
        "Age",
        fontsize=12,
        weight="bold",
        ha="center",
        va="bottom",
        transform=ax.transAxes,
    )


def _gender_panel(ax, df):
    """
    Stacked bar graph showing the homicide victims by gender.
    """
    # Get the data by year and gender
    N = df.groupby(["year", "sex"]).size().reset_index(name="N")

    # Plot a stacked bar graph
    colors = ["blue", "red"]
    order = ["Male", "Female"]
    N.pivot(index="year", columns="sex", values="N").fillna(0)[order].plot.bar(
        stacked=True, ax=ax, legend=False, color=[palette[c] for c in colors]
    )

    # Format the x-axis
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=11)
    ax.set_xlabel("")

    # Add a legend
    ax.legend(
        loc="lower center",
        edgecolor="none",
        framealpha=1,
        ncol=3,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.8),
    )

    # Format the y-axis
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)
    ax.set_yticks([0, 100, 200, 300, 400, 500])
    plt.setp(ax.get_yticklabels(), fontsize=11)
    ax.set_ylim(0, 525)

    # Add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)

    # Title
    ax.text(
        0.5,
        1.1,
        "Gender",
        fontsize=12,
        weight="bold",
        ha="center",
        va="bottom",
        transform=ax.transAxes,
    )


def _weapon_panel(ax, df):
    """
    Plot the annual homicide total for all homicides and firearms only.
    """
    # Plot the total per year
    N_all = df.groupby("year").size()
    color = palette["blue"]
    ax.plot(
        N_all.index.tolist(),
        N_all.values,
        marker="o",
        color=color,
        mec=color,
        mfc="white",
        mew=3,
        lw=4,
        label="All Homicides",
        zorder=10,
    )

    # Plot only the firearm-involved
    N_firearm = df.query("weapon == 'firearm'").groupby("year").size()
    color = palette["red"]
    ax.plot(
        N_firearm.index.tolist(),
        N_firearm.values,
        marker="o",
        color=color,
        mec=color,
        mfc="white",
        mew=3,
        lw=3,
        label="Firearm Only",
        zorder=10,
    )

    # Add totals as text for first and last year
    for (ha, index, offset) in [("center", 0, 0), ("left", -1, +0.25)]:
        for ii, N in enumerate([N_firearm, N_all]):
            va = "top" if ii == 0 else "bottom"
            if index != 0:
                y_offset = -25 if ii == 0 else 10
            else:
                y_offset = -30 if ii == 0 else 25
            ax.text(
                N.index[index] + offset,
                N.values[index] + y_offset,
                N.values[index],
                weight="bold",
                ha=ha,
                va=va,
                fontsize=10,
                bbox=dict(facecolor="white", pad=0, edgecolor="none"),
            )

    # Format the x-axis
    ax.set_xticks(sorted(df["year"].unique()))
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=11)

    # Format the y-axis
    ax.set_yticks([0, 100, 200, 300, 400, 500])
    plt.setp(ax.get_yticklabels(), fontsize=11)
    ax.set_ylim(0, 525)
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)

    # Add a legend
    ax.legend(
        loc="lower center",
        edgecolor="none",
        framealpha=1,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.92),
        ncol=1,
    )

    # Title
    ax.text(
        0.5,
        1.325,
        "Weapon Type",
        fontsize=12,
        weight="bold",
        ha="center",
        va="bottom",
        transform=ax.transAxes,
    )

    # Add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)


def _race_panel(ax, df):
    """
    Stacked bar graph showing breakdown of homicide by race: Black, White, and All Others
    """
    df["race"] = df["race"].replace({"Black": "Black/African American"})

    # Do Black/White/Other
    df.loc[~df.race.isin(["Black/African American", "White"]), "race"] = "All Others"
    N = df.groupby(["year", "race"]).size().reset_index(name="N")

    # Plot
    colors = ["blue", "yellow", "red"]
    order = ["Black/African American", "White", "All Others"]
    N.pivot(index="year", columns="race", values="N").fillna(0)[order].plot.bar(
        stacked=True, ax=ax, legend=False, color=[palette[c] for c in colors]
    )

    # Format the x-axis
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=11)
    ax.set_xlabel("")

    # Format the y-axis
    plt.setp(ax.get_yticklabels(), fontsize=11)
    ax.set_yticks([0, 100, 200, 300, 400, 500])
    ax.set_ylim(0, 525)
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)

    # Add a legend
    handles, labels = ax.get_legend_handles_labels()
    order = [1, 0, 2]
    ax.legend(
        [handles[idx] for idx in order],
        [labels[idx] for idx in order],
        loc="lower right",
        edgecolor="none",
        framealpha=1,
        ncol=2,
        fontsize=9,
        bbox_to_anchor=(1.15, 0.92),
        columnspacing=0.7,
    )

    # Title
    ax.text(
        0.5,
        1.325,
        "Race",
        fontsize=12,
        weight="bold",
        ha="center",
        va="bottom",
        transform=ax.transAxes,
    )

    # Add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)


def plot(fig_num, outfile):
    """
    Plot a 4x4 panel chart showing the following trends in homicides in Philadelphia: 

    1. Weapon type
    2. Race
    3. Gender
    4. Age

    Data range is 2006 to 2018.
    """
    # Load the data
    homicides = gv_data.PoliceHomicides.get()

    with plt.style.context(default_style):

        # Create the figure
        fig, axs = plt.subplots(
            nrows=2,
            ncols=2,
            figsize=(6.4, 5.5),
            gridspec_kw=dict(
                left=0.09, right=0.95, bottom=0.12, top=0.77, hspace=0.6, wspace=0.5
            ),
        )

        # Make each plot
        _weapon_panel(axs[0, 0], homicides)
        _race_panel(axs[0, 1], homicides)
        _gender_panel(axs[1, 0], homicides)
        _age_panel(axs[1, 1], homicides)

        # Add the footnote
        footnote = r"$\bf{Source}$: Police Department"
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
            "Defining the Issue: Homicides in Philadelphia Since 2006",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.93,
            "Homicides are driven by firearm deaths & overwhelmingly affect black men between the ages of 18 & 35",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )

        plt.savefig(outfile, dpi=300)

