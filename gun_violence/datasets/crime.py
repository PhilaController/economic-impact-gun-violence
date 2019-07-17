from . import EPSG
from .core import Dataset, geocode, replace_missing_geometries
from .geo import *
from .. import data_dir
import carto2gpd
import numpy as np
import os
import pandas as pd
import geopandas as gpd
import json
import requests
from bs4 import BeautifulSoup

__all__ = [
    "CrimeIncidents",
    "CriminalHomicides",
    "InquirerHomicides",
    "Shootings",
    "HomicideCounts",
]


class Shootings(Dataset):
    """
    Shooting incidents in Philadelphia

    Source: https://www.opendataphilly.org/dataset/shooting-victims
    """

    date_columns = ["date"]

    @classmethod
    def download(cls):
        url = "https://phl.carto.com/api/v2/sql"
        gdf = (
            replace_missing_geometries(carto2gpd.get(url, "shootings"))
            .fillna(np.nan)
            .to_crs(epsg=EPSG)
        )

        return (
            gdf.pipe(geocode, ZIPCodes.get())
            .pipe(geocode, Neighborhoods.get())
            .assign(
                time=lambda df: df.time.replace("<Null>", np.nan).fillna("00:00:00"),
                date=lambda df: pd.to_datetime(
                    df.date_.str.slice(0, 10).str.cat(df.time, sep=" ")
                ),
            )
            .drop(labels=["point_x", "point_y", "date_", "time", "objectid"], axis=1)
            .sort_values("date", ascending=False)
            .reset_index(drop=True)
        )

    @classmethod
    def years(cls):
        """
        Return a list of the years for which data is available
        """

        crimes = cls.dask()
        return crimes.year.unique().compute().tolist()

    @classmethod
    def crime_types(cls):
        """
        Return a list of the types of crime incidents 
        """
        crimes = cls.dask()
        return crimes.text_general_code.unique().compute().dropna().tolist()

    @classmethod
    def query_by_year(cls, *years):
        """
        Return the crime incidents only for the specified year(s).

        For a list of available years, see the ``years()`` function.
        """

        # load crimes as a dask dataframe
        crimes = cls.dask()

        # select and return
        selection = crimes.year.isin(years)
        return cls._format_data(crimes.loc[selection].compute())

    @classmethod
    def query_by_type(cls, *types):
        """
        Return the crime incidents only for the specified crime type(s).

        For a list of the types of crimes, see the ``crime_types()`` function.
        """

        # load crimes as a dask dataframe
        crimes = cls.dask()

        # select and return
        selection = crimes.text_general_code.isin(types)
        return cls._format_data(crimes.loc[selection].compute())


class CrimeIncidents(Dataset):
    """
    Crime incidents in Philadelphia

    Source: https://www.opendataphilly.org/dataset/crime-incidents
    """

    date_columns = ["dispatch_date_time"]

    @classmethod
    def download(cls):
        url = "https://phl.carto.com/api/v2/sql"
        fields = [
            "dc_dist",
            "dc_key",
            "dispatch_date_time",
            "location_block",
            "psa",
            "text_general_code",
            "ucr_general",
        ]
        gdf = replace_missing_geometries(
            carto2gpd.get(url, "incidents_part1_part2", fields=fields)
        ).to_crs(epsg=EPSG)

        return (
            gdf.pipe(geocode, ZIPCodes.get())
            .pipe(geocode, Neighborhoods.get())
            .assign(
                dispatch_date_time=lambda df: pd.to_datetime(df.dispatch_date_time),
                year=lambda df: df.dispatch_date_time.dt.year,
            )
            .sort_values("dispatch_date_time", ascending=False)
            .reset_index(drop=True)
        )

    @classmethod
    def years(cls):
        """
        Return a list of the years for which data is available
        """

        crimes = cls.dask()
        return crimes.year.unique().compute().tolist()

    @classmethod
    def crime_types(cls):
        """
        Return a list of the types of crime incidents 
        """
        crimes = cls.dask()
        return crimes.text_general_code.unique().compute().dropna().tolist()

    @classmethod
    def query_by_year(cls, *years):
        """
        Return the crime incidents only for the specified year(s).

        For a list of available years, see the ``years()`` function.
        """

        # load crimes as a dask dataframe
        crimes = cls.dask()

        # select and return
        selection = crimes.year.isin(years)
        return cls._format_data(crimes.loc[selection].compute())

    @classmethod
    def query_by_type(cls, *types):
        """
        Return the crime incidents only for the specified crime type(s).

        For a list of the types of crimes, see the ``crime_types()`` function.
        """

        # load crimes as a dask dataframe
        crimes = cls.dask()

        # select and return
        selection = crimes.text_general_code.isin(types)
        return cls._format_data(crimes.loc[selection].compute())


