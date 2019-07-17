from .. import data_dir
from . import EPSG
from .core import geocode, Dataset
from .geo import *
from .fred import PhillyMSAHousingIndex

import os
from glob import glob
import pandas as pd
import geopandas as gpd
import numpy as np

from phila_opa.db import OPAData00s
from phila_opa.select import residential

__all__ = ["ResidentialSales"]


def generate_sales_file(start_year=2006, end_year=2020, opa_data_dir=None):
    """
    Generate a sales file of all unique sales occuring between the specified dates.

    Notes
    -----
    This includes only residential sales.
    """

    # initialize the database
    if opa_data_dir is None:
        opa_data_dir = "/Users/nicholashand/LocalWork/Data/OPA/"
    db = OPAData00s(data_dir=opa_data_dir)

    # do tax years 2006 through 2019
    out = []
    for tax_year in range(start_year, end_year + 1):
        print(f"Processing tax year {tax_year}...")
        df = db.load_tax_year(tax_year, geocode=tax_year < 2020)
        out.append(residential(df))

    # concatenate, only keeping overlapping columns
    out = pd.concat(out, axis=0, join="inner")
    print("  Total number of sales = ", len(out))

    # sort by tax_year, smallest to largest
    out = out.sort_values(by="tax_year", ascending=True)

    # remove duplicates
    out = out.drop_duplicates(
        subset=["parcel_number", "sale_date", "sale_price"], keep="first"
    )
    print("  Number of non-duplicated sales = ", len(out))

    # output directory
    dirname = os.path.join(data_dir, "OPA")
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # save!
    path = os.path.join(dirname, f"sales_file_{start_year}_to_{end_year}.csv")
    out.to_csv(path, index=False)

    return out


def generate_value_added_sales_by_year(start_year=2006, end_year=2018):
    """
    Generate the sales files by year with value-added
    """

    # get the main sales file
    matches = glob(os.path.join(data_dir, "OPA", "sales_file_*.csv"))
    if not len(matches):
        sales_data = generate_sales_file()
    else:
        sales_data = pd.read_csv(matches[0])

    # format the data
    sales_data = (
        sales_data.assign(
            sale_date=lambda df: pd.to_datetime(df["sale_date"]),
            sale_year=lambda df: df.sale_date.dt.year,
            sale_price_psf=lambda df: df.sale_price / df.total_livable_area,
            test=lambda df: ~np.isinf(df.sale_price_psf) & df.sale_price_psf.notnull(),
            housing_index=lambda df: PhillyMSAHousingIndex.interpolate(df["sale_date"]),
        )
        .assign(
            housing_index=lambda df: df.housing_index / df.housing_index.max(),
            sale_price_indexed=lambda df: df.sale_price / df.housing_index,
        )
        .query("test == True")
        .drop(labels=["test"], axis=1)
    )

    # make sure the output directory exists
    dirname = os.path.join(data_dir, "OPA", "ValueAdded")
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # geocode!
    zip_codes = ZIPCodes.get()
    neighborhoods = Neighborhoods.get()

    # save each year
    for year in range(start_year, end_year + 1):
        print(f"Processing sale year {year}...")

        # get this year's data
        df = sales_data.query("sale_year == @year")

        # convert to geopandas
        gdf = (
            gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(
                    df["lng"].astype(float), df["lat"].astype(float)
                ),
                crs={"init": "epsg:4326"},
            )
            .to_crs(epsg=EPSG)
            .drop(labels=["lat", "lng"], axis=1)
        )

        # geocode
        gdf = gdf.pipe(geocode, zip_codes).pipe(geocode, neighborhoods)

        path = os.path.join(dirname, f"{year}.csv")
        gdf.to_csv(path, index=False)


def _get_IQR_limits(df, column, iqr_factor=1.5):
    assert column in df.columns

    # compute the inter quartile ratio
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    # trim by lower and upper bounds
    lower = Q1 - iqr_factor * IQR
    upper = Q3 + iqr_factor * IQR
    return lower, upper


def _remove_outliers(df, column, iqr_factor=1.5):
    lower, upper = _get_IQR_limits(df, column, iqr_factor=iqr_factor)
    return df.query("@lower < %s <= @upper" % column)


class ResidentialSales(Dataset):
    """
    Data for residential sales from 2006 to 2018, extracted from the OPA 
    annual certified assessments.

    Notes
    -----
    These are trimmed to remove outliers on an annual basis using 1.5 times 
    the interquartile range (IQR).
    """

    date_columns = ["sale_date"]

    @classmethod
    def download(cls):

        files = glob(os.path.join(data_dir, "OPA", "ValueAdded", "*.csv"))
        out = []
        for f in files:

            # load the data
            df = (
                pd.read_csv(f, low_memory=False)
                .query("sale_price > 1")
                .assign(
                    log_sale_price=lambda df: np.log10(df.sale_price),
                    log_sale_price_indexed=lambda df: np.log10(df.sale_price_indexed),
                    is_condo=lambda df: df.parcel_number.astype(str).str.startswith(
                        "888"
                    ),
                )
                .pipe(_remove_outliers, "log_sale_price")
            )
            out.append(df)

        return (
            pd.concat(out)
            .sort_values("sale_date", ascending=False)
            .reset_index(drop=True)
        )
