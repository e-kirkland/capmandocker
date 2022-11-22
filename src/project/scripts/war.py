# Standard library imports
import random as random
from os.path import join, dirname
import datetime
from re import I
import traceback

# Third-party imports
import nfl_data_py as nfl
import pandas as pd
import numpy as np
import scipy.stats as st
from dotenv import load_dotenv

from views.slack import slackbot
from views.players import upsert_player
from models.Players import Players


def get_league_multipliers():

    if slackbot.roster_data.get("scoring") is not None:
        scoring = slackbot.roster_data.get("scoring")
    else:
        print(
            """ERROR: No 'scoring' key/value in the league_users.json file.\n
                   Upload file at http://capman.fly.dev/upload""",
            flush=True,
        )
        return None

    return scoring


def compile_offensive_points(
    scoring,
    passing_yards,
    passing_td,
    passing_2pt,
    interceptions,
    rushing_yards,
    rushing_td,
    rushing_2pt,
    sack_fumbles_lost,
    rushing_fumbles_lost,
    receptions,
    receiving_yards,
    receiving_td,
    receiving_2pt,
):
    total_points = 0
    total_points += passing_yards * scoring["passing_yards_multiplier"]
    total_points += passing_td * scoring["passing_td_multiplier"]
    total_points += passing_2pt * scoring["passing_2pt_multiplier"]
    total_points += interceptions * scoring["interceptions_multiplier"]
    total_points += rushing_yards * scoring["rushing_yards_multiplier"]
    total_points += rushing_td * scoring["rushing_td_multiplier"]
    total_points += rushing_2pt * scoring["rushing_2pt_multiplier"]
    total_points += sack_fumbles_lost * scoring["sack_fumbles_lost_multiplier"]
    total_points += rushing_fumbles_lost * scoring["rushing_fumbles_lost_multiplier"]
    total_points += receptions * scoring["receptions_multiplier"]
    total_points += receiving_yards * scoring["receiving_yards_multiplier"]
    total_points += receiving_td * scoring["receiving_td_multiplier"]
    total_points += receiving_2pt * scoring["receiving_2pt_multiplier"]

    return total_points


def calculate_mean_std(df, position, years, k=12, start=0):
    try:
        pos_df = df[df["position"].isin(position)].copy()
    except KeyError as e:
        print("KEY ERROR: ", position)
        print("KEY ERROR DF: ", df.head())
        print("KEY ERROR DF COLUMNS: ", df.columns)
        raise e

    avg_year = pos_df.groupby(["player_name", "season"])["total_points"].mean()
    avg_year = avg_year.reset_index()

    top_dfs = []
    for year in years:
        avg_df = avg_year[avg_year["season"] == year]
        top_k = avg_df.sort_values(by="total_points", ascending=False)[
            start : start + k
        ]
        top_dfs.append(top_k)

    top_combined = pd.concat(top_dfs)
    mean = top_combined["total_points"].mean()
    std = top_combined["total_points"].std()

    return mean, std


def monte_carlo_game(df, num_iterations):
    total_points = []
    for n in range(0, num_iterations):
        points_series = df.apply(
            lambda x: random.normalvariate(x["mean"], x["std"]), axis=1
        )
        total_points.append(points_series.sum())

    return total_points


def calculate_player_wins(
    sleeper_id, position, num_games, df, avg_df, avg_team_mean, avg_team_std
):
    player_points = df[df["sleeper_id"] == sleeper_id]["total_points"]
    player_points_avg = player_points.mean()

    score_without_position = avg_df[avg_df["position"] != position]["mean"].sum()
    score_with_player = score_without_position + player_points_avg

    player_z = (score_with_player - avg_team_mean) / avg_team_std

    player_win_prob = st.norm.cdf(player_z)
    player_wins = player_win_prob * num_games

    return player_wins


