import streamlit as st
import sqlite3
import pandas as pd
import smtplib
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# Email settings (replace with your actual email)
SENDER_EMAIL = "@gmail.com"
EMAIL_PASSWORD = "----------"  # App password from Google, not your regular password
RECEIVER_EMAIL = "harshaltapre27@gmail.com"

def setup_database():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    
    # Create table 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY, 
            task TEXT, 
            datetime TEXT, 
            priority TEXT, 
            category TEXT, 
            status TEXT, 
            recurrence TEXT
        )
    ''')
    
    # Save changes and close connection
    conn.commit()
    conn.close()

# Save a new reminder to the database
def save_reminder(task, date, time, priority, category, recurrence):
    # Combine date and time into one string
    full_datetime = f"{date} {time}"
    
    # Connect to database
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    
    # Insert the new reminder
    cursor.execute("""
        INSERT INTO reminders 
        (task, datetime, priority, category, status, recurrence) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task, full_datetime, priority, category, "Pending", recurrence))
    
    # Save changes and close connection
    conn.commit()
    conn.close()

# Get all reminders from the database
def get_all_reminders():
    try:
        # Connect to database
        conn = sqlite3.connect("reminders.db")
        
        # Get all reminders as a list of tuples
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, datetime, priority, category, status, recurrence FROM reminders")
        rows = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        # If no reminders found, return empty DataFrame with correct columns
        if not rows:
            return pd.DataFrame(columns=['ID', 'Task', 'Datetime', 'Priority', 'Category', 'Status', 'Recurrence'])
        
        # Create DataFrame manually with correct column names
        df = pd.DataFrame(rows, columns=['ID', 'Task', 'Datetime', 'Priority', 'Category', 'Status', 'Recurrence'])
        return df
        
    except Exception as e:
        print(f"Error getting reminders: {e}")
        # Return empty DataFrame with correct columns if there's an error
        return pd.DataFrame(columns=['ID', 'Task', 'Datetime', 'Priority', 'Category', 'Status', 'Recurrence'])

# Delete a reminder by ID
def delete_reminder(reminder_id):
    # Connect to database
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    
    # Delete the reminder
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    
    # Save changes and close connection
    conn.commit()
    conn.close()

# Mark a reminder as completed
def complete_reminder(reminder_id):
    # Connect to database
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    
    # Update the reminder status
    cursor.execute("UPDATE reminders SET status = 'Completed' WHERE id = ?", (reminder_id,))
    
    # Save changes and close connection
    conn.commit()
    conn.close()

# --------- EMAIL FUNCTIONS ---------
# Send an email notification
def send_notification_email(task, datetime_str, priority, category):
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"Reminder: {task}"
    
    # Create the email body
    body = f"""Hello Harshal,

Your task '{task}' is due now at {datetime_str}.
Priority: {priority}
Category: {category}

Don't forget to complete it!

Best Regards,
Schedulr"""
    
    msg.attach(MIMEText(body, 'plain'))

    # Try to send the email
    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login with your credentials
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        
        # Send the email
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        
        # Close the connection
        server.quit()
        
        print(f"Email sent successfully for task: {task}")
        return True
    
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Check for tasks that are due
def check_for_due_tasks():
    try:
        # Get current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Connect to database
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        
        # Find pending tasks that are due now or overdue
        cursor.execute("""
            SELECT id, task, datetime, priority, category, recurrence 
            FROM reminders 
            WHERE status = 'Pending' AND datetime <= ?
        """, (current_time,))
        
        # Get all the due tasks
        due_tasks = cursor.fetchall()
        
        # For each due task
        for task in due_tasks:
            task_id, task_name, task_time, priority, category, recurrence = task
            
            # Send an email notification
            email_sent = send_notification_email(task_name, task_time, priority, category)
            
            # If email was sent successfully
            if email_sent:
                # If this is a one-time task
                if recurrence == "None":
                    # Mark it as completed
                    cursor.execute("UPDATE reminders SET status = 'Completed' WHERE id = ?", (task_id,))
                else:
                    # For recurring tasks, calculate the next occurrence
                    task_datetime = datetime.strptime(task_time, "%Y-%m-%d %H:%M")
                    
                    # Calculate new date based on recurrence type
                    if recurrence == "Daily":
                        new_datetime = task_datetime + timedelta(days=1)
                    elif recurrence == "Weekly":
                        new_datetime = task_datetime + timedelta(weeks=1)
                    else:
                        new_datetime = task_datetime + timedelta(days=1)
                    
                    # Update the task with the new date
                    new_time_str = new_datetime.strftime('%Y-%m-%d %H:%M')
                    cursor.execute("""
                        UPDATE reminders 
                        SET datetime = ? 
                        WHERE id = ?
                    """, (new_time_str, task_id))
        
        # Save changes and close connection
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error checking due tasks: {e}")

# Function that runs in the background to check for due tasks
def background_checker():
    print("Task checker started in background")
    
    while True:
        try:
            # Check for due tasks
            check_for_due_tasks()
        except Exception as e:
            print(f"Error in background checker: {e}")
        
        # Wait for 1 minute before checking again
        time.sleep(60)

# --------- STREAMLIT UI ---------
# Set up the database
setup_database()

# Start the background checker in a separate thread
checker_thread = threading.Thread(target=background_checker, daemon=True)
checker_thread.start()

# Create the main title
st.title("Schedulr: The Smart Reminder Assistant")

# Create the sidebar for adding new reminders
st.sidebar.header("Add a New Reminder")

# Input fields for the new reminder
task = st.sidebar.text_input("Task")
date = st.sidebar.date_input("Date")
time = st.sidebar.time_input("Time")
priority = st.sidebar.selectbox("Priority", ["High", "Medium", "Low"])
category = st.sidebar.selectbox("Category", ["Work", "Personal", "Study"])
recurrence = st.sidebar.selectbox("Recurrence", ["None", "Daily", "Weekly"])

# Add button to save the reminder
if st.sidebar.button("Add Reminder"):
    if task:  # Make sure task is not empty
        # Save the reminder
        save_reminder(
            task, 
            date.strftime('%Y-%m-%d'), 
            time.strftime('%H:%M'), 
            priority, 
            category, 
            recurrence
        )
        st.sidebar.success("Reminder Added Successfully!")
    else:
        st.sidebar.error("Please enter a task description")

# Create tabs for the main content
tab1, tab2 = st.tabs(["Your Reminders", "Manage Tasks"])

# Tab 1: View all reminders
with tab1:
    st.subheader("Your Reminders")
    
    # Refresh button
    if st.button("Refresh Reminders"):
        st.success("Reminders refreshed!")
    
    # Get all reminders
    reminders_df = get_all_reminders()
    
    # Display reminders if there are any
    if not reminders_df.empty:
        # Try to sort by priority, but don't crash if it fails
        try:
            priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
            reminders_df['PriorityOrder'] = reminders_df['Priority'].map(priority_order)
            reminders_df = reminders_df.sort_values(['PriorityOrder', 'Datetime'])
            reminders_df = reminders_df.drop('PriorityOrder', axis=1)
        except Exception as e:
            print(f"Error sorting reminders: {e}")
        
        # Display the dataframe
        st.dataframe(reminders_df)
    else:
        # No reminders found
        st.info("No reminders found. Add a reminder using the sidebar.")

# Tab 2: Manage tasks
with tab2:
    st.subheader("Manage Your Tasks")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    # Column 1: Mark as completed
    with col1:
        st.write("Mark Task as Completed")
        reminder_id = st.number_input("Enter Reminder ID", min_value=1, step=1)
        if st.button("Mark as Completed"):
            complete_reminder(reminder_id)
            st.success("Task Marked as Completed!")
    
    # Column 2: Delete task
    with col2:
        st.write("Delete Task")
        delete_id = st.number_input("Enter Reminder ID to Delete", min_value=1, step=1, key="delete")
        if st.button("Delete Reminder"):
            delete_reminder(delete_id)
            st.success("Reminder Deleted Successfully!")

# Display current time and info in the sidebar
st.sidebar.markdown("---")
st.sidebar.write(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.info("The system checks for due tasks every minute and sends email notifications automatically.")
