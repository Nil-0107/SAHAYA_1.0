SAHAYA

The AI flags. A human decides.

AI-Powered Dynamic Mental Health Monitoring and Distress Support System

<p align="center">
  <img src="https://img.shields.io/badge/Smart%20India%20Hackathon-2026-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/Problem%20Statement-SIH26094-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/Category-Software-success?style=for-the-badge">
  <img src="https://img.shields.io/badge/Theme-MedTech%20%2F%20HealthTech-purple?style=for-the-badge">
</p><p align="center">
  <strong>Team CodeYappers</strong>
</p>---

Table of Contents

- "About The Project" (#about-the-project)
- "The Problem" (#the-problem)
- "Our Solution" (#our-solution)
- "How It Works" (#how-it-works)
- "Key Technical Highlights" (#key-technical-highlights)
- "Tech Stack" (#tech-stack)
- "System Architecture" (#system-architecture)
- "Getting Started" (#getting-started)
- "Usage" (#usage)
- "Testing & Auditing" (#testing--auditing)
- "Project Structure" (#project-structure)
- "Impact & Benefits" (#impact--benefits)
- "Future Scope" (#future-scope)
- "Research & References" (#research--references)
- "Team" (#team)
- "License" (#license)

---

About The Project

SAHAYA is an AI-powered dynamic well-being monitoring and support platform designed for victims and complainants under the SC/ST (Prevention of Atrocities) Act throughout investigation, trial, and rehabilitation.

Legal proceedings move through defined milestones, while a person's well-being can change continuously between those milestones.

SAHAYA provides a structured support layer through:

- Consent-based periodic well-being check-ins
- Text, voice, and AI-assisted interaction
- Explainable machine-learning signals
- Deterministic priority classification
- Human-routed escalation
- Role-based dashboards
- Case-document management
- Notifications and activity records

«The AI flags. A human decides.»

SAHAYA is a support tool, not a diagnostic system. All demonstration data is synthetic.

---

The Problem

A legal case may progress from investigation to trial while the victim's changing well-being remains difficult to monitor.

Existing Gaps

- No continuous well-being monitoring between case milestones
- Support requests can remain disconnected from case workflows
- Manual prioritisation of support needs
- Fragmented access to case and support information
- Limited coordination between victims, counsellors and administrators
- Risk of automated systems making inappropriate decisions

The Core Challenge

How can changing distress signals be identified early while keeping responsibility and intervention with humans?

---

Our Solution

SAHAYA creates a human-in-the-loop support pipeline connecting well-being monitoring with authorised human intervention.

Well-being Check-in
        ↓
ML Analysis
        ↓
Priority Classification
        ↓
Human Escalation
        ↓
Support / Counselling
        ↓
Audit Record

The platform combines local machine learning, deterministic prioritisation, Gemini-powered assistance and a strict administrative hierarchy.

AI provides the signal. Humans make the decision.

---

How It Works

1. Role-Based Access

Role-specific access is provided for:

- Victims / Users
- Counsellors
- District Administrators
- State Administrators
- National Administrators

2. Well-Being Check-In

Users can submit open-ended responses through supported text, voice and AI-assisted interactions.

3. Machine-Learning Analysis

Responses are processed using a supplied TF-IDF + Logistic Regression baseline with a supplemental DistilBERT emotion classifier.

4. Priority Classification

The system converts available signals into operational priorities:

HIGH
STANDARD
REVIEW

5. AI Support

Google Gemini provides calm, policy-constrained assistance and does not perform medical or psychological diagnosis.

6. Human Escalation

Relevant support activity is routed to counsellors or authorised administrators according to role and assignment.

7. Case & Activity Tracking

Check-ins, support requests, case documents and relevant actions are recorded for authorised access.

---

Key Technical Highlights

Human-in-the-Loop AI

SAHAYA separates AI-generated signals from final human decisions.

AI Signal
   ↓
Priority Logic
   ↓
Human Review
   ↓
Human Action

Local ML Baseline

The baseline pipeline uses:

Text Response
     ↓
TF-IDF Vectorisation
     ↓
Logistic Regression
     ↓
Prediction + Confidence

Supplemental Emotion Model

SAHAYA uses:

bhadresh-savani/distilbert-base-uncased-emotion

The model provides an additional emotional signal across:

- sadness
- joy
- love
- anger
- fear
- surprise

The model is not a distress classifier or clinical diagnostic model.

Administrative Hierarchy

National Administrator
          ↓
State Administrator
          ↓
District Administrator
          ↓
Counsellor

Backend scope checks enforce the hierarchy rather than relying only on frontend visibility.

Voice Support

Voice interaction supports browser speech recognition with a server-side Gemini transcription fallback.

"pyttsx3" is used for text-to-speech / Read Aloud.

---

Tech Stack

Layer| Technology
Frontend| React + TypeScript
Styling| TailwindCSS
HTTP Client| Axios
Backend| FastAPI + Python
ORM| SQLAlchemy
Validation| Pydantic
Database| SQLite → PostgreSQL
Authentication| JWT + bcrypt
Machine Learning| scikit-learn
NLP| TF-IDF + Logistic Regression
Emotion Model| DistilBERT
AI Support| Google Gemini API
Voice| SpeechRecognition + Gemini
Text-to-Speech| pyttsx3

Planned: Twilio-based OTP authentication.

---

System Architecture

flowchart TB

    USER[Victim / User]

    subgraph FRONTEND["Frontend"]
        UI[React + TypeScript]
        CHECK[Well-being Check-in]
        DASH[Role Dashboards]
        CASE[Case Documents]
    end

    subgraph BACKEND["FastAPI Backend"]
        AUTH[Authentication & RBAC]
        API[REST API]
        ML[ML Inference]
        PRIORITY[Priority Engine]
        SUPPORT[Support & Escalation]
    end

    subgraph AI["AI / ML"]
        LR[TF-IDF + Logistic Regression]
        BERT[DistilBERT]
        GEMINI[Google Gemini]
    end

    DB[(SQLite / PostgreSQL)]

    USER --> UI

    UI --> CHECK
    UI --> DASH
    UI --> CASE

    CHECK --> API
    CASE --> API
    DASH --> AUTH

    API --> LR
    API --> BERT
    API --> GEMINI

    LR --> PRIORITY
    BERT --> PRIORITY

    PRIORITY --> SUPPORT

    AUTH --> DB
    SUPPORT --> DB

---

Getting Started

Prerequisites

- Python 3.10+
- Node.js and npm
- Git
- Gemini API key for AI features

Clone the Repository

git clone https://github.com/Nil-0107/SAHAYA_1.0.git
cd SAHAYA_1.0

Backend Setup

cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

Gemini Configuration

Create "backend/.env":

GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash

Restart FastAPI after changing the environment file.

Frontend Setup

cd frontend
npm install
npm run dev

The frontend expects:

http://127.0.0.1:8000/api/v1

Development Database

SAHAYA_ENV=development python3 -m app.db.init_db
SAHAYA_ENV=development python3 -m app.demo.seed_demo

Or:

SAHAYA_ENV=development ./scripts/seed-demo.sh

---

Usage

Victim / User

- Complete well-being check-ins
- Submit text or voice responses
- Receive AI-assisted support
- Upload case documents
- Request human support
- View authorised well-being information

Counsellor

- View assigned users
- Receive relevant case notifications
- Review authorised support information

Administrators

- Manage the administrative hierarchy
- Manage counsellor assignments
- Review authorised cases
- Monitor support requests and notifications

Demo accounts are available in:

docs/DEMO_ACCOUNTS.md

All demonstration data is synthetic and development-only.

---

Testing & Auditing

The development environment supports testing of:

- Authentication and role-based access
- Administrative scope enforcement
- Counsellor assignment
- Case creation
- Document uploads
- Support-request routing
- Notifications
- ML predictions and confidence
- Gemini integration
- Voice transcription
- Database seeding

The ML and AI components provide assistive signals only and are not clinical diagnostic systems.

---

Project Structure

SAHAYA_1.0/
│
├── backend/
├── frontend/
├── docs/
├── scripts/
│
├── logistic_regression_emotion_model(1).joblib
├── tfidf_vectorizer(1)(1).joblib
│
├── SAHAYA_OPENCODE_MASTER_BUILD_SPEC.md
├── WINDOWS_SETUP.md
├── backend_sahaya.pdf
├── prd_sahaya(1).pdf
├── ui_sahaya.pdf
├── sahaya_dynamic_distress_ui_updated.html
│
├── package-lock.json
├── .gitattributes
├── .gitignore
└── README.md

---

Impact & Benefits

Social

- Continuous well-being monitoring
- Earlier visibility of changing support needs
- Human-centred intervention
- Accessible text and voice interaction

Institutional

- Structured support workflow
- Role-scoped case access
- Faster support routing
- Centralised notifications and records

Responsible AI

- Human-in-the-loop decision making
- Explainable ML signals
- No autonomous diagnosis
- Server-side AI processing

Operational

- Automated notifications
- Case-document management
- Administrative hierarchy
- Confidence and trend tracking

---

Future Scope

- Twilio OTP authentication
- PostgreSQL production deployment
- Multilingual Indian-language support
- Improved domain-specific ML models
- Longitudinal well-being analytics
- Android / iOS application
- Professional counselling-service integration
- Advanced audit and reporting
- Production-grade security and encryption

---

Research & References

SAHAYA uses established open-source and AI technologies including:

- scikit-learn — TF-IDF and Logistic Regression
- Hugging Face DistilBERT — Emotion classification
- DAIR.AI Emotion Dataset — Six-class emotion data
- Google Gemini API — AI support and transcription
- FastAPI — Backend API
- React + TypeScript — Frontend
- SQLAlchemy — Database ORM

---

Smart India Hackathon 2026

Field| Details
Project| SAHAYA
Problem Statement| SIH26094
Theme| MedTech / HealthTech
Category| Software
Hackathon| Smart India Hackathon 2026
Team| CodeYappers

---

Team

Member| Role
Swapnil Das| Team Lead / Backend & Architecture
Udit Prasad| Backend
Joy Saha| Frontend
Debolina Ghosal| Frontend
Anupama Modak| PPT Presenter
Ankona Gope| Pitching & Presenting

Mentor

Indranil Sarkar — CSE Department

---

License

Distributed under the MIT License.

See the "LICENSE" file for more information.

---

<p align="center">
  <strong>SAHAYA — The AI flags. A human decides.</strong>
  <br>
  Smart India Hackathon 2026 · Team CodeYappers
</p>
