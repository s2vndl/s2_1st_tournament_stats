from tests.project_root import get_project_root
from s2_analytics.collect.fris_weapon_usage_collector import FriWeaponUsageCollector
from s2_analytics.constants import WEAPONS_PRIMARY
from s2_analytics.filters import PLAYLIST_CTF
from s2_analytics.importer import import_games
from tests.unit.test_assertions import assert_dataframes_equal


class TestFriWeaponUsageCollector:
    def test_collects_kills_and_analyzes_them(self):
        collector = FriWeaponUsageCollector().init()
        import_games(get_project_root() + "/fixtures/", period_days=99999, processors=[collector])

        actual = collector.get_data(['Barrett', 'Deagles', 'Rheinmetall'], 99999, 1, 99999)[["weapon", "date", "usage"]]
        expected = """
        weapon,date,usage
        Barrett,2023-01-12,74.99999999999999
        Deagles,2023-01-12,0.0
        Rheinmetall,2023-01-12,25.0
        """
        assert_dataframes_equal(expected, actual)

        actual = collector.get_data(['Barrett', 'Deagles'], 9999, 1, 9999)[["weapon", "date", "usage"]]
        expected = """
        weapon,date,usage
        Barrett,2023-01-12,100
        Deagles,2023-01-12,0.0
        """
        assert_dataframes_equal(expected, actual)

    def test_rolling_average(self):
        collector = FriWeaponUsageCollector().init()
        import_games(get_project_root() + "/fixtures/", period_days=99999, processors=[collector])

        actual = collector.get_data(['Barrett', 'Deagles', 'Rheinmetall'], 2, 1, 10)[["weapon", "date", "usage"]]
        expected = """
            weapon,date,usage
            Barrett,2023-01-12,74.99999999999999
            Deagles,2023-01-12,0.0
            Rheinmetall,2023-01-12,25.0
            """
        assert_dataframes_equal(expected, actual)

        actual = collector.get_data(['Barrett', 'Deagles'], 9999, 1, 9999)[["weapon", "date", "usage"]]
        expected = """
            weapon,date,usage
            Barrett,2023-01-12,100
            Deagles,2023-01-12,0.0
            """
        assert_dataframes_equal(expected, actual)

    def test_full_dataset(self):
        collector = FriWeaponUsageCollector().init()
        import_games(get_project_root() + "/logs_ranked/", period_days=90, processors=[collector], game_filters=[PLAYLIST_CTF])
        collector.get_data(WEAPONS_PRIMARY, 21, 5, 21 * 3 + 5)  # does not throw anything
        pass
