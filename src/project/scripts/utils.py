import pandas as pd

from core import create_response

from models.Rosters import Rosters
from models.Players import Players
from models.Settings import Settings
from views.players import players_upsert_df


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
