FROM python:3.8-slim as base

WORKDIR /opt/colab_ssh
RUN apt update && apt install -y curl sshfs unzip
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
  && unzip awscliv2.zip && ./aws/install && rm awscliv2.zip
RUN export POETRY_HOME=/opt/poetry && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
  && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry update
COPY ./app ./app
COPY ./documentation/openapi.yaml ./documentation/


FROM base AS build

RUN poetry install --no-root --no-dev
CMD uvicorn app.main:app --host "0.0.0.0" --port ${APP_PORT:-8080}


FROM base AS test

RUN poetry install --no-root
COPY tests ./tests
RUN isort --check --profile=black --line-length=79 .
RUN black --check --line-length=79 .
RUN flake8 app
RUN mypy --ignore-missing-imports --scripts-are-modules --allow-untyped-decorators --strict --no-strict-optional app/
RUN pylint --max-line-length=79 --errors-only --disable=E0401,E0611 app/
RUN python3 -m pytest --cov=app tests/


FROM base AS build_dev

RUN poetry install --no-root
CMD uvicorn app.main:app --host "0.0.0.0" --port ${APP_PORT:-8080} --reload
