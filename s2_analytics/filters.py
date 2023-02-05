def max_imbalance(max_difference: float):
    return lambda g: abs(0.5 - g.team_win_probabilities[list(g.teams.keys())[0]]) <= max_difference / 2


PLAYLIST_CTF = lambda g: "CTF" in g.playlist_code
BALANCED = max_imbalance(max_difference=0.10)
