# Use Python 3.12 slim image as base
FROM python:3.12-slim AS base

# Install system dependencies required for PyMuPDF and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Make uv executable
RUN chmod +x /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (creates .venv automatically)
RUN uv sync --frozen --no-dev

# Copy application code and configuration
COPY main.py ./
COPY utils/ ./utils/
COPY prompt_registry/ ./prompt_registry/
COPY .streamlit/ ./.streamlit/

# Expose Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check for the container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Use uv to run the Streamlit app
# uv run automatically activates the virtual environment
CMD ["uv", "run", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

