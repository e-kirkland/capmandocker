from models.Rosters import Rosters
from models.Players import Players


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
