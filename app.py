from datetime import datetime, timedelta
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from recommendations import get_user_recommendations

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
database_url = os.getenv("DATABASE_URL", "").strip()
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///kdl_ilms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    department = db.Column(db.String(120))
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    unit_head = db.Column(db.String(120))

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey("branch.id"), nullable=False)
    copies_total = db.Column(db.Integer, default=1)
    copies_available = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, default="")
    cover_url = db.Column(db.String(500), default="")
    branch = db.relationship("Branch", backref="materials")


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patron_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False)
    status = db.Column(db.String(40), default="Pending Verification")
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    patron = db.relationship("User", backref="reservations")
    material = db.relationship("Material", backref="reservations")


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patron_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False)
    borrowed_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="Active")
    patron = db.relationship("User", backref="loans")
    material = db.relationship("Material", backref="loans")

def expire_old_reservations():
    cutoff = datetime.utcnow() - timedelta(hours=48)

    expired_reservations = Reservation.query.filter(
        Reservation.status == "Pending Verification",
        Reservation.requested_at < cutoff
    ).all()

    for reservation in expired_reservations:
        reservation.status = "Expired"

        reservation.material.copies_available = min(
            reservation.material.copies_total,
            reservation.material.copies_available + 1
        )

    if expired_reservations:
        db.session.commit()


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required():
    return current_user() is not None


