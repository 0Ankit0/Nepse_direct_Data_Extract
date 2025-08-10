# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy all project files to the container
COPY . /app


# Install required Python packages
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
# Install Playwright browsers
RUN playwright install --with-deps

# Set the default command to run the Python script
CMD ["python", "sharesansar_tsp_scraper.py"]
