FROM python:3.12-slim-bookworm

ENV POETRY_VERSION=1.3.1 \
  POETRY_HOME="/opt/poetry/home" \
  POETRY_CACHE_DIR="/opt/poetry/cache" \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=false

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install --no-install-recommends -y curl \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install poetry using the official installer
RUN curl -sSL https://install.python-poetry.org | python

# Limit amount of concurrent install requests, to avoid hitting pypi rate-limits
RUN poetry config installer.max-workers 10

# Install project dependencies
WORKDIR /scraper
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-interaction --no-ansi -vvv

# Copy the source code in last to optimize rebuilding the image
COPY . .

ENTRYPOINT ["poetry"]
CMD ["run", "python", "-m", "src"]
