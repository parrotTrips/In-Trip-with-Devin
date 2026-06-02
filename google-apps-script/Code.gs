// Parrot Trips — Admin Menu for Google Sheets
// Paste this entire file into Extensions → Apps Script in the spreadsheet.

var BACKEND_URL = "https://parrot-trips-backend-428743191336.southamerica-east1.run.app";

// Creates the menu automatically when the spreadsheet opens.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🦜 Parrot Trips")
    .addItem("Import Trip Content → Supabase", "importTrip")
    .addSeparator()
    .addItem("Reset Trip Content (apaga fases e atividades)", "resetContent")
    .addItem("Reset Traveler Progress (zera barra de progresso)", "resetProgress")
    .addToUi();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getTripList() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Viagens");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Aba 'Viagens' não encontrada na planilha.");
    return null;
  }
  var data = sheet.getDataRange().getValues();
  var trips = [];
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    if (row[0]) {
      trips.push({ uuid: String(row[0]), name: String(row[1] || row[0]), date: String(row[2] || "") });
    }
  }
  return trips;
}

function callBackend(endpoint, trip_uuid) {
  var url = BACKEND_URL + endpoint;
  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ trip_uuid: trip_uuid }),
    muteHttpExceptions: true,
  };
  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();
  var body = response.getContentText();
  if (code >= 200 && code < 300) {
    return JSON.parse(body);
  } else {
    throw new Error("Backend error " + code + ": " + body);
  }
}

function showResult(result) {
  var msg = "✅ Done!\n\n";
  for (var key in result) {
    if (key !== "status") msg += key + ": " + result[key] + "\n";
  }
  SpreadsheetApp.getUi().alert(msg);
}

function promptForTrip(title) {
  var ui = SpreadsheetApp.getUi();
  var trips = getTripList();
  if (!trips || trips.length === 0) {
    ui.alert("No trips found in the 'Viagens' tab.");
    return null;
  }
  var list = trips.map(function(t, i) {
    return (i + 1) + ". " + t.name + " (" + t.date + ")\n   → " + t.uuid;
  }).join("\n\n");
  var response = ui.prompt(title, "Enter the trip_uuid:\n\n" + list, ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() !== ui.Button.OK) return null;
  return response.getResponseText().trim() || null;
}

// ── Menu actions ──────────────────────────────────────────────────────────────

function importTrip() {
  var trip_uuid = promptForTrip("🦜 Import Trip Content → Supabase");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function resetContent() {
  var ui = SpreadsheetApp.getUi();
  var confirm = ui.alert(
    "⚠️ Reset Trip Content",
    "This will DELETE all phases, activities and checklist items from the database for the chosen trip. Continue?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;
  var trip_uuid = promptForTrip("🦜 Reset Trip Content — choose trip");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/reset-content", trip_uuid));
  } catch (e) {
    ui.alert("❌ Error: " + e.message);
  }
}

function resetProgress() {
  var ui = SpreadsheetApp.getUi();
  var confirm = ui.alert(
    "⚠️ Reset Traveler Progress",
    "This will RESET the progress bar of all travelers for the chosen trip. Continue?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;
  var trip_uuid = promptForTrip("🦜 Reset Traveler Progress — choose trip");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/reset-progress", trip_uuid));
  } catch (e) {
    ui.alert("❌ Error: " + e.message);
  }
}
