import os
import sys

import gspread
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import logging
# import gspread
import pandas as pd
from datetime import datetime
from slack_sdk import WebClient
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import json

# Create "special time". When special time is reached, display
# the current week's cooks/cleaners
# TODO: Mentions
# TODO: Classes/functions?
# TODO: Catch errors in actual run script


# Debugging Log
logging.basicConfig(level=logging.DEBUG)

# Load secret tokens from the .env file
load_dotenv()

# Logging into Google Sheet

credentials_file = os.getenv("CREDENTIALS_PATH")

if not credentials_file:
    raise RuntimeError("CREDENTIALS_PATH is not set")
# credentials_file = "credentials.json"
print(credentials_file)
gc = None
try:
    gc = gspread.service_account(filename=credentials_file)
    print("Successful authentication")

except Exception as e:
    print(f"Failed authentication: {e}")
    exit()

my_google_sheet = None
sh = None
try:
    sh = gc.open("Family Dinner Scheduling")
    print("Opened Family Dinner Scheduling spreadsheet")
except gspread.SpreadsheetNotFound:
    print("Could not open spreadsheet. Check title and/or permissions")
    exit()
except Exception as e:
    print(f"Error: {e}")
    exit()


# Clients
# Starts bot and retrieves signing secret
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# # Default to first sheet
# worksheet = sh.sheet1

# Get Google Sheet into dataframe
# my_google_sheet = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQYHnqOIxpMCROUm4_j1VyYyjQlRSQBxbnbiYztpGuHSOCvDUPwGftHDEqoxry8nEq6R51ymkT8_h3N/pub?output=csv"
print(type(my_google_sheet))
try:
    my_data = sh.get_worksheet(0).get_all_values()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

try:
    df = pd.DataFrame(my_data[1:], columns=my_data[0])
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print(df.iloc[0, :])

# Changing column names
new_header = df.iloc[0].values
df.columns = new_header

# Remove redundant row
df = df.drop(index=0)

# Clean up index
df = df.reset_index(drop=True)

# TODO: Switch back to actual today
today = datetime.today()
# today = datetime(2026, 2, 2)
# date_format = "%m/%d/%Y"
# today = today.strftime(date_format)

# Logic: Where string = date

# The '#' removes the 0 for months before October
# print(datetime.strptime(df["Date"][0], "%m/%d/%y"))

# Find closest date to today
next_date = datetime.strptime(df["Date"][0], "%m/%d/%y")
i = 0
while next_date < today:
    i += 1
    print(i)
    print(next_date)
    try:
        next_date = datetime.strptime(df["Date"][i], "%m/%d/%y")
    except Exception as e:
        print("Could not convert date")
        print(f"Error: {e}")

    # Prevent infinite loop
    if i == len(df["Date"]):
        break


# Cooks
# print("Cooks")
# print(df.iloc[i, 2:6])
print(f"I: {i}")
cooks = df.iloc[i, 2:6]
# print("Cleaning")
# print(df.iloc[i, 6:10])

# Cleaners
cleaners = df.iloc[i, 6:10]

print(df.iloc[i, 2])
print(cooks)
print(cleaners)

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


# Message sender to be called upon
# Example
# Print message glorifying to God when called upon



# Listens to mention of the bot
@app.event("app_mention")
def handle_mention(event, say):
    say(f"{formatted_date}")
    say(f"{cooking_crew}")
    say(f"{cleaning_crew}")

combined_text = formatted_date + "\n" \
                + cooking_crew + "\n" \
                + cleaning_crew
print(combined_text)

ENV = os.getenv("BOT_ENV", "development")
testing = True
# Only send to real channel instead of bot testing channel once changes
# have been committed to the VM version
if ENV == "production":
    testing = False

print(testing)
# TODO: Change text output from formatted date to all data
def send_scheduled_message():
    channel = "#bot-testing"
    if not testing:
        channel = "#announcements"
    client.chat_postMessage(channel=channel,
                            text=combined_text)
    print("Sent!!!!")

time_test = datetime.now()
print(time_test)

if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone=timezone("US/Central"))
    # TODO: Add day
    scheduler.add_job(send_scheduled_message, "cron", day_of_week='thu', hour=16, minute=15)
    # scheduler.add_job(send_scheduled_message, "interval", seconds=30)
    print("Test1")
    scheduler.start()
    # Get app token from environment variable
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
    print("Test2")


# :dinner_sign:
