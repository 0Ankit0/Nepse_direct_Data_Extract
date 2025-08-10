#!/bin/bash
# Docker run scripts for ShareSansar TSP Scraper

echo "ShareSansar TSP Scraper Docker Utilities"
echo "========================================"

# Function to build the image
build_image() {
    echo "Building ShareSansar TSP Scraper Docker image..."
    docker build -t sharesansar-tsp-scraper:latest .
    echo "Build complete!"
}

# Function to run ShareSansar TSP scraper historical data
run_tsp_historical() {
    echo "Running ShareSansar TSP historical scraper..."
    docker run --rm \
        -v "$(pwd)/sharesansarTSP:/app/sharesansarTSP" \
        -e SCRAPER_MODE=historical \
        -e TSP_DATA_FOLDER=/app/sharesansarTSP \
        sharesansar-tsp-scraper:latest python sharesansar_tsp_scraper.py
}

# Function to run ShareSansar TSP scraper for recent data
run_tsp_recent() {
    local days=${1:-7}
    echo "Running ShareSansar TSP recent data scraper (last $days days)..."
    docker run --rm \
        -v "$(pwd)/sharesansarTSP:/app/sharesansarTSP" \
        -e SCRAPER_MODE=recent \
        -e DAYS_BACK="$days" \
        -e TSP_DATA_FOLDER=/app/sharesansarTSP \
        sharesansar-tsp-scraper:latest python sharesansar_tsp_scraper.py
}

# Function to run ShareSansar TSP scraper continuously
run_tsp_continuous() {
    local interval=${1:-120}
    echo "Running ShareSansar TSP continuous scraper (interval: ${interval} minutes)..."
    docker run -d \
        --name sharesansar-tsp \
        -v "$(pwd)/sharesansarTSP:/app/sharesansarTSP" \
        -e SCRAPER_MODE=continuous \
        -e SCRAPER_INTERVAL="$interval" \
        -e TSP_DATA_FOLDER=/app/sharesansarTSP \
        --restart unless-stopped \
        sharesansar-tsp-scraper:latest python sharesansar_tsp_scraper.py
    
    echo "Container 'sharesansar-tsp' started in background"
    echo "Use 'docker logs -f sharesansar-tsp' to view logs"
    echo "Use 'docker stop sharesansar-tsp' to stop"
}

# Function to run interactive mode
run_interactive() {
    echo "Running ShareSansar TSP scraper in interactive mode..."
    docker run -it --rm \
        -v "$(pwd)/sharesansarTSP:/app/sharesansarTSP" \
        sharesansar-tsp-scraper:latest python sharesansar_tsp_scraper.py
}

# Function to stop all containers
stop_all() {
    echo "Stopping all ShareSansar TSP scraper containers..."
    docker stop $(docker ps -q --filter ancestor=sharesansar-tsp-scraper) 2>/dev/null || echo "No running containers found"
}

# Function to view logs
view_logs() {
    local container=${1:-sharesansar-tsp}
    echo "Viewing logs for container: $container"
    docker logs -f "$container"
}

# Function to shell into container
shell() {
    echo "Opening shell in ShareSansar TSP scraper container..."
    docker run -it --rm \
        -v "$(pwd)/sharesansarTSP:/app/sharesansarTSP" \
        sharesansar-tsp-scraper:latest /bin/bash
}

# Main menu
case "$1" in
    build)
        build_image
        ;;
    historical)
        run_tsp_historical
        ;;
    recent)
        run_tsp_recent "$2"
        ;;
    continuous)
        run_tsp_continuous "$2"
        ;;
    interactive)
        run_interactive
        ;;
    stop)
        stop_all
        ;;
    logs)
        view_logs "$2"
        ;;
    shell)
        shell
        ;;
    *)
        echo "Usage: $0 {build|historical|recent|continuous|interactive|stop|logs|shell}"
        echo ""
        echo "ShareSansar TSP Scraper Commands:"
        echo "  build                    - Build the Docker image"
        echo "  historical               - Run ShareSansar TSP historical scraper (full data from 2020)"
        echo "  recent [days]            - Run ShareSansar TSP recent data scraper (default: 7 days)"
        echo "  continuous [interval]    - Run ShareSansar TSP continuous scraper (default: 120 min)"
        echo "  interactive              - Run in interactive mode"
        echo "  stop                     - Stop all running containers"
        echo "  logs [container]         - View container logs"
        echo "  shell                    - Open shell in container"
        echo ""
        echo "Examples:"
        echo "  $0 build"
        echo "  $0 historical"
        echo "  $0 recent 14"
        echo "  $0 continuous 180"
        echo "  $0 interactive"
        exit 1
        ;;
esac