def seed_database():
    if User.query.first():
        return

    kdl = Branch(name="Kenneth Dike Library", location="University of Ibadan", unit_head="Library Administration")
    faculty = Branch(name="Faculty/Departmental Library", location="University of Ibadan", unit_head="Demo Unit Head")
    db.session.add_all([kdl, faculty])
    db.session.flush()

    users = [
        User(user_code="E054579", name="Adewale Khaleed", email="patron@demo.ui", department="Computer Science",
             role="patron", password_hash=generate_password_hash("password")),
        User(user_code="OFF001", name="Demo Circulation Officer", email="officer@demo.ui", department="Library Services",
             role="officer", password_hash=generate_password_hash("password")),
        User(user_code="ADM001", name="System Administrator", email="admin@demo.ui", department="Library Administration",
             role="admin", password_hash=generate_password_hash("password")),
    ]
    db.session.add_all(users)
    db.session.flush()

    materials = [
    Material(
        title="Artificial Intelligence: A Modern Approach",
        author="Stuart Russell & Peter Norvig",
        subject="Artificial Intelligence",
        branch_id=kdl.id,
        copies_total=4,
        copies_available=3,
        description="A foundational text covering intelligent agents, search, reasoning and machine learning.",
        cover_url="https://covers.openlibrary.org/isbn/9780134610993-L.jpg"
    ),

    Material(
        title="Database System Concepts",
        author="Abraham Silberschatz",
        subject="Database Systems",
        branch_id=kdl.id,
        copies_total=5,
        copies_available=2,
        description="Core concepts in database design, transactions, indexing and database systems.",
        cover_url="https://covers.openlibrary.org/isbn/9780078022159-L.jpg"
    ),

    Material(
        title="Machine Learning",
        author="Tom M. Mitchell",
        subject="Machine Learning",
        branch_id=faculty.id,
        copies_total=3,
        copies_available=3,
        description="An introduction to machine learning concepts and algorithms.",
        cover_url="https://covers.openlibrary.org/isbn/9780070428072-L.jpg"
    ),

    Material(
        title="Software Engineering",
        author="Ian Sommerville",
        subject="Software Engineering",
        branch_id=kdl.id,
        copies_total=4,
        copies_available=4,
        description="Software processes, requirements, architecture, testing and project management.",
        cover_url="https://covers.openlibrary.org/isbn/9780133943030-L.jpg"
    ),

    Material(
        title="Python for Data Analysis",
        author="Wes McKinney",
        subject="Data Science",
        branch_id=kdl.id,
        copies_total=3,
        copies_available=3,
        description="Data analysis workflows using Python and pandas.",
        cover_url="https://covers.openlibrary.org/isbn/9781098104023-L.jpg"
    ),

    Material(
        title="Data Mining: Concepts and Techniques",
        author="Jiawei Han",
        subject="Data Mining",
        branch_id=faculty.id,
        copies_total=2,
        copies_available=2,
        description="Methods for discovering useful patterns and knowledge from data.",
        cover_url="https://covers.openlibrary.org/isbn/9780123814791-L.jpg"
    ),

    Material(
    title="Clean Code",
    author="Robert C. Martin",
    subject="Software Engineering",
    branch_id=kdl.id,
    copies_total=4,
    copies_available=4,
    description="A practical guide to writing readable, maintainable and professional software."
),

Material(
    title="Introduction to Algorithms",
    author="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest & Clifford Stein",
    subject="Computer Science",
    branch_id=kdl.id,
    copies_total=5,
    copies_available=5,
    description="A comprehensive introduction to algorithms, data structures, sorting, searching and graph algorithms."
),

Material(
    title="Computer Networking",
    author="Andrew S. Tanenbaum & David J. Wetherall",
    subject="Computer Networks",
    branch_id=kdl.id,
    copies_total=3,
    copies_available=3,
    description="An introduction to computer networks, protocols, network architecture and Internet technologies."
),

Material(
    title="Operating System Concepts",
    author="Abraham Silberschatz, Peter B. Galvin & Greg Gagne",
    subject="Operating Systems",
    branch_id=kdl.id,
    copies_total=4,
    copies_available=4,
    description="Fundamental concepts of operating systems including processes, memory, storage and security."
),

Material(
    title="Calculus",
    author="James Stewart",
    subject="Mathematics",
    branch_id=faculty.id,
    copies_total=4,
    copies_available=4,
    description="A comprehensive introduction to differential and integral calculus and their applications."
),

Material(
    title="Discrete Mathematics and Its Applications",
    author="Kenneth H. Rosen",
    subject="Mathematics",
    branch_id=faculty.id,
    copies_total=3,
    copies_available=3,
    description="Discrete mathematics covering logic, sets, relations, combinatorics, graph theory and algorithms."
),

Material(
    title="Principles of Economics",
    author="N. Gregory Mankiw",
    subject="Economics",
    branch_id=faculty.id,
    copies_total=4,
    copies_available=4,
    description="An introduction to economic principles, markets, supply and demand, production and national economies."
),

Material(
    title="Fundamentals of Physics",
    author="David Halliday, Robert Resnick & Jearl Walker",
    subject="Physics",
    branch_id=faculty.id,
    copies_total=3,
    copies_available=3,
    description="Fundamental principles of mechanics, electricity, magnetism, waves and modern physics."
),

Material(
    title="Campbell Biology",
    author="Lisa A. Urry, Michael L. Cain et al.",
    subject="Biology",
    branch_id=faculty.id,
    copies_total=3,
    copies_available=3,
    description="A comprehensive introduction to biological principles, genetics, evolution, cells and ecosystems."
),

Material(
    title="Organic Chemistry",
    author="Paula Yurkanis Bruice",
    subject="Chemistry",
    branch_id=faculty.id,
    copies_total=3,
    copies_available=3,
    description="An introduction to organic chemistry, molecular structure, reactions and chemical mechanisms."
),

Material(
    title="Research Methodology",
    author="C.R. Kothari",
    subject="Research Methods",
    branch_id=kdl.id,
    copies_total=4,
    copies_available=4,
    description="A practical guide to research design, data collection, analysis and interpretation."
),

Material(
    title="Principles of Marketing",
    author="Philip Kotler & Gary Armstrong",
    subject="Marketing",
    branch_id=faculty.id,
    copies_total=3,
    copies_available=3,
    description="Fundamental marketing concepts including consumer behaviour, market research, branding and strategy."
),
]
    db.session.add_all(materials)
    db.session.commit()

