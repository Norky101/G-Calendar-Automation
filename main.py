import os
import csv
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pprint import pprint
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

"""
Goal: Automate the process of adding events to a Google Calendar through reading a CSV file.

CSV Format exmaple: 

"Subject","Start Date","Start Time","End Date","End Time","Description","Location"
"Exercise","2024-10-14","07:00","2024-10-14","08:00","Workout","Gym"

Need:
1. GCP API Auth2 permissions to access Google Calendar API setup
2. store credentials.json in the same folder as this file
3. calendar_events.csv to store the events in the same folder as this file
4. calendar_id is the id of the calendar to add the events to.
3. run the script

"""

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
dotenv_path = find_dotenv()
logger.info(f"Found .env file: {dotenv_path}")
load_dotenv(dotenv_path)

# Print all environment variables (be careful with sensitive information)
logger.info("Environment variables:")
for key, value in os.environ.items():
    if key == 'CALENDAR_ID':
        logger.info(f"{key}: {value}")
    else:
        logger.info(f"{key}: [REDACTED]")

# Check if CALENDAR_ID is set
calendar_id = os.getenv('CALENDAR_ID')
if calendar_id:
    logger.info(f"CALENDAR_ID is set: {calendar_id}")
else:
    logger.error("CALENDAR_ID is not set in the environment variables")


# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# At the top of your script, define the path to credentials.json
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
CALENDAR_FILE = os.path.join(os.path.dirname(__file__), 'calendar_events.csv')

# Authenticate and create the service
def authenticate_google_calendar():
    """Authenticate the user and return the Google Calendar service."""
    creds = None
    if os.path.exists('token.json'):
        logger.debug("Found existing token.json file")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        logger.debug("Credentials are missing or invalid")
        if creds and creds.expired and creds.refresh_token:
            logger.debug("Attempting to refresh expired credentials")
            creds.refresh(Request())
        else:
            logger.debug("Starting new authentication flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        
        logger.debug("Saving credentials to token.json")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    logger.debug("Building Google Calendar service")
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_weekly_recurrence(start_date):
    recurrence_rule = f"RRULE:FREQ=WEEKLY;COUNT=52;BYDAY={start_date.strftime('%A')[:2].upper()}"
    return [recurrence_rule]

def add_events_from_csv(service, csv_file):
    with open(csv_file, newline='') as file:
        reader = csv.DictReader(file)
        
        logger.info(f"CSV columns: {reader.fieldnames}")
        
        first_row = next(reader, None)
        if first_row:
            logger.info("First row of CSV data:")
            pprint(first_row)
        
        file.seek(0)
        next(reader)  # Skip the header row
        
        # Use the calendar_id from the .env file
        calendar_id = os.getenv('CALENDAR_ID')
        logger.info(f"Using CALENDAR_ID: {calendar_id}")

        if not calendar_id:
            raise ValueError("CALENDAR_ID is not set in the environment variables")

        for row in reader:
            start_datetime = datetime.strptime(f"{row['Start Date']} {row['Start Time']}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{row['End Date']} {row['End Time']}", "%Y-%m-%d %H:%M")
            
            event = {
                'summary': row['Subject'],
                'location': row['Location'],
                'description': row['Description'],
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'recurrence': create_weekly_recurrence(start_datetime)
            }
            logger.info(f"Creating event: {event}")
            try:
                created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
                logger.info(f"Event created: {created_event.get('htmlLink')}")
            except HttpError as error:
                logger.error(f'An error occurred: {error}')

def main():
    try:
        # Check if CALENDAR_ID is loaded
        calendar_id = os.getenv('CALENDAR_ID')
        if not calendar_id:
            logger.error("CALENDAR_ID is not set in the environment variables")
            return

        logger.info("Starting authentication process")
        service = authenticate_google_calendar()
        logger.info("Authentication successful")
        add_events_from_csv(service, CALENDAR_FILE)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()
