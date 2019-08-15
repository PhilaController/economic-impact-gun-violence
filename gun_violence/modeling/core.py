import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from ..datasets import amenities

__all__ = ["add_neighborhood_features", "feature_engineer_sales", "get_modeling_inputs"]

BUILDING_CHARACTERISTICS = [
    "basements",
    "building_code_description",
    "central_air",
    "depth",
    "exterior_condition",
    "fireplaces",
    "frontage",
    "garage_spaces",
    "general_construction",
    "homestead_exemption",
    "interior_condition",
    "is_condo",
    "neighborhood",
    "number_of_bathrooms",
    "number_of_bedrooms",
    "number_of_rooms",
    "number_stories",
    "police_district",
    "topography",
    "total_area",
    "total_livable_area",
    "type_heater",
    "view_type",
    "year_built",
    "zip_code",
    "zoning",
]

CATEGORICAL = [
    "basements",
    "building_code_description",
    "central_air",
    "exterior_condition",
    "fireplaces",
    "garage_spaces",
    "general_construction",
    "homestead_exemption",
    "interior_condition",
    "is_condo",
    "neighborhood",
    "number_of_bathrooms",
    "number_of_bedrooms",
    "number_of_rooms",
    "number_stories",
    "sold_in_year_built",
    "topography",
    "type_heater",
    "view_type",
    "year_built",
    "zoning",
    "season",
    "spacetime_flag*",
]

REMOVE = [
    "geometry",
    "sale_price",
    "sale_price_indexed",
    "time_offset",
    "ln_sale_price",
    "ln_sale_price_indexed",
    "lat",
    "lng",
    "police_district",
    "zip_code",
    "sale_year",
]


def _knn_distance(coordinates, measureTo, k):
    """
    Return the average distance to the k nearest neighbors.
    """
    nbrs = NearestNeighbors(n_neighbors=k, algorithm="ball_tree").fit(measureTo)
    return nbrs.kneighbors(coordinates)


def add_neighborhood_features(sales):
    """
    Add (dis)amenity distance features to the dataset of sales.

    Parameters
    ----------
    sales : DataFrame
        the input data for sales
    
    Returns
    -------
    DataFrame : 
        the output data with the added feature columns
    """
    out = sales.copy()
    salesXY = np.vstack([sales.geometry.x, sales.geometry.y]).T

    features = {
        "Universities": [1, "dist_univ"],
        "Parks": [1, "dist_park"],
        "CityHall": [1, "dist_city_hall"],
        "SubwayStations": [1, "dist_subway"],
        "DryCleaners": [2, "dist_dry_clean"],
        "Cafes": [3, "dist_cafes"],
        "Bars": [3, "dist_bars"],
        "Schools": [2, "dist_schools"],
        "SchoolScores": [1, "closest_school_score"],
        "GroceryStores": [2, "dist_grocery"],
        "Libraries": [1, "dist_library"],
        "NewConstructionPermits": [5, "dist_permits"],
        "AggravatedAssaults": [5, "dist_agg_assaults"],
        "GraffitiRequests": [5, "dist_graffiti"],
        "AbandonedVehicleRequests": [5, "dist_abandoned_vehicle"],
    }
    for feature in features:
        k, column = features[feature]

        # load the amenity data
        amenityData = getattr(amenities, feature).get()

        # get neighbors
        dists, indices = _knn_distance(salesXY, amenityData[["x", "y"]].values, k)

        # calculate feature
        if feature != "SchoolScores":
            featureData = dists.mean(axis=1)
        else:
            featureData = amenityData["overall_score"].values[indices.squeeze()]

        out[column] = featureData

    return out


