#!/bin/bash
# Docker run scripts for NEPSE Scraper

echo "NEPSE Scraper Docker Utilities"
echo "=============================="

# Function to build the image
build_image() {
    echo "Building NEPSE Scraper Docker image..."
    docker build -t nepse-scraper:latest .
    echo "Build complete!"
}

# Function to run full historical scraper
run_historic() {
    echo "Running FULL historical scraper (ALL securities, 1 year data - takes hours!)"
    echo "This will scrape 318+ securities with complete historical data"
    docker run --rm \
        -v "$(pwd)/data:/app/data" \
        nepse-scraper:latest python auto_historic_scraper.py
}

# Function to run latest data scraper
run_latest() {
    echo "Running latest data scraper (recent data only)..."
    docker run --rm \
        -v "$(pwd)/data:/app/data" \
        -e SCRAPER_MODE=latest \
        nepse-scraper:latest python container_scraper.py
}

# Function to run continuous scraper
run_continuous() {
    local interval=${1:-60}
    echo "Running continuous scraper (interval: ${interval} minutes)..."
    docker run -d \
        --name nepse-continuous \
        -v "$(pwd)/data:/app/data" \
        -e SCRAPER_MODE=continuous \
        -e SCRAPER_INTERVAL="$interval" \
        --restart unless-stopped \
        nepse-scraper:latest python container_scraper.py
    
    echo "Container 'nepse-continuous' started in background"
    echo "Use 'docker logs -f nepse-continuous' to view logs"
    echo "Use 'docker stop nepse-continuous' to stop"
}

# Function to run specific securities scraper
run_specific() {
    local symbols=${1:-"NABIL,NICA,SCBL"}
    echo "Running specific securities scraper for: $symbols"
    docker run --rm \
        -v "$(pwd)/data:/app/data" \
        -e SCRAPER_MODE=specific \
        -e SYMBOLS="$symbols" \
        nepse-scraper:latest python container_scraper.py
}

# Function to run interactive mode
run_interactive() {
    echo "Running interactive scraper..."
    docker run -it --rm \
        -v "$(pwd)/data:/app/data" \
        nepse-scraper:latest python container_scraper.py
}

# Function to stop all containers
stop_all() {
    echo "Stopping all NEPSE scraper containers..."
    docker stop $(docker ps -q --filter ancestor=nepse-scraper) 2>/dev/null || echo "No running containers found"
}

# Function to view logs
view_logs() {
    local container=${1:-nepse-continuous}
    echo "Viewing logs for container: $container"
    docker logs -f "$container"
}

# Function to shell into container
shell() {
    echo "Opening shell in NEPSE scraper container..."
    docker run -it --rm \
        -v "$(pwd)/data:/app/data" \
        nepse-scraper:latest /bin/bash
}

# Function to run ShareSansar TSP scraper historical data
run_tsp_historical() {
    echo "Running ShareSansar TSP historical scraper..."
    docker run --rm \
        -v "$(pwd)/sharesansarTSP:/app/sharesansarTSP" \
        -e SCRAPER_MODE=historical \
        -e TSP_DATA_FOLDER=/app/sharesansarTSP \
        nepse-scraper:latest python sharesansar_tsp_scraper.py
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
        nepse-scraper:latest python sharesansar_tsp_scraper.py
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
        nepse-scraper:latest python sharesansar_tsp_scraper.py
    
    echo "Container 'sharesansar-tsp' started in background"
    echo "Use 'docker logs -f sharesansar-tsp' to view logs"
    echo "Use 'docker stop sharesansar-tsp' to stop"
}

# Main menu
case "$1" in
    build)
        build_image
        ;;
    historic)
        run_historic
        ;;
    latest)
        run_latest
        ;;
    continuous)
        run_continuous "$2"
        ;;
    specific)
        run_specific "$2"
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
    tsp-historical)
        run_tsp_historical
        ;;
    tsp-recent)
        run_tsp_recent "$2"
        ;;
    tsp-continuous)
        run_tsp_continuous "$2"
        ;;
    *)
        echo "Usage: $0 {build|historic|latest|continuous|specific|interactive|stop|logs|shell|tsp-historical|tsp-recent|tsp-continuous}"
        echo ""
        echo "NEPSE Scraper Commands:"
        echo "  build                    - Build the Docker image"
        echo "  historic                 - Run FULL historical scraper (ALL securities, 1 year data)"
        echo "  latest                   - Run latest data scraper once (recent data only)"
        echo "  continuous [interval]    - Run continuous scraper (default: 60 min)"
        echo "  specific [symbols]       - Run specific securities scraper"
        echo "  interactive              - Run in interactive mode"
        echo "  stop                     - Stop all running containers"
        echo "  logs [container]         - View container logs"
        echo "  shell                    - Open shell in container"
        echo ""
        echo "ShareSansar TSP Scraper Commands:"
        echo "  tsp-historical           - Run ShareSansar TSP historical scraper"
        echo "  tsp-recent [days]        - Run ShareSansar TSP recent data scraper (default: 7 days)"
        echo "  tsp-continuous [interval]- Run ShareSansar TSP continuous scraper (default: 120 min)"
        echo ""
        echo "Examples:"
        echo "  $0 build"
        echo "  $0 historic              (WARNING: Takes several hours!)"
        echo "  $0 latest"
        echo "  $0 continuous 30"
        echo "  $0 specific \"NABIL,NICA,SCBL\""
        echo "  $0 interactive"
        echo "  $0 tsp-historical"
        echo "  $0 tsp-recent 14"
        echo "  $0 tsp-continuous 180"
        exit 1
        ;;
esac
