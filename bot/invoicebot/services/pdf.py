from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from invoicebot.models import Client, InvoiceDraft, Profile
from invoicebot.services.template_catalog import get_template


def render_invoice_pdf(profile: Profile, draft: InvoiceDraft, client: Client | None) -> bytes:
    template = get_template(profile.default_template_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFillColor(colors.HexColor(template.accent))
    pdf.rect(0, height - 120, width, 120, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(40, height - 70, profile.company_name or "InvoiceBot Tradie")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, height - 95, f"Template: {template.name}")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, height - 150, "Bill To")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(40, height - 170, client.name if client else "Client to be selected")
    if client and client.company:
        pdf.drawString(40, height - 186, client.company)

    y = height - 240
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Description")
    pdf.drawString(330, y, "Qty")
    pdf.drawString(390, y, "Unit")
    pdf.drawString(470, y, "Total")
    y -= 20

    pdf.setFont("Helvetica", 11)
    for item in draft.items:
        pdf.drawString(40, y, item.description[:42])
        pdf.drawRightString(360, y, f"{item.quantity:g}")
        pdf.drawRightString(440, y, f"${item.unit_price_cents / 100:.2f}")
        pdf.drawRightString(540, y, f"${item.line_total_cents / 100:.2f}")
        y -= 18

    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(540, y, f"Subtotal ${draft.subtotal_cents / 100:.2f}")
    y -= 18
    pdf.drawRightString(540, y, f"GST ${draft.gst_cents / 100:.2f}")
    y -= 18
    pdf.drawRightString(540, y, f"Total ${draft.total_cents / 100:.2f}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
