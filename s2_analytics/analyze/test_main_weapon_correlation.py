import sqlite3

from s2_analytics.collect.sqlite_collector import SqliteCollector
from s2_analytics.constants import WEAPONS_PRIMARY, WEAPONS_SECONDARY, W_BARRETT, W_STEYR, W_DEAGLES, W_RPG
from s2_analytics.game_builder import GameBuilderFactory, GameBuilder
from s2_analytics.analyze.main_weapon_analyzer import MainWeaponRoundTagger
from s2_analytics.analyze.main_weapon_correlation import TeamRoundTagCorrelationAnalyzer
from s2_analytics.analyze.test_main_weapon_analyzer import NO_RESULT_TAG_FILTER
from s2_analytics.tools import process_games


class TestMainWeaponCorrelation:
    analyzer: TeamRoundTagCorrelationAnalyzer

    def setup_method(self):
        conn = sqlite3.connect("file::memory:")
        sqlite_collector = SqliteCollector(sqlite_conn=conn).init()
        self.analyzer = TeamRoundTagCorrelationAnalyzer(conn, sqlite_collector, [
            MainWeaponRoundTagger([WEAPONS_PRIMARY, WEAPONS_SECONDARY])
        ]).init()
        self.collectors = [sqlite_collector, self.analyzer]

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

        process_games([game], self.collectors)

        assert self.analyzer.tags_by_round(NO_RESULT_TAG_FILTER) == [
            # game, round, team, tag entries
            (1000, 1, "Red", "Barrett_x1"),
            (1000, 2, "Red", "SteyrAUG_x1"),
            (1000, 2, "Blue", "Barrett_x1")
        ]

    def test_tags_each_teamround_as_win_or_lose(self):
        game = GameBuilderFactory(teams={"Red": ["1", "2", "3"], "Blue": ["A", "B", "C"]}) \
            .add_game() \
            .add_round() \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], self.collectors)

        assert self.analyzer.tags_by_round() == [(1000, 1, 'Red', 'lose'),
                                                 (1000, 1, 'Blue', 'win')]

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

        process_games([game], self.collectors)

        assert self.analyzer.tags_by_round(NO_RESULT_TAG_FILTER) == [
            (1000, 1, 'Red', 'Barrett_x2'),
            (1000, 1, 'Red', 'SteyrAUG_x1'),
            (1000, 1, 'Blue', 'Deagles_x3')]

    def test_returns_count_of_each_tag_in_dataset(self):
        game = GameBuilderFactory(teams={"Red": ["1", "2", "3"], "Blue": ["A", "B", "C"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="1", weapon=W_BARRETT) \
            .add_kill(killer="3", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], self.collectors)

        assert self.analyzer.tag_counts(NO_RESULT_TAG_FILTER) == {
            'Barrett_x1': 1,
            'SteyrAUG_x1': 2}

    def test_calculates_correlation_between_victory_and_tags(self):
        game = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round() \
            .add_kill(killer="A", weapon=W_BARRETT) \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="A") \
            .build() \
            .finish()[0]

        process_games([game], self.collectors)
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

        process_games([game], self.collectors)
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
            .finish()[0]  # why [0] ??

        process_games([game], self.collectors)
        assert self.analyzer.calculate_win_correlation()["RPG_x1"] == 1.0

    def test_calculates_correlations_for_selected_map(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .add_round(map="ctf_ash") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="B") \
            .build() \
            .finish()

        process_games(games, self.collectors)
        correlation = self.analyzer.calculate_win_correlation(map_name="ctf_x")
        assert correlation["SteyrAUG_x1"] == 1.0

    def test_calculates_correlations_for_all_maps(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .add_round(map="ctf_ash") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="B") \
            .build() \
            .finish()

        process_games(games, self.collectors)
        correlation = self.analyzer.calculate_win_correlation_per_map()
        assert correlation["ctf_x"]["SteyrAUG_x1"] == 1.0
        assert correlation["ctf_ash"]["SteyrAUG_x1"] == -1.0

    def test_calculates_counts_of_tags_for_each_map(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_DEAGLES) \
            .add_cap(player="A") \
            .add_round(map="ctf_ash") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_kill(killer="B", weapon=W_BARRETT) \
            .add_cap(player="B") \
            .build() \
            .finish()

        process_games(games, self.collectors)
        per_map = self.analyzer.tag_counts_per_map(NO_RESULT_TAG_FILTER)
        assert per_map == {
            "ctf_x": {"SteyrAUG_x1": 1, "Deagles_x1": 1},
            "ctf_ash": {"SteyrAUG_x1": 1, "Barrett_x1": 1}
        }

    def test_sample_correlation_coefficient(self):
        builder = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}).add_game()

        def add_won_round_with_main_weapon(builder: GameBuilder, main_weapon: str, won: bool):
            return builder.add_round(map="ctf_x") \
                .add_kill(killer="A", weapon=main_weapon) \
                .add_cap(player="A" if won else "B")

        for i in range(0, 48):
            add_won_round_with_main_weapon(builder, W_STEYR, won=True)
        for i in range(0, 52):
            add_won_round_with_main_weapon(builder, W_STEYR, won=False)

        games = builder.build().finish()

        process_games(games, self.collectors)
        assert self.analyzer.calculate_win_correlation() == {
            "SteyrAUG_x1": -0.04
        }

    def test_calculates_correlation_for_weapon_on_all_maps(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x", winner="Red") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_round(map="ctf_ash", winner="Red") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .build() \
            .finish()

        process_games(games, self.collectors)
        corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        assert corr.tag == "SteyrAUG_x1"
        assert corr.correlation("ctf_x") == 1
        assert corr.correlation("ctf_ash") == -1
        assert corr.correlation("ctf_othermap") == 0

    def test_correlation_result_has_a_tag_name(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x", winner="Red") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_round(map="ctf_x", winner="Blue") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_round(map="ctf_ash", winner="Red") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .build() \
            .finish()

        process_games(games, self.collectors)
        corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        assert corr.tag == "SteyrAUG_x1"
        corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="Deagles_x1")
        assert corr.tag == "Deagles_x1"

    def test_counts_samples_for_weapon_on_all_maps(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x", winner="Red") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_round(map="ctf_x", winner="Blue") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_round(map="ctf_ash", winner="Red") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .build() \
            .finish()

        process_games(games, self.collectors)
        corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        assert corr.sample_count("ctf_x") == 2
        assert corr.sample_count("ctf_ash") == 1
        assert corr.sample_count("ctf_othermap") == 0
        assert corr.sample_count() == 3