def calculate_avg_player_wins(position, num_games, avg_df, avg_team_mean, avg_team_std):
    player_points = avg_df[avg_df["position"] == position]["mean"].sum()

    score_without_position = avg_df[avg_df["position"] != position]["mean"].sum()
    score_with_player = score_without_position + player_points

    player_z = (score_with_player - avg_team_mean) / avg_team_std

    player_win_prob = st.norm.cdf(player_z)
    player_wins = player_win_prob * num_games

    return player_wins


def calculate_war(
    sleeper_id, position, num_games, df, avg_df, avg_team_mean, avg_team_std
):
    player_wins = calculate_player_wins(
        sleeper_id, position, num_games, df, avg_df, avg_team_mean, avg_team_std
    )
    avg_player_wins = calculate_avg_player_wins(
        position, num_games, avg_df, avg_team_mean, avg_team_std
    )

    return player_wins - avg_player_wins


def create_merged_player_df(years=[2021, 2020, 2019]):

    # Download roster values for years
    rosters = nfl.import_rosters(years)

    player_merge_table = pd.DataFrame(
        rosters.groupby(["player_id", "sleeper_id", "player_name"])
        .size()
        .reset_index(name="Freq")
    )

    # Download yearly data from nfl_data_py
    yearly = nfl.import_weekly_data(years, downcast=True)

    yearly = yearly.drop(columns=["player_name", "position"])
    yearly = yearly.merge(
        player_merge_table, how="left", left_on="player_id", right_on="player_id"
    )
    yearly = yearly.drop(columns=["Freq", "player_name"])
    yearly = yearly.rename(
        columns={"player_display_name": "player_name", "position_group": "position"}
    )

    fantasy_players = Players.get_all_players_df()

    fantasy_players = fantasy_players.rename(
        columns={
            "position": "pg_position",
            "player": "pg_player_name",
            "player_id": "pg_player_id",
        }
    )

    merged = yearly.merge(
        fantasy_players,
        how="left",
        left_on=["player_name", "position"],
        right_on=["pg_player_name", "pg_position"],
    )

    # Consolidate sleeper ids
    merged["sleeper_id"] = merged["sleeper_id"].combine_first(merged["pg_player_id"])

    # Getting single record for each sleeper_id and position
    player_single_record = pd.DataFrame(
        fantasy_players.groupby(["pg_player_id", "pg_position", "pg_player_name"])
        .size()
        .reset_index(name="Freq")
    ).rename(
        columns={
            "pg_player_id": "sleeper_id",
            "pg_player_name": "player_name",
            "pg_position": "position",
        }
    )

    return merged, player_single_record


def calculate_average_team(merged, years=[2021, 2020, 2019]):

    scoring = get_league_multipliers()

    # Compile points for offensive players
    merged["total_points"] = merged.apply(
        lambda x: compile_offensive_points(
            scoring,
            x["passing_yards"],
            x["passing_tds"],
            x["passing_2pt_conversions"],
            x["interceptions"],
            x["rushing_yards"],
            x["rushing_tds"],
            x["rushing_2pt_conversions"],
            x["sack_fumbles_lost"],
            x["rushing_fumbles_lost"],
            x["receptions"],
            x["receiving_yards"],
            x["receiving_tds"],
            x["receiving_2pt_conversions"],
        ),
        axis=1,
    )

    # Format columns correctly
    merged["total_points"] = merged["total_points"].astype(float)

    merged = merged.reset_index()

    df_list = []

    qb_mean, qb_std = calculate_mean_std(merged, position=["QB"], years=years, k=32)
    df_list.append(["QB", qb_mean, qb_std, 10])

    rb_mean, rb_std = calculate_mean_std(merged, position=["RB"], years=years, k=64)
    df_list.append(["RB", rb_mean, rb_std, 10])

    rb2_mean, rb2_std = calculate_mean_std(merged, position=["RB"], years=years, k=64)
    df_list.append(["RB2", rb2_mean, rb2_std, 10])

    wr_mean, wr_std = calculate_mean_std(merged, position=["WR"], years=years, k=64)
    df_list.append(["WR", wr_mean, wr_std, 10])

    wr2_mean, wr2_std = calculate_mean_std(merged, position=["WR"], years=years, k=32)
    df_list.append(["WR2", wr2_mean, wr2_std, 10])

    te_mean, te_std = calculate_mean_std(merged, position=["TE"], years=years, k=32)
    df_list.append(["TE", te_mean, te_std, 10])

    avg_df = pd.DataFrame(df_list, columns=["position", "mean", "std", "n"])

    return avg_df


