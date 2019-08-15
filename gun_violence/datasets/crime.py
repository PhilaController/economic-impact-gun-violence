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
    "CriminalHomicideIncidents",
    "InquirerHomicides",
    "Shootings",
    "HomicideCounts",
    "PoliceHomicides",
]


class Shootings(Dataset):
    """
    Shooting incidents in Philadelphia

    Source: https://www.opendataphilly.org/dataset/shooting-victims
    """

    date_columns = ["date"]

    @classmethod
    def download(cls, **kwargs):
        url = "https://phl.carto.com/api/v2/sql"
        gdf = (
            replace_missing_geometries(carto2gpd.get(url, "shootings"))
            .fillna(np.nan)
            .to_crs(epsg=EPSG)
        )

        return (
            gdf.pipe(geocode, ZIPCodes.get())
            .pipe(geocode, Neighborhoods.get())
            .pipe(geocode, PoliceDistricts.get())
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
    def download(cls, **kwargs):
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
            .pipe(geocode, PoliceDistricts.get())
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
    def download(cls, **kwargs):
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
        where = "text_general_code LIKE '%Homicide - Criminal%'"
        gdf = replace_missing_geometries(
            carto2gpd.get(url, "incidents_part1_part2", fields=fields, where=where)
        ).to_crs(epsg=EPSG)

        return (
            gdf.pipe(geocode, ZIPCodes.get())
            .pipe(geocode, Neighborhoods.get())
            .pipe(geocode, PoliceDistricts.get())
            .assign(
                dispatch_date_time=lambda df: pd.to_datetime(df.dispatch_date_time),
                year=lambda df: df.dispatch_date_time.dt.year,
                text_general_code=lambda df: df.text_general_code.str.strip(),
                time_offset=lambda df: (
                    df.dispatch_date_time
                    - pd.to_datetime("1/1/2006").tz_localize("UTC")
                )
                .dt.total_seconds()
                .values,
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
    def download(cls, **kwargs):

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
            .pipe(geocode, PoliceDistricts.get())
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
    def download(cls, **kwargs):

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


class PoliceHomicides(Dataset):
    """
    Data for Philadelphia homicides from the Police Department

    Source
    ------
    Email from Michael Urciuoli on July 30
    """

    date_columns = ["dispatch_date_time"]

    @classmethod
    def download(cls, **kwargs):

        path = os.path.join(
            data_dir,
            cls.__name__,
            "Homicides_01_01_06_thru_12_31_18 (with_age_race_sex_hispanic).xlsx",
        )

        # Load and format the raw excel file
        df = (
            pd.read_excel(path, sheet_name="Data")
            .assign(
                TIME_=lambda df: df.TIME_.fillna(""),
                HISPANIC=lambda df: np.where(df.HISPANIC == "Y", 1, 0),
                RACE=lambda df: df.RACE.replace(
                    {"B": "Black", "W": "White", "A": "Asian", "I": "Other/Unknown"}
                ),
                SEX=lambda df: df.SEX.replace({"M": "Male", "F": "Female"}),
                dispatch_date_time=lambda df: pd.to_datetime(
                    df["DATE"].str.cat(df["TIME_"], sep=" ")
                ).dt.tz_localize("UTC"),
                year=lambda df: df.dispatch_date_time.dt.year,
                time_offset=lambda df: (
                    df.dispatch_date_time
                    - pd.to_datetime("1/1/2006").tz_localize("UTC")
                )
                .dt.total_seconds()
                .values,
            )
            .rename(
                columns={
                    "DCNUMBER": "dc_key",
                    "LOCATION": "location_block",
                    "RACE": "race",
                    "HISPANIC": "hispanic",
                    "AGE": "age",
                    "Weapon": "weapon",
                    "SEX": "sex",
                }
            )
            .drop(labels=["DATE", "TIME_", "DISTRICT"], axis=1)
        )

        # Format all gun types into a single "firearm" value
        df["weapon"] = df["weapon"].str.lower()
        firearm = df["weapon"].str.match("han.+g.+n|.*gun.*|.*rifle.*", na=False)
        df.loc[firearm, "weapon"] = "firearm"

        # Make the GeoDataFrame
        gdf = (
            gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["X_COORD"], df["Y_COORD"]),
                crs={"init": "epsg:3857"},
            )
            .to_crs(epsg=EPSG)
            .drop(labels=["X_COORD", "Y_COORD"], axis=1)
        )

        # Load the missing geocodes
        missing = pd.read_excel(
            os.path.join(data_dir, cls.__name__, "missing_geocodes.xlsx")
        )
        missing = gpd.GeoDataFrame(
            missing,
            geometry=gpd.points_from_xy(missing["lng"], missing["lat"]),
            crs={"init": "epsg:4326"},
        ).to_crs(epsg=EPSG)

        # Do the merge
        merged = pd.merge(
            gdf,
            missing[["dc_key", "geometry"]],
            on="dc_key",
            how="left",
            suffixes=("", "_r"),
        )
        merged.loc[merged.geometry.x.isnull(), "geometry"] = np.nan
        merged.geometry = merged.geometry.fillna(merged.geometry_r)

        return (
            merged.drop(labels=["geometry_r"], axis=1)
            .pipe(geocode, ZIPCodes.get())
            .pipe(geocode, PoliceDistricts.get())
            .pipe(geocode, Neighborhoods.get())
            .sort_values("dispatch_date_time", ascending=False)
            .reset_index(drop=True)
        )

