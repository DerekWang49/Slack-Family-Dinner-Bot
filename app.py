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
import pprint

# Create "special time". When special time is reached, display
# the current week's cooks/cleaners
# TODO: Classes/functions?
# TODO: Catch errors in actual run script

class VarStates:
    def __init__(self):
        self.testing = True
        self.cooks = None
        self.cleaners = None
        self.cooking_crew = None
        self.cleaning_crew = None
        self.user_data = None
        self.formatted_date = None
        self.combined_text = None


state = VarStates()
# Load secret tokens from the .env file
load_dotenv()


# Clients
# Starts bot and retrieves signing secret
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def main():

    # Debugging Log
    logging.basicConfig(level=logging.DEBUG)

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


    ENV = os.getenv("BOT_ENV", "development")
    state.testing = True
    # Only send to real channel instead of bot testing channel once changes
    # have been committed to the VM version
    if ENV == "production":
        print("Production!")
        state.testing = False

    print(state.testing)

    today = datetime.today()
    if state.testing:
        today = datetime.today()
        # today = datetime(2026, 6, 13)

    #
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
    state.cooks = df.iloc[i, 2:6]
    # print("Cleaning")
    # print(df.iloc[i, 6:10])

    # Cleaners
    state.cleaners = df.iloc[i, 6:10]

    print(df.iloc[i, 2])
    print(state.cooks)
    print(state.cleaners)

    state.cooking_crew = ":cook: Cooking Crew: "
    state.cleaning_crew = ":broom: Cleaning Crew: "

    with open('slack_user_id.json') as json_user_data:
        state.user_data = json.load(json_user_data)

    # if "Derek" in user_data:
    #     print(f'Derek\'s id: {user_data["Derek"]}')

    # Add names to the string
    for i in range(len(state.cooks)):
        if (state.cooks[i] in state.user_data):
            state.cooking_crew += f"<@{state.user_data[state.cooks[i]]}>"
        else:
            state.cooking_crew += str(state.cooks[i])
        if i != len(state.cooks) - 1:
            state.cooking_crew += ", "
    for i in range(len(state.cleaners)):
        if (state.cleaners[i] in state.user_data):
            state.cleaning_crew += f"<@{state.user_data[state.cleaners[i]]}>"
            print("I'm still standing")
        else:
            state.cleaning_crew += str(state.cleaners[i])

        if i != len(state.cleaners) - 1:
            state.cleaning_crew += ", "

    state.formatted_date = ":dinner_sign: Family Dinner Crew for " + next_date.strftime("%B %d, %Y") + ": "
    # What do I want
    # Print out schedule every week

    #
    # date_format = "%Y-%m-%d"


    # Logic: Just find date that is either today or in the future


    # Message sender to be called upon
    # Example
    # Print message glorifying to God when called upon

    state.combined_text = state.formatted_date + "\n" \
                    + state.cooking_crew + "\n" \
                    + state.cleaning_crew
    print(state.combined_text)



# Listens to mention of the bot
@app.event("app_mention")
def handle_mention(event, say):
    say(f"{state.formatted_date}")
    say(f"{state.cooking_crew}")
    say(f"{state.cleaning_crew}")



def send_scheduled_message():
    channel = "#bot-testing"
    if not state.testing:
        channel = "#announcements"
    client.chat_postMessage(channel=channel,
                            text=state.combined_text)
    print("Sent!!!!")

def send_direct_message():
    for i in range(len(state.cooks)):
        cook_text = "This is a reminder that you are on cooking crew for this Sunday's family dinner! :relaxed:"
        if state.cooks[i] in state.user_data:
            client.chat_postMessage(channel=state.user_data[state.cooks[i]],
                                    text=cook_text)
            print("Direct message sent")
    for i in range(len(state.cleaners)):
        clean_text = "This is a reminder that you are on cleaning crew for this Sunday's family dinner! :relaxed:"
        if state.cleaners[i] in state.user_data:
            client.chat_postMessage(channel=state.user_data[state.cleaners[i]], text=clean_text)
            print("Direct message sent")



time_test = datetime.now()
print(time_test)
print()

if __name__ == "__main__":
    main()
    scheduler = BackgroundScheduler(timezone=timezone("US/Central"))
    # TODO: Add day
    scheduler.add_job(send_scheduled_message, "cron", day_of_week='mon', hour=15, minute=30)
    scheduler.add_job(send_direct_message, "cron", day_of_week='fri', hour=11, minute=00)
    scheduler.start()
    # Get app token from environment variable
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()


# :dinner_sign:
