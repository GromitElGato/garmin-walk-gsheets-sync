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

    print("✅ Verbonden met Garmin Connect\n")

    activities = garmin.get_activities(0, 1)

    if not activities:
        print("Geen activiteiten gevonden.")
        exit(0)

    activity = activities[0]

    activity_id = activity.get("activityId")
    start_time = activity.get("startTimeLocal")
    activity_name = activity.get("activityName")
    distance = activity.get("distance")
    duration = activity.get("duration")

    garmin_url = f"https://connect.garmin.com/modern/activity/{activity_id}"

    print("Laatste activiteit:")
    print("-------------------")
    print("ID:", activity_id)
    print("Datum/tijd:", start_time)
    print("Naam:", activity_name)
    print("Afstand:", distance, "meter")
    print("Duur:", duration, "seconden")
    print("Link:", garmin_url)

except Exception as e:
    print("❌ Fout:", e)
    exit(1)
