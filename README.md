# 🚗 Ontario Road Test Notifier

A free, automated GitHub Action bot that monitors Ontario DriveTest centres for available road test appointments (G and G2). When a new slot opens up that matches your criteria, it sends you an email notification instantly.

## Features

- **Automated Monitoring:** Runs every 2 hours via GitHub Actions (can be customized).
- **API-Based:** Fetches data directly from the hidden JSON API used by the website (much faster and more reliable than HTML scraping).
- **Custom Filters:** Only alerts you for the specific cities and license types (G or G2) you care about.
- **Spam-Free:** Uses a deduplication system (`notified_dates.json`) so you only get an email when a *new* appointment appears, not every time the bot runs.
- **Beautiful Email Alerts:** Sends an HTML-formatted email via EmailJS with a clean table of available dates.
- **Self-Updating:** Automatically commits the updated `notified_dates.json` file back to the repository so it never forgets what it has already emailed you about.

## How It Works

1. Every 2 hours, GitHub Actions spins up a virtual machine.
2. The Python script (`check_dates.py`) fetches the latest available dates from the DriveTest statistics JSON.
3. It filters the results based on your `MY_LOCATIONS` and `MY_LICENSE_TYPES`.
4. If a new appointment is found (one that hasn't been emailed before), it uses EmailJS to send you an alert.
5. The bot saves a record of the alert to `notified_dates.json` and commits it to the repository to prevent spamming you on the next run.

## Setup Guide

### Step 1: Fork this Repository
Click the **Fork** button at the top right of this page to create your own copy.

### Step 2: Create an EmailJS Account
You need a free [EmailJS](https://www.emailjs.com/) account to send emails.
1. Create an account and log in.
2. **Email Services:** Add a new service (e.g., Gmail) and copy your **Service ID**. *(You may need to reconnect your Gmail account if the token expires).*
3. **Email Templates:** Create a new template.
   - **Subject:** `🚗 Road Test Appointment Found!`
   - **Content (HTML):**
     ```html
     <h2>Road Test Appointment Available!</h2>
     <p>Hello {{user_name}},</p>
     <p>The bot found the following appointment(s) matching your criteria:</p>
     {{message}}
     <p>Log in to the DriveTest portal to book it before it's gone!</p>
     <p>Best regards,<br>{{from_name}}</p>
