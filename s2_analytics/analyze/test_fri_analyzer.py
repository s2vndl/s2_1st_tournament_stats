from os.path import dirname, abspath

from pandas import Timestamp

from s2_analytics.constants import WEAPONS_PRIMARY
from s2_analytics.filters import PLAYLIST_CTF
from s2_analytics.analyze.fris_analyzer import FriWeaponUsageAnalyzer, FriWeaponUsageCollector
from s2_analytics.importer import import_games
from s2_analytics.test_assertions import assert_dataframes_equal


BASE_PATH = dirname(abspath(__file__)) + "/../../"


class TestFrisPlayerRoundAnalyzer:
    player1 = "fri"
    player2 = "vndl"
    player3 = "thewall"

    def test_picks_up_only_configured_guns(self):
        sut = FriWeaponUsageAnalyzer([["knife"]])
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player1, "rpg")
        sut.process_kill(self.player1, "rpg")
        assert sut.report() == {"knife": 1.}

        sut = FriWeaponUsageAnalyzer([["rpg"]])
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player1, "rpg")
        sut.process_kill(self.player1, "rpg")
        assert sut.report() == {"rpg": 1.}

    def test_calculates_exact_usage_ratio(self):
        sut = FriWeaponUsageAnalyzer([["mp5", "ak"]])
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player1, "knife")
        assert sut.report() == {"ak": 1 / 3, "mp5": 2 / 3}

    def test_doesnt_blow_up_without_data(self):
        analyzer = FriWeaponUsageAnalyzer([[]])
        assert analyzer.report() == {}

    def test_calculates_weapon_usage(self):
        sut = FriWeaponUsageAnalyzer([["mp5", "ak", "minigun"]])
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player2, "minigun")
        sut.process_kill(self.player2, "mp5")
        assert sut.report()["ak"] == 1.
        assert sut.report()["minigun"] == 0.5
        assert sut.report()["mp5"] == 0.5

    def test_counts_usage_of_groups_of_guns_independently(self):
        sut = FriWeaponUsageAnalyzer([["mp5", "ak", "minigun"], ["knife", "rpg"]])
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player2, "minigun")
        sut.process_kill(self.player2, "mp5")
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player2, "knife")
        assert sut.report() == {"ak": 1, "knife": 2, "mp5": 0.5, "minigun": 0.5, "rpg": 0}

    def test_total_usage_should_be_equal_to_player_count_if_one_group_specified(self):
        sut = FriWeaponUsageAnalyzer([["mp5", "ak", "minigun"]])
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player2, "minigun")
        sut.process_kill(self.player2, "minigun")
        sut.process_kill(self.player3, "minigun")
        assert sum(sut.report().values()) == 3.

    def test_total_usage_should_be_equal_to_player_count_times_group_count(self):
        sut = FriWeaponUsageAnalyzer([["mp5", "ak", "minigun"], ["knife", "rpg"]])
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player2, "mp5")
        sut.process_kill(self.player2, "knife")
        assert sum(sut.report().values()) == 4


def _date(iso_string) -> Timestamp:
    return Timestamp.fromisoformat(iso_string)


class TestImportWithAnalyzer:
    def test_collects_kills_and_analyzes_them(self):
        collector = FriWeaponUsageCollector().init()
        import_games(BASE_PATH + "/fixtures/", period_days=99999, processors=[collector])

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
        import_games(BASE_PATH + "/fixtures/", period_days=99999, processors=[collector])

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
        import_games(BASE_PATH + "logs_ranked/", period_days=90, processors=[collector], game_filters=[PLAYLIST_CTF])
        collector.get_data(WEAPONS_PRIMARY, 21, 5, 21 * 3 + 5)  # does not throw anything
        pass
