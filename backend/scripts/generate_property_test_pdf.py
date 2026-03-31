from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def draw_paragraph(c: canvas.Canvas, text: str, x: float, y: float, max_width: float, leading: float = 14) -> float:
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line)
            y -= leading
            line = word
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def page_header(c: canvas.Canvas, title: str, page_no: int):
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 18 * mm, "Property Technical & Legal Dossier")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 20 * mm, height - 18 * mm, f"Page {page_no}")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, height - 28 * mm, title)
    c.line(20 * mm, height - 30 * mm, width - 20 * mm, height - 30 * mm)


def section_page(c: canvas.Canvas, title: str, bullets: list[str], notes: str, page_no: int):
    width, height = A4
    page_header(c, title, page_no)
    y = height - 40 * mm
    c.setFont("Helvetica", 10)

    for item in bullets:
        bullet = f"- {item}"
        y = draw_paragraph(c, bullet, 24 * mm, y, width - 44 * mm)
        y -= 2
        if y < 45 * mm:
            c.showPage()
            page_no += 1
            page_header(c, title + " (cont.)", page_no)
            y = height - 40 * mm
            c.setFont("Helvetica", 10)

    y -= 4
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, y, "Additional Notes")
    y -= 14
    c.setFont("Helvetica", 10)
    y = draw_paragraph(c, notes, 24 * mm, y, width - 44 * mm)
    return page_no


