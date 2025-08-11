# Multi-stage Dockerfile for HuggingFace Spaces with Ollama
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_PORT=11434
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies including Ollama requirements
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements first for better Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories including separated web files
RUN mkdir -p logs cache templates static

# Expose ports for both app and Ollama
EXPOSE 7860 11434

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting HuggingFace Spaces Web3 Research Co-Pilot..."\n\
\n\
# Start Ollama server in background\n\
echo "📦 Starting Ollama server..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to be ready\n\
echo "⏳ Waiting for Ollama to be ready..."\n\
while ! curl -s http://localhost:11434/api/tags > /dev/null; do\n\
  sleep 2\n\
  echo "   ... still waiting for Ollama"\n\
done\n\
\n\
echo "✅ Ollama server is ready!"\n\
\n\
# Pull the Llama 3.1 8B model\n\
echo "📥 Pulling llama3.1:8b model (this may take a few minutes)..."\n\
ollama pull llama3.1:8b\n\
echo "✅ Model llama3.1:8b ready!"\n\
\n\
# Start the main application\n\
echo "🌐 Starting Web3 Research Co-Pilot web application..."\n\
python app.py &\n\
APP_PID=$!\n\
\n\
# Function to handle shutdown\n\
cleanup() {\n\
    echo "🛑 Shutting down gracefully..."\n\
    kill $APP_PID $OLLAMA_PID 2>/dev/null || true\n\
    wait $APP_PID $OLLAMA_PID 2>/dev/null || true\n\
    echo "✅ Shutdown complete"\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Wait for processes\n\
wait $APP_PID $OLLAMA_PID' > start.sh

# Make startup script executable
RUN chmod +x start.sh

# Health check with longer startup time for model download
HEALTHCHECK --interval=30s --timeout=10s --start-period=600s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start command
CMD ["./start.sh"]
