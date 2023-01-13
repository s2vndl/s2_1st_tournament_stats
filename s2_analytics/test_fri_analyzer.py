from .fris_analyzer import FriWeaponUsageAnalyzer


def _add_kills(detector: FriWeaponUsageAnalyzer, weapon: str, kill_count: int):
    for i in range(0, kill_count):
        detector.process_kill(weapon)


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
