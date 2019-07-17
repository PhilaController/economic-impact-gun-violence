import geopandas as gpd
import pandas as pd
from abc import ABC, abstractclassmethod
import os, json
from . import EPSG
from .. import data_dir


class Dataset(ABC):
    """
    Abstract base class representing a dataset.
    """

    date_columns = []

    @classmethod
    def _format_data(cls, data):
        """
        Internal method to format the data
        """
        # convert to GeoDataFrame
        if "geometry" in data.columns:
            from shapely import wkt

            data.geometry = data.geometry.apply(wkt.loads)
            data = gpd.GeoDataFrame(
                data, geometry="geometry", crs={"init": f"epsg:{EPSG}"}
            )

        # convert date columns
        for col in cls.date_columns:
            data[col] = pd.to_datetime(data[col])

        return data

    @classmethod
    def meta(cls):
        path = os.path.join(data_dir, cls.__name__, "meta.json")
        if os.path.exists(path):
            return json.load(open(path, "r"))
        else:
            return {}

    @classmethod
    def now(cls):
        return str(pd.datetime.now())

    @classmethod
    def dask(cls):
        """
        Load the data as an out-of-memory dask dataframe
        """
        import dask.dataframe as dd

        path = os.path.join(data_dir, cls.__name__, "data.csv")
        return dd.read_csv(path, assume_missing=True)

    @classmethod
    def get(cls, fresh=False):
        """
        Load the dataset, optionally downloading a fresh copy.
        """
        dirname = os.path.join(data_dir, cls.__name__)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            fresh = True

        if not os.path.exists(os.path.join(dirname, "data.csv")) or fresh:

            # download and save a fresh copy
            data = cls.download()
            data.to_csv(os.path.join(dirname, "data.csv"), index=False)

            # save the download time
            meta = {"download_time": cls.now()}
            json.dump(meta, open(os.path.join(dirname, "meta.json"), "w"))

        else:
            data = cls._format_data(pd.read_csv(os.path.join(dirname, "data.csv")))

        return data

    @abstractclassmethod
    def download(cls):
        raise NotImplementedError


def geocode(df, polygons):
    """
    Geocode the input data set of Point geometries using 
    the specified polygon boundaries.

    Parameters
    ----------
    df : geopandas.GeoDataFrame
        the point data set 
    polygons : geopandas.GeoDataFrame
        the Polygon geometries
    
    Returns
    -------
    GeoDataFrame : 
        a copy of ``df`` with the data from ``polygons`` matched 
        according to the point-in-polygon matching
    """
    # convert the CRS
    polygons = polygons.to_crs(df.crs)

    valid = df.geometry.notnull()
    geocoded = gpd.sjoin(df.loc[valid], polygons, op="within", how="left").drop(
        labels=["index_right"], axis=1
    )

    return pd.concat([geocoded, df.loc[~valid]], sort=True)


def replace_missing_geometries(df):
    """
    Utility function to replace missing geometries with empty Point() objects.
    """
    from shapely.geometry import Point

    mask = df.geometry.isnull()
    empty = pd.Series(
        [Point() for i in range(mask.sum())], index=df.loc[mask, "geometry"].index
    )
    df.loc[mask, "geometry"] = empty

    return df
