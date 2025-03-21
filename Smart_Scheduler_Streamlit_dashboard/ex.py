import os
import pickle
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define OAuth 2.0 Scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Authenticate and Get Service
def authenticate_gmail():
    creds = None
    # Load saved credentials
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

# Send Email
def send_email(subject, body, receiver_email):
    service = authenticate_gmail()

    # Create Email Message
    message = MIMEText(body)
    message["to"] = receiver_email
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": encoded_message})
            .execute()
        )
        print("📧 Email sent successfully! Message ID:", send_message["id"])
    except Exception as e:
        print("❌ Error sending email:", str(e))

# Example Usage
send_email(
    subject="🚀 Task Reminder",
    body="This is an automated reminder for your task!",
    receiver_email="harshaltapre27@yahoo.com"
)