def add_new_materials():
    kdl = Branch.query.filter_by(name="Kenneth Dike Library").first()
    faculty = Branch.query.filter_by(name="Faculty/Departmental Library").first()

    if not kdl or not faculty:
        print("Branches not found. Cannot add materials.")
        return

    new_materials = [
        Material(
            title="Clean Code",
            author="Robert C. Martin",
            subject="Software Engineering",
            branch_id=kdl.id,
            copies_total=4,
            copies_available=4,
            description="A practical guide to writing readable, maintainable and professional software."
        ),

        Material(
            title="Introduction to Algorithms",
            author="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest & Clifford Stein",
            subject="Computer Science",
            branch_id=kdl.id,
            copies_total=5,
            copies_available=5,
            description="A comprehensive introduction to algorithms, data structures, sorting, searching and graph algorithms."
        ),

        Material(
            title="Computer Networking",
            author="Andrew S. Tanenbaum & David J. Wetherall",
            subject="Computer Networks",
            branch_id=kdl.id,
            copies_total=3,
            copies_available=3,
            description="An introduction to computer networks, protocols, network architecture and Internet technologies."
        ),

        Material(
            title="Operating System Concepts",
            author="Abraham Silberschatz, Peter B. Galvin & Greg Gagne",
            subject="Operating Systems",
            branch_id=kdl.id,
            copies_total=4,
            copies_available=4,
            description="Fundamental concepts of operating systems including processes, memory, storage and security."
        ),

        Material(
            title="Calculus",
            author="James Stewart",
            subject="Mathematics",
            branch_id=faculty.id,
            copies_total=4,
            copies_available=4,
            description="A comprehensive introduction to differential and integral calculus and their applications."
        ),

        Material(
            title="Discrete Mathematics and Its Applications",
            author="Kenneth H. Rosen",
            subject="Mathematics",
            branch_id=faculty.id,
            copies_total=3,
            copies_available=3,
            description="Discrete mathematics covering logic, sets, relations, combinatorics, graph theory and algorithms."
        ),

        Material(
            title="Principles of Economics",
            author="N. Gregory Mankiw",
            subject="Economics",
            branch_id=faculty.id,
            copies_total=4,
            copies_available=4,
            description="An introduction to economic principles, markets, supply and demand, production and national economies."
        ),

        Material(
            title="Fundamentals of Physics",
            author="David Halliday, Robert Resnick & Jearl Walker",
            subject="Physics",
            branch_id=faculty.id,
            copies_total=3,
            copies_available=3,
            description="Fundamental principles of mechanics, electricity, magnetism, waves and modern physics."
        ),

        Material(
            title="Campbell Biology",
            author="Lisa A. Urry, Michael L. Cain et al.",
            subject="Biology",
            branch_id=faculty.id,
            copies_total=3,
            copies_available=3,
            description="A comprehensive introduction to biological principles, genetics, evolution, cells and ecosystems."
        ),

        Material(
            title="Organic Chemistry",
            author="Paula Yurkanis Bruice",
            subject="Chemistry",
            branch_id=faculty.id,
            copies_total=3,
            copies_available=3,
            description="An introduction to organic chemistry, molecular structure, reactions and chemical mechanisms."
        ),

        Material(
            title="Research Methodology",
            author="C.R. Kothari",
            subject="Research Methods",
            branch_id=kdl.id,
            copies_total=4,
            copies_available=4,
            description="A practical guide to research design, data collection, analysis and interpretation."
        ),

        Material(
            title="Principles of Marketing",
            author="Philip Kotler & Gary Armstrong",
            subject="Marketing",
            branch_id=faculty.id,
            copies_total=3,
            copies_available=3,
            description="Fundamental marketing concepts including consumer behaviour, market research, branding and strategy."
        ),
    ]

    added = 0

    for material in new_materials:
        existing = Material.query.filter_by(title=material.title).first()

        if not existing:
            db.session.add(material)
            added += 1

    db.session.commit()

    print(f"Added {added} new materials.")

