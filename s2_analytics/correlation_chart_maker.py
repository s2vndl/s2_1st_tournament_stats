from collections import namedtuple
from typing import Union

import pandas as pd
import seaborn as sns

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnchoredText

from s2_analytics.main_weapon_correlation import OneWeaponCorrelations


class MinMax:
    def __init__(self, min: Union[float, int], max: Union[float, int]):
        self.min = min
        self.max = max

    def update(self, value: float):
        if self.min > value:
            self.min = value
        if self.max < value:
            self.max = value

    def as_tuple(self) -> tuple[float, float]:
        return self.min, self.max


class CorrelationChartMaker:
    def _chart_height(self, maps_count):
        return max(3, maps_count / 15 * 3.3) if maps_count > 0 else 1.5

    def plot_multiple(self, weapon_corr: list[OneWeaponCorrelations], min_samples=0):
        weapon_corr = [w.filter(min_samples) for w in weapon_corr]
        chart_height = sum([self._chart_height(len(w.maps)) for w in weapon_corr])

        minmax_corr = MinMax(0, 0)
        minmax_samples = MinMax(0, 0)
        for w in weapon_corr:
            for map in w.maps:
                minmax_corr.update(w.correlation(map))
                minmax_samples.update(w.sample_count(map))

        fig, axes = plt.subplots(len(weapon_corr), 2)
        fig: Figure
        fig.suptitle(f"Weapon/Win correlation")
        axes: list["AxesSubplot"]
        for i, corr in enumerate(weapon_corr):
            # fig.suptitle(f"{corr.tag}")
            corr_ax = axes[i][0]
            samples_ax = axes[i][1]
            corr_ax.set(xlabel=None, ylabel=None)
            samples_ax.set(xlabel=None, ylabel=None)
            corr_ax.set(xlim=(minmax_corr.min, minmax_corr.max))
            samples_ax.set(xlim=(minmax_samples.min, minmax_samples.max))
            corr_ax.set(title=f"{corr.tag}/win correlation", xlabel=None, ylabel=None)
            samples_ax.set(title=f"{corr.tag}/win sample count", xlabel=None, ylabel=None)
            self._subplot(corr, min_samples, corr_ax, samples_ax)

    def plot(self, weapon_corr: OneWeaponCorrelations, min_samples=None, count_max: float= None,
             corr_minmax:tuple[float, float] = None):
        if min_samples is not None:
            weapon_corr = weapon_corr.filter(min_samples)
        maps_count = len(weapon_corr.maps)
        chart_height = self._calculate_chart_height(maps_count)
        fig, axes = plt.subplots(1, 2, figsize=(10, chart_height), tight_layout=True, sharey=True)
        fig: Figure
        fig.suptitle(f"Weapon/Win correlation by map for {weapon_corr.tag}")
        axes: list["AxesSubplot"]
        axes = axes.flatten()
        self._subplot(weapon_corr, min_samples, axes[0], axes[1], count_max, corr_minmax)

    def _calculate_chart_height(self, maps_count):
        return 1.5 + maps_count / 15 * 3

    def _subplot(self, weapon_corr: OneWeaponCorrelations, min_samples: int, ax_corr, ax_cnt,
                 count_max: int = None, corr_minmax: MinMax = None):
        data = []
        skipped_maps = []
        for map in weapon_corr.maps:
            sample_count = weapon_corr.sample_count(map)
            if min_samples is not None and sample_count < min_samples:
                skipped_maps.append(map)
            else:
                data.append((f"{map:>20}", weapon_corr.correlation(map), sample_count))

        if count_max is not None:
            ax_cnt.set(xlim=(0, count_max))
        if corr_minmax is not None:
            ax_corr.set(xlim=corr_minmax)
        frame = pd.DataFrame(data, columns=["map", "corr", "cnt"]).sort_values(["corr"], ascending=False)
        if len(skipped_maps) > 0:
            at = AnchoredText(
                f"skipped {len(skipped_maps)} maps with less than {min_samples} samples", prop=dict(size=7),
                frameon=True,
                loc='lower right')
            ax_cnt.add_artist(at)

        if len(frame) > 0:
            sns.barplot(frame, x="corr", y="map", ax=ax_corr) \
                .set(xlabel="Round victory correlation coefficient", ylabel=None)
            sns.barplot(frame, x="cnt", y="map", ax=ax_cnt) \
                .set(xlabel="Count of entries", ylabel=None)