def build_content() -> list[tuple[str, list[str], str]]:
    pages = []
    pages.append((
        "Executive Summary",
        [
            "Asset type: Mixed-use residential building",
            "Location: Urban residential corridor, close to schools and transport",
            "Site area: 1,180 sqm; built area: 3,960 sqm",
            "Floors: Basement + Ground + 4 upper levels",
            "Occupancy profile: 82% residential, 18% retail",
            "Current occupancy level: 91%",
            "Estimated annual gross rental yield: 7.4%",
            "Requested sale value provided by owner: aligned with district benchmark range",
            "Main utility systems remain operational with routine interruptions in peak season",
            "Asset managed by third-party facility manager since 2018",
        ],
        "The property demonstrates stable revenue fundamentals and generally acceptable technical condition for its age profile."
    ))

    technical_topics = [
        "Structural Assessment",
        "Envelope & Facade",
        "Roofing Systems",
        "Basement & Drainage",
        "HVAC & Ventilation",
        "Electrical Infrastructure",
        "Vertical Transport",
        "Fire Safety",
        "Water Distribution",
        "Wastewater Systems",
        "Apartment Interior Review",
        "Retail Unit Condition",
        "Common Areas",
        "Parking Facilities",
        "External Works",
        "Acoustic Comfort",
        "Thermal Performance",
        "Lighting & Emergency Circuits",
        "Security Systems",
        "Smart Metering",
    ]

    subtle_findings = [
        "Historical maintenance records mention localized dampness at basement north wall after heavy rainfall events.",
        "Two stair handrails were measured marginally below the latest recommended height standard.",
        "Panelboard labeling is complete, though a few branch circuits still reference legacy naming from pre-2016 rewiring.",
        "Façade sealant at expansion joints shows early shrinkage in sun-exposed western elevation.",
        "One roof membrane patch from 2022 remains serviceable but should be monitored before next rainy season.",
        "Boiler room inventory lists insulation wraps of unknown composition on two legacy pipe elbows pending laboratory confirmation.",
        "Lift machine room logbook shows intermittent overheat alarms during July and August high-load periods.",
        "A minor horizontal crack pattern in corridor plaster aligns with prior settlement note already closed in 2021.",
        "Emergency luminaire runtime test on level 4 achieved borderline duration relative to the target benchmark.",
        "A small set of ceramic tiles in lobby threshold exhibits reduced slip resistance when wet.",
    ]

    for i, topic in enumerate(technical_topics, start=1):
        bullets = [
            f"Inspection zone: {topic} - primary review completed with photographic evidence.",
            "No immediate shutdown risk identified during visual inspection.",
            "Maintenance response times remain within operator service-level reports.",
            "Component lifecycle tracking is present for major equipment.",
            subtle_findings[(i - 1) % len(subtle_findings)],
            "Preventive maintenance planning is documented for the next 12 months.",
            "Capital expenditure reserves appear adequate for routine replacement cycles.",
        ]
        notes = (
            "Condition profile is acceptable for continued operation. A focused follow-up review is advised where wear patterns "
            "or legacy components are recorded to preserve compliance and asset value stability."
        )
        pages.append((topic, bullets, notes))

    legal_topics = [
        "Title & Ownership",
        "Permits & Municipal Files",
        "Tenancy Agreements",
        "Insurance & Claims History",
        "Compliance Register",
        "Environmental & Materials Review",
        "Dispute & Litigation Check",
    ]

    legal_subtle = [
        "One addendum references an annex that is archived offsite and not yet digitized in the current data room.",
        "Permit closure for a minor 2014 mezzanine reconfiguration is stamped but the municipal index still lists it as pending reconciliation.",
        "Two retail leases include renewal options with capped increases below current inflation assumptions.",
        "Past insurer correspondence includes a moisture-related claim closed without payout due to deductible threshold.",
        "Compliance matrix indicates an accessibility upgrade recommendation with implementation window extending into next fiscal year.",
        "Historical vendor statement mentions obsolete adhesive products in a prior refurbishment without quantified inventory remaining onsite.",
        "A neighborhood boundary filing was contested in 2011 and resolved; notarized closure note is referenced but not attached in this copy set.",
    ]

    for i, topic in enumerate(legal_topics, start=1):
        bullets = [
            f"Document family reviewed: {topic}.",
            "Core records are coherent across owner, operator, and municipal copies.",
            legal_subtle[i - 1],
            "No active high-severity legal blockers found in the examined set.",
            "Recommendations focus on documentation consolidation and minor compliance housekeeping.",
        ]
        notes = (
            "Legal posture is generally manageable. Completing archival retrieval and harmonizing legacy references would "
            "reduce execution friction during transaction close."
        )
        pages.append((topic, bullets, notes))

    pages.append((
        "Financial Snapshot",
        [
            "Trailing 12-month gross income and occupancy ratios are within local market median levels.",
            "Operating expense variance mostly reflects seasonal energy costs and lift maintenance spikes.",
            "Service charge recoveries are high with limited arrears concentration.",
            "Reserve account is funded, though projected envelope resealing may need slight top-up in next cycle.",
            "Sensitivity scenario suggests moderate downside resilience under vacancy stress assumptions.",
        ],
        "Financial profile supports transaction review, with prudent adjustment for deferred minor works and selected lease clauses."
    ))

    pages.append((
        "Recommendations & Next Steps",
        [
            "Run focused intrusive check at basement moisture-prone segments.",
            "Update electrical panel branch legend and emergency-light battery set on upper level.",
            "Collect laboratory confirmation for legacy insulation material fragments.",
            "Request municipality reconciliation note for historical permit index mismatch.",
            "Retrieve missing annexes and notarized closure artifacts into the transaction room.",
            "Reassess selected lease renewals against revised CPI outlook.",
        ],
        "Overall, the asset can proceed in diligence with targeted corrective actions tracked before final close."
    ))

    while len(pages) < 30:
        idx = len(pages) + 1
        pages.append((
            f"Appendix {idx - 29}",
            [
                "Photo register summary attached by zone and date.",
                "Mechanical equipment inventory cross-referenced to maintenance records.",
                "Meter readings captured during inspection window.",
                "Sampling notes archived under technical annex references.",
                "No outlier observations beyond previously logged maintenance exceptions.",
            ],
            "Appendix content prepared for audit trail continuity and reviewer traceability."
        ))

    return pages


def generate_pdf(path: Path):
    c = canvas.Canvas(str(path), pagesize=A4)
    sections = build_content()
    page_no = 1

    for title, bullets, notes in sections[:30]:
        page_no = section_page(c, title, bullets, notes, page_no)
        c.showPage()
        page_no += 1

    c.save()


if __name__ == "__main__":
    out_dir = Path("mock_uploads")
    out_dir.mkdir(exist_ok=True)
    output_file = out_dir / "property_dossier_test_30_pages.pdf"
    generate_pdf(output_file)
    print(f"Generated: {output_file.resolve()}")
