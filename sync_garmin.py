import os
import requests
from datetime import datetime

from garminconnect import Garmin


def main():
    print("=== Garmin wandelingen synchroniseren ===")

    garmin_email = os.environ.get("GARMIN_EMAIL")
    garmin_password = os.environ.get("GARMIN_PASSWORD")
    apps_script_url = os.environ.get("APPS_SCRIPT_URL")

    if not garmin_email or not garmin_password or not apps_script_url:
        print("❌ Vereiste GitHub Secrets ontbreken.")
        print(f"GARMIN_EMAIL: {'✓' if garmin_email else '✗'}")
        print(f"GARMIN_PASSWORD: {'✓' if garmin_password else '✗'}")
        print(f"APPS_SCRIPT_URL: {'✓' if apps_script_url else '✗'}")
        return

    # Garmin
    print("Verbinden met Garmin Connect...")

    try:
        garmin = Garmin(garmin_email, garmin_password)
        garmin.login()
        print("✅ Verbonden met Garmin Connect")
    except Exception as e:
        print(f"❌ Garmin-login mislukt: {e}")
        return

    # Activiteiten ophalen
    print("Activiteiten ophalen...")

    try:
        activities = garmin.get_activities(0, 50)
        print(f"✓ {len(activities)} activiteiten opgehaald")
    except Exception as e:
        print(f"❌ Activiteiten ophalen mislukt: {e}")
        return

    # Alleen wandelactiviteiten
    walking_activities = []

    for activity in activities:
        activity_type = (
            activity.get("activityType", {})
            .get("typeKey", "")
            .lower()
        )

        if activity_type in [
            "walking",
            "hiking",
            "indoor_walking",
        ]:
            walking_activities.append(activity)

    print(f"✓ {len(walking_activities)} wandelactiviteiten gevonden")

    if not walking_activities:
        print("Geen wandelactiviteiten gevonden.")
        return

    # Oudste eerst
    walking_activities.reverse()

    new_entries = 0

    for activity in walking_activities:

        try:
            activity_id = activity.get("activityId")

            if not activity_id:
                print("⚠️ Activiteit zonder ID overgeslagen")
                continue

            activity_name = activity.get(
                "activityName",
                "Wandeling"
            )

            start_time = activity.get("startTimeLocal")

            if not start_time:
                print(
                    f"⚠️ Geen starttijd voor activiteit "
                    f"{activity_id}"
                )
                continue

            # Afstand in meters
            distance = float(
                activity.get("distance", 0) or 0
            )

            # Duur in seconden
            duration = float(
                activity.get("duration", 0) or 0
            )

            # Garmin-link
            link = (
                f"https://connect.garmin.com/modern/activity/"
                f"{activity_id}"
            )

            # Datum controleren
            try:
                datetime.strptime(
                    start_time,
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                datetime.fromisoformat(start_time)

            payload = {
                "sheet": "2026",
                "activity_id": str(activity_id),
                "activity_name": activity_name,
                "start_time": start_time,
                "distance": distance,
                "duration": duration,
                "link": link,
            }

            print(
                f"→ Versturen: {activity_name} | "
                f"{round(distance)} m | "
                f"{activity_id}"
            )

            response = requests.post(
                apps_script_url,
                json=payload,
                timeout=30
            )

            print(
                f"  HTTP-status: {response.status_code}"
            )

            try:
                result = response.json()
                print(f"  Antwoord: {result}")
            except Exception:
                print(
                    f"  Antwoord: {response.text}"
                )
                continue

            if result.get("success"):
                if result.get("added"):
                    print("  ✅ Nieuwe wandeling toegevoegd")
                    new_entries += 1
                else:
                    print("  ↪ Bestaat al")
            else:
                print(
                    f"  ❌ Apps Script fout: "
                    f"{result.get('error')}"
                )

        except Exception as e:
            print(
                f"❌ Fout bij verwerken activiteit: {e}"
            )

    print()
    print("======================================")
    print(
        f"🎉 {new_entries} nieuwe wandelingen "
        f"toegevoegd."
    )
    print("======================================")


if __name__ == "__main__":
    main()
