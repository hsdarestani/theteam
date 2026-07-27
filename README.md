# Team Performance Hub

A private, German-language coaching dashboard focused on simple workflows for squad status, player evaluations, training planning, match tracking, calendar overview and printable reports.

## Product principles

- One primary action per screen
- Core coaching decisions visible before detailed data
- Four-value player evaluation: mentality, physicality, performance and potential
- Attendance changes saved with one click
- Internal calendar without third-party API sharing
- Print/PDF-friendly reports with trainer comments
- First-run setup instead of a shared default password

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/setup/` to create the first trainer account. A demo squad and example data are created automatically.

## Production

Production uses Docker Compose with Django, PostgreSQL and Caddy. Caddy obtains and renews the TLS certificate for `eintracht.smarbiz.sbs` automatically.

GitHub Actions deploys pushes to `main` using repository secrets:

- `HOST`: production server IP or hostname
- `PASS`: root SSH password

The first deployment creates `/opt/eintracht/.env` with random application and database secrets. The first trainer account is created interactively at `/setup/`.

## Privacy baseline

- No public application API
- HTTPS and HSTS
- Secure session and CSRF cookies
- PostgreSQL data stays on the assigned server
- No analytics, tracking pixels or external font requests
- Pages are marked `noindex,nofollow`

This is an application baseline; a formal GDPR review, retention policy and role/permission concept should be completed before storing real athlete health or sensitive performance data.
