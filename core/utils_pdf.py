"""
PDF Generation Utility for Rentora Invoice Emails.
Uses xhtml2pdf to render Django templates into PDF byte buffers.
"""
import io
import logging
from django.template.loader import get_template
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)


def render_invoice_pdf(booking):
    """
    Render the invoice_pdf.html template into a PDF byte buffer.
    Returns (BytesIO buffer, success boolean).
    """
    try:
        from django.template.exceptions import TemplateDoesNotExist
        template = get_template('emails/invoice_pdf.html')
    except TemplateDoesNotExist as e:
        logger.error(f"Failed to load invoice_pdf.html template: {e}")
        return None, False
        
    context = {'booking': booking}
    html = template.render(context)

    buffer = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(html), dest=buffer)

    if result.err:
        logger.error(f"PDF generation failed for booking {booking.booking_reference}: {result.err}")
        return None, False

    buffer.seek(0)
    return buffer, True