def update_new_book_covers():
    covers = {
        "Clean Code":
            "https://covers.openlibrary.org/b/olid/OL29220209M-L.jpg",

        "Introduction to Algorithms":
            "https://covers.openlibrary.org/b/olid/OL37074298M-L.jpg",

        "Computer Networking":
            "https://covers.openlibrary.org/b/olid/OL26773997M-L.jpg",

        "Operating System Concepts":
            "https://covers.openlibrary.org/b/olid/OL27478658M-L.jpg",

        "Calculus":
            "https://covers.openlibrary.org/b/olid/OL27022867M-L.jpg",

        "Discrete Mathematics and Its Applications":
            "https://covers.openlibrary.org/b/olid/OL9251298M-L.jpg",

        "Principles of Economics":
            "https://covers.openlibrary.org/b/olid/OL27997722M-L.jpg",

        "Fundamentals of Physics":
            "https://covers.openlibrary.org/b/olid/OL10279309M-L.jpg",

        "Campbell Biology":
            "https://covers.openlibrary.org/b/olid/OL32193627M-L.jpg",

        "Organic Chemistry":
            "https://covers.openlibrary.org/b/olid/OL32207318M-L.jpg",

        "Research Methodology":
            "https://covers.openlibrary.org/b/olid/OL27054216M-L.jpg",

        "Principles of Marketing":
            "https://covers.openlibrary.org/b/olid/OL32207814M-L.jpg",
    }

    for title, url in covers.items():
        material = Material.query.filter_by(title=title).first()

        if material:
            material.cover_url = url

    db.session.commit()

    print("New book covers updated.")

def migrate_database():
    with db.engine.connect() as connection:
        result = connection.execute(
            db.text("PRAGMA table_info(material)")
        )

        columns = [row[1] for row in result]

        if "cover_url" not in columns:
            connection.execute(
                db.text(
                    "ALTER TABLE material ADD COLUMN cover_url VARCHAR(500)"
                )
            )
            connection.commit()
            print("Database migration: cover_url column added.")
        else:
            print("Database migration: cover_url already exists.")

def update_book_covers():
    covers = {
        "Artificial Intelligence: A Modern Approach":
            "https://covers.openlibrary.org/b/olid/OL28002220M-L.jpg",

        "Database System Concepts":
            "https://covers.openlibrary.org/b/olid/OL29316583M-L.jpg",
        "Machine Learning":
            "https://covers.openlibrary.org/b/olid/OL662216M-L.jpg",

        "Software Engineering":
            "https://covers.openlibrary.org/b/olid/OL28179584M-L.jpg",

        "Python for Data Analysis":
            "https://covers.openlibrary.org/b/olid/OL37924259M-L.jpg",

        "Data Mining: Concepts and Techniques":
            "https://covers.openlibrary.org/b/olid/OL25761541M-L.jpg",
    }

    for title, url in covers.items():
        material = Material.query.filter_by(title=title).first()

        if material:
            material.cover_url = url

    db.session.commit()
@app.context_processor
def inject_now():
    now = datetime.utcnow()

    def overdue_fine(due_at):
        if due_at and due_at < now:
            days_late = (now.date() - due_at.date()).days
            return days_late * 50
        return 0

    return {
        "now": now,
        "overdue_fine": overdue_fine
    }

@app.context_processor
def inject_user():
    return {"logged_in_user": current_user()}


