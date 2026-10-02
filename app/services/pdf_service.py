import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from app.models.booking import Booking


def generate_booking_receipt_pdf(booking: Booking, user_email: str, user_name: str) -> io.BytesIO:
    """
    Generate an official diagnostic booking receipt & invoice PDF in memory.
    Returns a BytesIO buffer containing the PDF document.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0d9488")  # Teal 600
    dark_text = colors.HexColor("#1e293b")      # Slate 800
    muted_text = colors.HexColor("#64748b")     # Slate 500

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
    )

    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=muted_text,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=dark_text,
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=dark_text,
    )

    cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=dark_text,
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>EVE HEALTHCARE</b><br/><font size='8' color='#64748b'>Diagnostics & Preventive Care</font>", title_style),
            Paragraph(
                f"<b>RECEIPT / INVOICE</b><br/>"
                f"<font size='8' color='#64748b'>Invoice No: INV-{booking.booking_reference[4:]}<br/>"
                f"Date: {datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p')}</font>",
                ParagraphStyle("RightHeader", parent=styles["Normal"], alignment=2, fontName="Helvetica", fontSize=9, textColor=dark_text),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)

    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=15))

    # 2. Patient & Centre Info in 2 Columns
    centre_name = "EVE Partner Centre"
    centre_loc = "Main Facility"
    test_name = "Diagnostic Test"
    test_desc = "Clinical Laboratory Test"

    if booking.centre_test:
        if booking.centre_test.centre:
            centre_name = booking.centre_test.centre.name
            centre_loc = f"{booking.centre_test.centre.address}, {booking.centre_test.centre.city}"
        if booking.centre_test.test:
            test_name = booking.centre_test.test.name
            test_desc = booking.centre_test.test.description or ""

    patient_info = f"""
    <b>PATIENT DETAILS:</b><br/>
    <b>Name:</b> {user_name}<br/>
    <b>Email:</b> {user_email}<br/>
    <b>Booking Ref:</b> <font color='#0d9488'><b>{booking.booking_reference}</b></font>
    """

    centre_info = f"""
    <b>CENTRE & APPOINTMENT:</b><br/>
    <b>Diagnostic Centre:</b> {centre_name}<br/>
    <b>Location:</b> {centre_loc}<br/>
    <b>Appointment:</b> <font color='#b45309'><b>{booking.appointment_datetime.strftime('%A, %d %B %Y at %I:%M %p')}</b></font>
    """

    info_data = [
        [
            Paragraph(patient_info, cell_style),
            Paragraph(centre_info, cell_style),
        ]
    ]
    info_table = Table(info_data, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # 3. Itemized Billing Table
    story.append(Paragraph("Billing Breakdown", section_heading))
    story.append(Spacer(1, 8))

    # Check for payment transaction
    txn_id = "N/A"
    pay_status = booking.status.value
    pay_method = "Pending"
    if booking.payments:
        last_payment = booking.payments[-1]
        txn_id = last_payment.transaction_id
        pay_status = last_payment.status.value
        pay_method = last_payment.payment_method

    bill_data = [
        [
            Paragraph("Item & Test Description", cell_bold),
            Paragraph("Type", cell_bold),
            Paragraph("Status", cell_bold),
            Paragraph("Amount (INR)", cell_bold),
        ],
        [
            Paragraph(f"<b>{test_name}</b><br/><font size='7' color='#64748b'>{test_desc}</font>", cell_style),
            Paragraph("Laboratory Test", cell_style),
            Paragraph(f"<font color='{'#16a34a' if booking.status.value == 'CONFIRMED' else '#ea580c'}'><b>{booking.status.value}</b></font>", cell_style),
            Paragraph(f"INR {booking.amount:,.2f}", cell_style),
        ],
        [
            Paragraph("<b>Total Amount Paid / Payable:</b>", cell_bold),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph(f"<b>INR {booking.amount:,.2f}</b>", cell_bold),
        ],
    ]

    bill_table = Table(bill_data, colWidths=[3.2 * inch, 1.3 * inch, 1.2 * inch, 1.3 * inch])
    bill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), dark_text),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e6fffa")),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 15))

    # 4. Payment Reference Box
    pay_summary = f"""
    <b>Payment Information:</b><br/>
    • <b>Status:</b> {pay_status} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Method:</b> {pay_method} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Txn ID:</b> {txn_id}
    """
    pay_table = Table([[Paragraph(pay_summary, cell_style)]], colWidths=[7.0 * inch])
    pay_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4" if pay_status == "SUCCESS" or booking.status.value == "CONFIRMED" else "#fffbeb")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac" if pay_status == "SUCCESS" or booking.status.value == "CONFIRMED" else "#fde68a")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(pay_table)
    story.append(Spacer(1, 15))

    # 5. Medical Preparation Guidelines
    instructions = """
    <b>Patient Preparation Guidelines:</b><br/>
    1. Fasting of 10-12 hours is recommended prior to sample collection for blood/lipid tests.<br/>
    2. Please arrive at least 15 minutes before your scheduled appointment time.<br/>
    3. Carry a valid government photo ID and this digital receipt upon arrival.<br/>
    4. Digital diagnostic test reports will be available within 24 to 48 hours.
    """
    instr_table = Table([[Paragraph(instructions, cell_style)]], colWidths=[7.0 * inch])
    instr_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5e5")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(instr_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # 6. Footer
    footer_text = """
    <font size='7' color='#94a3b8'>
    EVE Healthcare Technologies Pvt. Ltd. • ISO 9001:2015 & NABL Accredited Partner Network<br/>
    This is an electronically generated medical invoice and requires no physical signature.<br/>
    Support: support@evehealthcare.com | Emergency Helpline: +91 (800) 123-4567
    </font>
    """
    story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer
