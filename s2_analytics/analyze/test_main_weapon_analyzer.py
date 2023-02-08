from s2_analytics.analyze.main_weapon_analyzer import MainWeaponAnalyzer


class TestMainWeaponAnalyzer:
    player1 = "fri"
    player2 = "vndl"
    player3 = "thewall"

    def test_picks_up_only_configured_guns(self):
        sut = MainWeaponAnalyzer([["knife"]], {"blue": [self.player1]})
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player1, "rpg")
        sut.process_kill(self.player1, "rpg")
        assert sut.report() == {"blue": {"knife": 1}}

        sut = MainWeaponAnalyzer([["rpg"]], {"blue": [self.player1]})
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player1, "rpg")
        sut.process_kill(self.player1, "rpg")
        assert sut.report() == {"blue": {"rpg": 1}}

    def test_calculates_most_used_weapons(self):
        sut = MainWeaponAnalyzer([["mp5", "ak"]], {"blue": [self.player1]})
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player1, "knife")
        assert sut.report() == {"blue": {"mp5": 1}}

    def test_doesnt_blow_up_without_data(self):
        analyzer = MainWeaponAnalyzer([[]], {})
        assert analyzer.report() == {}

    def test_calculates_main_weapon_used_by_each_player(self):
        sut = MainWeaponAnalyzer([["mp5", "ak", "minigun"]], {"A": [self.player1, self.player2]})
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player2, "minigun")
        sut.process_kill(self.player2, "mp5")
        sut.process_kill(self.player2, "mp5")
        assert sut.report()["A"] == {"ak": 1, "mp5": 1}

    def test_calculates_counts_of_main_weapons_per_team(self):
        sut = MainWeaponAnalyzer([["mp5", "ak", "minigun"]], {"A": [self.player1, self.player2], "B": [self.player3]})
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player2, "mp5")
        sut.process_kill(self.player3, "mp5")
        assert sut.report() == {"A": {"mp5": 2}, "B": {"mp5": 1}}

    def test_weapon_used_for_more_than_50_percent_of_kills_is_only_considered_main(self):
        sut = MainWeaponAnalyzer([["mp5", "ak", "minigun"]], {"A": [self.player1]})
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player1, "mp5")
        assert sut.report()["A"] == {}
        sut.process_kill(self.player1, "mp5")
        assert sut.report()["A"] == {"mp5": 1}

    def test_main_weapons_are_calculated_for_each_team_separately(self):
        sut = MainWeaponAnalyzer([["mp5", "ak", "minigun"]], {"A": [self.player1], "B": [self.player2]})
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player2, "mp5")
        assert sut.report() == {"A": {"mp5": 1}, "B": {"mp5": 1}}

    def test_calculates_main_weapon_from_each_group_of_guns_independently(self):
        sut = MainWeaponAnalyzer([["mp5", "ak", "minigun"], ["knife", "rpg"]], {"teamA": [self.player1]})
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "ak")
        sut.process_kill(self.player1, "mp5")
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player1, "rpg")
        sut.process_kill(self.player1, "knife")
        sut.process_kill(self.player1, "knife")
        assert sut.report()["teamA"] == {"knife": 1, "ak": 1}


NO_RESULT_TAG_FILTER = lambda t: t not in ["win", "lose"]