class CriminalHomicideIncidents(Dataset):
    """
    Criminal homicide incidents in Philadelphia

    Source: https://www.opendataphilly.org/dataset/crime-incidents
    """

    date_columns = ["dispatch_date_time"]

    @classmethod
    def download(cls):
        url = "https://phl.carto.com/api/v2/sql"
        fields = [
            "dc_dist",
            "dc_key",
            "dispatch_date_time",
            "location_block",
            "psa",
            "text_general_code",
            "ucr_general",
        ]
        where = "text_general_code = 'Homicide - Criminal'"
        gdf = replace_missing_geometries(
            carto2gpd.get(url, "incidents_part1_part2", fields=fields, where=where)
        ).to_crs(epsg=EPSG)

        return (
            gdf.pipe(geocode, ZIPCodes.get())
            .pipe(geocode, Neighborhoods.get())
            .assign(
                dispatch_date_time=lambda df: pd.to_datetime(df.dispatch_date_time),
                year=lambda df: df.dispatch_date_time.dt.year,
            )
            .sort_values("dispatch_date_time", ascending=False)
            .reset_index(drop=True)
        )


class InquirerHomicides(Dataset):
    """
    Data for Philadelphia homicides scraped from the Inquirer's website.

    Source
    ------
    http://data.philly.com/philly/crime/homicides/
    """

    date_columns = ["date"]

    @classmethod
    def download(cls):

        path = os.path.join(data_dir, cls.__name__, "homicides.json")
        d = json.load(open(path))
        out = []
        for key in d:
            out += d[key]

        df = (
            pd.DataFrame(out)
            .rename(
                columns=dict(
                    a="age",
                    hDt="date",
                    m="motive",
                    r="race",
                    v="victim",
                    w="weapon",
                    s="sex",
                    t="time",
                )
            )
            .assign(
                date=lambda df: pd.to_datetime(df["date"].str.cat(df["time"], sep=" ")),
                year=lambda df: df["date"].dt.year,
            )
            .drop(labels=["time", "n"], axis=1)
        )
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

        return (
            gdf.pipe(geocode, ZIPCodes.get())
            .pipe(geocode, Neighborhoods.get())
            .sort_values("date", ascending=False)
            .reset_index(drop=True)
        )


class HomicideCounts(Dataset):
    """
    The total homicide count and year-to-date values, as given 
    on the Philadelphia Police Department's website.

    Source
    ------
    https://www.phillypolice.com/crime-maps-stats/
    """

    @classmethod
    def download(cls):

        # parse the website
        url = "https://www.phillypolice.com/crime-maps-stats/"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")

        # load the tables
        tables = soup.select("#homicide-stats")

        # parse YTD values
        years = [int(x.text) for x in tables[0].select("tr")[0].select("th")[1:]]
        elements = tables[0].select("tr")[1].select("td")
        totals = list(
            map(
                int,
                [elements[1].select_one(".homicides-count").text]
                + [x.text for x in elements[2:]],
            )
        )
        YTD = pd.Series(
            totals, index=pd.Index(years, name="year"), name="homicide_count_ytd"
        )

        # full-year values
        years = [int(x.text) for x in tables[1].select("tr")[0].select("th")[1:]]
        values = [int(x.text) for x in tables[1].select("tr")[1].select("td")[1:]]
        full_year = pd.Series(
            values, index=pd.Index(years, name="year"), name="homicide_count"
        )

        # return
        return pd.concat([YTD, full_year], axis=1)
