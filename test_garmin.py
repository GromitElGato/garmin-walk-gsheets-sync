import os
from garminconnect import Garmin

garmin_email = os.environ.get("GARMIN_EMAIL")
garmin_password = os.environ.get("GARMIN_PASSWORD")

if not garmin_email or not garmin_password:
    print("❌ Garmin logingegevens ontbreken.")
    exit(1)

print("Verbinden met Garmin Connect...")

try:
    garmin = Garmin(garmin_email, garmin_password)
    garmin.login()
    print("✅ Verbonden met Garmin Connect")

    activities = garmin.get_activities(0, 5)

    print(f"\nLaatste {len(activities)} activiteiten:\n")

    for activity in activities:
        print(
            activity.get("activityId"),
            "|",
            activity.get("startTimeLocal"),
            "|",
            activity.get("activityName"),
            "|",
            activity.get("distance"),
            "meter"
        )

except Exception as e:
    print("❌ Fout:", e)
    exit(1)
