"""
A line chart the average price per square foot for the two distance
bins used in the analysis, aggregated by the time relative to the 
homicide occurrence
"""
from .. import datasets as gv_data
from ..modeling import test_pta, get_binned_pta_data
from . import default_style, palette, digital_standards
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib.transforms as transforms
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel


def plot_gp(ax, x, y, noise=0.01, color="k", label=""):
    x_pred = np.linspace(x.min(), x.max(), 100)
    kernel = ConstantKernel(1) * RBF(length_scale=1)
    noise = y * noise

    gp = GaussianProcessRegressor(
        kernel=kernel, n_restarts_optimizer=100, alpha=noise ** 2
    ).fit(np.atleast_2d(x.values).T, y.values)
    y_mean, sigma = gp.predict(np.atleast_2d(x_pred).T, return_std=True)

    ax.plot(x_pred, y_mean, color=color, lw=1, zorder=10)
    ax.plot(
        x,
        y,
        ls="",
        color=color,
        mfc="white",
        mec=color,
        marker="o",
        mew=2,
        zorder=10,
        label=label,
    )
    plt.fill_between(
        x_pred,
        y_mean - 1.9600 * sigma,
        y_mean + 1.9600 * sigma,
        alpha=0.5,
        color=color,
        zorder=10,
    )


def _load_data():
    """
    Load the data we will need.
    """
    # Load sales and homicides
    sales = gv_data.ResidentialSales.get()
    homicides = gv_data.PoliceHomicides.get()

    # Remove any null entries
    sales = sales.loc[sales.geometry.notnull()]
    homicides = homicides.loc[homicides.geometry.notnull()]

    # Perform the PTA calculation
    salesNoCondos = sales.loc[~sales.is_condo]
    result = test_pta(salesNoCondos, homicides, time_window=180, distances=[0.75, 1.5])

    # Bin
    pta_075 = get_binned_pta_data(
        result["spacetime_flag_within_0.75"], bin_size=30, time_window=180
    )
    pta_15 = get_binned_pta_data(
        result["spacetime_flag_within_1.5"], bin_size=30, time_window=180
    )
    return pta_075, pta_15


def plot(fig_num, outfile):
    """
    A line chart the average price per square foot for the two distance
    bins used in the analysis, aggregated by the time relative to the 
    homicide occurrence
    """
    # Load the data
    pta_075, pta_15 = _load_data()

    with plt.style.context(default_style):

        # Initialize the axes/figure
        fig, ax = plt.subplots(
            figsize=(6, 4),
            gridspec_kw=dict(left=0.03, bottom=0.12, right=0.99, top=0.7),
        )

        plot_gp(
            ax,
            pta_075["bin_centers"],
            pta_075["sale_price_psf"],
            noise=0.01,
            color=digital_standards["dark-ben-franklin"],
            label="Sales from 0 to 0.75 miles",
        )
        plot_gp(
            ax,
            pta_15["bin_centers"],
            pta_15["sale_price_psf"],
            noise=0.01,
            color=palette["dark-gray"],
            label="Sales from 0.75 to 1.5 miles",
        )

        ax.legend(
            loc="lower right",
            ncol=1,
            bbox_transform=ax.transAxes,
            bbox_to_anchor=(1, 1),
            fontsize=10,
            columnspacing=0.2,
            handletextpad=0.2,
        )

        ax.axvspan(xmin=-60, xmax=60, color=palette["light-gray"], zorder=1, alpha=0.5)
        ax.axvline(x=0, c=palette["medium-gray"], lw=1, zorder=1)
        ax.set_ylim(79, 101)
        ax.set_yticks([80, 85, 90, 95, 100])
        ax.set_yticklabels([f"${x}" for x in ax.get_yticks()], fontsize=12)
        plt.setp(ax.get_yticklabels(), ha="left")
        ax.set_xlabel(
            "Days before and after homicide occurrence", fontsize=11, weight="bold"
        )
        fig.text(
            0.005,
            1.05,
            "Average sale price\nper square foot",
            fontsize=11,
            weight="bold",
            transform=transforms.blended_transform_factory(
                fig.transFigure, ax.transAxes
            ),
            ha="left",
            va="bottom",
        )

        ax.annotate(
            "Period studied",
            xy=(20, 98),
            xycoords="data",
            xytext=(65, 97),
            textcoords="data",
            arrowprops=dict(
                arrowstyle="->",
                lw=1,
                color=palette["almost-black"],
                connectionstyle="arc3,rad=0.3",
            ),
            weight="bold",
            bbox=dict(facecolor="white", pad=0),
        )
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
            0.95,
            "Average Sale Prices Aggregated by Time Relative to Homicide Occurrence",
            weight="bold",
            fontsize=11,
            ha="left",
            va="top",
        )
        fig.text(
            0.005,
            0.90,
            "The two distance bins used in the analysis appear consistent with the parallel trend assumption",
            fontsize=10,
            ha="left",
            va="top",
            style="italic",
        )
        plt.savefig(outfile)