@app.route("/")
def home():
    featured = Material.query.order_by(Material.title).limit(4).all()
    return render_template("home.html", featured=featured)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form.get("user_code", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(user_code=code).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        user_code = request.form["user_code"].strip().upper()
        email = request.form["email"].strip().lower()
        department = request.form["department"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check password confirmation
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        # Check existing user code
        existing_user = User.query.filter_by(
            user_code=user_code
        ).first()

        if existing_user:
            flash("This matric/staff number is already registered.", "danger")
            return render_template("register.html")

        # Check existing email
        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash("This email address is already registered.", "danger")
            return render_template("register.html")

        # Create patron account
        user = User(
            user_code=user_code,
            name=name,
            email=email,
            department=department,
            role="patron",
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. You can now sign in.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/officer/reservation/<int:reservation_id>/checkout", methods=["POST"])
def checkout_reservation(reservation_id):
    if not login_required() or current_user().role != "officer":
        return redirect(url_for("login"))

    reservation = db.get_or_404(Reservation, reservation_id)

    # Only pending reservations can be checked out
    if reservation.status != "Pending Verification":
        flash("This reservation has already been processed.", "warning")
        return redirect(url_for("officer_dashboard"))

    # Prevent duplicate active loans
    existing_loan = Loan.query.filter_by(
        patron_id=reservation.patron_id,
        material_id=reservation.material_id,
        status="Active"
    ).first()

    if existing_loan:
        flash("This patron already has an active loan for this material.", "warning")
        return redirect(url_for("officer_dashboard"))

    # Create the active loan
    loan = Loan(
        patron_id=reservation.patron_id,
        material_id=reservation.material_id,
        due_at=datetime.utcnow() + timedelta(days=14),
        status="Active"
    )

    # Mark reservation as confirmed
    reservation.status = "Confirmed"

    db.session.add(loan)
    db.session.commit()

    flash("Reservation confirmed and material checked out successfully.", "success")

    return redirect(url_for("officer_dashboard"))



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))
    user = current_user()

    if user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    if user.role == "officer":
        return redirect(url_for("officer_dashboard"))

    loans = Loan.query.filter_by(patron_id=user.id, status="Active").order_by(Loan.due_at).all()
    reservations = Reservation.query.filter_by(patron_id=user.id).order_by(Reservation.requested_at.desc()).all()

    # Transparent academic-project recommendation logic.
    history_subjects = {loan.material.subject for loan in user.loans}
    recommendations = []
    for material in Material.query.all():
        score = 0
        if material.subject.lower() in (user.department or "").lower():
            score += 40
        if any(word.lower() in material.subject.lower() or material.subject.lower() in word.lower()
               for word in history_subjects):
            score += 30
        if material.subject.lower() in {"artificial intelligence", "machine learning", "data science", "database systems"}:
            score += 10
        if material not in [loan.material for loan in loans]:
            recommendations.append((score, material))
    recommendations.sort(key=lambda x: (-x[0], x[1].title))
    recommendations = [m for score, m in recommendations[:4]]

    return render_template("dashboard.html", loans=loans, reservations=reservations,
                           recommendations=recommendations)


@app.route("/catalogue")
def catalogue():
    q = request.args.get("q", "").strip()
    subject = request.args.get("subject", "").strip()
    branch_id = request.args.get("branch_id", type=int)

    query = Material.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Material.title.ilike(like), Material.author.ilike(like),
                   Material.subject.ilike(like))
        )
    if subject:
        query = query.filter(Material.subject == subject)
    if branch_id:
        query = query.filter(Material.branch_id == branch_id)

    materials = query.order_by(Material.title).all()
    patrons = User.query.filter_by(
    role="patron"
).order_by(User.name).all()
    subjects = [row[0] for row in db.session.query(Material.subject).distinct().order_by(Material.subject)]
    branches = Branch.query.order_by(Branch.name).all()
    return render_template("catalogue.html", materials=materials, subjects=subjects,
                           branches=branches, q=q, subject=subject, branch_id=branch_id)
@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()

    if not q:
        return {"results": []}

    like = f"%{q}%"

    materials = Material.query.filter(
        db.or_(
            Material.title.ilike(like),
            Material.author.ilike(like),
            Material.subject.ilike(like)
        )
    ).order_by(Material.title).limit(6).all()

    results = []

    for material in materials:
        results.append({
            "id": material.id,
            "title": material.title,
            "author": material.author,
            "subject": material.subject,
            "available": material.copies_available > 0
        })

    return {"results": results}

