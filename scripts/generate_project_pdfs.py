from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], fontSize=22, leading=28, alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name="DocSubtitle", parent=styles["BodyText"], fontSize=11, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=18))
styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading1"], fontSize=16, leading=20, textColor=colors.HexColor("#111111"), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name="SubHeading", parent=styles["Heading2"], fontSize=13, leading=17, textColor=colors.HexColor("#222222"), spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallNote", parent=styles["BodyText"], fontSize=9, leading=13, textColor=colors.HexColor("#666666"), spaceBefore=6))


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(doc.leftMargin, 18, "Cyber Cafe Management System")
    canvas.drawRightString(A4[0] - doc.rightMargin, 18, f"Page {doc.page}")
    canvas.restoreState()


PROJECT_FACTS = {
    "title": "Cyber Cafe Management System",
    "stack": "Python, Flask, Jinja templates, in-memory data structures",
    "roles": "Admin and User",
    "features": [
        "Username/password login for admin and user accounts",
        "Google OAuth sign-in integration using Google OAuth 2.0 web flow",
        "Station allocation and live countdown management",
        "Retail POS cart and checkout flow",
        "QR-based payment step with screenshot upload",
        "Admin verification queue for uploaded payment proofs",
        "User dashboard with ranks, station availability, and pricing",
    ],
    "limitations": [
        "Current data is stored in memory and resets when the server restarts",
        "Uploaded screenshots are stored on the local filesystem",
        "No database persistence yet for users, sessions, or payments",
    ],
}


def title_block(story, title, subtitle):
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(title, styles["DocTitle"]))
    story.append(Paragraph(subtitle, styles["DocSubtitle"]))
    story.append(Spacer(1, 0.15 * inch))



def add_paragraphs(story, paragraphs):
    for text in paragraphs:
        story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 0.08 * inch))



def add_bullets(story, items):
    flow = ListFlowable(
        [ListItem(Paragraph(item, styles["BodyText"])) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
    )
    story.append(flow)
    story.append(Spacer(1, 0.08 * inch))



def add_table(story, rows, col_widths=None):
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d6d6d6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.12 * inch))



