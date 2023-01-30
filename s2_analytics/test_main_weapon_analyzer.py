from typing import Union, Callable

from s2_analytics.constants import WEAPONS_PRIMARY, W_STEYR, W_BARRETT, W_DEAGLES, WEAPONS_SECONDARY, W_RPG
from s2_analytics.game_builder import GameBuilderFactory
from s2_analytics.importer import RoundData
from s2_analytics.main_weapon_analyzer import MainWeaponAnalyzer, MainWeaponRoundTagger
from s2_analytics.team_round_tag_correlation_analyzer import TeamRoundTagCorrelationAnalyzer
from s2_analytics.tools import process_games


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


class TestMainWeaponCorrelation:
    analyzer: TeamRoundTagCorrelationAnalyzer

    def setup_method(self):
        self.analyzer = TeamRoundTagCorrelationAnalyzer([MainWeaponRoundTagger([WEAPONS_PRIMARY, WEAPONS_SECONDARY])])

    def test_creates_main_weapon_tags_for_each_round(self):
        game = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="A", weapon=W_BARRETT) \
            .add_cap(player="A") \
            .add_round() \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_BARRETT) \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], [self.analyzer])

        assert [
                   {"win": 1, "Barrett_x1": 1},
                   {"win": 0},
                   {"win": 1, "SteyrAUG_x1": 1},
                   {"win": 0, "Barrett_x1": 1}
               ] == self.analyzer.tags_by_round

    def test_create_x2_or_x3_tags_if_team_used_same_main_weapons(self):
        game = GameBuilderFactory(teams={"Red": ["1", "2", "3"], "Blue": ["A", "B", "C"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="1", weapon=W_BARRETT) \
            .add_kill(killer="2", weapon=W_BARRETT) \
            .add_kill(killer="3", weapon=W_STEYR) \
            .add_kill(killer="A", weapon=W_DEAGLES) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_kill(killer="C", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], [self.analyzer])

        assert [
                   {'Barrett_x2': 1, 'SteyrAUG_x1': 1, 'win': 0},
                   {'Deagles_x3': 1, 'win': 1}
               ] == self.analyzer.tags_by_round

    def test_calculates_correlation_between_victory_and_tags(self):
        game = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="A", weapon=W_BARRETT) \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], [self.analyzer])
        assert self.analyzer.calculate_win_correlation() == {"Barrett_x1": 1.0, "SteyrAUG_x1": -1.0}

    def test_calculates_correlation_between_victory_and_tags_with_more_data(self):
        game = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_BARRETT) \
            .add_cap(player="A") \
            .add_round() \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], [self.analyzer])
        assert self.analyzer.calculate_win_correlation()["SteyrAUG_x1"] == 1.0
        assert self.analyzer.calculate_win_correlation()["Barrett_x1"] < 0.6
        assert self.analyzer.calculate_win_correlation()["Deagles_x1"] < 0.6

    def test_calculates_correlation_of_secondary_weapons_as_well(self):
        game = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="A", weapon=W_RPG) \
            .add_kill(killer="A", weapon=W_RPG) \
            .add_kill(killer="B", weapon=W_BARRETT) \
            .add_cap(player="A") \
            .add_round() \
            .add_kill(killer="A", weapon=W_DEAGLES) \
            .add_kill(killer="A", weapon=W_RPG) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], [self.analyzer])
        assert self.analyzer.calculate_win_correlation()["RPG_x1"] == 1.0

    def test_calculations_ignore_some_rounds(self):
        game = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_cap(player="A") \
            .add_round(map="ctf_ash") \
            .add_kill(killer="A", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        analyzer = self._create_analyzer()
        process_games([game], [analyzer])
        assert analyzer.calculate_win_correlation()["SteyrAUG_x1"] < 0.6

        analyzer = self._create_analyzer(lambda r: r.map == "ctf_x")
        process_games([game], [analyzer])

        assert analyzer.calculate_win_correlation()["SteyrAUG_x1"] == 1.0

    def _create_analyzer(self, round_filter: Union[Callable[[RoundData], bool], None] = None):
        return TeamRoundTagCorrelationAnalyzer(
            [MainWeaponRoundTagger([WEAPONS_PRIMARY, WEAPONS_SECONDARY])],
            round_filter=round_filter
        )
