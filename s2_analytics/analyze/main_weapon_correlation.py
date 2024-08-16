from collections import namedtuple
from typing import Union

Correlation = namedtuple("Correlation", ["correlation", "sample_count"])


class OneWeaponCorrelations:
    def __init__(self, tag: str, correlations_by_map: dict[str, Correlation]):
        self.tag = tag
        self._total_samples = 0
        for correlation in correlations_by_map.values():
            assert isinstance(correlation.sample_count, int)
            assert 0 <= correlation.sample_count
            assert isinstance(correlation.correlation, float)
            self._total_samples += correlation.sample_count
        self._correlations_by_map = correlations_by_map

    @property
    def maps(self) -> list[str]:
        return list(self._correlations_by_map.keys())

    def correlation(self, map: str) -> float:
        return self._correlations_by_map[map].correlation if map in self._correlations_by_map else 0.0

    def sample_count(self, map: Union[str, None] = None):
        if map is None:
            return self._total_samples
        elif map not in self._correlations_by_map:
            return 0
        else:
            return self._correlations_by_map[map].sample_count

    def filter(self, min_samples):
        return OneWeaponCorrelations(self.tag, {map: data for map, data in self._correlations_by_map.items() if data.sample_count >= min_samples})