def feature_engineer_sales(sales, include_cols=["spacetime_flag", "dist"]):
    """
    Return a clean version of the input sales data after
    performing multiple feature engineering steps.

    Parameters
    ----------
    sales : DataFrame
        the input sales data

    Returns
    -------
    DataFrame : 
        the cleaned version of the data
    """
    building_characteristics = [
        col for col in BUILDING_CHARACTERISTICS if col in sales.columns
    ]

    def add_other_category(data, N=25):
        return data.replace(data.value_counts(dropna=False).iloc[N:].index, "Other")

    # spacetime flags
    extra_cols = [
        col
        for col in sales.columns
        if any(col.startswith(base) for base in include_cols)
    ]

    out = (
        sales.loc[
            :,
            building_characteristics
            + [
                "geometry",
                "ln_sale_price",
                "ln_sale_price_indexed",
                "sale_price",
                "sale_price_indexed",
                "sale_year",
                "sale_date",
                "time_offset",
            ]
            + extra_cols,
        ]
        .assign(
            year_built=lambda df: pd.to_numeric(df.year_built, errors="coerce"),
            sold_in_year_built=lambda df: np.where(df.sale_year == df.year_built, 1, 0),
        )
        .assign(
            month=lambda df: df.sale_date.dt.month,
            central_air=lambda df: np.where(df.central_air == "Y", 1, 0),
            is_condo=lambda df: np.where(df.is_condo, 1, 0),
            fireplaces=lambda df: np.where(df.fireplaces > 0, 1, 0),
            homestead_exemption=lambda df: np.where(df.homestead_exemption == 0, 0, 1),
            season=lambda df: np.select(
                [
                    df.month.isin([1, 2, 12]),
                    df.month.isin([3, 4, 5]),
                    df.month.isin([6, 7, 8]),
                    df.month.isin([9, 10, 11]),
                ],
                ["Winter", "Spring", "Summer", "Fall"],
            ),
            garage_spaces=lambda df: df.garage_spaces.clip(upper=2),
            number_of_bathrooms=lambda df: df.number_of_bathrooms.clip(upper=2),
            number_of_bedrooms=lambda df: df.number_of_bedrooms.clip(upper=5),
            number_of_rooms=lambda df: df.number_of_rooms.clip(upper=8),
            number_stories=lambda df: df.number_stories.clip(upper=4),
            log_total_area=lambda df: np.log10(df.total_area),
            log_total_livable_area=lambda df: np.log10(df.total_livable_area),
            year_built=lambda df: np.select(
                [
                    df.year_built < 1970,
                    (df.year_built >= 1970) & (df.year_built < 1980),
                    (df.year_built >= 1980) & (df.year_built < 1990),
                    (df.year_built >= 1990) & (df.year_built < 2000),
                    (df.year_built >= 2000) & (df.year_built < 2010),
                    (df.year_built >= 2010) & (df.year_built < 2020),
                ],
                ["1970_earlier", "1970s", "1980s", "1990s", "2000s", "2010s"],
            ),
        )
        .dropna(subset=["neighborhood"])
        .drop(labels=["sale_date", "month", "total_area", "total_livable_area"], axis=1)
        .assign(lat=lambda df: df.geometry.y, lng=lambda df: df.geometry.x)
        .assign(
            log_total_area=lambda df: df.log_total_area.fillna(0),
            log_total_livable_area=lambda df: df.log_total_livable_area.fillna(0),
        )
    )

    # Fix Interior Condition which has mixed dtypes
    if "interior_condition" in out.columns:
        valid = out["interior_condition"].notnull()
        IC = out.loc[valid, "interior_condition"]
        out.loc[valid, "interior_condition"] = (
            pd.to_numeric(IC, errors="coerce")
            .fillna(IC)
            .apply(lambda x: x if isinstance(x, str) else "%.0f" % x)
        )

    # Add an "Other" category for zoning and building descriptions
    for col in ["zoning", "building_code_description"]:
        if col in out.columns:
            out[col] = add_other_category(out[col].str.strip(), N=25)

    # Set categorical dtypes
    categorical = out.filter(regex="|".join(CATEGORICAL)).columns
    for col in categorical:
        out[col] = out[col].astype("category")

    return out


def get_modeling_inputs(
    sales, dropna=False, endog="ln_sale_price_indexed", as_panel=False
):
    """
    Return the inputs to the regression model.

    Parameters
    ----------
    sales : DataFrame
        the input sales data
    dropna : bool, optional
        drop the NaN values instead of imputing
    endog : str, optional
        the name of the dependent variable
    as_panel : bool, optional
        whether to return the data in a panel format, with the neighborhood and 
        sale year as indices

    Returns
    -------
    X, Y: array_like
        the X and Y features
    """
    assert endog in REMOVE

    # Engineer features
    features = feature_engineer_sales(sales)

    # Do not remove the dependent variable
    unnecessary = list(REMOVE)
    unnecessary.remove(endog)

    if as_panel:
        unnecessary.remove("sale_year")

    # Trim unnecessary columns
    features = features.drop(labels=unnecessary, axis=1)

    # Drop NaNs?
    if dropna:
        features = features.dropna()

    index_cols = []
    if as_panel:
        index_cols = ["neighborhood", "sale_year"]

    # Get column types
    cat_cols = [
        col
        for col in features.columns
        if features.dtypes[col].kind == "O" and col not in index_cols
    ]
    num_cols = [
        col
        for col in features.columns
        if features.dtypes[col].kind != "O" and col != endog and col not in index_cols
    ]

    # One-Hot encode
    oneHotData = []
    for col in cat_cols:
        if col.startswith("spacetime"):
            oneHotData.append(features[col])
        else:
            oneHotData.append(
                pd.get_dummies(
                    features[col].astype("category"), prefix=col, drop_first=True
                )
            )
    oneHotData = pd.concat(oneHotData, axis=1)

    # remove flags
    flags = [col for col in features.columns if col.startswith("spacetime")]
    if len(flags):
        features = features.drop(labels=flags, axis=1)

    # Merge in OHE
    features = (
        pd.merge(features, oneHotData, left_index=True, right_index=True)
        .replace([np.inf, -np.inf], np.nan)
        .drop(
            labels=[col for col in cat_cols if not col.startswith("spacetime")], axis=1
        )
    )

    # New categorical columns
    cat_cols = list(oneHotData.columns)

    # Setup the pipeline
    num_pipe = Pipeline(
        [("si", SimpleImputer(strategy="median")), ("ss", StandardScaler())]
    )
    ct = ColumnTransformer(transformers=[("num", num_pipe, num_cols)])

    # the Y variable
    Y = features[endog].copy()

    # the index
    index = None
    if as_panel:
        index = features[index_cols].copy()

    # the X variable
    features = features.drop(labels=[endog] + index_cols, axis=1)
    transformed_features = np.concatenate(
        [features[cat_cols].values, ct.fit_transform(features)], axis=1
    )
    X = pd.DataFrame(transformed_features, columns=cat_cols + num_cols).assign(
        const=1.0
    )

    # reset index
    Y = Y.reset_index(drop=True)
    if index is not None:
        index = index.reset_index(drop=True)

    if as_panel:
        X = pd.concat([X, index], axis=1).set_index(index_cols)
        Y = pd.concat([Y, index], axis=1).set_index(index_cols)

    return X, Y

