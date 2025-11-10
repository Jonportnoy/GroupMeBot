from __future__ import print_function

import time
from contextlib import nullcontext
from idlelib.replace import replace
from operator import indexOf

from groupy.client import Client
from groupy.api.bots import *
from creds import *
import os.path

import os, pickle
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

client = Client.from_token(token)
group = client.groups.get(nu_chi)
bot = client.bots.list()[1].manager


# Choose scope: readonly OR full (edit). Start with readonly.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
bot_print_array = []


def get_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as f:
            pickle.dump(creds, f)
    return build('calendar', 'v3', credentials=creds)


def bot_post(i: int, *args):
    if i:
        event_text()
    else:
        print(f"No events in the next {args[0]} day(s)!")


def list_next_events(service, n=7):
    now = datetime.now(timezone.utc).isoformat()
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=n)).replace(hour=0, minute=0, second=0).isoformat()
    events = service.events().list(
        calendarId='q7smrar352glt664bd9b0smdtk@group.calendar.google.com',
        timeMin=now,
        timeMax=tomorrow,
        singleEvents=True,      # expand recurring series
        orderBy='startTime',
        maxResults=10
    ).execute().get('items', [])
    if not events:
        bot_post(0, n)
        return "no events"
    for i, e in enumerate(events):
        bot_print = {}
        start = e['start'].get('dateTime') or e['start'].get('date')
        start = datetime.fromisoformat(start).strftime("%m-%d-%Y at %I:%M %p")
        bot_print["event_date"] = start
        bot_print['name'] = e.get('summary','(no title)')
        try:
            description = e['description']
            bot_print["description"] = description
            if "Attending" in description and "not attending" not in description.lower():
                start = description.find("Attending")
                end = description.find("<br>", start)

                if end != -1:
                    attending = description[start:end]
                    bot_print["attendance"] = attending
                else:
                    attending = description[start:]  # no <br> found after Attending
                    bot_print["attendance"] = attending
            if 'rms:' in description.lower():
                rms_start = description.lower().find("rms:")
                rms_end = description.lower().find("\n", rms_start)
                bot_print['rms'] = description[rms_start:rms_end]
        except KeyError:
            bot_print["no_des"] = "No description for event. Please check if there are rms, set up, and/or cleanup for this event."
        finally:
            bot_print_array.append(bot_print)

def event_text():
    for curr_event in bot_print_array:
        text = curr_event['name'] + ' - ' + curr_event['event_date'] +'\n'
        if 'attendance' in curr_event:
            text += "    " + curr_event["attendance"] + '\n'

        if 'description' in curr_event and len(curr_event['description']) < 50:
            text += "    " + curr_event['description'] + '\n'
        elif 'no_des' in curr_event:
            text += "    " + curr_event['no_des'] + '\n'
        if 'rms' in curr_event:
            text += "    " + curr_event["rms"] + '\n'

        print(text)


def main():

    ten_am = (datetime.now() + timedelta(days=0)).replace(hour=10, minute=0, second=0, microsecond=0)
    while True:
        now = datetime.now().replace(microsecond=0)
        if now == ten_am:
            svc = get_service()
            if list_next_events(svc, 1) == 'no events':
                ten_am = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
                continue
            bot_post(1)
            ten_am = (datetime.now() + timedelta(days=0)).replace(hour=10, minute=0, second=0, microsecond=0)
        time.sleep(1)
        print(int(ten_am.timestamp() - now.timestamp()), 'seconds to program execution.')




if __name__ == "__main__":
    main()
