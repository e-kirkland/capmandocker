import pandas as pd

from core import create_response

from models.Rosters import Rosters
from models.Players import Players
from models.Settings import Settings
from views.players import players_upsert_df, drop_player, add_player, trade_player
from views.settings import update_settings_internal


def get_roster_id(text, lookupdict):

    # Cleaning text
    text = text.lower().strip()

    roster_id = "999"

    for n in range(1, 11):
        id = n
        array = lookupdict[str(n)]
        for word in array:
            if word in text:
                roster_id = str(id)
                break
            else:
                pass

    return str(roster_id)


def get_team_name(roster_id):

    _roster = Rosters.get_by_roster_id(roster_id)

    return _roster.display_name


def get_my_roster(roster_id):

    rosterdf = Players.get_df_by_roster_id(roster_id)

    rosterdf.sort_values(by=["position", "salary"], inplace=True)

    rosterdf["salary"] = rosterdf["salary"].apply(lambda x: str(x))

    rosterdf.fillna("0", inplace=True)

    message = """| Position | Player | Team | Salary | \n"""

    for n, row in rosterdf.iterrows():
        playermessage = (
            "| "
            + row["position"]
            + " | "
            + row["player"]
            + " | "
            + row["team"]
            + " | "
            + row["salary"]
            + " |\n"
        )
        message = message + playermessage

    return message


def get_my_cap(roster_id, slackbot):

    salary_sum = Players.get_roster_salary_sum(roster_id)

    team_name = get_team_name(roster_id)

    # Getting league_id
    if slackbot.roster_data.get("league_id") is not None:
        league_id = slackbot.roster_data.get("league_id")
    else:
        return create_response(
            status=400,
            message="""No 'league_id' key/value in the league_users.json file.\n
                   Upload file at http://capman.fly.dev/upload""",
        )

    # Get settings and league cap
    _settings = Settings.get_by_league_id(league_id)
    current_cap = _settings.salary_cap

    available = current_cap - salary_sum

    returnstring = f"""CAP AVAILABILITY FOR *{team_name}*:
                       \nCurrent cap spending is *${str(salary_sum)}*.
                       \nAvailable cap room is *${str(available)}*."""

    return returnstring


def get_salary_csv(slackbot):

    player_df = Players.get_all_players_df()

    # Getting filepath for output csv
    if slackbot.media_folder is not None:
        media_folder = slackbot.media_folder
    else:
        return create_response(
            status=400,
            message="""No 'MEDIA_FOLDER' found. Check the .env file.""",
        )

    csv_filepath = media_folder + "/players.csv"

    player_df.to_csv(csv_filepath, index=None)

    return csv_filepath


def reset_salary_data(fname):

    try:

        # Open csv as df
        df = pd.read_csv(fname)

        # Format for push to postgres
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
        df = df[keepcols]

        msg = players_upsert_df(df)

        return "SUCCESSFULLY UPDATED LEAGUE"

    except Exception as e:

        return f"FAILED UPLOADING TO POSTGRES: {e}"


def process_roster_drops(drops):

    keys = [x for x in drops.keys()]
    values = [x for x in drops.values()]

    for n in range(0, len(keys)):

        _player = drop_player(keys[n])

        print(f"DROPPING PLAYER, UPDATED RECORD: {_player}", flush=True)

    return "DROPS SUCCESSFULLY PROCESSED"


def process_roster_adds(adds, salary=None):

    keys = [x for x in adds.keys()]
    values = [x for x in adds.values()]

    for n in range(0, len(keys)):
        player_id = str(keys[n])
        roster_id = str(values[n])

        # Check for salary data
        if salary:
            if isinstance(salary, list) and salary[n] != None:
                player_salary = int(salary[n])
            elif isinstance(salary, int):
                player_salary = int(salary)
            else:
                player_salary = None
        else:
            player_salary = None

        _player = add_player(player_id, roster_id, salary)

        print(f"ADDING PLAYER, UPDATED RECORD: {_player}", flush=True)

    return "ADDS SUCCESSFULLY PROCESSED"


def process_waiver_transaction(transaction):

    if transaction["status"] == "complete":
        adds = transaction["adds"]
        drops = transaction["drops"]
        bid = transaction["settings"]["waiver_bid"]

        if drops:
            msg = process_roster_drops(drops)
            print(msg, flush=True)
        else:
            pass

        if adds:
            msg = process_roster_adds(adds, bid)
            print(msg, flush=True)
        else:
            pass

    else:
        print("WAIVER TRANSACTION UNSUCCESSFUL, BYPASSING...", flush=True)
        pass

    return


def process_free_agent_transaction(transaction):

    adds = transaction["adds"]
    drops = transaction["drops"]
    salary = 1

    if drops:
        msg = process_roster_drops(drops)
        print(msg, flush=True)
    else:
        pass

    if adds:
        msg = process_roster_adds(adds, salary)
        print(msg, flush=True)
    else:
        pass

    return


def process_other_transaction(transaction):

    adds = transaction["adds"]
    drops = transaction["drops"]
    budgets = transaction["waiver_budget"]

    # Check if all values are populated, indicates likely trade
    if all(v is not None for v in [adds, drops]):
        keys = [x for x in adds.keys()]
        values = [x for x in adds.values()]
        drops_keys = [x for x in drops.keys()]

        # Check if transaction is a trade
        if set(keys) == set(drops_keys):
            print("TRADE DETECTED")

            # Process trades
            for n in range(0, len(keys)):

                _player = trade_player(player_id=str(keys[n]), roster_id=str(values[n]))
                print(f"TRADING PLAYER, UPDATED RECORD: {_player}", flush=True)

        else:
            print(f"UNKONWN TRANSACTION: {transaction}")
            pass

    else:

        msg = process_roster_drops(drops)
        if len(budgets) == 0:
            budgets = None
        msg = process_roster_adds(adds, budgets)

    return


def update_from_transactions(transactions, lastTransaction):

    # Get all new transactions
    new_transactions = [
        x for x in transactions if int(x["transaction_id"]) > int(lastTransaction)
    ]

    print("NEW TRANSACTIONS FOUND: ", len(new_transactions), flush=True)

    # Sort transactions in ascending order, so we execute in order
    new_transactions = sorted(new_transactions, key=lambda i: (i["transaction_id"]))

    # Process each new transaction
    for transaction in new_transactions:
        transaction_type = transaction["type"]
        print(f"TRANSACTION: {transaction}", flush=True)

        # Check type and process
        if transaction_type == "waiver":
            process_waiver_transaction(transaction)

        elif transaction_type == "free_agent":
            process_free_agent_transaction(transaction)

        elif transaction_type != None:
            process_other_transaction(transaction)

        else:
            print("TRANSACTION NOT PROCESSED", flush=True)

    return "ALL TRANSACTIONS PROCESSED"


def store_most_recent_transaction(leagueID, lastTransaction):

    data = {"transaction_id": str(lastTransaction)}

    msg = update_settings_internal(leagueID, data)

    print(msg, flush=True)

    return msg
