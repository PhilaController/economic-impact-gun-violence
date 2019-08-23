default_style = {
    "font.family": "Open Sans",
    "axes.linewidth": 3,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "patch.edgecolor": "white",
    "axes.edgecolor": "white",
    "font.family": "Open Sans",
    "savefig.facecolor": "white",
}

from .price_vs_homicides_by_hood import plot as price_vs_homicides_by_hood
from .homicide_trends import plot as homicide_trends
from .homicides_by_hood import plot as homicides_by_hood
from .prices_near_homicides import plot as prices_near_homicides
from .population_change import plot as population_change
from .homicides_poverty import plot as homicides_poverty
from .cost_benefit import plot as cost_benefit
