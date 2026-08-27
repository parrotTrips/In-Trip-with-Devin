// Parrot Trips — Admin Menu for Google Sheets
// Paste this entire file into Extensions → Apps Script in the spreadsheet.

var BACKEND_URL = "https://parrot-trips-backend-428743191336.southamerica-east1.run.app";

// Creates the menu automatically when the spreadsheet opens.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🦜 Parrot Trips")
    .addItem("⬇️ Import Trips from App", "syncTrips")
    .addSeparator()
    .addItem("🚀 Export Trip Content to App", "importTrip")
    .addItem("🆘 Export Emergency Contacts to App", "importEmergencyContacts")
    .addItem("📍 Export Recommendations to App", "importRecommendations")
    .addItem("❓ Export FAQ to App", "importFaq")
    .addItem("📄 Export Cancellation Policy to App", "importCancellationPolicy")
    .addSeparator()
    .addItem("💬 Import Feedbacks from App", "importFeedbacks")
    .addSeparator()
    .addItem("▶️ Start Trip", "startTrip")
    .addItem("🔁 Reset Trip to Pre-Trip", "resetTrip")
    .addSeparator()
    .addItem("🗑️ Clear Trip Content", "resetContent")
    .addSeparator()
    .addItem("🔧 Setup Sheet Headers", "setupSheetHeaders")
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

    // Preserve existing service_agreement_url values before clearing
    var existingAgreements = {};
    var existingData = sheet.getDataRange().getValues();
    if (existingData.length > 1) {
      var existingHeader = existingData[0].map(function(h) { return String(h).trim().toLowerCase(); });
      var uuidCol = existingHeader.indexOf("trip_uuid");
      var agreementCol = existingHeader.indexOf("service_agreement_url");
      if (uuidCol >= 0 && agreementCol >= 0) {
        for (var i = 1; i < existingData.length; i++) {
          var row = existingData[i];
          if (row[uuidCol] && row[agreementCol]) {
            existingAgreements[String(row[uuidCol]).trim()] = String(row[agreementCol]).trim();
          }
        }
      }
    }

    sheet.clearContents();
    var header = [["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim", "service_agreement_url"]];
    var rows = trips.map(function(t) {
      return [t.trip_uuid, t.title, t.start_date, t.end_date, existingAgreements[t.trip_uuid] || ""];
    });
    sheet.getRange(1, 1, 1, 5).setValues(header);
    sheet.getRange(1, 1, 1, 5).setFontWeight("bold");
    if (rows.length > 0) {
      sheet.getRange(2, 1, rows.length, 5).setValues(rows);
    }

    ui.alert("✅ Imported " + trips.length + " active trip(s) from the App to the Viagens tab.");
  } catch (e) {
    ui.alert("❌ Import from App failed: " + e.message);
  }
}

function importTrip() {
  var trip_uuid = promptForTrip("🦜 Export Trip Content to App");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function importEmergencyContacts() {
  var trip_uuid = promptForTrip("🆘 Export Emergency Contacts to App");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import-emergency-contacts", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function importRecommendations() {
  var trip_uuid = promptForTrip("📍 Export Recommendations to App");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import-recommendations", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function importFaq() {
  var trip_uuid = promptForTrip("❓ Export FAQ to App");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import-faq", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function importCancellationPolicy() {
  var trip_uuid = promptForTrip("📄 Export Cancellation Policy to App");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/import-cancellation-policy", trip_uuid));
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Error: " + e.message);
  }
}

function importFeedbacks() {
  var trip_uuid = promptForTrip("💬 Import Feedbacks from App");
  if (!trip_uuid) return;
  try {
    showResult(callBackend("/admin/trips/sync-feedback-to-sheet", trip_uuid));
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

function setupSheetHeaders() {
  var ui = SpreadsheetApp.getUi();
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var TABS = [
    {
      name: "Viagens",
      headers: ["trip_uuid", "nome_da_viagem", "data_inicio", "data_fim", "service_agreement_url"],
      note: "service_agreement_url → URL do PDF do contrato para cada viagem"
    },
    {
      name: "Fases",
      headers: ["trip_uuid", "ordem", "fase", "titulo", "subtitulo", "icone", "descricao_curta", "descricao_completa", "ideal_pace"],
      note: "ideal_pace → marque 'x' na fase que os viajantes deveriam estar neste momento"
    },
    {
      name: "Checklist",
      headers: ["trip_uuid", "fase", "ordem", "label", "obrigatorio"],
      note: "obrigatorio → 'sim' ou 'não'"
    },
    {
      name: "Links",
      headers: ["trip_uuid", "fase", "ordem", "label", "url"],
      note: ""
    },
    {
      name: "Roteiro",
      headers: ["trip_uuid", "dia", "data", "dia_titulo", "dia_subtitulo", "dia_icon", "dia_descricao_curta", "dia_descricao_completa", "atividade_nome", "atividade_tipo", "atividade_horario", "atividade_duracao_min", "atividade_descricao_curta", "atividade_info_pratica", "atividade_preco_brl", "atividade_endereco", "atividade_max_scans"],
      note: ""
    },
    {
      name: "Emergency Contacts",
      headers: ["trip_uuid", "name", "role", "phone", "sort_order"],
      note: "Emergency contacts shown to travelers — police, SAMU, hotel, hospital, etc."
    },
    {
      name: "Recomendacoes",
      headers: ["trip_uuid", "name", "description", "address", "photo_url", "sort_order", "category", "neighborhood", "location", "highlight", "price_range", "rating", "map_url", "emoji"],
      note: "Local recommendations. category examples: restaurants, bars, cafes, beaches, wellness, shopping. location examples: rio, ilha-grande. rating is optional."
    },
    {
      name: "Feedbacks",
      headers: ["feedback_id", "trip_uuid", "traveler_name", "phone", "feedback", "created_at"],
      note: "Read-only operational view. Use Import Feedbacks from App to refresh this tab."
    },
    {
      name: "FAQ",
      headers: ["trip_uuid", "question", "answer", "sort_order"],
      note: "Frequently asked questions shown to travelers in the Information section."
    },
    {
      name: "Cancellation Policy",
      headers: ["trip_uuid", "title", "body", "sort_order"],
      note: "Cancellation policy sections. Each row is one policy block with a title and body text."
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
      // Check if ideal_pace column is missing from Fases
      var existingHeader = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0]
        .map(function(h) { return String(h).trim().toLowerCase(); });
      var missing = tab.headers.filter(function(h) {
        return existingHeader.indexOf(h.toLowerCase()) < 0;
      });
      if (missing.length > 0) {
        // Append missing headers at the end
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
  msg += "\nNow you can fill in the content and run Export Trip Content to App.";

  ui.alert("🔧 Sheet Setup Complete", msg, ui.ButtonSet.OK);
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