def build_full_report(path):
    story = []
    title_block(story, "Cyber Cafe Management System", "Comprehensive project report generated from the current Flask implementation")

    story.append(Paragraph("Table of Contents", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "1. Project Overview",
            "2. Objectives and Scope",
            "3. Feature Summary",
            "4. System Design",
            "5. Authentication and Access Control",
            "6. Payment Flow and Proof Verification",
            "7. Deployment and Configuration",
            "8. Limitations and Future Enhancements",
        ],
    )

    story.append(Paragraph("1. Project Overview", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "The Cyber Cafe Management System is a Flask-based web application designed to manage computer station usage, simple retail sales, user dashboards, QR-code-based payments, and payment-proof verification. The project is implemented as a lightweight single-application deployment with HTML templates rendered by Flask.",
            "The system currently targets a small cyber cafe environment where a single administrator can manage sessions and payments while customers can view ranks, free stations, and service pricing.",
        ],
    )

    story.append(Paragraph("2. Objectives and Scope", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "Provide a login system for staff and users",
            "Allow staff to allocate and release computer stations",
            "Support a simple POS workflow for services and products",
            "Introduce QR payment confirmation with screenshot upload",
            "Allow admin review and approval of payment submissions",
            "Prepare the project for GitHub hosting and live deployment on a Python platform",
        ],
    )

    story.append(Paragraph("3. Feature Summary", styles["SectionHeading"]))
    add_bullets(story, PROJECT_FACTS["features"])

    story.append(Paragraph("4. System Design", styles["SectionHeading"]))
    story.append(Paragraph("4.1 Architecture", styles["SubHeading"]))
    add_paragraphs(
        story,
        [
            "The presentation layer is implemented with server-rendered Jinja templates. The application layer is a single Flask app contained in app.py. The data layer is currently an in-memory collection of Python dictionaries and lists used to store users, stations, retail items, rankings, logs, and payment requests.",
        ],
    )
    add_table(
        story,
        [
            ["Layer", "Current Implementation"],
            ["Presentation", "Jinja templates: login.html, admin.html, user.html"],
            ["Application", "Flask routes, business logic, session handling"],
            ["Storage", "In-memory lists/dicts plus uploaded payment screenshots on disk"],
            ["External Services", "Google OAuth endpoints and QR code generation URL"],
        ],
        col_widths=[1.5 * inch, 4.8 * inch],
    )

    story.append(Paragraph("4.2 Core Modules", styles["SubHeading"]))
    add_table(
        story,
        [
            ["Module", "Purpose"],
            ["Authentication", "Local login and Google OAuth sign-in"],
            ["Station Management", "Allocate, release, and monitor PC sessions"],
            ["Retail POS", "Add items, calculate totals, continue to payment"],
            ["Payment Verification", "Collect screenshot proof and let admin verify or reject"],
            ["User Dashboard", "Display rank, usage summary, pricing, and station availability"],
        ],
        col_widths=[1.8 * inch, 4.5 * inch],
    )

    story.append(Paragraph("5. Authentication and Access Control", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "The application uses Flask session storage for login state. Local authentication supports static admin and user credentials. Google OAuth is also integrated using the standard authorization code flow, and an optional configured admin email can be elevated to the admin role after Google login.",
        ],
    )
    add_bullets(
        story,
        [
            "login_required protects all logged-in views",
            "admin_required restricts admin-only routes",
            "Google sign-in requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET",
            "Redirect URI must match the Google Cloud configuration exactly",
        ],
    )

    story.append(Paragraph("6. Payment Flow and Proof Verification", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "After items are added to the cart, the admin continues to a QR payment page. The total amount, payment reference, receiver information, and QR image are displayed. The payer then uploads a screenshot of the payment confirmation. That screenshot is saved under static/uploads/payments and a payment request is created with pending status.",
            "The admin verification screen lists submitted payments, uploaded screenshots, item details, amount, and status. Each payment can then be verified or rejected.",
        ],
    )
    add_bullets(
        story,
        [
            "Accepted file types: PNG, JPG, JPEG, WEBP",
            "Status values: pending, verified, rejected",
            "Payment QR can use a fixed image URL or generated UPI QR data",
        ],
    )

    story.append(Paragraph("7. Deployment and Configuration", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "The application is GitHub-ready and can be deployed to platforms such as Render, Railway, or PythonAnywhere. Runtime configuration is controlled through environment variables for Flask secrets, Google OAuth credentials, and payment settings.",
        ],
    )
    add_table(
        story,
        [
            ["Variable", "Purpose"],
            ["SECRET_KEY", "Flask session signing key"],
            ["FLASK_DEBUG", "Enable or disable debug mode"],
            ["GOOGLE_CLIENT_ID", "Google OAuth client identifier"],
            ["GOOGLE_CLIENT_SECRET", "Google OAuth client secret"],
            ["GOOGLE_ADMIN_EMAIL", "Google account that should receive admin access"],
            ["PAYMENT_UPI_ID", "UPI ID used for payment QR creation"],
            ["PAYMENT_RECEIVER", "Display name for payment receiver"],
        ],
        col_widths=[2.2 * inch, 4.1 * inch],
    )

    story.append(Paragraph("8. Limitations and Future Enhancements", styles["SectionHeading"]))
    add_bullets(story, PROJECT_FACTS["limitations"] + [
        "Move all core data to SQLite or PostgreSQL",
        "Add user-side payment history and notifications",
        "Add admin analytics dashboards and downloadable reports",
        "Store uploads in cloud storage for production",
    ])

    story.append(Paragraph("Conclusion", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "The current implementation provides a complete working prototype covering login, station handling, retail checkout, payment proof collection, and admin verification. It is suitable as a strong academic or prototype project and can be extended into a production-ready system with persistent storage and stronger operational controls.",
        ],
    )

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=36).build(story, onFirstPage=on_page, onLaterPages=on_page)



