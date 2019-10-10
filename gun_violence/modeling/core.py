import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from ..datasets import amenities

__all__ = [
    "add_neighborhood_features",
    "feature_engineer_sales",
    "get_modeling_inputs",
    "run_regression",
]

# fields related to building characteristics
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
    "season",
    "topography",
    "total_area",
    "total_livable_area",
    "type_heater",
    "view_type",
    "year_built",
    "zip_code",
    "zoning",
]

# categorical fieldss
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

# fields we don't need to do the modeling
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
    Internal function to return the average distance to the k-nearest neighbors.
    
    Parameters
    ----------
    coordinates : array_like
        the 2D array of coordinates for sales
    measureTo : array_like
        the coordinates of the thing we are measuring to
    k : int
        the number of neighbors to find
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

    # the features to calculate distances to
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


def feature_engineer_sales(sales, always_include=["spacetime_flag", "dist"]):
    """
    Return a clean version of the input sales data after
    performing multiple feature engineering steps.

    Parameters
    ----------
    sales : DataFrame
        the input sales data
    always_include : list, optional
        list of any columns to include in the output data 

    Returns
    -------
    DataFrame : 
        the cleaned version of the data
    """
    # Extract building characteristics that are present
    building_characteristics = [
        col for col in BUILDING_CHARACTERISTICS if col in sales.columns
    ]

    def add_other_category(data, N=25):
        return data.replace(data.value_counts(dropna=False).iloc[N:].index, "Other")

    # Columns to keep
    extra_cols = [
        col
        for col in sales.columns
        if any(col.startswith(base) for base in always_include)
    ]

    # Do the formatting
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
    sales,
    dropna=False,
    endog="ln_sale_price_indexed",
    use_features=None,
    as_panel=False,
    engineer_sales=True,
):
    """
    Return the inputs to the regression model, optionally performing
    feature engineering first.

    Parameters
    ----------
    sales : DataFrame
        the input sales data
    dropna : bool, optional
        drop the NaN values instead of imputing
    endog : str, optional
        the name of the dependent variable
    use_features : list of str, optional
        if provided, only include these building characteristics in the output
    as_panel : bool, optional
        whether to return the data in a panel format, with the neighborhood and 
        sale year as indices
    engineer_sales : bool, optional
        whether to perform feature engineering first.

    Returns
    -------
    X, Y: array_like
        the X and Y feature inputs to the regression
    """
    assert endog in REMOVE

    # Engineer features
    if engineer_sales:
        features = feature_engineer_sales(sales)
    else:
        features = sales.copy()

    # Trim to specific building characteristics
    if use_features is not None:

        # make sure we have panel columns
        if as_panel:
            for col in ["neighborhood"]:
                if col not in use_features:
                    use_features.append(col)

        # remove unnecessary
        drop = [
            col
            for col in BUILDING_CHARACTERISTICS
            if col in features.columns and col not in use_features
        ]
        features = features.drop(labels=drop, axis=1)

    # Do not remove the dependent variable
    unnecessary = list(REMOVE)
    unnecessary.remove(endog)

    # Keep sale year for panel data
    if as_panel:
        unnecessary.remove("sale_year")

    # Trim unnecessary columns
    unnecessary = [col for col in unnecessary if col in features.columns]
    features = features.drop(labels=unnecessary, axis=1)

    # Drop NaNs?
    if dropna:
        features = features.dropna()

    # Specify index columns for panel data
    index_cols = []
    if as_panel:
        index_cols = ["neighborhood", "sale_year"]

    # Get categorical and numerical field types
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

    # One-Hot encode the categorical data
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

    # Remove flags before merging
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

    # The names of the new categorical columns
    cat_cols = list(oneHotData.columns)

    # Setup the pipeline
    num_pipe = Pipeline(
        [("si", SimpleImputer(strategy="median")), ("ss", StandardScaler())]
    )
    ct = ColumnTransformer(transformers=[("num", num_pipe, num_cols)])

    # the Y variable
    Y = features[endog].copy()

    # Index for panel data
    index = None
    if as_panel:
        index = features[index_cols].copy()

    # The X variables
    features = features.drop(labels=[endog] + index_cols, axis=1)
    transformed_features = np.concatenate(
        [features[cat_cols].values, ct.fit_transform(features)], axis=1
    )

    # Make into a DataFrame and add a constant
    X = pd.DataFrame(transformed_features, columns=cat_cols + num_cols).assign(
        const=1.0
    )

    # Reset index
    Y = Y.reset_index(drop=True)
    if index is not None:
        index = index.reset_index(drop=True)

    # Add index for panel data
    if as_panel:
        X = pd.concat([X, index], axis=1).set_index(index_cols)
        Y = pd.concat([Y, index], axis=1).set_index(index_cols)

    return X, Y


def run_regression(
    salesWithFlags,
    use_features=None,
    entity_effects=True,
    time_effects=True,
    cov_type="clustered",
    cluster_entity=True,
):
    """
    Run a panel regression on the input sales data.

    Parameters
    ----------
    salesWithFlags : pandas.DataFrame
        the sales data with any interaction flags already added
    use_features : list of str, optional
        if specified, only include these property characteristics in the regression
    entity_effects : bool, optional
        include neighborhood fixed effects
    time_effects : bool, optional
        include year fixed effects
    cov_type : str, optional
        the covariance type to use
    cluster_entity : bool, optional
        if using clustered errors, cluster at the neighborhood level
    """
    from linearmodels import PanelOLS

    # get the modeling inputs
    X, Y = get_modeling_inputs(
        salesWithFlags, dropna=False, as_panel=True, use_features=use_features
    )

    # initialize the panel regression
    mod = PanelOLS(Y, X, entity_effects=entity_effects, time_effects=time_effects)

    # return the regression result
    return mod.fit(cov_type=cov_type, cluster_entity=cluster_entity)
