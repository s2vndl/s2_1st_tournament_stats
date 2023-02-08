import random
import sqlite3

from matplotlib import pyplot as plt

from s2_analytics.collect.sqlite_collector import SqliteCollector
from s2_analytics.constants import WEAPONS_PRIMARY, WEAPONS_SECONDARY, W_STEYR
from s2_analytics.plot.correlation_chart_maker import CorrelationChartMaker
from tests.game_builder import GameBuilderFactory
from s2_analytics.analyze.main_weapon_analyzer import MainWeaponRoundTagger
from s2_analytics.collect.team_round_tag_collector import TeamRoundTagCorrelationAnalyzer
from s2_analytics.tools import process_games
from tests.plotter import PlotShowForTests


class TestWeaponWinCorrelationPlotting:
    def setup_method(self):
        self.plot_show = PlotShowForTests()
        conn = sqlite3.connect("file::memory:")
        sqlite_collector = SqliteCollector(sqlite_conn=conn).init()
        self.analyzer = TeamRoundTagCorrelationAnalyzer(conn, sqlite_collector, [
            MainWeaponRoundTagger([WEAPONS_PRIMARY, WEAPONS_SECONDARY])
        ]).init()
        self.collectors = [sqlite_collector, self.analyzer]

        teams = {"Red": ["A"], "Blue": ["B"]}
        self.factory = GameBuilderFactory(teams=teams)

    def test_charting_weapon_correlation_per_map(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_cap(player="A") \
            .add_round(map="ctf_x") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="B") \
            .add_round(map="ctf_ash") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="A") \
            .build() \
            .finish()

        process_games(games, self.collectors)
        tag_corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        CorrelationChartMaker().plot(tag_corr)
        self.plot_show.show()
        pass

    def test_skipping_maps_with_not_enough_samples_in_weapon_correlation_per_map(self):
        games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
            .add_game() \
            .add_round(map="ctf_x") \
            .add_kill(killer="A", weapon=W_STEYR) \
            .add_cap(player="A") \
            .add_round(map="ctf_x") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="B") \
            .add_round(map="ctf_ash") \
            .add_kill(killer="B", weapon=W_STEYR) \
            .add_cap(player="A") \
            .build() \
            .finish()

        process_games(games, self.collectors)
        tag_corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        CorrelationChartMaker().plot(tag_corr, min_samples=2)
        self.plot_show.show()
        pass

    def test_many_maps(self):
        rand = random.Random(1)

        teams = {"Red": ["A"], "Blue": ["B"]}
        teams_names = list(teams.keys())
        game_builder = GameBuilderFactory(teams=teams).add_game()
        for samples in range(0, 200):
            winner = teams_names[rand.randint(0, 1)]
            round_builder = game_builder.add_round(map=f"ctf_map{rand.randint(1, 40)}", winner=winner)
            round_builder.add_kill(killer="A", weapon=W_STEYR)

        games = game_builder.build().finish()

        process_games(games, self.collectors)
        tag_corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        CorrelationChartMaker().plot(tag_corr, min_samples=3)
        self.plot_show.show()
        pass

    def test_few_maps(self):
        rand = random.Random(1)

        teams = {"Red": ["A"], "Blue": ["B"]}
        teams_names = list(teams.keys())
        game_builder = GameBuilderFactory(teams=teams).add_game()
        for samples in range(0, 50):
            winner = teams_names[rand.randint(0, 1)]
            round_builder = game_builder.add_round(map=f"ctf_map{rand.randint(0, 5)}", winner=winner)
            round_builder.add_kill(killer="A", weapon=W_STEYR)

        games = game_builder.build().finish()

        process_games(games, self.collectors)
        tag_corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        CorrelationChartMaker().plot(tag_corr, min_samples=3)
        self.plot_show.show()
        pass

    def test_doesnt_throw_if_no_data(self):
        process_games([], self.collectors)
        tag_corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        CorrelationChartMaker().plot(tag_corr, min_samples=3)
        self.plot_show.show()
        pass

    def test_custom_limits(self):
        self._generate_games_for_corr(round_count=20, map_count=1, weapon=W_STEYR)
        games = self.factory.finish()

        process_games(games, self.collectors)
        tag_corr = self.analyzer.correlations_for_weapon_tag(weapon_tag="SteyrAUG_x1")
        CorrelationChartMaker().plot(tag_corr, min_samples=3, count_max=100, corr_minmax=(-2, 2))
        self.plot_show.show()
        pass

    def _generate_games_for_corr(self, round_count, map_count, weapon):
        rand = random.Random(1)
        teams_names = list(self.factory._teams.keys())
        game_builder = self.factory.add_game()
        for samples in range(0, round_count):
            winner = teams_names[rand.randint(0, 1)]
            round_builder = game_builder.add_round(map=f"ctf_map{rand.randint(1, map_count)}", winner=winner)
            round_builder.add_kill(killer="A", weapon=weapon)

        game_builder.build()