def build_system_design(path):
    story = []
    title_block(story, "Cyber Cafe System Design", "Architecture, routes, data structures, and operational flow")

    story.append(Paragraph("1. High-Level Architecture", styles["SectionHeading"]))
    add_table(
        story,
        [
            ["Component", "Description"],
            ["Browser Client", "Admin and user interfaces rendered from Flask templates"],
            ["Flask Server", "Handles routing, session logic, OAuth, POS, and payment management"],
            ["Upload Storage", "Local filesystem storage for payment screenshots"],
            ["Third-party OAuth", "Google accounts OAuth 2.0 authorization"],
            ["QR Generation", "UPI payment payload encoded as QR image URL"],
        ],
        col_widths=[1.8 * inch, 4.5 * inch],
    )

    story.append(Paragraph("2. Route Design", styles["SectionHeading"]))
    add_table(
        story,
        [
            ["Route", "Purpose"],
            ["/", "Login page and local credential authentication"],
            ["/login/google", "Start Google OAuth"],
            ["/auth/google/callback", "Receive Google OAuth callback"],
            ["/admin", "Admin station dashboard"],
            ["/admin/pos", "Retail POS view"],
            ["/admin/pos/checkout", "QR payment screen"],
            ["/admin/pos/payment", "Upload payment screenshot"],
            ["/admin/payments", "Payment verification queue"],
            ["/user", "User dashboard"],
            ["/api/stations", "JSON station status API"],
        ],
        col_widths=[2.2 * inch, 4.1 * inch],
    )

    story.append(Paragraph("3. Data Structures", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "USERS: predefined login accounts and roles",
            "stations: station state, active session, timing, and charge",
            "retail_items: available products and services",
            "customers: leaderboard and user summary data",
            "activity_log: recent system actions",
            "payment_requests: uploaded proof submissions and verification state",
        ],
    )

    story.append(Paragraph("4. Operational Flows", styles["SectionHeading"]))
    story.append(Paragraph("4.1 Admin Station Flow", styles["SubHeading"]))
    add_bullets(
        story,
        [
            "Admin logs in",
            "Admin selects station and duration",
            "Session timer starts and dashboard updates remaining time",
            "Admin can release the station manually",
        ],
    )
    story.append(Paragraph("4.2 Payment Flow", styles["SubHeading"]))
    add_bullets(
        story,
        [
            "Admin adds items to cart",
            "System calculates total and creates a payment reference",
            "QR page shows amount and payment receiver details",
            "User pays externally and screenshot is uploaded",
            "Admin verifies or rejects the proof submission",
        ],
    )

    story.append(Paragraph("5. Security and Access Notes", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "Session-based access control is used throughout the app",
            "Admin-only routes are protected by admin_required",
            "Google OAuth uses state tokens to mitigate CSRF during sign-in",
            "Payment screenshot upload is limited by allowed file extension",
            "Production deployment should use a regenerated secret key and HTTPS",
        ],
    )

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=36).build(story, onFirstPage=on_page, onLaterPages=on_page)



