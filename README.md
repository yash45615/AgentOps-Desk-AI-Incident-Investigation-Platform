# AgentOps Desk

**A developer-focused incident investigation and observability workspace.**

AgentOps Desk is a full-stack application for managing software incidents, collecting supporting evidence, running agent-assisted investigations, and tracking audit events through a modern dashboard.

It combines a Python FastAPI backend with a React and TypeScript frontend to provide a structured workspace for investigating incidents and organizing technical findings.

## Features

- **Incident Management** — Create, view, search, and manage software incidents.
- **Evidence Collection** — Associate evidence with incidents to keep relevant investigation information organized.
- **Agent-Assisted Investigations** — Run investigations against incident context and review the resulting findings.
- **Audit Events** — Expose audit events through a dedicated API endpoint.
- **REST API** — Build and interact with incident-management functionality through FastAPI endpoints.
- **Interactive Dashboard** — Browse incidents, filter by severity and status, and inspect related evidence and investigations.
- **API Security** — Protect agent and audit API routes using API-key authentication.
- **Automated Testing** — Validate backend behavior with a pytest test suite.
- **Code Quality Checks** — Use Ruff for Python linting and formatting, and Oxlint for frontend linting.

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest
- Ruff

### Frontend
- React
- TypeScript
- Vite
- Lucide React
- Oxlint

## Architecture

```text
AgentOps Desk
│
├── Backend
│   ├── FastAPI application
│   ├── Incident management API
│   ├── Evidence API
│   ├── Investigation API
│   ├── Agent API
│   ├── Audit events API
│   ├── SQLAlchemy data layer
│   └── API-key security
│
└── Frontend
    ├── React dashboard
    ├── Incident list and filters
    ├── Incident details
    ├── Evidence management
    ├── Investigation results
    └── API client
```

## Getting Started

### Prerequisites

Install the following before running the application:

- Python 3.11 or a compatible version supported by the project
- Node.js and npm
- Git

Use the Python version specified in the project's dependency or project configuration if it differs from the version above.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AgentOpsDesk
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your repository's actual URL.

### 2. Set up the backend

From the project root, create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project's dependencies using the dependency file included in the repository. For example, if it uses `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

If the project uses a different dependency manager or file, follow its configuration instead.

Configure any required environment variables according to the project's settings. Do not commit real API keys, passwords, or local environment files.

### 3. Start the backend

From the project root:

```powershell
python -m uvicorn app.main:app --reload
```

The API should be available at:

- API base: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 4. Set up the frontend

Open a second terminal:

```powershell
cd frontend
npm install
```

Start the development server:

```powershell
npm run dev
```

Open the local URL printed by Vite, usually:

`http://localhost:5173`

Ensure the backend is running and that the frontend API base URL is configured correctly for your local environment.

## API Overview

The application exposes endpoints for incident management, evidence collection, investigations, agent operations, and audit events.

| Endpoint | Purpose |
|---|---|
| `/api/v1/incidents` | Incident management |
| `/api/v1/incidents/{incident_id}/evidence` | Evidence associated with an incident |
| `/api/v1/incidents/{incident_id}/investigations` | Investigations associated with an incident |
| `/api/v1/audit/events` | Retrieve audit events |

The audit events endpoint is registered in the FastAPI application. Agent and audit routes use API-key protection, so valid authentication configuration may be required to access them.

For exact request schemas, parameters, and available operations, see the interactive API documentation at `/docs`.

## Running Tests

From the project root, activate the virtual environment and run:

```powershell
python -m pytest -q
```

Run Python linting:

```powershell
ruff check app
```

Check Python formatting:

```powershell
ruff format --check app
```

For frontend verification:

```powershell
cd frontend
npm run build
npm run lint
```

The backend verification completed during development with **42 passing tests**. The frontend production build also succeeded. Frontend linting reported two React effect warnings, which remain known cleanup items.

## Security Notes

- Keep API keys and secrets out of source control.
- Store local environment configuration in an ignored `.env` file where appropriate.
- Use a valid API key when accessing protected endpoints.
- Review CORS and authentication configuration before exposing the application beyond local development.
- Do not use development server settings as a substitute for production deployment hardening.

## Project Goals

AgentOps Desk explores practical software engineering concepts including:

- REST API design
- Full-stack application development
- Relational data modeling
- Incident and evidence management
- Agent-assisted investigation workflows
- API authentication
- Audit event access
- Automated testing and code quality

## Current Status

The core application has been implemented and locally verified.

- Backend: **42 tests passing**
- Python linting: **Passed**
- Python formatting: **Passed**
- Frontend production build: **Passed**
- Frontend linting: Two non-blocking React effect warnings remain

These results reflect the development verification performed locally; they do not imply production deployment or independent security certification.

## Future Improvements

Potential next steps include:

- Add a dedicated audit-event viewer to the dashboard.
- Expand automated tests for API failures and edge cases.
- Improve loading and error-state handling in the frontend.
- Add deployment configuration and CI checks.
- Include screenshots and a short demonstration of the investigation workflow.

## License

Choose a license before distributing the project. If you intend to make the repository open source, consider adding an appropriate `LICENSE` file.
