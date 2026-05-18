# Cyber Cafe Management System

A small Flask app for managing cyber cafe logins, station sessions, retail POS, customer registrations with Aadhaar upload, and customer rankings.

## Project structure

- `app.py` - Flask application entry point
- `templates/` - Jinja HTML templates
- `requirements.txt` - Python dependencies

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`

## Default login

- Admin: `admin / admin123`
- User: `user1 / user123`

## User registration

- New users can create their own account from the login page.
- Aadhaar card upload is mandatory during account creation.
- Uploaded Aadhaar files are stored in `static/uploads/aadhaar/`.

## Environment variables

- `SECRET_KEY` - Flask session secret for production
- `HOST` - server host, default `0.0.0.0`
- `PORT` - server port, default `5000`
- `FLASK_DEBUG` - set to `0` in production
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GOOGLE_ADMIN_EMAIL` - optional email to treat as admin after Google sign-in
- `PAYMENT_UPI_ID` - UPI ID encoded into the QR payment screen
- `PAYMENT_RECEIVER` - display name shown on the QR payment screen
- `PAYMENT_QR_IMAGE_URL` - optional fixed QR image URL if you do not want generated UPI QR links

## Deploying live

GitHub hosts your code, but it does not run Flask apps by itself. Push this repository to GitHub, then deploy it on a Python host such as Render, Railway, or PythonAnywhere.

Recommended start command:

```bash
gunicorn app:app
```

Set these environment variables on the host:

- `SECRET_KEY` to a strong random value
- `FLASK_DEBUG=0`
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` if you want Google login enabled

### Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/cqmystic/cybercafe.git
git push -u origin main
```

### Make it live on Render

1. Push the code to GitHub.
2. Open Render and create a new `Web Service` from the GitHub repo.
3. Use these settings:
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `gunicorn app:app`
4. Add the environment variables from `.env.example` except keep real secrets only in Render.
5. Add your live Google redirect URI after deploy: `https://your-render-url.onrender.com/auth/google/callback`
6. Redeploy after saving the environment variables.

## Google sign-in setup

1. Create OAuth credentials in Google Cloud Console.
2. Add an authorized redirect URI:
	- `http://127.0.0.1:5000/auth/google/callback` for local use
	- your live domain plus `/auth/google/callback` for production
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your environment.
4. Optionally set `GOOGLE_ADMIN_EMAIL` if one Google account should open the admin dashboard.

## Payment proof flow

1. Add items in Retail POS.
2. Continue to the QR payment screen.
3. Let the customer scan the QR and pay.
4. Upload the payment screenshot.
5. Review it in the admin Payments page and mark it verified or rejected.

## Notes

- This app currently stores data in memory, so restarting the server resets sessions and activity.
- Uploaded screenshots are stored in `static/uploads/payments/`.
- Aadhaar uploads are stored in `static/uploads/aadhaar/`.
- Station sessions support preset or custom durations such as 1 hour 20 minutes, billed pro-rata.
- For real production use, the next step is moving users, sessions, and sales into a database.