from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# --- USERS ---
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # Relationships
    created_plans = db.relationship("Plan", back_populates="creator")
    participations = db.relationship("PlanParticipant", back_populates="user")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# --- PLANS ---
class Plan(db.Model):
    __tablename__ = "plans"
    
    id = db.Column(db.Integer, primary_key=True)
    hash_id = db.Column(db.String(20), unique=True, nullable=False)  # like /5Gsi7kxi
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Creator (owner of the plan)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", back_populates="created_plans")

    # Participants (many-to-many via PlanParticipant)
    participants = db.relationship("PlanParticipant", back_populates="plan")

    # Expenses in this plan
    expenses = db.relationship("Expense", back_populates="plan", cascade="all, delete-orphan")


# --- PLAN PARTICIPANTS (association table) ---
class PlanParticipant(db.Model):
    __tablename__ = "plan_participants"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    role = db.Column(db.String(20), default="member")  # e.g. "owner", "member"
    name = db.Column(db.String(100), nullable=False) 
    
    # Relationships
    user = db.relationship("User", back_populates="participations")
    plan = db.relationship("Plan", back_populates="participants")


# --- EXPENSES ---
class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Who paid?
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    payer_name = db.Column(db.String(100), nullable=False)  # Store payer name for reference
    payer = db.relationship("User")

    # Which plan does this belong to?
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    plan = db.relationship("Plan", back_populates="expenses")

    # Expense shares (split among participants)
    shares = db.relationship("ExpenseShare", back_populates="expense", cascade="all, delete-orphan")


# --- EXPENSE SHARES (per participant) ---
class ExpenseShare(db.Model):
    __tablename__ = "expense_shares"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey("plan_participants.id", ondelete="SET NULL"), nullable=True)
    name = db.Column(db.String(100), nullable=False)  # Name of the participant for this share
    amount = db.Column(db.Float, nullable=False)

    # Relationships
    expense = db.relationship("Expense", back_populates="shares")
    participant = db.relationship("PlanParticipant")
