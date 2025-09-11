FROM python:3.10-slim

# Fetch OS packages updates, upgrade packages, and install packages required for build
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get install -y \
    --no-install-recommends gcc build-essential python3-dev vim zsh curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama 
RUN curl -fsSL https://ollama.com/install.sh | sh

RUN ollama --version

# Create app directory
WORKDIR /app

# Install Python requirements
COPY pyproject.toml ./pyproject.toml
RUN pip install .

# Copy application code
COPY . .

EXPOSE 8000
EXPOSE 11434

RUN chmod +x start.sh

CMD ["./start.sh"]