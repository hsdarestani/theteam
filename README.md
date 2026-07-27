# The Team Performance Hub

A private, brandable and multilingual coaching dashboard for squad status, player evaluations, training planning, match tracking, calendar overview and printable reports.

This repository is based on the complete `hsdarestani/eintracht` application and adds a reusable team identity layer.

## Team identity administration

After creating the first administrator at `/setup/`, open:

- `/admin/core/teamidentity/1/change/`

The singleton **Team identity** panel can change the application without editing source code:

- team name, short name, application name and tagline
- PNG, JPG or WebP team logo
- primary, dark-primary, secondary, background, surface and text colors
- German, English, Arabic or Persian interface language
- automatic or explicit LTR/RTL direction
- custom phrase translations through JSON
- optional advanced CSS overrides

Uploaded identity assets are stored on the persistent Docker volume `team_media`.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/setup/` to create the first administrator account. A fictional demo squad is created automatically.

## Production

Production uses Docker Compose with Django, PostgreSQL and Caddy. Caddy obtains and renews the TLS certificate for `team.smarbiz.sbs` automatically.

GitHub Actions deploys pushes to `main` using repository secrets:

- `HOST`: `5.75.203.165` or the production server hostname
- `PASS`: root SSH password

The deployment directory is `/opt/theteam`. The first deployment creates `/opt/theteam/.env` with random application and database secrets.

## Privacy baseline

- No public application API
- HTTPS and HSTS
- Secure session and CSRF cookies
- PostgreSQL data stays on the assigned server
- No analytics, tracking pixels or external font requests
- Pages are marked `noindex,nofollow`

A formal GDPR review, retention policy and role/permission concept should be completed before storing real athlete health or sensitive performance data.
