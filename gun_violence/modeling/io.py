import pickle
import pandas as pd


def save_regression_result(result, filename, **meta):
    """
    Save a regression result to a file.

    Parameters
    ----------
    result : linearmodels.panel.results.PanelEffectsResults
        the panel regression result
    filename : str
        the name of the file to save the result to
    **meta : key/value pairs
        any additional meta information to save to the file
    """
    allowed = (pd.Series, pd.DataFrame, list, tuple, int, float, str)
    out = {}

    for key in dir(result):
        if key.startswith("_"):
            continue
        value = getattr(result, key)
        if isinstance(value, allowed):
            out[key] = value

    out["datetime"] = result._datetime
    out["summary"] = result.summary.as_text()
    out.update(meta)

    # save to pickle file
    pickle.dump(out, open(filename, "wb"))


def load_regression_result(filename):
    """
    Load a regression result from the specified file

    Parameters
    ----------
    filename : str
        the file to load the result from

    Returns
    -------
    result : dict
        the dictionary holding the relevant result information
    """
    return pickle.load(open(filename, "rb"))

