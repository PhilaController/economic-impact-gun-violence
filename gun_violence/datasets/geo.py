import esri2gpd
from . import EPSG
from .core import Dataset

__all__ = ["Neighborhoods", "ZIPCodes", "CensusTracts2000", "CensusTracts2010"]


class Neighborhoods(Dataset):
    """
    Polygons representing Philadelphia's neighborhoods.

    Notes
    -----
    These are Zillow-based neighborhoods.

    Source
    ------
    https://phl.maps.arcgis.com/home/item.html?id=ab9d26be1df8486c8d5d706fb32b33d5
    """

    @classmethod
    def download(self):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/Philly_Neighborhoods/FeatureServer/0"
        return (
            esri2gpd.get(url, fields=["MAPNAME"])
            .to_crs(epsg=EPSG)
            .rename(columns={"MAPNAME": "neighborhood"})
        )


class ZIPCodes(Dataset):
    """
    Polygons representing Philadelphia's ZIP codes.

    Notes
    -----
    These are from the 2018 Census ZIP Code Tabulation Areas (ZCTAs).

    Source
    ------
    https://phl.maps.arcgis.com/home/item.html?id=ab9d26be1df8486c8d5d706fb32b33d5
    """

    @classmethod
    def download(self):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Philadelphia_ZCTA_2018/FeatureServer/0"
        return esri2gpd.get(url, fields=["zip_code"]).to_crs(epsg=EPSG)


class CensusTracts2010(Dataset):
    """
    Polygons representing Philadelphia's census tracts used in the 2010 Census.

    Source
    ------
    https://phl.maps.arcgis.com/home/item.html?id=8bc0786524a4486bb3cf0f9862ad0fbf
    """

    @classmethod
    def download(self):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Census_Tracts_2010/FeatureServer/0"
        return (
            esri2gpd.get(url, fields=["GEOID10", "NAME10"])
            .rename(
                columns={"GEOID10": "census_tract_id", "NAME10": "census_tract_name"}
            )
            .to_crs(epsg=EPSG)
        )


class CensusTracts2000(Dataset):
    """
    Polygons representing Philadelphia's census tracts used in the 2000 Census.

    Source
    ------
    https://phl.maps.arcgis.com/home/item.html?id=a3c0cee49de447be9fd0d5820f9e930f
    """

    @classmethod
    def download(self):

        url = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Census_Tracts_2000/FeatureServer/0"
        return (
            esri2gpd.get(url, fields=["TEXTNUM", "STFID"])
            .rename(
                columns={"STFID": "census_tract_id", "TEXTNUM": "census_tract_name"}
            )
            .to_crs(epsg=EPSG)
        )

