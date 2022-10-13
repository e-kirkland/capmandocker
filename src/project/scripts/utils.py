from core import create_response

from models.Rosters import Rosters
from models.Players import Players
from models.Settings import Settings


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

    print("ROSTER DF: ", rosterdf.head(), flush=True)

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

    print("GETTING SALARY SUM FOR ROSTER_ID: ", roster_id, flush=True)
    salary_sum = Players.get_roster_salary_sum(roster_id)
    print("CURRENT SALARY SUM: ", salary_sum)

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

    returnstring = f"Current cap spending is *${str(salary_sum)}*. \n\nAvailable cap room is *${str(available)}*."

    return returnstring
