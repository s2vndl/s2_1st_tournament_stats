def max_imbalance(max_win_prob_diff: float):
    return lambda g: abs(0.5 - g.team_win_probabilities[list(g.teams.keys())[0]]) <= max_win_prob_diff / 2


PLAYLIST_CTF = lambda g: "CTF" in g.playlist_code
BALANCED = max_imbalance(max_win_prob_diff=0.20)
