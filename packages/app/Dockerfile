FROM public.ecr.aws/docker/library/python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apt-get update && \
  apt-get install -y --no-install-recommends gcc git wget curl

# install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

# copy source code
COPY . /app
RUN uv sync --frozen --no-install-project --no-dev

# copy env
COPY env/dev.env /app/.env

ENTRYPOINT []

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uv", "run", "--", "chainlit", "run", "app.py"]
