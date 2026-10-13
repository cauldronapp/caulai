"""Generate the Phase 1A Executive Acceptance Certificate PDF (one page, $0, offline)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import datetime

OUT = "/app/docs/PHASE_1A_ACCEPTANCE_CERTIFICATE.pdf"

INK = colors.HexColor("#0f172a")
ACCENT = colors.HexColor("#b45309")
MUTED = colors.HexColor("#475569")
LINE = colors.HexColor("#cbd5e1")
BG = colors.HexColor("#f8fafc")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Brand", parent=styles["Normal"], fontName="Helvetica-Bold",
                          fontSize=10, textColor=ACCENT, spaceAfter=2, leading=12,
                          alignment=TA_CENTER))
styles.add(ParagraphStyle("TitleC", parent=styles["Title"], fontName="Helvetica-Bold",
                          fontSize=20, textColor=INK, spaceAfter=2, leading=24,
                          alignment=TA_CENTER))
styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontSize=9.5, textColor=MUTED,
                          alignment=TA_CENTER, spaceAfter=4, leading=13))
styles.add(ParagraphStyle("H", parent=styles["Normal"], fontName="Helvetica-Bold",
                          fontSize=10.5, textColor=INK, spaceBefore=8, spaceAfter=3))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=8.8, textColor=INK,
                          leading=12.5))
styles.add(ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.3, textColor=INK,
                          leading=11))
styles.add(ParagraphStyle("CellB", parent=styles["Normal"], fontName="Helvetica-Bold",
                          fontSize=8.3, textColor=INK, leading=11))
styles.add(ParagraphStyle("Foot", parent=styles["Normal"], fontSize=7.3, textColor=MUTED,
                          leading=10))

today = datetime.date.today().strftime("%d %B %Y")
story = []

story.append(Paragraph("CAULDRON TECHNOLOGIES, INC.", styles["Brand"]))
story.append(Paragraph("Phase 1A Acceptance Certificate", styles["TitleC"]))
story.append(Paragraph("CAUL AI &mdash; Cauldron Growth OS Command Center (Private Enterprise Platform)",
                       styles["Sub"]))
story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceBefore=4, spaceAfter=8))

# Attestation
story.append(Paragraph(
    "This certifies that <b>Phase 1A</b> of the CAUL AI Command Center has been delivered, "
    "independently tested, and <b>formally accepted</b> by the Executive Owner. The platform "
    "operates as a standalone, private, PostgreSQL-backed system of record with <b>no external "
    "service connectivity and $0 external spend</b>. Authentication runs as a clearly labeled "
    "provider-neutral <b>stub</b>; all connectors remain <b>Not Connected</b>.",
    styles["Body"]))

# Meta table
meta = [
    [Paragraph("Program", styles["CellB"]), Paragraph("CAUL AI &mdash; Phase 1A", styles["Cell"]),
     Paragraph("Acceptance Date", styles["CellB"]), Paragraph(today, styles["Cell"])],
    [Paragraph("Exec Owner", styles["CellB"]), Paragraph("Sean Gaden", styles["Cell"]),
     Paragraph("Status", styles["CellB"]), Paragraph("<b>ACCEPTED &mdash; CLOSED</b>", styles["Cell"])],
    [Paragraph("Datastore", styles["CellB"]), Paragraph("PostgreSQL 15 (dev + staging)", styles["Cell"]),
     Paragraph("External Spend", styles["CellB"]), Paragraph("$0", styles["Cell"])],
]
mt = Table(meta, colWidths=[1.1*inch, 2.25*inch, 1.2*inch, 2.1*inch])
mt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), BG),
    ("BOX", (0,0), (-1,-1), 0.6, LINE),
    ("INNERGRID", (0,0), (-1,-1), 0.4, LINE),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(Spacer(1, 6))
story.append(mt)

# Scope & controls (two columns)
story.append(Paragraph("Scope &amp; Controls Delivered", styles["H"]))
scope_items = [
    "Provider-neutral OIDC/OAuth2 auth interface + labeled stub; JWT httpOnly sessions, server-side expiry/revocation",
    "Server-side RBAC, default-deny; complete resource&times;action matrix; CI-enforced route coverage",
    "Recommendation &amp; approval state machines with digest binding, quorum, no self/expired/service-identity approval",
    "Tamper-evident hash-chained audit; INSERT-only at DB level; canonical sequencing + verify + checkpoints",
    "Emergency controls: global/granular pause-resume, queue cancel/drain, revoke, rollback (stub paths)",
    "Separate physical dev/staging databases; least-privilege app user; idempotent seed with production guards",
    "Connector contract-test suite (StubConnector); all live connectors remain Not Connected",
    "Full Command Center UI, all states, responsive, WCAG 2.1 AA",
]
rows = []
for i in range(0, len(scope_items), 2):
    left = Paragraph("&bull;&nbsp; " + scope_items[i], styles["Cell"])
    right = Paragraph("&bull;&nbsp; " + scope_items[i+1], styles["Cell"]) if i+1 < len(scope_items) else Paragraph("", styles["Cell"])
    rows.append([left, right])
st = Table(rows, colWidths=[3.33*inch, 3.33*inch])
st.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING", (0,0), (-1,-1), 2),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
]))
story.append(st)

# Test evidence
story.append(Paragraph("Test &amp; Security Evidence", styles["H"]))
ev = [
    [Paragraph("Automated test suite", styles["CellB"]), Paragraph("44 / 44 pytest passed (RBAC, audit, adversarial, route-coverage, seed-guard, connector-contract, hardening)", styles["Cell"])],
    [Paragraph("Audit integrity", styles["CellB"]), Paragraph("Hash chain CHAIN VERIFIED &mdash; 0 issues at acceptance", styles["Cell"])],
    [Paragraph("Security remediations", styles["CellB"]), Paragraph("CORS allowlist (no wildcard); CSRF middleware; rate limiting; BOLA ownership checks; env-specific cron HMAC", styles["Cell"])],
    [Paragraph("Session cookie", styles["CellB"]), Paragraph("HttpOnly; Secure; SameSite=Lax; server-side revocable; CSP frame-ancestors 'none'; HSTS; X-Frame-Options DENY", styles["Cell"])],
    [Paragraph("Accessibility", styles["CellB"]), Paragraph("WCAG 2.1 AA UI remediation + manual screen-reader review pass", styles["Cell"])],
]
et = Table(ev, colWidths=[1.55*inch, 5.11*inch])
et.setStyle(TableStyle([
    ("BOX", (0,0), (-1,-1), 0.6, LINE),
    ("INNERGRID", (0,0), (-1,-1), 0.4, LINE),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("BACKGROUND", (0,0), (0,-1), BG),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(et)

# Boundaries deferred to 1B
story.append(Paragraph("Explicit Boundaries (Deferred to Phase 1B &mdash; requires separate written approval)", styles["H"]))
story.append(Paragraph(
    "Auth0 / live IdP connection &nbsp;&bull;&nbsp; true separate-server infrastructure isolation &nbsp;&bull;&nbsp; "
    "activation of real connectors &nbsp;&bull;&nbsp; off-box checkpoint export &nbsp;&bull;&nbsp; any production environment "
    "or external integration. None of the above were enabled in Phase 1A.",
    styles["Body"]))

# Signature block
story.append(Spacer(1, 16))
sig = [
    [Paragraph("_______________________________", styles["Cell"]),
     Paragraph("_______________________________", styles["Cell"])],
    [Paragraph("Sean Gaden &mdash; Executive Owner", styles["CellB"]),
     Paragraph("Date: " + today, styles["CellB"])],
]
sigt = Table(sig, colWidths=[3.33*inch, 3.33*inch])
sigt.setStyle(TableStyle([
    ("TOPPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,0), 2),
    ("BOTTOMPADDING", (0,1), (-1,1), 8),
]))
story.append(sigt)

story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4, spaceAfter=4))
story.append(Paragraph(
    "Confidential &mdash; Cauldron Technologies, Inc. &nbsp;|&nbsp; Phase 1A is a non-production, "
    "stub-authenticated build with no external connectivity. This certificate records internal "
    "acceptance only and makes no production or IdP claim.",
    styles["Foot"]))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(3)
    canvas.line(0.5*inch, 0.5*inch, letter[0]-0.5*inch, 0.5*inch)
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=letter,
                        leftMargin=0.7*inch, rightMargin=0.7*inch,
                        topMargin=0.6*inch, bottomMargin=0.6*inch,
                        title="CAUL AI Phase 1A Acceptance Certificate",
                        author="Cauldron Technologies, Inc.")
doc.build(story, onFirstPage=_footer)
print("WROTE", OUT)
