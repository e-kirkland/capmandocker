import pandas as pd
from sleeper_wrapper import League, Players


def get_current_rosters(league_id):
    players = Players()
    all_players = players.get_all_players()
    playerdf = pd.DataFrame.from_dict(all_players, orient="index")

    league = League(league_id)
    rosters = league.get_rosters()

    roster_dict = [{"id": x["roster_id"], "players": x["players"]} for x in rosters]
    roster_df = pd.DataFrame(roster_dict)
    roster_df = roster_df.explode("players")

    merged = roster_df.merge(playerdf, right_index=True, left_on="players")

    keepcols = ["id", "players", "full_name", "position", "team"]
    keepdf = merged[keepcols]
    keepdf = keepdf.sort_values(
        by=["id", "position", "full_name"], ascending=[True, True, True]
    )

    keepdf.to_csv(
        "/Users/williamkirkland/Data/KDS/capmandocker/data/current_rosters.csv",
        index=False,
    )

    return


if __name__ == "__main__":
    get_current_rosters(786278549685440512)
