from .. import datasets as gv_data
from . import default_style
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from phila_colors import palette


def _plot_age(ax, df):
    """
    Plot the distribution of homicides by age.
    """

    # plot the histogram
    ax.hist(df.age.values, bins="auto", histtype="bar", color=palette["dark-gray"])

    # format the x-axis
    ax.set_xlim(0, 95)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90])
    plt.setp(ax.get_xticklabels(), fontsize=11)
    ax.set_xlabel("Victim Age", weight="bold", fontsize=11)

    # format the y-axis
    ax.set_yticklabels(["{:,.0f}".format(x) for x in ax.get_yticks()], fontsize=11)
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)

    # add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)
    sns.despine(ax=ax, bottom=True)

    # title
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


def _plot_gender(ax, df):
    """
    Plot the gender breakdown
    """
    # get the data by gender
    N = df.groupby(["year", "sex"]).size().reset_index(name="N")

    # plot a stacked bar graph
    colors = ["dark-ben-franklin", "love-park-red"]
    order = ["Male", "Female"]
    N.pivot(index="year", columns="sex", values="N").fillna(0)[order].plot.bar(
        stacked=True, ax=ax, legend=False, color=[palette[c] for c in colors]
    )

    # format the x-axis
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=11)
    ax.set_xlabel("")

    # add a legend
    ax.legend(
        loc="lower right",
        edgecolor="none",
        framealpha=1,
        ncol=3,
        fontsize=10,
        bbox_to_anchor=(1, 0.8),
    )

    # format the y-axis
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)
    ax.set_yticks([0, 100, 200, 300, 400, 500])
    plt.setp(ax.get_yticklabels(), fontsize=11)
    ax.set_ylim(0, 525)

    # add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)
    sns.despine(ax=ax, bottom=True)

    # title
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


def _plot_annual_count(ax, df):
    """
    Plot the annual totals by weapon type
    """
    # Plot the total per year
    N_all = df.groupby("year").size()
    color = palette["ben-franklin-blue"]
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
        zorder=10
    )

    # Plot only the firearm-involved
    N_firearm = df.query("weapon == 'firearm'").groupby("year").size()
    color = palette["love-park-red"]
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
        zorder=10
    )

    # add totals for first and last year
    for (ha, index, offset) in [("center", 0, 0), ("left", -1, +0.25)]:
        for ii, N in enumerate([N_firearm, N_all]):
            va = 'top' if ii == 0 else 'bottom'
            y_offset = -25 if ii == 0 else 10
            ax.text(
                N.index[index] + offset,
                N.values[index] + y_offset,
                N.values[index],
                weight="bold",
                ha=ha,
                va=va,
                fontsize=10,
                bbox=dict(facecolor='white', pad=0, edgecolor='none')
            )

    # format the x-axis
    ax.set_xticks(sorted(df["year"].unique()))
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=11)

    # format the y-axis
    ax.set_yticks([0, 100, 200, 300, 400, 500])
    plt.setp(ax.get_yticklabels(), fontsize=11)
    ax.set_ylim(0, 525)
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)

    # add a legend
    ax.legend(
        loc="lower right",
        edgecolor="none",
        framealpha=1,
        fontsize=10,
        bbox_to_anchor=(1, 0.9),
    )

    # title
    ax.text(
        0.5,
        1.3,
        "Weapon Type",
        fontsize=12,
        weight="bold",
        ha="center",
        va="bottom",
        transform=ax.transAxes,
    )

    # add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)
    sns.despine(ax=ax, bottom=True)


def _plot_race(ax, df):
    """
    Plot the counts by race
    """

    # Do Black/White/Other
    df.loc[~df.race.isin(["Black", "White"]), "race"] = "All Others"
    N = df.groupby(["year", "race"]).size().reset_index(name="N")

    # plot
    colors = ["dark-ben-franklin", "bell-yellow", "love-park-red"]
    order = ["Black", "White", "All Others"]
    N.pivot(index="year", columns="race", values="N").fillna(0)[order].plot.bar(
        stacked=True, ax=ax, legend=False, color=[palette[c] for c in colors]
    )

    # format the x-axis
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=11)
    ax.set_xlabel("")

    # format the y-axis
    plt.setp(ax.get_yticklabels(), fontsize=11)
    ax.set_yticks([0, 100, 200, 300, 400, 500])
    ax.set_ylim(0, 525)
    ax.set_ylabel("Number of Homicides", weight="bold", fontsize=11)

    # add a legend
    ax.legend(
        loc="lower right",
        edgecolor="none",
        framealpha=1,
        ncol=2,
        fontsize=10,
        bbox_to_anchor=(1, 0.9),
    )

    # title
    ax.text(
        0.5,
        1.3,
        "Race",
        fontsize=12,
        weight="bold",
        ha="center",
        va="bottom",
        transform=ax.transAxes,
    )

    # add a y=0 line
    ax.axhline(y=0, c="k", lw=1, clip_on=False, zorder=10)
    sns.despine(ax=ax, bottom=True)


def plot(fig_num, outfile):

    # load the data
    homicides = gv_data.PoliceHomicides.get()

    with plt.style.context("fivethirtyeight"):
        plt.rcParams.update(default_style)

        # create the figure
        grid_kws = dict(
            left=0.09, right=0.95, bottom=0.12, top=0.78, hspace=0.6, wspace=0.5
        )
        nrows = 2
        ncols = 2
        fig, axs = plt.subplots(
            nrows=nrows, ncols=ncols, figsize=(6.4, 5.5), gridspec_kw=grid_kws
        )

        # make each plot
        _plot_annual_count(axs[0, 0], homicides)
        _plot_race(axs[0, 1], homicides)
        _plot_gender(axs[1, 0], homicides)
        _plot_age(axs[1, 1], homicides)

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

