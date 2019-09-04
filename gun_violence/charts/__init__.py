from phila_style.matplotlib import get_theme
from phila_style import *

palette = get_default_palette()
digital_standards = get_digital_standards()
default_style = get_theme()


from .price_vs_homicides_by_hood import plot as price_vs_homicides_by_hood
from .homicide_trends import plot as homicide_trends
from .homicides_by_hood import plot as homicides_by_hood
from .prices_near_homicides import plot as prices_near_homicides
from .population_change import plot as population_change
from .homicides_poverty import plot as homicides_poverty
from .cost_benefit import plot as cost_benefit
from .added_revenue import plot as added_revenue
from .lives_saved import plot as lives_saved
