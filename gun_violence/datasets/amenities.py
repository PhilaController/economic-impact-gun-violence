import esri2gpd
import osm2gpd
import carto2gpd
import geopandas as gpd
import pandas as pd
import os
from . import EPSG
from .. import data_dir
from .core import Dataset
from .geo import CityLimits


__all__ = [
    "Universities",
    "Parks",
    "CityHall",
    "SubwayStations",
    "DryCleaners",
    "Cafes",
    "Bars",
    "Schools",
    "SchoolScores",
    "GroceryStores",
    "Libraries",
    "NewConstructionPermits",
    "AggravatedAssaults",
    "GraffitiRequests",
    "AbandonedVehicleRequests",
]


class Universities(Dataset):
    """
    Points representing buildings associated with Philadelphia's 
    colleges and universities.

    Source
    ------
    http://phl.maps.arcgis.com/home/item.html?id=8ad76bc179cf44bd9b1c23d6f66f57d1
    """

    @classmethod
    def download(cls, **kwargs):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/Universities_Colleges/FeatureServer/0"
        return (
            esri2gpd.get(url, fields=["NAME"])
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class Parks(Dataset):
    """
    Locations of Philadelphia's parks.

    Source
    ------
    http://phl.maps.arcgis.com/home/item.html?id=4df9250e3d624ea090718e56a9018694
    """

    @classmethod
    def download(cls, **kwargs):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/PPR_Assets/FeatureServer/0"
        return (
            esri2gpd.get(url)
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class CityHall(Dataset):
    """
    Location of Philadelphia's City Hall.

    Source
    ------
    http://phl.maps.arcgis.com/home/item.html?id=5146960d4d014f2396cb82f31cd82dfe
    """

    @classmethod
    def download(cls, **kwargs):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/CITY_LANDMARKS/FeatureServer/0"
        return (
            esri2gpd.get(
                url, where="NAME = 'City Hall' AND FEAT_TYPE = 'Municipal Building'"
            )
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class SubwayStations(Dataset):
    """
    Locations of Philadelphia subway stops. 

    Source
    ------
    OpenStreetMap
    """

    @classmethod
    def download(cls, **kwargs):

        city_limits = CityLimits.get().to_crs(epsg=4326)
        subway = osm2gpd.get(*city_limits.total_bounds, where="station=subway").to_crs(
            epsg=4326
        )
        return (
            gpd.sjoin(subway, city_limits, op="within")
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class DryCleaners(Dataset):
    """
    Locations of Philadelphia dry cleaners.

    Source
    ------
    OpenStreetMap
    """

    @classmethod
    def download(cls, **kwargs):

        city_limits = CityLimits.get().to_crs(epsg=4326)
        df = osm2gpd.get(*city_limits.total_bounds, where="shop=dry_cleaning").to_crs(
            epsg=4326
        )
        return (
            gpd.sjoin(df, city_limits, op="within")
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class Cafes(Dataset):
    """
    Locations of Philadelphia cafes.

    Source
    ------
    OpenStreetMap
    """

    @classmethod
    def download(cls, **kwargs):

        city_limits = CityLimits.get().to_crs(epsg=4326)
        df = osm2gpd.get(*city_limits.total_bounds, where="amenity=cafe").to_crs(
            epsg=4326
        )
        return (
            gpd.sjoin(df, city_limits, op="within")
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class GroceryStores(Dataset):
    """
    Locations of Philadelphia grocery stores.

    Source
    ------
    OpenStreetMap
    """

    @classmethod
    def download(cls, **kwargs):

        city_limits = CityLimits.get().to_crs(epsg=4326)
        df = osm2gpd.get(*city_limits.total_bounds, where="shop=supermarket").to_crs(
            epsg=4326
        )
        return (
            gpd.sjoin(df, city_limits, op="within")
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class Bars(Dataset):
    """
    Locations of Philadelphia bars.
    """

    @classmethod
    def download(cls, **kwargs):

        city_limits = CityLimits.get().to_crs(epsg=4326)
        df = osm2gpd.get(*city_limits.total_bounds, where="amenity=bar").to_crs(
            epsg=4326
        )
        return (
            gpd.sjoin(df, city_limits, op="within")
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class Libraries(Dataset):
    """
    Locations of Philadelphia libraries.

    Source
    ------
    https://phl.maps.arcgis.com/home/item.html?id=b3c133c3b15d4c96bcd4d5cc09f19f4e
    """

    @classmethod
    def download(cls, **kwargs):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/City_Facilities_pub/FeatureServer/0"
        return (
            esri2gpd.get(
                url, where="ASSET_SUBT1_DESC = 'Library Branch'", fields=["ASSET_NAME"]
            )
            .to_crs(epsg=EPSG)
            .rename(columns={"ASSET_NAME": "asset_name"})
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class Schools(Dataset):
    """
    Locations of Philadelphia schools.

    Source
    ------
    https://phl.maps.arcgis.com/home/item.html?id=d46a7e59e2c246c891fbee778759717e
    """

    @classmethod
    def download(cls, **kwargs):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Schools/FeatureServer/0"
        return (
            esri2gpd.get(url, fields=["LOCATION_ID"])
            .to_crs(epsg=EPSG)
            .rename(columns={"LOCATION_ID": "ulcs_code"})
            .dropna(subset=["ulcs_code"])
            .assign(
                ulcs_code=lambda df: df.ulcs_code.astype(int),
                x=lambda df: df.geometry.x,
                y=lambda df: df.geometry.y,
            )
        )


class SchoolScores(Dataset):
    """
    School performance scores for the 2017-2018 school year.

    Source
    ------
    https://www.philasd.org/performance/programsservices/open-data/school-performance/#school_progress_report
    """

    @classmethod
    def download(cls, **kwargs):

        # load the performance scores locally
        # fill missing values with median score
        scores = (
            pd.read_excel(
                os.path.join(
                    data_dir,
                    cls.__name__,
                    "SPR_SY1718_School_Metric_Scores_20190129.xlsx",
                ),
                sheet_name="SPR SY2017-2018",
                usecols=["ULCS Code", "Overall Score"],
            )
            .rename(
                columns={"ULCS Code": "ulcs_code", "Overall Score": "overall_score"}
            )
            .assign(
                overall_score=lambda df: pd.to_numeric(
                    df.overall_score, errors="coerce"
                )
            )
            .assign(
                overall_score=lambda df: df.overall_score.fillna(
                    df.overall_score.median()
                )
            )
        )

        return pd.merge(Schools.get(), scores, on="ulcs_code")


class NewConstructionPermits(Dataset):
    """
    The number of new construction permits granted.

    Source
    ------
    https://www.opendataphilly.org/dataset/licenses-and-inspections-building-permits
    """

    @classmethod
    def download(cls, **kwargs):

        # grab the permit data from CARTO
        df = carto2gpd.get(
            "https://phl.carto.com/api/v2/sql",
            "li_permits",
            where=(
                "permitissuedate < '2019-01-01' "
                "AND permitdescription='NEW CONSTRUCTION PERMIT'"
            ),
        )
        return (
            df.dropna(subset=["geometry"])
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class AggravatedAssaults(Dataset):
    """
    The number of aggravated assaults in Philadelphia.

    Source
    ------
    https://www.opendataphilly.org/dataset/crime-incidents
    """

    @classmethod
    def download(cls, **kwargs):

        # grab the crime data from CARTO
        df = carto2gpd.get(
            "https://phl.carto.com/api/v2/sql",
            "incidents_part1_part2",
            where=(
                "dispatch_date < '2019-01-01'"
                " AND Text_General_Code IN ('Aggravated Assault No Firearm', 'Aggravated Assault Firearm')"
            ),
        )
        return (
            df.dropna(subset=["geometry"])
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class GraffitiRequests(Dataset):
    """
    The number of 311 requests for graffiti Philadelphia.

    Source
    ------
    https://www.opendataphilly.org/dataset/311-service-and-information-requests
    """

    @classmethod
    def download(cls, **kwargs):

        # grab the crime data from CARTO
        df = carto2gpd.get(
            "https://phl.carto.com/api/v2/sql",
            "public_cases_fc",
            where=(
                "requested_datetime < '2019-01-01'"
                " AND service_name = 'Graffiti Removal'"
            ),
        )
        return (
            df.dropna(subset=["geometry"])
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )


class AbandonedVehicleRequests(Dataset):
    """
    The number of 311 requests for abandonded vehicles in Philadelphia.

    Source
    ------
    https://www.opendataphilly.org/dataset/311-service-and-information-requests
    """

    @classmethod
    def download(cls, **kwargs):

        # grab the crime data from CARTO
        df = carto2gpd.get(
            "https://phl.carto.com/api/v2/sql",
            "public_cases_fc",
            where=(
                "requested_datetime < '2019-01-01'"
                " AND service_name = 'Abandoned Vehicle'"
            ),
        )
        return (
            df.dropna(subset=["geometry"])
            .to_crs(epsg=EPSG)
            .assign(x=lambda df: df.geometry.x, y=lambda df: df.geometry.y)
        )

