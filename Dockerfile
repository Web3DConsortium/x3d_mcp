# Production server image for x3d_mcp.
#
# Runs the MCP server in Streamable HTTP mode by default, so the image
# is deploy-ready for hosts that auto-detect a Dockerfile at the repo
# root (Render, Fly.io, Railway, Cloud Run, etc.). The host injects the
# PORT environment variable; HOST defaults to 0.0.0.0.
#
# Local quickstart:
#   docker build -t x3d-mcp .
#   docker run -p 8000:8000 x3d-mcp
#   # then point an MCP client at http://localhost:8000/mcp
#
# The CI / pytest image lives in Dockerfile.test.

FROM python:3.12-slim

WORKDIR /app

# Copy only what the runtime needs. Tests, datasets, and examples are
# excluded to keep the image lean; see Dockerfile.test for the CI image.
COPY pyproject.toml ./
COPY src/ ./src/

# Install runtime dependencies only (no [dev] / pytest).
RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=streamable-http
ENV PORT=8000

EXPOSE 8000

CMD ["python", "src/server.py"]