@app.route("/material/<int:material_id>")
def material_detail(material_id):
    material = db.get_or_404(Material, material_id)

    materials = Material.query.all()

    user = current_user()

    recommendations = get_user_recommendations(
        materials,
        user,
        current_material=material,
        limit=4
    )

    return render_template(
        "material.html",
        material=material,
        recommendations=recommendations
    )

@app.route("/reserve/<int:material_id>", methods=["POST"])
def reserve(material_id):
    if not login_required() or current_user().role != "patron":
        return redirect(url_for("login"))

    material = db.get_or_404(Material, material_id)
    existing = Reservation.query.filter_by(
        patron_id=current_user().id, material_id=material.id
    ).filter(Reservation.status.in_(["Pending Verification", "Confirmed"])).first()

    if existing:
        flash("You already have an active reservation for this material.", "warning")
    elif material.copies_available < 1:
        flash("This material is currently unavailable.", "danger")
    else:
        reservation = Reservation(patron_id=current_user().id, material_id=material.id)
        material.copies_available -= 1
        db.session.add(reservation)
        db.session.commit()
        flash("Reservation submitted successfully.", "success")
    return redirect(url_for("material_detail", material_id=material.id))

@app.route("/reservation/<int:reservation_id>/cancel", methods=["POST"])
def cancel_reservation(reservation_id):
    if not login_required() or current_user().role != "patron":
        return redirect(url_for("login"))

    reservation = db.get_or_404(Reservation, reservation_id)

    # Make sure the patron owns this reservation
    if reservation.patron_id != current_user().id:
        return redirect(url_for("dashboard"))

    if reservation.status != "Pending Verification":
        flash("This reservation cannot be cancelled.", "warning")
        return redirect(url_for("dashboard"))

    # Return the reserved copy to availability
    reservation.material.copies_available = min(
        reservation.material.copies_total,
        reservation.material.copies_available + 1
    )

    reservation.status = "Cancelled"

    db.session.commit()

    flash("Reservation cancelled successfully.", "success")
    return redirect(url_for("dashboard"))

@app.route("/officer")
def officer_dashboard():
    if not login_required() or current_user().role != "officer":
        return redirect(url_for("login"))
        expire_old_reservations()
    loans = Loan.query.filter_by(
        status="Active"
    ).order_by(Loan.due_at).all()
    loan_history = Loan.query.filter_by(
        status="Returned"
    ).order_by(Loan.returned_at.desc()).limit(20).all()
    reservations = Reservation.query.order_by(
        Reservation.requested_at.desc()
    ).limit(10).all()
    return render_template(
        "officer.html",
        loans=loans,
        loan_history=loan_history,
        reservations=reservations
    )

@app.route("/officer/return/<int:loan_id>", methods=["POST"])
def process_return(loan_id):
    if not login_required() or current_user().role != "officer":
        return redirect(url_for("login"))
    loan = db.get_or_404(Loan, loan_id)
    if loan.status == "Active":
        loan.status = "Returned"
        loan.returned_at = datetime.utcnow()
        loan.material.copies_available = min(loan.material.copies_total, loan.material.copies_available + 1)
        db.session.commit()
        flash("Return processed successfully.", "success")
    return redirect(url_for("officer_dashboard"))

@app.route("/admin")
def admin_dashboard():
    if not login_required() or current_user().role != "admin":
        return redirect(url_for("login"))
        expire_old_reservations()
    stats = {
    "materials": Material.query.count(),
    "patrons": User.query.filter_by(role="patron").count(),
    "active_loans": Loan.query.filter_by(status="Active").count(),
    "reservations": Reservation.query.count(),
    "pending_reservations": Reservation.query.filter_by(
        status="Pending Verification"
    ).count(),
}
    materials = Material.query.order_by(Material.title).all()
    loan_subjects = (
    db.session.query(
        Material.subject,
        db.func.count(Loan.id)
    )
    .join(Loan, Loan.material_id == Material.id)
    .group_by(Material.subject)
    .order_by(db.func.count(Loan.id).desc())
    .all()
)
    max_loan_count = max(
    [count for subject, count in loan_subjects],
    default=1
)
    patrons = User.query.filter_by(
    role="patron"
).order_by(User.name).all()
    return render_template(
        "admin.html",
        stats=stats,
        materials=materials,
        patrons=patrons,
        loan_subjects=loan_subjects,
        max_loan_count=max_loan_count
    )

