import fredapi
import os
import numpy as np
import pandas as pd
from scipy.interpolate import InterpolatedUnivariateSpline
from .core import Dataset


class PhillyMSAHousingIndex(Dataset):
    """
    The All-Transactions House Price Index for the Philadelphia MSA

    Source
    ------
    https://fred.stlouisfed.org/series/ATNHPIUS37964Q
    """

    date_columns = ["date"]

    @classmethod
    def download(self):

        api_key = os.environ.get("FRED_API_KEY", None)
        if api_key is None:
            raise ValueError(
                "Please set the environment key 'FRED_API_KEY' to download resources from FRED"
            )
        f = fredapi.Fred(api_key=api_key)
        df = f.get_series(series_id="ATNHPIUS37964Q")

        return df.rename_axis("date").reset_index(name="housing_index").dropna()

    @classmethod
    def interpolate(cls, dates):
        """
        Return the housing price index, interpolated at the input dates
        """
        data = cls.get()
        x = (data["date"] - data["date"].min()) / np.timedelta64(1, "D")
        y = data["housing_index"]
        f = InterpolatedUnivariateSpline(x, y)

        valid = (dates > data["date"].min()) & (dates < data["date"].max())

        interpolated = f(
            (dates.loc[valid] - data["date"].min()) / np.timedelta64(1, "D")
        )
        out = pd.Series(np.nan, index=dates.index)
        out.loc[valid] = interpolated
        return out.values
