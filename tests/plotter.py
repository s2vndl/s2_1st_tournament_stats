import inspect
import os

from matplotlib import pyplot as plt

from s2_analytics.tools import PlotShow
from tests.project_root import get_project_root


class PlotShowForTests(PlotShow):
    def __init__(self):
        self.chart_no = 0

    def show(self):
        self.chart_no += 1
        caller_method = inspect.stack()[1][3]
        chart_id = f"{caller_method}_{self.chart_no}"
        plt.savefig(get_project_root() + f"/tests/generated_plots/{chart_id}.png")
        if "DO_NOT_SHOW_PLOTS" not in os.environ:
            super().show()
