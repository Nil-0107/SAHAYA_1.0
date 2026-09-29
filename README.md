SAHAYA — The AI flags. A human decides.

<p align="center">
  <strong>AI-powered Dynamic Mental Health Monitoring & Distress Support Platform</strong>
</p><p align="center">
  <img src="https://img.shields.io/badge/Smart%20India%20Hackathon-2026-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/PS-SIH26094-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/Category-Software-success?style=for-the-badge">
  <img src="https://img.shields.io/badge/Theme-MedTech%20%2F%20HealthTech-purple?style=for-the-badge">
</p><p align="center">
  <strong>Team CodeYappers</strong>
</p>---

📌 Table of Contents

- "About The Project" (#-about-the-project)
- "The Problem" (#-the-problem)
- "Our Solution" (#-our-solution)
- "How It Works" (#-how-it-works)
- "Tech Stack" (#-tech-stack)
- "System Architecture" (#-system-architecture)
- "Getting Started" (#-getting-started)
- "Usage" (#-usage)
- "Testing & Auditing" (#-testing--auditing)
- "Project Structure" (#-project-structure)
- "Impact & Benefits" (#-impact--benefits)
- "Future Scope" (#-future-scope)
- "Research & References" (#-research--references)
- "Team" (#-team)
- "License" (#-license)

---

🧠 About The Project

SAHAYA is an AI-powered dynamic well-being monitoring and support platform designed for victims and complainants under the SC/ST (Prevention of Atrocities) Act throughout investigation, trial, and rehabilitation.

Legal cases move through milestones, but a person's well-being can change continuously.

SAHAYA provides:

- Consent-based periodic well-being check-ins
- Text, voice, and AI-assisted interaction
- Explainable ML-based emotional signals
- Deterministic priority classification
- Human-routed escalation
- Role-based dashboards
- Case-document management
- Notifications and audit-oriented records

«The AI flags. A human decides.»

SAHAYA is a support tool, not a diagnostic system. All demonstration data is synthetic.

---

⚠️ The Problem

A legal case can progress from investigation to trial while the victim's changing well-being remains difficult to monitor.

Existing gaps

- No continuous well-being monitoring between case milestones
- Support requests can remain disconnected from case workflows
- Manual prioritisation of support needs
- Fragmented access to case and support information
- Limited coordination between victims, counsellors and administrators
- Risk of AI systems making opaque or inappropriate decisions

«The challenge: identify changing distress signals early while keeping the final decision with a human.»

---

💡 Our Solution

SAHAYA creates a human-in-the-loop support pipeline:

Check-in
   ↓
ML Analysis
   ↓
Priority Classification
   ↓
Human Escalation
   ↓
Counselling / Support
   ↓
Audit Record

The system combines local ML inference, rule-based prioritisation, Gemini-powered assistance, and a strict administrative hierarchy.

AI provides signals — humans take action.

---

🔄 How It Works

1. Role-Based Access

Victims, counsellors, district, state and national administrators receive role-specific access.

2. Well-being Check-in

Users submit open-ended responses through text, voice or supported AI interaction.

3. ML Analysis

Responses are processed using a TF-IDF + Logistic Regression baseline, with a supplemental DistilBERT emotion model.

4. Priority Engine

Signals are converted into operational priorities:

HIGH
STANDARD
REVIEW

5. AI Support

Gemini provides calm, policy-constrained assistance without diagnosing the user.

6. Human Escalation

Relevant cases are routed to counsellors or authorised administrators according to role and assignment.

7. Case & Audit Tracking

Check-ins, support requests, case documents and relevant actions are recorded for authorised access.

---

🛠️ Tech Stack

Layer| Technology
Frontend| React + TypeScript
Styling| TailwindCSS
HTTP| Axios
Backend| FastAPI + Python
ORM| SQLAlchemy
Validation| Pydantic
Database| SQLite → PostgreSQL
Authentication| JWT + bcrypt
ML| scikit-learn
NLP| TF-IDF + Logistic Regression
Emotion Model| DistilBERT
AI Support| Google Gemini API
Voice| SpeechRecognition + Gemini
TTS| pyttsx3

«Twilio OTP integration is planned for a future release and is not required by the current implementation.»

---

🏗️ System Architecture

flowchart TB

    USER[Victim / User]

    subgraph FRONTEND["React + TypeScript"]
        UI[SAHAYA Interface]
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

    subgraph AI["AI Layer"]
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

    API --> ML
    ML --> PRIORITY
    ML --> BERT

    API --> GEMINI
    PRIORITY --> SUPPORT
    AUTH --> DB
    SUPPORT --> DB

---

🚀 Getting Started

Prerequisites

- Python 3.10+
- Node.js + npm
- Git
- Gemini API key for AI features

Clone

git clone https://github.com/Nil-0107/SAHAYA_1.0.git
cd SAHAYA_1.0

Backend

cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

Environment

Create "backend/.env":

GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash

Frontend

cd frontend
npm install
npm run dev

Frontend API:

http://127.0.0.1:8000/api/v1

---

🖥️ Usage

Victim / User

- Complete well-being check-ins
- Use text or voice input
- Receive AI-assisted support
- Upload case documents
- Request human support
- View authorised well-being information

Counsellor

- View assigned users
- Receive relevant case notifications
- Review authorised support information

Administrators

- Manage administrative hierarchy
- Manage counsellor assignments
- Review authorised cases and support requests
- Monitor notifications and escalations

Demo credentials are available in:

docs/DEMO_ACCOUNTS.md

All demo data is synthetic and development-only.

---

🧪 Testing & Auditing

SAHAYA includes development workflows for testing:

- Authentication and role-based access
- Administrative scope enforcement
- Case creation and document uploads
- Support-request routing
- Notifications
- ML predictions and confidence
- Gemini integration
- Voice transcription
- Demo database seeding

The ML models provide assistive signals only and are not clinical diagnostic systems.

---

📂 Project Structure

SAHAYA_1.0/
├── backend/
├── frontend/
├── docs/
├── scripts/
├── logistic_regression_emotion_model(1).joblib
├── tfidf_vectorizer(1)(1).joblib
├── SAHAYA_OPENCODE_MASTER_BUILD_SPEC.md
├── WINDOWS_SETUP.md
├── backend_sahaya.pdf
├── prd_sahaya(1).pdf
├── ui_sahaya.pdf
├── sahaya_dynamic_distress_ui_updated.html
├── package-lock.json
├── .gitignore
└── README.md

---

📈 Impact & Benefits

👤 Social

- Continuous well-being monitoring
- Earlier visibility of changing support needs
- Human-centred intervention
- Accessible text and voice interaction

🏛️ Institutional

- Structured support workflow
- Role-scoped case access
- Faster support routing
- Centralised notifications and records

🤖 Responsible AI

- Human-in-the-loop decision making
- Explainable ML signals
- No autonomous diagnosis
- Server-side AI processing

⚙️ Operational

- Automated notifications
- Case-document management
- Administrative hierarchy
- Confidence and trend tracking

---

🔮 Future Scope

- Twilio OTP authentication
- PostgreSQL production deployment
- Multilingual Indian-language support
- Improved domain-specific ML models
- Longitudinal well-being analytics
- Dedicated Android/iOS application
- Professional counselling-service integration
- Advanced audit and reporting
- Production-grade encryption and security controls

---

📚 Research & References

SAHAYA is built using established open-source and AI technologies:

- scikit-learn — TF-IDF & Logistic Regression
- Hugging Face DistilBERT — Emotion classification
- DAIR.AI Emotion Dataset — Six-class emotion data
- Google Gemini API — AI support and voice transcription
- FastAPI — Backend API
- React + TypeScript — Frontend
- SQLAlchemy — Database ORM

---

🏆 Smart India Hackathon 2026

Field| Details
Project| SAHAYA
Problem Statement| SIH26094
Theme| MedTech / HealthTech
Category| Software
Team| CodeYappers
Hackathon| Smart India Hackathon 2026

---

👨‍💻 Team

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

📄 License

Distributed under the MIT License.

See the "LICENSE" file for more information.

---

<p align="center">
  <strong>SAHAYA — The AI flags. A human decides.</strong>
  <br>
  Built for Smart India Hackathon 2026 by Team CodeYappers
</p>
