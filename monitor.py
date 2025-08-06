import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
from email.mime.text import MIMEText

COURSES_PAGE_URL = "https://www.vgregion.se/f/regionhalsan/Barnmorskemottagninginbjudningar/forlossningsforberedandeprofylaxkurs/kursgoteborg/"
CHECK_INTERVAL = 3600  # Check every hour

# Telegram settings
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Baseline date
BASELINE_DATE = date(2025, 9, 11)  # Only notify after this date

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def get_new_courses():
    """Return list of courses with dates after baseline."""
    response = requests.get(COURSES_PAGE_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all("li", class_="list-block__result-item")

    new_courses = []
    for item in items:
        time_tag = item.find("time")
        if not time_tag or not time_tag.has_attr("datetime"):
            continue

        # Parse date from datetime attribute
        course_date = datetime.strptime(time_tag["datetime"], "%Y-%m-%d").date()

        if course_date > BASELINE_DATE:
            link_tag = item.find("a")
            title = link_tag.get_text(strip=True) if link_tag else "Profylaxkurs"
            url = link_tag["href"] if link_tag and link_tag.has_attr("href") else COURSES_PAGE_URL
            new_courses.append((course_date, title, url))

    return new_courses

def monitor_by_time_with_telegram():
    global BASELINE_DATE
    print("Starting monitor by date... Baseline date: ", BASELINE_DATE)

    try:
        new_courses = get_new_courses()

        if new_courses:
            for course_date, title, url in new_courses:
                msg = (
                    f"⚠️ <b>New Profylaxkurs Available!</b>\n\n"
                    f"📅 <b>Date:</b> {course_date.strftime('%A, %d %B %Y')}\n"
                    f"📍 <b>Location:</b> {title}\n\n"
                    f"🔗 <a href='{url}'>View Course Details</a>\n\n"
                    f"➡️ <a href='{COURSES_PAGE_URL}'>See All Courses</a>"
                )

                print(msg)
                send_telegram_message(msg)

            # Update baseline to last found date
            last_date = max(c[0] for c in new_courses)
            BASELINE_DATE = last_date

        else:
            print("No new courses after baseline.")
    except Exception as e:
        print(f"Error during monitoring: {e}")

    time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_by_time_with_telegram()
