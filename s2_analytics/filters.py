PLAYLIST_CTF = lambda g: "CTF" in g.playlist_code
SIMILAR_WIN_PROB = lambda g: abs(0.5 - g.team_win_probabilities[list(g.teams.keys())[0]]) <= 0.05
