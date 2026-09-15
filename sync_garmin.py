import os
import sys
import requests
from datetime import datetime

from garminconnect import Garmin


def main():
    print("=== Garmin wandelingen synchroniseren ===")

    garmin_email = os.environ.get("GARMIN_EMAIL")
    garmin_password = os.environ.get("GARMIN_PASSWORD")
    apps_script_url = os.environ.get("APPS_SCRIPT_URL")
    sync_token = os.environ.get("GARMIN_SYNC_TOKEN")

    # ======================================
    # GitHub Secrets controleren
    # ======================================

    if (
        not garmin_email
        or not garmin_password
        or not apps_script_url
        or not sync_token
    ):
        print("❌ Vereiste GitHub Secrets ontbreken.")
        print(f"GARMIN_EMAIL: {'✓' if garmin_email else '✗'}")
        print(f"GARMIN_PASSWORD: {'✓' if garmin_password else '✗'}")
        print(f"APPS_SCRIPT_URL: {'✓' if apps_script_url else '✗'}")
        print(f"GARMIN_SYNC_TOKEN: {'✓' if sync_token else '✗'}")
        sys.exit(1)

    # ======================================
    # Verbinden met Garmin
    # ======================================

    print("Verbinden met Garmin Connect...")

    try:
        garmin = Garmin(garmin_email, garmin_password)
        garmin.login()
        print("✅ Verbonden met Garmin Connect")

    except Exception as e:
        print(f"❌ Garmin-login mislukt: {e}")
        sys.exit(1)

    # ======================================
    # Activiteiten ophalen
    # ======================================

    print("Activiteiten ophalen...")

    try:
        activities = garmin.get_activities(0, 50)
        print(f"✓ {len(activities)} activiteiten opgehaald")

    except Exception as e:
        print(f"❌ Activiteiten ophalen mislukt: {e}")
        sys.exit(1)

    # ======================================
    # Alleen wandelactiviteiten
    # ======================================

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

    print(
        f"✓ {len(walking_activities)} "
        f"wandelactiviteiten gevonden"
    )

    if not walking_activities:
        print("Geen wandelactiviteiten gevonden.")
        sys.exit(0)

    # ======================================
    # Oudste eerst
    # ======================================

    walking_activities.reverse()

    new_entries = 0
    failed_entries = 0

    # ======================================
    # Activiteiten verwerken
    # ======================================

    for activity in walking_activities:

        try:
            activity_id = activity.get("activityId")

            if not activity_id:
                print("⚠️ Activiteit zonder ID overgeslagen")
                failed_entries += 1
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
                failed_entries += 1
                continue

            distance = float(
                activity.get("distance", 0) or 0
            )

            duration = float(
                activity.get("duration", 0) or 0
            )

            link = (
                "https://connect.garmin.com/modern/activity/"
                f"{activity_id}"
            )

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
                "token": sync_token,
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

            if response.status_code != 200:
                print(
                    f"  ❌ HTTP-fout: "
                    f"{response.status_code}"
                )
                print(
                    f"  Antwoord: {response.text}"
                )
                failed_entries += 1
                continue

            try:
                result = response.json()
                print(f"  Antwoord: {result}")

            except Exception:
                print(
                    f"  ❌ Ongeldig antwoord van Apps Script: "
                    f"{response.text}"
                )
                failed_entries += 1
                continue

            if result.get("success"):

                if result.get("added"):
                    print(
                        "  ✅ Nieuwe wandeling toegevoegd"
                    )
                    new_entries += 1

                else:
                    print(
                        "  ↪ Bestaat al"
                    )

            else:
                print(
                    f"  ❌ Apps Script fout: "
                    f"{result.get('error')}"
                )
                failed_entries += 1

        except Exception as e:

            print(
                f"❌ Fout bij verwerken activiteit: {e}"
            )

            failed_entries += 1

    # ======================================
    # Eindresultaat
    # ======================================

    print()
    print("======================================")
    print(
        f"Nieuwe wandelingen toegevoegd: "
        f"{new_entries}"
    )
    print(
        f"Mislukte activiteiten: "
        f"{failed_entries}"
    )
    print("======================================")

    if failed_entries > 0:
        print(
            "❌ Synchronisatie voltooid met fouten."
        )
        sys.exit(1)

    print(
        "🎉 Synchronisatie succesvol voltooid."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
