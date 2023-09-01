from typing import Optional

import numpy as np


def knots_to_mph(knots) -> Optional[float]:
    try:
        if isinstance(knots, str):
            knots = float(knots)
        return knots * 1.15078
    except (TypeError, ValueError):
        return np.nan