@app.route("/admin/patron/<int:patron_id>")
def patron_detail(patron_id):
    if not login_required() or current_user().role != "admin":
        return redirect(url_for("login"))

    patron = User.query.filter_by(
        id=patron_id,
        role="patron"
    ).first_or_404()

    active_loans = Loan.query.filter_by(
        patron_id=patron.id,
        status="Active"
    ).order_by(Loan.due_at).all()

    loan_history = Loan.query.filter_by(
        patron_id=patron.id,
        status="Returned"
    ).order_by(Loan.returned_at.desc()).all()

    reservations = Reservation.query.filter_by(
        patron_id=patron.id
    ).order_by(Reservation.requested_at.desc()).all()

    return render_template(
        "patron_detail.html",
        patron=patron,
        active_loans=active_loans,
        loan_history=loan_history,
        reservations=reservations
    )

@app.route("/admin/material/add", methods=["GET", "POST"])
def add_material():
    if not login_required() or current_user().role != "admin":
        return redirect(url_for("login"))

    branches = Branch.query.order_by(Branch.name).all()

    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        subject = request.form["subject"].strip()
        description = request.form["description"].strip()
        branch_id = int(request.form["branch_id"])
        copies_total = int(request.form["copies_total"])

        material = Material(
            title=title,
            author=author,
            subject=subject,
            branch_id=branch_id,
            copies_total=copies_total,
            copies_available=copies_total,
            description=description
        )

        db.session.add(material)
        db.session.commit()

        flash("Material added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "add_material.html",
        branches=branches
    )
@app.route("/admin/material/<int:material_id>/edit", methods=["GET", "POST"])
def edit_material(material_id):
    if not login_required() or current_user().role != "admin":
        return redirect(url_for("login"))

    material = db.get_or_404(Material, material_id)
    branches = Branch.query.order_by(Branch.name).all()

    if request.method == "POST":
        material.title = request.form["title"].strip()
        material.author = request.form["author"].strip()
        material.subject = request.form["subject"].strip()
        material.description = request.form["description"].strip()
        material.branch_id = int(request.form["branch_id"])

        new_total = int(request.form["copies_total"])

        # Keep the number of borrowed/reserved copies consistent
        unavailable = material.copies_total - material.copies_available

        if new_total < unavailable:
            flash(
                "Total copies cannot be lower than the number currently unavailable.",
                "danger"
            )
            return redirect(url_for("edit_material", material_id=material.id))

        material.copies_total = new_total
        material.copies_available = new_total - unavailable

        db.session.commit()

        flash("Material updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "edit_material.html",
        material=material,
        branches=branches
    )
@app.route("/admin/material/<int:material_id>/delete", methods=["POST"])
def delete_material(material_id):
    if not login_required() or current_user().role != "admin":
        return redirect(url_for("login"))

    material = db.get_or_404(Material, material_id)

    active_loan = Loan.query.filter_by(
        material_id=material.id,
        status="Active"
    ).first()

    active_reservation = Reservation.query.filter(
        Reservation.material_id == material.id,
        Reservation.status == "Pending Verification"
    ).first()

    if active_loan or active_reservation:
        flash(
            "This material cannot be deleted because it has an active loan or reservation.",
            "danger"
        )
        return redirect(url_for("admin_dashboard"))

    db.session.delete(material)
    db.session.commit()

    flash("Material deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))
with app.app_context():
    db.create_all()
    migrate_database()
    seed_database()
    add_new_materials()
    update_book_covers()
    update_new_book_covers()

if __name__ == "__main__":
    app.run(debug=True)