def simulate_avg_points(avg_df, n_iter=10000):

    # Calculate total points with simulation
    total_points = monte_carlo_game(avg_df, n_iter)
    # Calculate avg/stdev
    avg_team_mean = np.mean(total_points)
    avg_team_std = np.std(total_points)

    return avg_team_mean, avg_team_std


def calculate_all_players_war(merged, player_df, avg_df, avg_team_mean, avg_team_std):

    # Get dataframe to calculate war
    keepcols = ["sleeper_id", "position", "player_name"]
    player_df = player_df[keepcols]
    positions_keep = ["QB", "RB", "WR", "TE"]
    player_df = player_df[player_df["position"].isin(positions_keep)]

    # Calculate WAR for all players
    player_df["war"] = player_df.apply(
        lambda x: calculate_war(
            x["sleeper_id"],
            x["position"],
            15,
            merged,
            avg_df,
            avg_team_mean,
            avg_team_std,
        ),
        axis=1,
    )

    player_df = player_df.dropna(subset=["war", "sleeper_id"])
    player_df = player_df.sort_values(by=["war"], ascending=False)

    return player_df


def calculate_league_war(years=[2021, 2020, 2019]):

    merged, player_df = create_merged_player_df(years)

    avg_df = calculate_average_team(merged, years=years)

    avg_team_mean, avg_team_std = simulate_avg_points(avg_df, n_iter=10000)

    # Reducing player point calculations to previous 20 games
    merged = merged.sort_values(by=["season", "week"], ascending=False)
    merged["player_count"] = merged.groupby(["sleeper_id", "player_name", "position"])[
        "sleeper_id"
    ].transform("count")

    # Reducing to players with more than 3 games to consider
    merged = merged[merged["player_count"] >= 3]
    merged = merged.drop(columns=["player_count"])
    # merged = merged.groupby("sleeper_id").head(20).reset_index(drop=True)

    # Limiting WAR to previous 6-game stretch
    merged = merged.groupby("sleeper_id").head(6).reset_index(drop=True)

    player_df = calculate_all_players_war(
        merged, player_df, avg_df, avg_team_mean, avg_team_std
    )

    return player_df


def calculate_value(salary, war):
    if salary:
        if war:
            if salary == 0.0:
                return 0.0
            else:
                if war == 0.9:
                    return 0.0
                else:
                    return war / salary
        else:
            return 0.0
    else:
        return 0.0


def get_year_dates(num_years=3):

    cur_year = int(datetime.datetime.now().strftime("%Y"))
    all_years = []
    for n in range(0, num_years):
        all_years.append(cur_year - n)

    return all_years


def determine_years_to_pull():

    cur_year = int(datetime.datetime.now().strftime("%Y"))
    df = nfl.import_weekly_data(years=[cur_year], columns=["season", "week"])
    unique_weeks = [x for x in df["week"].unique()]

    # If we are past week 4, return 1 to pull from current season
    if len(unique_weeks) >= 4:
        return 1

    # Otherwise, pull form previous season as well
    else:
        return 2


