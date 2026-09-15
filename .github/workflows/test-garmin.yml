name: Garmin synchronisatie

on:
  workflow_dispatch:

  schedule:
    - cron: "0 6 * * *"

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install garminconnect requests

      - name: Sync Garmin walks to Google Sheets
        env:
          GARMIN_EMAIL: ${{ secrets.GARMIN_EMAIL }}
          GARMIN_PASSWORD: ${{ secrets.GARMIN_PASSWORD }}
          APPS_SCRIPT_URL: ${{ secrets.APPS_SCRIPT_URL }}
          GARMIN_SYNC_TOKEN: ${{ secrets.GARMIN_SYNC_TOKEN }}
        run: |
          python sync_garmin.py
