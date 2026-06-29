from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "parrot_test_service_agreement.pdf"

GREEN = colors.HexColor("#087f38")
TEXT = colors.HexColor("#111111")
MUTED = colors.HexColor("#3f3f3f")


def draw_header(canvas, doc):
    width, height = letter
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.rect(0, height - 0.88 * inch, width, 0.88 * inch, stroke=0, fill=1)

    center_x = width / 2
    top_y = height - 0.17 * inch

    canvas.setStrokeColor(colors.white)
    canvas.setFillColor(colors.white)
    canvas.setLineWidth(1.2)

    # Minimal parrot mark inspired by the brand symbol. The HTML keeps the full SVG.
    canvas.circle(center_x - 4, top_y - 7, 2.2, stroke=0, fill=1)
    canvas.line(center_x - 4, top_y - 10, center_x - 1, top_y - 28)
    canvas.line(center_x - 1, top_y - 28, center_x + 8, top_y - 34)
    canvas.line(center_x - 1, top_y - 28, center_x - 12, top_y - 32)
    canvas.arc(center_x - 15, top_y - 36, center_x + 12, top_y - 15, 210, 105)

    canvas.setFont("Times-Roman", 17)
    canvas.drawCentredString(center_x, height - 0.60 * inch, "PARROT")
    canvas.drawCentredString(center_x, height - 0.78 * inch, "TRIPS")
    canvas.restoreState()


def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.75 * inch, 0.28 * inch, "Parrot Trips - Test Service Agreement")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.28 * inch, str(doc.page))
    canvas.restoreState()


def on_page(canvas, doc):
    draw_header(canvas, doc)
    draw_footer(canvas, doc)


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        name="TitleCenter",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=TEXT,
        spaceAfter=12,
    ))
    base.add(ParagraphStyle(
        name="Body",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=10.8,
        leading=14.2,
        textColor=TEXT,
        spaceAfter=8,
    ))
    base.add(ParagraphStyle(
        name="Muted",
        parent=base["Body"],
        textColor=MUTED,
        spaceAfter=10,
    ))
    base.add(ParagraphStyle(
        name="Label",
        parent=base["Body"],
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    ))
    base.add(ParagraphStyle(
        name="Value",
        parent=base["Body"],
        alignment=TA_CENTER,
    ))
    base.add(ParagraphStyle(
        name="Section",
        parent=base["Body"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=12,
        spaceAfter=5,
    ))
    return base


def p(text: str, style):
    return Paragraph(text, style)


def customer_details(style):
    data = [
        [
            p("<b>Name:</b> Marcelo Angelo", style["Body"]),
            p("<b>Email:</b> marcelo.test@example.com", style["Body"]),
        ],
        [
            p("<b>Date of Birth:</b> March 9, 1995", style["Body"]),
            p("<b>Phone Number:</b> +55 12 99129-6651", style["Body"]),
        ],
        [
            p("<b>Passport Number:</b> Brazil AB123456", style["Body"]),
            p("<b>Trip ID:</b> TEST-2026-FULL", style["Body"]),
        ],
    ]
    table = Table(data, colWidths=[2.85 * inch, 2.85 * inch], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def summary_table(style):
    rows = [
        ("Trip Name", "Parrot Brazil Test Trip"),
        ("Hired package and items", "Parrot Brazil Test Trip 2026 | Shared Room"),
        (
            "Starting and finishing dates:",
            "This trip will officially begin in Rio de Janeiro on July 1st, 2026, "
            "then move to Ilha Grande on July 4th and return to Rio on July 7th, 2026.",
        ),
        ("Accommodation:", "Shared room in selected partner hotels and guesthouses."),
        (
            "Booked hotels:",
            "Rio de Janeiro:<br/>Parrot Ipanema House - Rua das Palmeiras, 539 - Ipanema, Rio de Janeiro - RJ"
            "<br/><br/>Ilha Grande:<br/>Parrot Beach Lodge - Rua da Praia, 815 - Vila do Abraao, Angra dos Reis - RJ",
        ),
        ("Flights:", "No flights included."),
        (
            "Transportation:",
            "Ground transfers in Rio de Janeiro and boat transfer to Ilha Grande for scheduled group activities.",
        ),
        (
            "Base activities included:",
            "Welcome gathering in Rio de Janeiro<br/>Group transfer to Ilha Grande<br/>Guided beach day and local orientation<br/>Farewell dinner coordination",
        ),
    ]

    data = [[p(label, style["Label"]), p(value, style["Value"])] for label, value in rows]
    table = Table(data, colWidths=[2.45 * inch, 4.35 * inch], hAlign="CENTER", repeatRows=0)
    table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 2, GREEN),
        ("LINEBELOW", (0, 0), (-1, -1), 2, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def agreement_copy(style):
    sections = [
        (
            "General Terms",
            "The traveler understands that this document is a test agreement prepared for internal validation "
            "of the Parrot Trips application experience. All names, dates, accommodations, addresses, prices, "
            "and itinerary items in this document are fictional or generic.",
        ),
        (
            "Payment and Package",
            "The package described above includes only the items explicitly listed in this agreement. Optional "
            "activities, personal expenses, international flights, travel insurance, meals not listed, and "
            "independent transportation are not included unless separately confirmed in writing.",
        ),
        (
            "Traveler Responsibilities",
            "The traveler is responsible for valid travel documents, passport accuracy, visa requirements, "
            "health requirements, insurance decisions, and punctual arrival for scheduled group activities.",
        ),
        (
            "Changes and Operations",
            "Parrot Trips may adjust hotels, timings, transportation details, activity order, or meeting points "
            "when needed for safety, weather, supplier availability, or operational reasons.",
        ),
        (
            "Test Use Only",
            "This agreement is not intended for legal execution. It is a sample document created to test the "
            "Service Agreement link and traveler-facing PDF experience inside the Parrot Trips app.",
        ),
    ]

    flowables = []
    for title, body in sections:
        flowables.append(p(title, style["Section"]))
        flowables.append(p(body, style["Body"]))
    return flowables


def signature_table(style):
    data = [
        [p("Traveler Signature<br/>Marcelo Angelo", style["Body"]), p("Parrot Trips Representative<br/>Operations Team", style["Body"])]
    ]
    table = Table(data, colWidths=[3.0 * inch, 3.0 * inch], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1.5, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def build():
    style = styles()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.78 * inch,
        leftMargin=0.78 * inch,
        topMargin=1.38 * inch,
        bottomMargin=0.62 * inch,
        title="Parrot Trips Service Agreement - Test Trip",
        author="Parrot Trips",
    )

    story = [
        p("Service Agreement", style["TitleCenter"]),
        p("Customer details:", style["Muted"]),
        customer_details(style),
        Spacer(1, 6),
        p("Details of the itinerary and included items:", style["Body"]),
        summary_table(style),
        PageBreak(),
        p("Traveler Acknowledgement", style["TitleCenter"]),
    ]
    story.extend(agreement_copy(style))
    story.extend([Spacer(1, 34), signature_table(style)])

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
