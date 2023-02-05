from .rolling_average import RollingAveragePeriod


def test_periods_visible():
    period = RollingAveragePeriod(10, 3, 0.5)
    assert period.periods_visible == 3


def test_data_needed():
    period = RollingAveragePeriod(10, 3, 0.5)
    assert period.days_of_data_needed == 35


def test_min_days_for_average():
    period = RollingAveragePeriod(10, 3, 0.5)
    assert period.min_days_for_avg == 5


def test_total_period_days():
    period = RollingAveragePeriod(10, 3, 0.5)
    assert period.total_days_visible == 30
