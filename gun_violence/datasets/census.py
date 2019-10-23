import os
import pandas as pd
import numpy as np
from census import Census
from .. import data_dir
from .core import Dataset
from .geo import CensusTracts2010


__all__ = [
    "EducationalAttainment",
    "MedianHouseholdIncome",
    "PercentBlack",
    "PublicAssistance",
    "FemaleHouseholders",
    "UnemploymentRate",
    "PercentUnder18",
    "PercentInPoverty",
    "Population",
]


class CensusDataset(Dataset):
    """
    A class to represent a dataset downloaded from the Census API.
    """

    @classmethod
    def get_path(cls, year=2017):
        return os.path.join(data_dir, cls.__name__, str(year))

    @staticmethod
    def get_census_data(fields, year=2017, dataset=None):
        """
        Download the requested fields from the American Community Survey
        using the Census API.

        Parameters
        ----------
        fields : list of str
            the names of the census variables to download
        year : int, optional
            the year of data to download
        """
        # get the census tracts
        tracts = CensusTracts2010.get().assign(
            tract=lambda df: df.census_tract_id.astype(str).str.slice(-6)
        )

        # initialize the api
        api = Census(api_key=os.enviro.get("CENSUS_API_KEY", None), year=year)

        # this is a hack to support ACS5 subject tables
        if dataset is not None:
            api.acs5.dataset = dataset

        # download data for all tracts in Philadelphia County
        return pd.merge(
            tracts,
            pd.DataFrame(api.acs5.state_county_tract(fields, "42", "101", "*")),
            on="tract",
        )


class EducationalAttainment(CensusDataset):
    """
    Educational attainment, as described by the percentage of high 
    school graduates per census tract. 

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {
            "B15002_011E": "male_high_school_graduate",
            "B15002_028E": "female_high_school_graduate",
            "B15002_001E": "total",
        }
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .assign(
                high_school_degree=lambda df: (
                    df.male_high_school_graduate + df.female_high_school_graduate
                )
                / df.total
            )
            .loc[:, ["census_tract_id", "high_school_degree", "geometry"]]
        )


class MedianHouseholdIncome(CensusDataset):
    """
    The median household income for census tracts in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"B19013_001E": "median_household_income"}
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .loc[:, ["census_tract_id", "median_household_income", "geometry"]]
        )


class PercentBlack(CensusDataset):
    """
    The percentage of black/African American people for every 
    census tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"B03002_004E": "black_alone", "B03002_001E": "total"}
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .assign(percent_black=lambda df: df.black_alone / df.total)
            .loc[:, ["census_tract_id", "percent_black", "geometry"]]
        )


class PublicAssistance(CensusDataset):
    """
    The percentage of people receiving public assistance by
    census tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"B19058_002E": "public_assistance", "B19058_001E": "total"}
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .assign(
                percent_public_assistance=lambda df: df.public_assistance / df.total
            )
            .loc[:, ["census_tract_id", "percent_public_assistance", "geometry"]]
        )


class FemaleHouseholders(CensusDataset):
    """
    The percentage of households with a female head by census 
    tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"B11001_006E": "female_householder", "B11001_001E": "total"}
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .assign(
                percent_female_householder=lambda df: df.female_householder / df.total
            )
            .loc[:, ["census_tract_id", "percent_female_householder", "geometry"]]
        )


class UnemploymentRate(CensusDataset):
    """
    The unemployment rate by census tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"S2301_C04_001E": "unemployment_rate"}
        return (
            cls.get_census_data(
                ["NAME"] + list(columns), dataset="acs5/subject", **kwargs
            )
            .rename(columns=columns)
            .assign(
                unemployment_rate=lambda df: df.unemployment_rate.where(
                    df.unemployment_rate > 0
                )
                / 100
            )
            .loc[:, ["census_tract_id", "unemployment_rate", "geometry"]]
        )


class PercentUnder18(CensusDataset):
    """
    The percentage of people under the age of 18 by census tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {
            "B01001_001E": "universe",
            "B01001_003E": "male_under_5",
            "B01001_004E": "male_5_to_9",
            "B01001_005E": "male_10_to_14",
            "B01001_006E": "male_15_to_17",
            "B01001_027E": "female_under_5",
            "B01001_028E": "female_5_to_9",
            "B01001_029E": "female_10_to_14",
            "B01001_030E": "female_15_to_17",
        }
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .assign(
                universe=lambda df: pd.to_numeric(df.universe),
                percent_under_18=lambda df: (
                    df.male_under_5
                    + df.male_5_to_9
                    + df.male_10_to_14
                    + df.male_15_to_17
                    + df.female_under_5
                    + df.female_5_to_9
                    + df.female_10_to_14
                    + df.female_15_to_17
                )
                / df.universe,
            )
            .loc[:, ["census_tract_id", "percent_under_18", "geometry"]]
        )


class PercentInPoverty(CensusDataset):
    """
    The percentage of households below the poverty line by 
    census tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"B17001_001E": "universe", "B17001_002E": "below_poverty_line"}
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .assign(percent_in_poverty=lambda df: df.below_poverty_line / df.universe)
            .loc[:, ["census_tract_id", "percent_in_poverty", "geometry"]]
        )


class Population(CensusDataset):
    """
    Population by census tract in Philadelphia.

    Source
    ------
    American Community Survey
    """

    @classmethod
    def download(cls, **kwargs):

        columns = {"B01003_001E": "total_population"}
        return (
            cls.get_census_data(["NAME"] + list(columns), **kwargs)
            .rename(columns=columns)
            .loc[:, ["census_tract_id", "total_population", "geometry"]]
        )