def update_league_war():
    print("UPDATING LEAGUE WAR", flush=True)

    num_years = determine_years_to_pull()

    years = get_year_dates(num_years=num_years)
    print("YEARS TO ANALYZE: ", years)

    player_df = calculate_league_war(years)

    # Getting existing players table
    fantasy_players = Players.get_all_players_df()
    fantasy_players = fantasy_players.drop(columns=["war", "value"])

    fantasy_players = fantasy_players.drop_duplicates(subset=["player_id"])

    # Get sleeper ID for null values in player_df
    null_player_df = player_df[player_df["sleeper_id"].isna()]
    nonnull_player_df = player_df[~player_df["sleeper_id"].isna()]
    fantasy_players_merge = fantasy_players[["player_id", "player", "position"]]
    fantasy_players_merge = fantasy_players_merge.rename(
        columns={"player": "pg_player", "position": "pg_position"}
    )
    null_player_df = null_player_df.drop(columns=["sleeper_id"])
    fantasy_players_merge = fantasy_players_merge.rename(
        columns={"player_id": "sleeper_id"}
    )
    new_player_df = null_player_df.merge(
        fantasy_players_merge,
        how="left",
        left_on=["player_name", "position"],
        right_on=["pg_player", "pg_position"],
    )

    keepcols = nonnull_player_df.columns
    new_player_df = new_player_df[keepcols]

    player_df = pd.concat([new_player_df, nonnull_player_df])

    player_df = player_df.drop_duplicates(subset=["sleeper_id"])

    try:
        # Merging
        player_df = player_df.drop(columns=["position", "player_name"])
        merged = fantasy_players.merge(
            player_df, how="left", left_on="player_id", right_on="sleeper_id"
        )
    except Exception as e:
        msg = traceback.print_exc()
        return msg

    # Calculating value
    merged["salary"] = pd.to_numeric(merged["salary"])
    merged["value"] = merged.apply(
        lambda x: calculate_value(x["salary"], x["war"]), axis=1
    )

    keepcols = [
        "player_id",
        "player",
        "position",
        "team",
        "salary",
        "roster_id",
        "injured_reserve",
        "war",
        "value",
    ]
    current_players = merged[keepcols]

    for n in range(0, len(current_players)):
        player_id = current_players["player_id"][n]
        war = current_players["war"][n]
        value = current_players["value"][n]

        if war != np.NaN and value != np.NaN:
            war = "{:.2f}".format(war)
            value = "{:.3f}".format(value)
            data = {"war": war, "value": value}

            _player = upsert_player(player_id, data)

        else:
            pass

    return "SUCCESS"


def calculate_starter_war(players_df):

    total_war = 0

    # Get top qb war
    qb_df = players_df[players_df["position"] == "QB"]
    qb_war = qb_df["war"].max()
    total_war += qb_war

    # Get top TE war
    te_df = players_df[players_df["position"] == "TE"]
    te_war = te_df["war"].max()
    total_war += te_war

    # Get top 4 RB war
    rb_df = players_df[players_df["position"] == "RB"]
    rb_df = rb_df.sort_values(by="war", ascending=False)
    rb_df = rb_df.head(4)
    rb_war = rb_df["war"].sum()
    total_war += rb_war

    # Get top 4 WR war
    wr_df = players_df[players_df["position"] == "WR"]
    wr_df = wr_df.sort_values(by="war", ascending=False)
    wr_df = wr_df.head(4)
    wr_war = wr_df["war"].sum()
    total_war += wr_war

    return total_war


def calculate_league_starter_war(active_players):

    roster_ids = active_players["roster_id"].unique()

    return_dicts = []
    for id in roster_ids:
        id_dict = {}
        id_dict["roster_id"] = id

        id_df = active_players[active_players["roster_id"] == id]
        id_war = calculate_starter_war(id_df)
        id_dict["starter_war"] = id_war

        return_dicts.append(id_dict)

    return_df = pd.DataFrame(return_dicts)

    return return_df


if __name__ == "__main__":

    player_df = calculate_league_war(years=[2021, 2020, 2019])
    print(player_df.head(100))
