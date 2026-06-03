// Parrot Trips — Admin Menu for Google Sheets
// Paste this entire file into Extensions → Apps Script in the spreadsheet.

var BACKEND_URL = "https://parrot-trips-backend-428743191336.southamerica-east1.run.app";

// Creates the menu automatically when the spreadsheet opens.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🦜 Parrot Trips")
    .addItem("🔄 Sync Trips from Supabase", "syncTrips")
    .addSeparator()
    .addItem("Import Trip Content → Supabase", "importTrip")
    .addSeparator()
    .addItem("🚀 Iniciar Viagem → In-Trip", "startTrip")
    .addItem("🔁 Reset Trip → Pre-Trip (testes)", "resetTrip")
    .addSeparator()
    .addItem("Reset Trip Content (apaga fases e atividades)", "resetContent")
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

function callBackend(endpoint, trip_uuid, customBody) {
  var url = BACKEND_URL + endpoint;
  var body = customBody ? customBody : { trip_uuid: trip_uuid };
  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(body),
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

function syncTrips() {
  var ui = SpreadsheetApp.getUi();
  try {
    var response = UrlFetchApp.fetch(BACKEND_URL + "/admin/trips", { muteHttpExceptions: true });
    var code = response.getResponseCode();
    if (code < 200 || code >= 300) {
      throw new Error("Backend error " + code + ": " + response.getContentText());
    }
    var data = JSON.parse(response.getContentText());
    var trips = data.trips;

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Viagens");
    if (!sheet) {
      sheet = ss.insertSheet("Viagens");
    }

    sheet.clearContents();
    var header = [["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim"]];
    var rows = trips.map(function(t) {
      return [t.trip_uuid, t.title, t.start_date, t.end_date];
    });
    sheet.getRange(1, 1, 1, 4).setValues(header);
    sheet.getRange(1, 1, 1, 4).setFontWeight("bold");
    if (rows.length > 0) {
      sheet.getRange(2, 1, rows.length, 4).setValues(rows);
    }

    ui.alert("✅ Synced " + trips.length + " active trip(s) to the Viagens tab.");
  } catch (e) {
    ui.alert("❌ Sync failed: " + e.message);
  }
}

function importTrip() {
  var trip_uuid = promptForTrip("🦜 Import Trip Content → Supabase");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function startTrip() {
  var ui = SpreadsheetApp.getUi();
  var confirm = ui.alert(
    "🚀 Iniciar Viagem → In-Trip",
    "This will:\n• Clear phase progress (barra zera)\n• Preserve checklist completions\n• Switch trip mode to IN-TRIP\n\nUse this on the real trip start day.\n\nContinue?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;
  var trip_uuid = promptForTrip("🦜 Iniciar Viagem — choose trip");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/start-trip", trip_uuid));
  } catch (e) {
    ui.alert("❌ Error: " + e.message);
  }
}

function resetTrip() {
  var ui = SpreadsheetApp.getUi();
  var confirm = ui.alert(
    "🔁 Reset Trip → Pre-Trip",
    "This will:\n• Clear ALL checklist completions\n• Clear ALL phase progress\n• Set trip mode back to PRE-TRIP\n\nThe trip returns to its launch state. Use for testing only.\n\nContinue?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;
  var trip_uuid = promptForTrip("🦜 Reset Trip → Pre-Trip — choose trip");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/reset-trip", trip_uuid));
  } catch (e) {
    ui.alert("❌ Error: " + e.message);
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
