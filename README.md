# LeadHive Automation

LeadHive Automation is a production-ready full-stack SaaS starter for ethical web design outreach. It collects public business data, analyzes websites for concrete quality issues, generates personalized outreach drafts, tracks outreach status, exports CSV files, and keeps controlled email sending disabled until you explicitly enable it.

## What It Does

- Accepts a city and business niche.
- Collects public business records from OpenStreetMap/Nominatim/Overpass data.
- Stores business name, website, public email, phone, address, and source URL.
- Scores websites from 0 to 100.
- Detects missing HTTPS, missing mobile viewport, missing title/meta description, weak CTA visibility, slow load speed, outdated structure, and missing contact form.
- Generates non-spammy personalized email drafts using the real business name and detected issues.
- Stores data in SQLite locally or PostgreSQL in production.
- Exports leads to CSV with Pandas.
- Provides an authenticated React dashboard for leads, scores, statuses, drafts, and sending.
- Supports SMTP/Gmail sending with rate limiting, opt-out text, and logging.
- Keeps sending disabled by default.

## Project Structure

```text
LeadHive Automation/
├── analyzer/
│   ├── __init__.py
│   └── website_analyzer.py
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── deps.py
│   │   │   ├── email.py
│   │   │   ├── export.py
│   │   │   ├── jobs.py
│   │   │   └── leads.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── lead.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── email.py
│   │   │   ├── jobs.py
│   │   │   └── leads.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── lead_pipeline.py
│   │   │   └── serializers.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── Procfile
│   ├── __init__.py
│   └── requirements.txt
├── dashboard/
│   └── README.md
├── database/
│   └── init.sql
├── email_generator/
│   ├── __init__.py
│   └── generator.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LeadDetail.tsx
│   │   │   ├── LeadTable.tsx
│   │   │   ├── SearchPanel.tsx
│   │   │   ├── StatCard.tsx
│   │   │   └── StatusBadge.tsx
│   │   ├── pages/
│   │   │   ├── AuthPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── api.ts
│   │   ├── utils/
│   │   │   └── download.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vercel.json
│   └── vite.config.ts
├── scraper/
│   ├── __init__.py
│   └── public_sources.py
├── sender/
│   ├── __init__.py
│   └── smtp_sender.py
├── templates/
│   └── outreach_email.txt
├── .gitignore
├── railway.json
├── render.yaml
└── README.md
```

## Ethical Outreach Defaults

LeadHive is intentionally conservative:

- It only reads public sources and public websites.
- It does not bypass logins, captchas, or paywalls.
- It checks robots.txt before automated website review.
- It creates drafts first.
- It disables email sending by default.
- It includes opt-out text in every generated email.
- It supports manual status tracking for sent, draft, replied, bounced, and opted-out leads.

## Run Locally on Windows with VS Code

### 1. Install Prerequisites

Install these first:

- Python 3.11 or newer
- Node.js 20 or newer
- Git
- VS Code

Optional but useful VS Code extensions:

- Python
- Pylance
- Tailwind CSS IntelliSense
- ESLint

### 2. Open the Project

Open VS Code, then choose **File > Open Folder** and select this project folder.

Open a VS Code terminal with **Terminal > New Terminal**.

### 3. Configure the Backend

From the project root:

```powershell
copy backend\.env.example backend\.env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

If your Windows drive has limited free space, use the lightweight local install instead. It skips the larger optional production packages while keeping the app runnable:

```powershell
pip install -r backend\requirements-local.txt
```

If PowerShell blocks the virtual environment activation, run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Update `backend\.env` and set a long random `SECRET_KEY`.

Keep this for local SQLite:

```env
DATABASE_URL=sqlite:///./database/leadhive.db
EMAIL_SENDING_ENABLED=false
```

Install Playwright browsers only if you want Playwright fallback analysis:

```powershell
playwright install chromium
```

Then set:

```env
ENABLE_PLAYWRIGHT_ANALYSIS=true
```

### 4. Start the Backend

Run this from the project root:

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the health check:

```text
http://127.0.0.1:8000/health
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

### 5. Configure the Frontend

Open a second VS Code terminal:

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Create an account from the app. Search for a city and niche, for example:

```text
City: Austin, Texas
Business niche: dentist
Limit: 10
```

The first search can take time because it fetches public records and analyzes each website.

## Optional Email Sending

Email sending is disabled by default. Leave it disabled until you have reviewed your outreach process, obtained any necessary consent, and confirmed compliance with your local laws and provider policies.

To enable SMTP/Gmail sending, set these in `backend\.env`:

```env
EMAIL_SENDING_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail-address@gmail.com
SMTP_PASSWORD=your-google-app-password
SMTP_FROM_EMAIL=your-gmail-address@gmail.com
SMTP_FROM_NAME="Your Agency"
EMAIL_RATE_LIMIT_PER_HOUR=20
UNSUBSCRIBE_TEXT="If this is not relevant, reply with 'unsubscribe' and we will not contact you again."
```

For Gmail, use a Google App Password, not your normal account password.

## CSV Export

Click the download icon in the dashboard header. The frontend calls:

```text
GET /api/export/leads.csv
```

The CSV includes business details, score, detected issues, email status, and the generated outreach draft.

## Database Notes

Local development uses SQLite:

```text
database/leadhive.db
```

Production should use PostgreSQL:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
```

The app creates tables on startup through SQLAlchemy. `database/init.sql` is included for review and manual database setup.

## Backend API

Main endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/jobs/search`
- `GET /api/leads`
- `GET /api/leads/{lead_id}`
- `PATCH /api/leads/{lead_id}/status`
- `POST /api/leads/opt-out`
- `POST /api/email/send/{lead_id}`
- `GET /api/export/leads.csv`

## Deployment: Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and select the repository.
3. Render will read `render.yaml`.
4. Set `FRONTEND_ORIGIN` to your deployed frontend URL.
5. Keep `EMAIL_SENDING_ENABLED=false` for the first deploy.
6. Deploy.

Render will provision PostgreSQL and pass the database connection string to the backend.

## Deployment: Railway

1. Push this repository to GitHub.
2. Create a new Railway project from the repository.
3. Add a PostgreSQL database.
4. Set environment variables:

```env
APP_ENV=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=use-a-long-random-secret
FRONTEND_ORIGIN=https://your-frontend-domain.com
EMAIL_SENDING_ENABLED=false
```

5. Railway will use `railway.json` to start the FastAPI app.

## Deployment: Vercel Frontend

1. Import the repository into Vercel.
2. Set the project root to `frontend`.
3. Set environment variable:

```env
VITE_API_URL=https://your-backend-url.com
```

4. Deploy.
5. Update backend `FRONTEND_ORIGIN` to the Vercel URL.

## Production Checklist

- Replace `SECRET_KEY`.
- Use PostgreSQL.
- Set `FRONTEND_ORIGIN` exactly.
- Keep sending disabled until legal/compliance review is complete.
- Configure real agency identity in email templates.
- Add Redis-backed rate limiting before running multiple backend instances.
- Add Alembic migrations before heavy production use.
- Add monitoring and request logs on the hosting provider.
- Review public-source API usage policies for your traffic volume.
