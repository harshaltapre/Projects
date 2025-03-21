import streamlit as st
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

# Database Connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harshal@27",
        database="SmartScheduler"
    )

# Fetch tasks from DB
def fetch_tasks():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks ORDER BY assigned_time ASC")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

# Add new task
def add_task(task_name, description, assigned_time, priority):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task_name, task_description, assigned_time, priority, status) VALUES (%s, %s, %s, %s, %s)",
                   (task_name, description, assigned_time, priority, "Pending"))
    conn.commit()
    conn.close()

# Update task status
def update_task_status(task_id, status):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
    conn.commit()
    conn.close()

# Send Email Notification
def send_email(task_name, assigned_time):
    sender_email = "harshaltapre28@gmail.com"  
    sender_password = "pwjw iesz pxux cjad" 
    receiver_email = "harshaltapre27@yahoo.com" 
    
    subject = f"Reminder: Task '{task_name}' Due Soon!"
    body = f"Your task '{task_name}' is scheduled at {assigned_time}. Please complete it on time!\n\nYour SmartScheduler"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        # Connect to Gmail SMTP Server & Send Email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

        print(" Email sent successfully! ")
    except Exception as e:
        print(f" Failed to send email: {e}")

# Check and send notifications
def check_and_notify():
    tasks = fetch_tasks()
    now = datetime.now()

    for task in tasks:
        task_time = task["assigned_time"]
        if task_time <= now and task["status"] == "Pending":
            send_email(task["task_name"], task_time)
            update_task_status(task["id"], "Completed")

# Streamlit UI
st.title(" SmartScheduler - Task Manager")

# Form to add task
with st.form("task_form"):
    task_name = st.text_input("Task Name")
    description = st.text_area("Task Description")
    date = st.date_input("Select Date")
    time = st.time_input("Select Time")
    assigned_time = datetime.combine(date, time)  # Combine date & time
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    submit = st.form_submit_button("Add Task")

    if submit:
        add_task(task_name, description, assigned_time, priority)
        st.success("Task Added Successfully!")

# Display tasks
st.subheader(" Your Tasks")
tasks = fetch_tasks()

for task in tasks:
    st.write(f" **{task['task_name']}** ({task['priority']}) - {task['assigned_time']}")
    if st.button(f"Mark as Completed {task['id']}"):
        update_task_status(task["id"], "Completed")
        st.success("Task marked as completed!")

# Run Notification Check
if st.button("Check for Notifications"):
    check_and_notify()
    st.info("Checked for due tasks and sent notifications!")  