def build_user_guide(path):
    story = []
    title_block(story, "Cyber Cafe User and Admin Guide", "Step-by-step operating guide for the current project")

    story.append(Paragraph("1. Login Methods", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "Admin can sign in with admin / admin123",
            "User can sign in with user1 / user123",
            "Google sign-in is available when Google OAuth credentials are configured",
        ],
    )

    story.append(Paragraph("2. Admin Guide", styles["SectionHeading"]))
    story.append(Paragraph("2.1 Manage Stations", styles["SubHeading"]))
    add_bullets(
        story,
        [
            "Open the Computer Stations page",
            "Choose 1 Hr, 2 Hr, or 3 Hr",
            "Enter the customer name and start the session",
            "Release the station when the customer finishes",
        ],
    )
    story.append(Paragraph("2.2 Retail POS", styles["SubHeading"]))
    add_bullets(
        story,
        [
            "Open Retail POS",
            "Add items to cart",
            "Review the total and continue to payment",
        ],
    )
    story.append(Paragraph("2.3 Payment Verification", styles["SubHeading"]))
    add_bullets(
        story,
        [
            "Display the QR to the customer",
            "Collect payment screenshot upload",
            "Open the Payments page",
            "Review amount and proof image",
            "Verify or reject the payment",
        ],
    )

    story.append(Paragraph("3. User Guide", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "Sign in from the main login screen",
            "Check current rank, sessions, and total spent",
            "Review available computer stations",
            "View current pricing for cafe services and products",
        ],
    )

    story.append(Paragraph("4. Troubleshooting", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "If Google login shows access blocked, verify redirect URIs in Google Cloud Console",
            "If payment proof upload fails, make sure the file is PNG, JPG, JPEG, or WEBP",
            "If data disappears after restart, that is expected in the current in-memory version",
            "If the QR details are wrong, update PAYMENT_UPI_ID and PAYMENT_RECEIVER in the environment",
        ],
    )

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=36).build(story, onFirstPage=on_page, onLaterPages=on_page)



def build_deployment_guide(path):
    story = []
    title_block(story, "Cyber Cafe Deployment Guide", "Local setup, environment variables, and live hosting checklist")

    story.append(Paragraph("1. Local Setup", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "Create and activate a virtual environment",
            "Install dependencies from requirements.txt",
            "Configure .env values for Google and payment settings",
            "Run python app.py locally",
        ],
    )

    story.append(Paragraph("2. Production Checklist", styles["SectionHeading"]))
    add_bullets(
        story,
        [
            "Set SECRET_KEY to a strong random value",
            "Set FLASK_DEBUG=0",
            "Deploy with gunicorn app:app",
            "Configure the exact Google redirect URIs for local and live domains",
            "Regenerate OAuth client secret if it has been exposed during testing",
        ],
    )

    story.append(Paragraph("3. Required Environment Variables", styles["SectionHeading"]))
    add_table(
        story,
        [
            ["Variable", "Example"],
            ["SECRET_KEY", "change-this-in-production"],
            ["GOOGLE_CLIENT_ID", "<google client id>"],
            ["GOOGLE_CLIENT_SECRET", "<google client secret>"],
            ["GOOGLE_ADMIN_EMAIL", "admin@example.com"],
            ["PAYMENT_UPI_ID", "name@bank"],
            ["PAYMENT_RECEIVER", "Cyber Cafe"],
        ],
        col_widths=[2.2 * inch, 4.1 * inch],
    )

    story.append(Paragraph("4. Hosting Notes", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "GitHub stores the code but does not host the Flask runtime. Use a Python-capable host such as Render, Railway, or PythonAnywhere. Store secrets in host-managed environment variables rather than committing them into a repository.",
            "For production, move uploaded screenshots and business data to persistent storage so restarts do not erase state.",
        ],
    )

    story.append(Paragraph("5. Recommended Next Upgrade", styles["SectionHeading"]))
    add_paragraphs(
        story,
        [
            "The strongest next improvement is introducing SQLite or PostgreSQL for users, payments, sessions, and logs. That single change would make the project much more credible for deployment and academic submission.",
        ],
    )

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=36).build(story, onFirstPage=on_page, onLaterPages=on_page)



def main():
    build_full_report(DOCS_DIR / "Cyber_Cafe_Project_Report.pdf")
    build_system_design(DOCS_DIR / "Cyber_Cafe_System_Design.pdf")
    build_user_guide(DOCS_DIR / "Cyber_Cafe_User_Admin_Guide.pdf")
    build_deployment_guide(DOCS_DIR / "Cyber_Cafe_Deployment_Guide.pdf")
    print("Generated PDFs in", DOCS_DIR)


if __name__ == "__main__":
    main()
