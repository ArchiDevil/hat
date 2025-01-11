# HAT - Human Assisted Translator project

This is a CAT to work with texts. Now in experimental stage. Uses Python and
FastAPI as a backend library. For a frontend Vue with its stack is used.

## Running the backend

To run the backed navigate to `backend` directory and create virtual
environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install all dependencies:

```bash
pip install -r requirements.txt
python3 -m nltk.downloader punkt_tab
```

Then run FastAPI server:

```bash
uvicorn asgi:app
```

You will need PostgreSQL server running on a local machine. Set up connection
string to the environment variable `DATABASE_URL` or update `settings.py` file.

### Running backend's tests

To run tests you need to install `pytest` and `pytest-asyncio` packages. They
are already listed in `requirements.txt` file, so you if you installed all
dependencies from a previous section you are good to go.

It order to run tests you need to run `pytest` command from the `backend`
directory.

```bash
pytest
```

## Running the worker

To run the worker navigate to `backend` directory and create virtual environment
if not yet:

```bash
python3 -m venv.venv
source.venv/bin/activate
```

Then install all dependencies:

```bash
pip install -r requirements.txt
python3 -m nltk.downloader punkt_tab
```

Then run the worker:

```bash
python3 worker.py
```

The worker is being tested by the same test suite as the backend.

## Running the frontend

To run the frontend you need to install all dependencies first. Navigate to
`frontend` directory and run:

```bash
pnpm install
```

Then you can run the development server:

```bash
pnpm run dev
```

This will start the development server on `localhost:5173` address. Open your
browser and check the website. When development server is run you need to run
backend server as well.

### Running frontend's tests

To run frontend's tests you need to run:

```bash
pnpm run test
```

## Running the production version

Before setting up the production version you need to adjust environment configs.
To do this copy `.env.example` to `.env` and fill in all needed variables.

Also you have to adjust `alembic.ini` file to match your database settings. It
is located in `backend` directory.

To run production version of the tool you need to use `docker-compose`:

```bash
docker-compose up -d --build
```

You can have two separate `.env` files for local testing and for production
deployment. To do this make two copies of `.env.template` with different names:
`.env-local` for local testing and `.env-prod` for production and specify
which file to use by setting `--env-file` parameter when running docker-compose.

```bash
docker-compose --env-file .env.prod up -d --build
```

This will build all needed images and run services in detached mode. Please
note that reverse proxy is listening to `6916` port on the localhost, so you
need to set up something to listed on the domain name if you need.

The production version is located at https://hat.codecliffs.ru

## Backend linting

To run linting for backend code execute the following command:

```bash
ruff format . && ruff check --select I --fix . && ruff check  --fix .
```
