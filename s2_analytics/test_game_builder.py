from s2_analytics.game_builder import GameBuilder
from s2_analytics.tools import process_game


class TestGameBuilder:
    def test_builder_builds_nicely(self):
        teams = {"Red": ["85D4CB1D1C2A72CD"], "Blue": ["C19637F2290726EB"]}
        game = GameBuilder(1673564249000, teams, match_quality=0.5034282868653599) \
            .add_round(start=1673564296797, end_time=1673564552013, map="ctf_x") \
            .add_kill(time=1673564310905, killer="C19637F2290726EB", victim="85D4CB1D1C2A72CD", weapon="Barrett") \
            .add_cap(time=1673564527881, player="C19637F2290726EB") \
            .add_round(start=1673564298797, end_time=1673564554013, map="ctf_ash") \
            .add_kill(time=1673564312905, killer="C19637F2290726EB", victim="85D4CB1D1C2A72CD", weapon="Rheinmetall") \
            .add_kill(time=1673564313105, killer="C19637F2290726EB", victim="85D4CB1D1C2A72CD", weapon="Barrett") \
            .add_cap(time=1673564529881, player="C19637F2290726EB") \
            .build()

        assert process_game("../fixtures/game_1666666666000.json") == game
