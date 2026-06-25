# Docker Setup

## What Docker Does For This Project

Docker packages the Agentic BI Copilot app with Python, dependencies, project files, generated runtime folders, and a startup command. This lets another person clone the repository and run the Streamlit app without manually creating a virtual environment.

The container starts from `python:3.11-slim`, installs the Python dependencies from `requirements.txt`, copies the project into `/app`, ensures runtime folders exist, creates `data/processed/business.db` if it is missing, and launches Streamlit on port `8501`.

## Files Added

- `Dockerfile`: Builds the Python image and defines the container startup command.
- `docker-compose.yml`: Defines the `agentic-bi-copilot` service and maps port `8501`.
- `.dockerignore`: Keeps local virtualenvs, Git metadata, generated databases, and generated outputs out of the image build context.
- `scripts/docker_start.py`: Ensures runtime folders and the sample database exist before launching Streamlit.

## Build And Run

From the project root:

```powershell
docker compose up --build
```

Then open:

```text
http://localhost:8501
```

## Stop The App

Press `Ctrl+C` in the terminal running Docker Compose, then run:

```powershell
docker compose down
```

## Troubleshooting Port 8501

If port `8501` is already in use, Docker Compose may fail to start the app or may report that the port is unavailable.

Options:

- Stop the other local process using port `8501`.
- Stop another Streamlit session if one is already running.
- Change the left side of the port mapping in `docker-compose.yml`, for example:

```yaml
ports:
  - "8502:8501"
```

Then open `http://localhost:8502`.
