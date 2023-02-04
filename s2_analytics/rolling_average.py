from dataclasses import dataclass

from math import ceil


@dataclass
class RollingAveragePeriod:
    window_days: int
    periods_visible: float        # 1.0 means chart will cover overal {period_days} days
    required_values_ratio: float  # 1.0 means all entries needed otherwise NaN

    @property
    def days_of_data_needed(self):
        return ceil(self.window_days * self.periods_visible) + ceil(self.window_days * self.required_values_ratio)

    @property
    def total_days_visible(self):
        return ceil(self.window_days * self.periods_visible)

    @property
    def min_days_for_avg(self):
        return ceil(self.window_days * self.required_values_ratio)