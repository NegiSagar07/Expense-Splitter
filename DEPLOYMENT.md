# 🚀 Expense Splitter — Production Deployment Guide (Render + Docker)

This guide covers deploying the Expense Splitter backend to **Render's Free Tier** using Docker and PostgreSQL.

---

## 📋 Prerequisites

1. A **GitHub** or **GitLab** account with this repository pushed.
2. A free **Render** account ([render.com](https://render.com)).
3. A free **UptimeRobot** account ([uptimerobot.com](https://uptimerobot.com)) for keep-alive pings.

---

## ⚡ Option 1: Automatic Deployment using Render Blueprint (Recommended)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your repository (`Expense-Splitter`).
4. Render will automatically detect `render.yaml` and provision:
   - **PostgreSQL Database** (`expense-splitter-db`)
   - **Docker Web Service** (`expense-splitter-api`)
5. Click **Apply**. Render will build the Docker container and automatically run `alembic upgrade head` before launching.

---

## 🛠️ Option 2: Manual Deployment via Render Dashboard

If you prefer to configure manually:

### Step 1: Create PostgreSQL Database
1. Go to **Render Dashboard** → **New +** → **PostgreSQL**.
2. Set:
   - **Name**: `expense-splitter-db`
   - **Database**: `expense_splitter_db`
   - **User**: `expense_user`
   - **Plan**: Free
3. Copy the **Internal Database URL** (e.g. `postgresql://expense_user:...@dpg-xxx-a/expense_splitter_db`).

### Step 2: Create Web Service
1. Go to **Render Dashboard** → **New +** → **Web Service**.
2. Connect your repository.
3. Set configuration:
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Pre-Deploy Command**: `alembic upgrade head`
4. Add **Environment Variables**:
   - `DATABASE_URL` = *(Internal Database URL copied from Step 1 — change prefix from `postgres://` to `postgresql+asyncpg://`)*
   - `SECRET_KEY` = *(Generate a secure random string: `openssl rand -hex 32`)*
   - `ALGORITHM` = `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `30`
   - `ALLOWED_ORIGINS` = `http://localhost:3007,https://your-frontend-domain.onrender.com`
   - `JOIN_REQUEST_EXPIRY_DAYS` = `7`
   - `DEBUG` = `false`
5. Click **Create Web Service**.

---

## ⏰ Step 3: Prevent Render Free Tier Sleep (Keep-Alive Setup)

Render's free web services spin down after 15 minutes of inactivity. To keep your API fast and responsive for you and your friends:

1. Sign up at [UptimeRobot.com](https://uptimerobot.com) (free).
2. Click **Add New Monitor**:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `Expense Splitter API Health`
   - **URL (or IP)**: `https://your-app-name.onrender.com/api/v1/health`
   - **Monitoring Interval**: Every 5 or 10 minutes
3. Click **Create Monitor**.

This sends a periodic GET request to `/api/v1/health` returning `{"status": "ok"}`, keeping your service awake 24/7 at $0 cost!

---

## 🧪 Post-Deployment Verification

Once deployed, test your live API endpoints:

```bash
# 1. Health check
curl https://your-app-name.onrender.com/api/v1/health

# 2. Interactive Swagger Docs
https://your-app-name.onrender.com/api/docs
```

---

## 🔄 Applying Database Migrations in Production

Every time you push a commit with new Alembic migrations to GitHub, Render automatically triggers `alembic upgrade head` during the pre-deploy phase before launching the updated container!
