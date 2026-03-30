from __future__ import annotations

import base64
from datetime import timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from invoicebot.models import Client, InvoiceDraft, Profile
from invoicebot.services.tax import discount_total_cents, gross_subtotal_cents, gst_cents, gst_label, gst_summary_label, total_cents
from invoicebot.services.template_catalog import get_template

ROWS_PER_PAGE = 7
MAX_ITEMS_PER_INVOICE = ROWS_PER_PAGE * 2


def _draw_wrapped_lines(pdf: canvas.Canvas, x: float, y: float, lines: list[str], *, width: float, step: float = 14) -> float:
    current_y = y
    for line in lines:
        if not line:
            continue
        text = line
        while text:
            split_at = len(text)
            while split_at > 0 and pdf.stringWidth(text[:split_at], "Helvetica", 10) > width:
                split_at -= 1
            if split_at <= 0:
                break
            chunk = text[:split_at]
            if split_at < len(text):
                last_space = chunk.rfind(" ")
                if last_space > 10:
                    chunk = chunk[:last_space]
                    split_at = last_space
            pdf.drawString(x, current_y, chunk.strip())
            text = text[split_at:].strip()
            current_y -= step
    return current_y


def _money(cents: int) -> str:
    return f"{cents / 100:,.2f}"


def _money_unit(cents: int) -> str:
    return f"{cents / 100:,.2f}"


def _draw_logo(pdf: canvas.Canvas, profile: Profile, *, x: float, y: float, width: float, height: float, accent) -> None:
    pdf.setStrokeColor(accent)
    pdf.roundRect(x, y, width, height, 8, fill=0, stroke=1)

    if not profile.logo_url.startswith("data:image/"):
        pdf.setFillColor(accent)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(x + (width / 2), y + (height / 2) - 4, "Your Logo")
        return

    try:
        _, encoded = profile.logo_url.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        image = ImageReader(BytesIO(image_bytes))
        image_width, image_height = image.getSize()
    except Exception:
        pdf.setFillColor(accent)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(x + (width / 2), y + (height / 2) - 4, "Your Logo")
        return

    scale = min((width - 16) / image_width, (height - 12) / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    draw_x = x + ((width - draw_width) / 2)
    draw_y = y + ((height - draw_height) / 2)
    pdf.drawImage(image, draw_x, draw_y, draw_width, draw_height, preserveAspectRatio=True, mask="auto")


def _draw_label_value_block(
    pdf: canvas.Canvas,
    *,
    x: float,
    top_y: float,
    width: float,
    accent,
    title: str,
    eyebrow: str,
    headline: str,
    lines: list[str],
) -> None:
    pdf.setStrokeColor(colors.HexColor("#d7dce4"))
    pdf.setDash(3, 3)
    pdf.roundRect(x, top_y - 150, width, 150, 8, fill=0, stroke=1)
    pdf.setDash()

    pdf.setFillColor(accent)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x + 12, top_y - 18, title)

    pdf.setFillColor(colors.HexColor("#8f8f8f"))
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x + 12, top_y - 36, eyebrow)

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(x + 12, top_y - 54, headline)

    pdf.setFont("Helvetica", 10)
    _draw_wrapped_lines(pdf, x + 12, top_y - 74, lines, width=width - 24)


def _draw_table_header(pdf: canvas.Canvas, *, page_left: float, page_right: float, content_width: float, table_top: float) -> None:
    pdf.setFillColor(colors.HexColor("#f1f3f6"))
    pdf.rect(page_left, table_top - 18, content_width, 18, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#535862"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(page_left + 8, table_top - 12, "Item")
    pdf.drawString(page_left + 246, table_top - 12, "HRS/QTY")
    pdf.drawString(page_left + 324, table_top - 12, "Rate")
    pdf.drawString(page_left + 382, table_top - 12, "Disc")
    pdf.drawString(page_left + 432, table_top - 12, "GST")
    pdf.drawRightString(page_right - 8, table_top - 12, "Subtotal")


def _draw_items_table(pdf: canvas.Canvas, items: list, profile: Profile, *, page_left: float, page_right: float, table_top: float) -> float:
    y = table_top - 34
    row_height = 42
    for item in items:
        pdf.setStrokeColor(colors.HexColor("#e5e7eb"))
        pdf.line(page_left, y - 18, page_right, y - 18)
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 10)
        _draw_wrapped_lines(pdf, page_left + 8, y, [item.description], width=205, step=11)
        pdf.drawString(page_left + 260, y, f"{item.quantity:g}")
        pdf.drawString(page_left + 334, y, _money_unit(item.unit_price_cents))
        if item.discount_cents:
            if item.discount_percent is not None:
                discount_text = f"-{item.discount_percent:g}%"
            else:
                discount_text = f"-{_money(item.discount_cents)}"
            pdf.drawString(page_left + 382, y, discount_text)
        else:
            pdf.drawString(page_left + 382, y, "-")
        pdf.drawString(page_left + 436, y, gst_label(profile))
        pdf.drawRightString(page_right - 8, y, _money(item.line_total_cents))
        y -= row_height
    return y


