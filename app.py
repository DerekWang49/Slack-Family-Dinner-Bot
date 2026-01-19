import os
import sys
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import logging
# import gspread
import pandas as pd
from datetime import datetime


# TODO: Move to Oracle
# TODO: Automatic messaging every week with messages
# TODO: Mentions
# TODO: Pick the correct Google Sheet
# TODO: Classes/functions?
# Debugging Log
logging.basicConfig(level=logging.DEBUG)

# Load secret tokens from the .env file
load_dotenv()

# Get Google Sheet into dataframe
my_google_sheet = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQYHnqOIxpMCROUm4_j1VyYyjQlRSQBxbnbiYztpGuHSOCvDUPwGftHDEqoxry8nEq6R51ymkT8_h3N/pub?output=csv"
try:
    df = pd.read_csv(my_google_sheet)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print(df)

# Changing column names
new_header = df.iloc[0].values
df.columns = new_header

# Remove redundant row
df = df.drop(index=0)

# Clean up index
df = df.reset_index(drop=True)

today = datetime.today()
# date_format = "%m/%d/%Y"
# today = today.strftime(date_format)

# Logic: Where string = date

# The '#' removes the 0 for months before October
# print(datetime.strptime(df["Date"][0], "%m/%d/%y"))

# Find closest date to today
next_date = datetime.strptime(df["Date"][0], "%m/%d/%y")
print("Length: ")
print(len(df["Date"]))
i = 0
while next_date < today:
    try:
        next_date = datetime.strptime(df["Date"][i], "%m/%d/%y")
    except Exception as e:
        print("Could not convert date")
        print(f"Error: {e}")
    i += 1
    print(next_date)

    # Prevent infinite loop
    if i == len(df["Date"]):
        break


# Cooks
# print("Cooks")
# print(df.iloc[i, 2:6])
cooks = df.iloc[i, 2:6]
# print("Cleaning")
# print(df.iloc[i, 6:10])

# Cleaners
cleaners = df.iloc[i, 6:10]


cooking_crew = ":cook: Cooking Crew: "
cleaning_crew = ":broom: Cleaning Crew: "

# Add names to the string
for i in range(len(cooks)):
    cooking_crew += str(cooks[i])
    if i != len(cooks) - 1:
        cooking_crew += ", "
for i in range(len(cleaners)):
    cleaning_crew += str(cleaners[i])
    if i != len(cleaners) - 1:
        cleaning_crew += ", "

formatted_date = ":dinner_sign: Family Dinner Crew for " + next_date.strftime("%B %d, %Y") + ": "
# What do I want
# Print out schedule every week

#
# date_format = "%Y-%m-%d"


# Logic: Just find date that is either today or in the future

# Starts bot and retrieves signing secret
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Example
# Print message glorifying to God when called upon


# Listens to mention of the bot
@app.event("app_mention")
def handle_mention(event, say):
    say(f"{formatted_date}")
    say(f"{cooking_crew}")
    say(f"{cleaning_crew}")


if __name__ == "__main__":
    # Get app token from environment variable
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()

# :dinner_sign:
