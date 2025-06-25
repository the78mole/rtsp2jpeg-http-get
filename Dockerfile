FROM python:3.12-slim

# Install dependencies for OpenCV (minimal, no GUI)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set workdir
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install project with uv
RUN uv pip install --system -e .

# Expose port (optional)
EXPOSE 8080

ENV PYTHONUNBUFFERED=1

# Default command
CMD ["rtsp2jpeg"]

