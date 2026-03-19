# Use slim Debian Bookworm (stable) base image to avoid Trixie package issues
FROM python:3.11-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && apt-get install -y \
    build-essential \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libglib2.0-0 \
    git \
    curl \
    wget \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt .

# Install Python packages
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# # Install silero-vad from GitHub (fix: no space after git+)
# RUN git clone https://github.com/snakers4/silero-vad /tmp/silero-vad \
#     && pip install --no-cache-dir /tmp/silero-vad \
#     && rm -rf /tmp/silero-vad

# Copy the rest of the application
COPY . .

# Optional: Download Vosk model (uncomment if needed)
# RUN wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip -O model.zip \
#     && unzip model.zip \
#     && mv vosk-model-en-us-0.22 model \
#     && rm model.zip

# Expose the application port
EXPOSE 8000

# Run the application via startup script
CMD ["bash", "scripts/run.sh"]