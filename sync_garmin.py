import os
import json
from datetime import datetime

from garminconnect import Garmin
from google.oauth2.service_account import Credentials
import gspread


SHEET_NAME = "2026"


def main():
    print("=== Garmin wandelingen synchroniseren ===")

    # Credentials
    garmin_email = os.environ.get("GARMIN_EMAIL")
    garmin_password = os.environ.get("GARMIN_PASSWORD")
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    sheet_id = os.environ.get("SHEET_ID")

    if not all([garmin_email, garmin_password, google_creds_json, sheet_id]):
        print("❌ Vereiste GitHub Secrets ontbreken.")
        print(f"GARMIN_EMAIL: {'✓' if garmin_email else '✗'}")
        print(f"GARMIN_PASSWORD: {'✓' if garmin_password else '✗'}")
        print(f"GOOGLE_CREDENTIALS: {'✓' if google_creds_json else '✗'}")
        print(f"SHEET_ID: {'✓' if sheet_id else '✗'}")
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

    # Google Sheets
    print("Verbinden met Google Sheets...")

    try:
        creds_dict = json.loads(google_creds_json)

        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )

        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.worksheet(SHEET_NAME)

        print(f"✅ Verbonden met tabblad '{SHEET_NAME}'")

    except Exception as e:
        print(f"❌ Google Sheets verbinding mislukt: {e}")
        return

    # Bestaande links ophalen
    try:
        existing_data = sheet.get_all_values()

        existing_links = set()

        for row in existing_data[1:]:
            if len(row) >= 5 and row[4]:
                existing_links.add(row[4].strip())

        print(f"✓ {len(existing_links)} bestaande links gevonden")

    except Exception as e:
        print(f"❌ Bestaande gegevens konden niet worden gelezen: {e}")
        return

    # Wandelingen verwerken
    new_entries = 0

    for activity in reversed(walking_activities):

        try:
            activity_id = activity.get("activityId")

            if not activity_id:
                print("⚠️ Activiteit zonder ID overgeslagen")
                continue

            garmin_link = (
                f"https://connect.garmin.com/modern/activity/{activity_id}"
            )

            # Dubbele activiteit vermijden
            if garmin_link in existing_links:
                print(f"↪ Bestaat al: {garmin_link}")
                continue

            # Datum en tijd
            start_time = activity.get("startTimeLocal")

            if not start_time:
                print(f"⚠️ Geen starttijd voor activiteit {activity_id}")
                continue

            try:
                activity_datetime = datetime.strptime(
                    start_time,
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                activity_datetime = datetime.fromisoformat(start_time)

            # Afstand in meters
            distance_meters = round(
                activity.get("distance", 0) or 0
            )

            # Duur
            duration_seconds = round(
                activity.get("duration", 0) or 0
            )

            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60

            duration = f"{hours}:{minutes:02d}:{seconds:02d}"

            # Naam
            activity_name = activity.get(
                "activityName",
                "Wandeling"
            )

            # Kolommen A t/m E
            row = [
                activity_datetime.strftime("%-d-%-m-%Y %H:%M:%S"),
                activity_name,
                distance_meters,
                duration,
                garmin_link,
            ]

            # Rij toevoegen
            sheet.append_row(
                row,
                value_input_option="USER_ENTERED"
            )

            print(
                f"✅ Toegevoegd: {activity_datetime} | "
                f"{activity_name} | "
                f"{distance_meters} m | "
                f"{duration}"
            )

            existing_links.add(garmin_link)
            new_entries += 1

        except Exception as e:
            print(f"❌ Fout bij verwerken activiteit: {e}")

    print()
    print("======================================")

    if new_entries:
        print(
            f"🎉 {new_entries} nieuwe wandelingen toegevoegd."
        )
    else:
        print("✓ Geen nieuwe wandelingen gevonden.")

    print("======================================")


if __name__ == "__main__":
    main()
