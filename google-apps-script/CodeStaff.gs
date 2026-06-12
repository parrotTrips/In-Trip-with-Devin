// Parrot Trips — Staff Admin Menu for Google Sheets
// Paste this entire file into Extensions → Apps Script in the STAFF spreadsheet.

var BACKEND_URL = "https://parrot-trips-backend-428743191336.southamerica-east1.run.app";

// Creates the menu automatically when the spreadsheet opens.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🦜 Parrot Staff")
    .addItem("🔄 Sync Trips from Supabase", "syncTrips")
    .addSeparator()
    .addItem("Import Contacts → Supabase", "importContacts")
    .addSeparator()
    .addItem("👤 Set Staff Role (phone → staff)", "setStaffRole")
    .addItem("👤 Remove Staff Role (phone → traveler)", "removeStaffRole")
    .addSeparator()
    .addItem("🔧 Setup Sheet Headers (primeira vez)", "setupSheetHeaders")
    .addToUi();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getTripList() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Viagens");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Aba 'Viagens' não encontrada. Run 'Sync Trips' first.");
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

function callBackend(endpoint, customBody) {
  var url = BACKEND_URL + endpoint;
  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(customBody),
    muteHttpExceptions: true,
  };
  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();
  var text = response.getContentText();
  if (code >= 200 && code < 300) {
    return JSON.parse(text);
  } else {
    throw new Error("Backend error " + code + ": " + text);
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
    ui.alert("No trips found. Run 'Sync Trips' first.");
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
    if (!sheet) sheet = ss.insertSheet("Viagens");

    sheet.clearContents();
    var header = [["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim"]];
    var rows = trips.map(function(t) {
      return [t.trip_uuid, t.title, t.start_date, t.end_date];
    });
    sheet.getRange(1, 1, 1, 4).setValues(header);
    sheet.getRange(1, 1, 1, 4).setFontWeight("bold");
    if (rows.length > 0) sheet.getRange(2, 1, rows.length, 4).setValues(rows);

    ui.alert("✅ Synced " + trips.length + " active trip(s) to the Viagens tab.");
  } catch (e) {
    ui.alert("❌ Sync failed: " + e.message);
  }
}

function importContacts() {
  var trip_uuid = promptForTrip("🦜 Import Contacts → Supabase");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import-contacts", { trip_uuid: trip_uuid }));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function setStaffRole() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.prompt(
    "👤 Set Staff Role",
    "Enter the WhatsApp phone number with country code:\nExample: +5511999999999",
    ui.ButtonSet.OK_CANCEL
  );
  if (response.getSelectedButton() !== ui.Button.OK) return;
  var phone = response.getResponseText().trim();
  if (!phone) { ui.alert("No phone entered."); return; }

  try {
    var result = callBackend("/admin/users/set-role", { phone: phone, role: "staff" });
    ui.alert("✅ Done!\n\n" + result.name + " (" + result.phone + ") is now role=staff.");
  } catch (e) {
    ui.alert("❌ Error: " + e.message);
  }
}

function removeStaffRole() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.prompt(
    "👤 Remove Staff Role → traveler",
    "Enter the WhatsApp phone number with country code:\nExample: +5511999999999",
    ui.ButtonSet.OK_CANCEL
  );
  if (response.getSelectedButton() !== ui.Button.OK) return;
  var phone = response.getResponseText().trim();
  if (!phone) { ui.alert("No phone entered."); return; }

  try {
    var result = callBackend("/admin/users/set-role", { phone: phone, role: "traveler" });
    ui.alert("✅ Done!\n\n" + result.name + " (" + result.phone + ") is now role=traveler.");
  } catch (e) {
    ui.alert("❌ Error: " + e.message);
  }
}

function setupSheetHeaders() {
  var ui = SpreadsheetApp.getUi();
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var TABS = [
    {
      name: "Viagens",
      headers: ["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim"],
      note: "Populado automaticamente pelo Sync Trips"
    },
    {
      name: "Contatos",
      headers: ["trip_uuid", "category", "name", "role", "phone", "sort_order"],
      note: "category → ex: 'Local guides', 'Accommodation', 'Emergency' | sort_order → ordem dentro da categoria"
    },
    {
      name: "Staff",
      headers: ["phone", "nome", "funcao", "trip_uuid"],
      note: "Registro dos membros de staff por viagem (referência — use o menu para gerenciar roles no Supabase)"
    }
  ];

  var created = [], updated = [], skipped = [];

  TABS.forEach(function(tab) {
    var sheet = ss.getSheetByName(tab.name);
    if (!sheet) {
      sheet = ss.insertSheet(tab.name);
      var range = sheet.getRange(1, 1, 1, tab.headers.length);
      range.setValues([tab.headers]);
      range.setFontWeight("bold");
      range.setBackground("#d9ead3");
      if (tab.note) {
        sheet.getRange(2, 1).setValue("← " + tab.note);
        sheet.getRange(2, 1).setFontColor("#888888").setFontStyle("italic");
      }
      created.push(tab.name);
    } else {
      var existingHeader = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0]
        .map(function(h) { return String(h).trim().toLowerCase(); });
      var missing = tab.headers.filter(function(h) {
        return existingHeader.indexOf(h.toLowerCase()) < 0;
      });
      if (missing.length > 0) {
        var nextCol = sheet.getLastColumn() + 1;
        missing.forEach(function(h, i) {
          var cell = sheet.getRange(1, nextCol + i);
          cell.setValue(h);
          cell.setFontWeight("bold");
          cell.setBackground("#fff2cc");
        });
        updated.push(tab.name + " (added: " + missing.join(", ") + ")");
      } else {
        skipped.push(tab.name);
      }
    }
  });

  var msg = "";
  if (created.length) msg += "✅ Created: " + created.join(", ") + "\n";
  if (updated.length) msg += "🟡 Updated: " + updated.join(", ") + "\n";
  if (skipped.length) msg += "⬜ Already OK: " + skipped.join(", ") + "\n";
  msg += "\nFill in the Contatos tab and run 'Import Contacts → Supabase'.";

  ui.alert("🔧 Sheet Setup Complete", msg, ui.ButtonSet.OK);
}
