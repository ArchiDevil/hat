# HAT - Human Assisted Translator project

This is a CAT to work with texts. Now in experimental stage. Uses Python and
Quart as a backend library.

## Running the development server

To run development server navigate to `backend` directory and create virtual
environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

Then run Quart dev server:

```bash
python3 app/app.py
```

You will need PostgreSQL server running on a local machine. Set up connection
string to the environment variable `DATABASE_URL` or update `__init__.py` file.

## Running the production version

Before setting up the production version you need to adjust environment configs.
To do this copy `.env.example` to `.env` and fill in all needed variables.

Also you have to adjust `alembic.ini` file to match your database settings. It
is located in `backend` directory.

To run production version of the tool you need to use `docker compose`:

```bash
docker-compose up -d --build
```

This will build all needed images and run services in detached mode. Please
note that reverse proxy is listening to `80` port on the localhost, so you need
to set up something to listed on the domain name if you need.

The production version is located (or will be if not yet) at
https://hat.codecliffs.ru
