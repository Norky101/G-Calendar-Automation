# G-Calendar-Automation

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