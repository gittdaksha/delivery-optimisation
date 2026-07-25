# Start from the official slim Python 3.11 image
# slim = stripped-down version; smaller size, no GUI tools, no compilers
# → full python:3.11 image is ~900MB; slim is ~130MB
FROM python:3.11-slim

# Set the working directory inside the container
# → all subsequent commands (COPY, RUN, CMD) run from /app
# → if /app does not exist, Docker creates it automatically
WORKDIR /app

# Copy requirements.txt first — before copying source code
# → Docker builds images in layers; each instruction is one layer
# → Docker caches layers that have not changed
# → requirements.txt changes rarely; src/ changes often
# → this order means pip install is only re-run when requirements.txt changes,
#   not every time you edit a Python file — much faster rebuilds
COPY requirements.txt .

# Install Python packages
# --no-cache-dir = do not store the pip download cache inside the image
# → saves ~50-100MB of image size
# → the cache is useless inside an image; packages are already installed
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data into the container
COPY src/ ./src/
COPY data/ ./data/

# Default command when the container starts
# → docker run <image> runs this unless you override it
# → CMD is overridable: docker run <image> python src/ingest.py runs ingest instead
CMD ["python", "src/generate_data.py"]
