# Parrot Trips — Google Apps Script

Admin menu for the Google Sheets spreadsheet. Allows importing content and resetting Supabase data directly from the spreadsheet.

## How to install

1. Open the [Parrot Trips spreadsheet](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP)
2. Click **Extensions → Apps Script**
3. Delete all existing content in the editor
4. Paste the contents of `Code.gs`
5. Save (Ctrl+S)
6. Close the editor and reload the spreadsheet
7. The **🦜 Parrot Trips** menu will appear in the top bar

## Menu actions

| Menu item | What it does |
|---|---|
| **Import Trip Content → Supabase** | Reads Fases/Checklist/Links/Roteiro tabs and imports to the database |
| **Reset Trip Content** | Deletes all phases, activities and checklist items for a trip |
| **Reset Traveler Progress** | Resets progress bar for all travelers (~1 week before departure) |

## How to use

1. Click **🦜 Parrot Trips** → choose an action
2. A dialog opens with a list of available trips (read from the `Viagens` tab)
3. Type the `trip_uuid` of the desired trip
4. Confirm — the result appears in an alert dialog
