from os.path import join, dirname

from sleeper_wrapper import League, Players
import pandas as pd

from models.Rosters import Rosters
from models.Settings import Settings
from views.players import players_upsert_df
from views.rosters import records_upsert_df
from scripts import utils


def get_transactions(leagueID):
    try:

        # Instantiate league based on id
        league = League(leagueID)

        # Blank transactions value to start
        transactions = []

        # List of possible weeks
        weeklist = range(0, 18)
        print("WEEKLIST: ", weeklist)

        for n in weeklist:

            print(f"TRYING TRANSACTIONS FOR WEEK {n}", flush=True)
            # Try to get transactions for week number
            week_transactions = league.get_transactions(n)
            if week_transactions:
                print("TRANSACTIONS RETRIEVED: ", len(week_transactions), flush=True)
            transactions = week_transactions + transactions

        return transactions

    except Exception as e:

        return print(e)


def get_most_recent_transaction(transactions):

    # Get most recent transaction
    transaction = transactions[0]
    transactionid = transaction["transaction_id"]

    print("TRANSACTION: ", transactionid)

    return str(transactionid)


def check_transaction(leagueID):

    try:

        transactions = get_transactions(leagueID)
        print("ALL TRANSACTIONS: ", transactions, flush=True)

        transactionID = get_most_recent_transaction(transactions)
        print("LATEST TRANSACTION FOUND: ", transactionID, flush=True)

        _settings = Settings.get_by_league_id(leagueID)
        lastTransaction = _settings.transaction_id
        print("LAST STORED TRANSACTIN: ", lastTransaction, flush=True)

        if int(transactionID) <= int(lastTransaction):
            print("SAME TRANSACTION, NO NEED TO UPDATE", flush=True)
            return "NO UPDATE"

        elif int(transactionID) > int(lastTransaction):
            print("NEW TRANSACTIONS FOUND, NEED TO UPDATE ROSTERS")
            msg = utils.update_from_transactions(transactions, lastTransaction)

            msg = utils.store_most_recent_transaction(leagueID, transactionID)

            return msg

        else:
            return "NO TRANSACTIONS PROCESSED"

    except Exception as e:

        return f"TRANSACTION UPATE ERROR: {e}"


def get_players():
    try:
        # Get all player data
        players = Players()
        all_players = players.get_all_players()

        # Convert json to dataframe
        playerdf = pd.DataFrame.from_dict(all_players, orient="index")

        # Format playerdf for postgres upload
        playerdf["player"] = playerdf["full_name"]
        keepcols = ["player_id", "player", "position", "team"]
        playerdf = playerdf[keepcols]

        # Limiting to only fantasy-relevant players
        offensepos = ["WR", "RB", "TE", "QB", "K", "DEF"]
        playerdf = playerdf[playerdf["position"].isin(offensepos)]

        # Storing placeholders for salary
        playerdf["salary"] = 0

        # Storing placeholders for injured_reserve
        playerdf["injured_reserve"] = False

        # Storing placeholder for war
        playerdf["war"] = 0.0

        # Storing placeholder for value
        playerdf["value"] = 0.0

        return playerdf

    except Exception as e:
        return e


def compile_team_data(users, rosters):

    try:

        # # Compile roster data
        rosterdf = pd.DataFrame(rosters)

        print("ROSTER DF LEN: ", len(rosterdf), flush=True)

        # Narrowing to relevant fields
        keepcols = ["roster_id", "players", "owner_id"]
        rosterdf = rosterdf[keepcols]

        # Compile user data for each roster
        userdf = pd.DataFrame(users)

        # Narrowing to relevant fields
        keepcols = ["user_id", "display_name"]
        userdf = userdf[keepcols]

        # Compiling both dataframes
        compiled = rosterdf.merge(
            userdf, "left", left_on="owner_id", right_on="user_id"
        )

        print("COMPILED DF: ", compiled.head(), flush=True)
        print("COMPILED DF COLUMNS: ", compiled.columns, flush=True)

        # Renaming players to player_ids
        compiled = compiled.rename(columns={"players": "player_ids"})

        keepcols = ["roster_id", "display_name", "player_ids"]
        compiled = compiled[keepcols]

        # Storing columns for salary_total and players_total
        compiled["salary_total"] = 0
        compiled["players_total"] = 0

        print("FINAL DF: ", compiled.head(), flush=True)

        return compiled

    except Exception as e:
        raise e


def get_teams(leagueID):

    try:

        # Instantiate league based on id
        league = League(leagueID)

        # Get data on all league users for team metadata
        users = league.get_users()

        # Get data on all rosters
        rosters = league.get_rosters()

        print("ROSTERS: ", rosters[0], flush=True)

        # Compile team info
        teamsdf = compile_team_data(users, rosters)

        print("TEAMS DF COMPILED: ", teamsdf.head(), flush=True)
        print("TEAMS DF COLUMNS: ", teamsdf.columns, flush=True)

        # Post team data to postgres
        msg = records_upsert_df(teamsdf)

        print("ROSTERS POSTED", flush=True)

        return teamsdf

    except Exception as e:

        return e


def match_player_to_roster(player, rosters):

    match_id = "999"
    for index, row in rosters.iterrows():
        players = row["player_ids"]
        if players != None:
            if player in players:
                match_id = row["roster_id"]
            else:
                pass
        else:
            pass

    return match_id


def get_league(leagueID):
    try:
        print("GETTING LEAGUE DATA", flush=True)
        # Pull player rosters
        playerdf = get_players()

        print("PLAYERS: ", playerdf.head(), flush=True)

        # Get all roster data
        teams = get_teams(leagueID)

        print("TEAMS: ", teams.head(), flush=True)

        # Matching players to rosters based on current teams
        playerdf["roster_id"] = playerdf["player_id"].apply(
            lambda x: match_player_to_roster(x, teams)
        )

        print("PLAYER DF: ", playerdf.head(), flush=True)
        msg = players_upsert_df(playerdf)

        # Get current transactions
        transactions = get_transactions(leagueID)

        # Store most recent transaction
        transaction_id = get_most_recent_transaction(transactions)
        print("MOST RECENT TRANSACTION: ", transaction_id, flush=True)

        return transaction_id

    except Exception as e:
        print("ERROR: ", e, flush=True)
        return e