def _draw_summary(
    pdf: canvas.Canvas,
    draft: InvoiceDraft,
    profile: Profile,
    *,
    page_left: float,
    page_right: float,
    content_width: float,
    summary_title_y: float,
    summary_title: str,
) -> None:
    summary_x = page_left + 275
    summary_width = content_width - 275
    pdf.setFillColor(colors.HexColor("#f1f3f6"))
    pdf.rect(summary_x, summary_title_y - 20, summary_width, 24, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#535862"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(summary_x + (summary_width / 2), summary_title_y - 12, summary_title)
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(page_right - 8, summary_title_y - 4, "NZD")

    line_y = summary_title_y - 44
    summary_rows = [
        ("Subtotal", gross_subtotal_cents(draft)),
    ]
    if discount_total_cents(draft):
        summary_rows.append(("Discounts", -discount_total_cents(draft)))
    summary_rows.extend([
        (gst_summary_label(profile), gst_cents(draft, profile)),
        ("Total", total_cents(draft, profile)),
    ])
    for label, amount in summary_rows:
        pdf.setStrokeColor(colors.HexColor("#e5e7eb"))
        pdf.line(summary_x, line_y - 8, page_right, line_y - 8)
        pdf.setFillColor(colors.HexColor("#535862"))
        pdf.setFont("Helvetica", 10)
        pdf.drawString(summary_x + 10, line_y, label)
        pdf.drawRightString(page_right - 8, line_y, _money(amount))
        line_y -= 28
    return line_y


def _draw_payment_details(
    pdf: canvas.Canvas,
    profile: Profile,
    *,
    page_left: float,
    page_right: float,
    start_y: float,
) -> None:
    if not profile.bank_details:
        return

    box_x = page_left + 275
    box_width = page_right - box_x
    box_top = start_y - 6
    box_bottom = max(36, box_top - 54)

    pdf.setFillColor(colors.HexColor("#f7f8fa"))
    pdf.roundRect(box_x, box_bottom, box_width, box_top - box_bottom, 8, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#535862"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(box_x + 10, box_top - 16, "Payment details")
    pdf.setFont("Helvetica", 9.5)
    _draw_wrapped_lines(
        pdf,
        box_x + 10,
        box_top - 32,
        [profile.bank_details],
        width=box_width - 20,
        step=11,
    )


def _draw_first_page_header(
    pdf: canvas.Canvas,
    *,
    profile: Profile,
    client: Client | None,
    accent,
    template_name: str,
    document_label: str,
    width: float,
    height: float,
    page_left: float,
    page_right: float,
) -> float:
    pdf.setFillColor(accent)
    pdf.rect(0, height - 26, width, 26, fill=1, stroke=0)
    _draw_logo(pdf, profile, x=page_left, y=height - 82, width=110, height=34, accent=accent)

    pdf.setFillColor(colors.HexColor("#636a73"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(page_right, height - 58, document_label)
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(page_right, height - 74, template_name)

    left_box_x = page_left
    top_box_y = height - 108
    box_width = 248
    gap = 24

    business_lines = [
        profile.address,
        profile.email,
        profile.phone,
        f"NZ GST/IRD Number {profile.gst_number}" if profile.gst_number else "",
    ]
    client_lines = [
        client.company if client else "",
        client.address if client else "",
        client.email if client else "",
        client.phone if client else "",
    ]

    _draw_label_value_block(
        pdf,
        x=left_box_x,
        top_y=top_box_y,
        width=box_width,
        accent=accent,
        title="Your details:",
        eyebrow="FROM",
        headline=profile.company_name or "Your business",
        lines=business_lines,
    )
    _draw_label_value_block(
        pdf,
        x=left_box_x + box_width + gap,
        top_y=top_box_y,
        width=box_width,
        accent=accent,
        title="Client's details:",
        eyebrow="TO",
        headline=client.name if client else "Client to be selected",
        lines=client_lines,
    )
    return top_box_y


def _render_document_pdf(
    profile: Profile,
    draft: InvoiceDraft,
    client: Client | None,
    *,
    document_label: str,
    number_label: str,
    number_value: str,
    summary_title: str,
    include_due_date: bool,
) -> bytes:
    template = get_template(profile.default_template_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    if len(draft.items) > MAX_ITEMS_PER_INVOICE:
        raise ValueError(f"{document_label.title()}s are limited to {MAX_ITEMS_PER_INVOICE} items.")

    accent = colors.HexColor(template.accent)
    page_left = 35
    page_right = width - 40
    content_width = page_right - page_left
    top_box_y = _draw_first_page_header(
        pdf,
        profile=profile,
        client=client,
        accent=accent,
        template_name=template.name,
        document_label=document_label,
        width=width,
        height=height,
        page_left=page_left,
        page_right=page_right,
    )

    document_date = draft.created_at.strftime("%b %d, %Y")
    due_date = (draft.created_at + timedelta(days=7)).strftime("%b %d, %Y")

    meta_y = top_box_y - 182
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(page_left, meta_y, f"{number_label} : {number_value}")
    if include_due_date:
        pdf.drawString(page_left + 280, meta_y, f"Due Date : {due_date}")
        pdf.drawString(page_left, meta_y - 20, f"{document_label.title()} Date : {document_date}")
    else:
        pdf.drawString(page_left, meta_y - 20, f"{document_label.title()} Date : {document_date}")

    table_top = meta_y - 52
    item_pages = [draft.items[index:index + ROWS_PER_PAGE] for index in range(0, len(draft.items), ROWS_PER_PAGE)]
    _draw_table_header(pdf, page_left=page_left, page_right=page_right, content_width=content_width, table_top=table_top)
    y = _draw_items_table(pdf, item_pages[0], profile, page_left=page_left, page_right=page_right, table_top=table_top)

    if len(item_pages) == 2:
        pdf.setFillColor(colors.HexColor("#636a73"))
        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(page_right - 8, 28, "Page 1 of 2")
        pdf.showPage()

        pdf.setFillColor(accent)
        pdf.rect(0, height - 26, width, 26, fill=1, stroke=0)
        pdf.setFillColor(colors.HexColor("#636a73"))
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(page_left, height - 58, f"{number_label} : {number_value}")
        pdf.drawRightString(page_right, height - 58, f"Page 2 of 2")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(page_left, height - 74, f"Client: {client.name if client else 'No client selected'}")

        table_top = height - 108
        _draw_table_header(pdf, page_left=page_left, page_right=page_right, content_width=content_width, table_top=table_top)
        y = _draw_items_table(pdf, item_pages[1], profile, page_left=page_left, page_right=page_right, table_top=table_top)

    summary_end_y = _draw_summary(
        pdf,
        draft,
        profile,
        page_left=page_left,
        page_right=page_right,
        content_width=content_width,
        summary_title_y=y - 4,
        summary_title=summary_title,
    )
    _draw_payment_details(
        pdf,
        profile,
        page_left=page_left,
        page_right=page_right,
        start_y=summary_end_y,
    )

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def render_invoice_pdf(profile: Profile, draft: InvoiceDraft, client: Client | None) -> bytes:
    invoice_number = f"{profile.invoice_prefix}-{profile.next_invoice_number:04d}"
    return _render_document_pdf(
        profile,
        draft,
        client,
        document_label="INVOICE",
        number_label="Invoice No",
        number_value=invoice_number,
        summary_title="Invoice Summary",
        include_due_date=True,
    )


def render_quote_pdf(profile: Profile, draft: InvoiceDraft, client: Client | None) -> bytes:
    quote_number = f"{profile.quote_prefix}-{profile.next_quote_number:04d}"
    return _render_document_pdf(
        profile,
        draft,
        client,
        document_label="QUOTE",
        number_label="Quote No",
        number_value=quote_number,
        summary_title="Quote Summary",
        include_due_date=False,
    )
