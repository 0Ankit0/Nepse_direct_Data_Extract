#!/bin/bash
# Shell script to run ReportScraper and TSP scraper in background, monitor logs, and restart if needed

REPORT_SCRIPT="./.venv/bin/python ReportScraper.py"
TSP_SCRIPT="./.venv/bin/python sharesansar_tsp_scraper.py"
REPORT_LOG="ReportScraper.log"
TSP_LOG="sharesansar_tsp_scraper.log"

start_scraper() {
    local script_cmd="$1"
    local log_file="$2"
    nohup $script_cmd > "$log_file" 2>&1 &
    echo $!
}

kill_scraper() {
    local pid=$1
    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        kill $pid
        wait $pid 2>/dev/null
    fi
}

# Start both scrapers
report_pid=$(start_scraper "$REPORT_SCRIPT" "$REPORT_LOG")
tsp_pid=$(start_scraper "$TSP_SCRIPT" "$TSP_LOG")

last_report_size=0
last_tsp_size=0
last_report_time=$(date +%s)
last_tsp_time=$(date +%s)

while true; do
    sleep 300  # 5 minutes
    restart_report=0
    restart_tsp=0

    # Check ReportScraper log
    if [ -f "$REPORT_LOG" ]; then
        size=$(stat -c%s "$REPORT_LOG")
        if [ "$size" -ne "$last_report_size" ]; then
            last_report_size=$size
            last_report_time=$(date +%s)
        else
            restart_report=1
        fi
        if grep -qiE 'error|exception|traceback|exit' "$REPORT_LOG"; then
            restart_report=1
        fi
    else
        restart_report=1
    fi

    # Check TSP scraper log
    if [ -f "$TSP_LOG" ]; then
        size=$(stat -c%s "$TSP_LOG")
        if [ "$size" -ne "$last_tsp_size" ]; then
            last_tsp_size=$size
            last_tsp_time=$(date +%s)
        else
            restart_tsp=1
        fi
        if grep -qiE 'error|exception|traceback|exit' "$TSP_LOG"; then
            restart_tsp=1
        fi
    else
        restart_tsp=1
    fi

    # Restart if needed
    if [ "$restart_report" -eq 1 ]; then
        echo "Restarting ReportScraper..."
        kill_scraper $report_pid
        report_pid=$(start_scraper "$REPORT_SCRIPT" "$REPORT_LOG")
        last_report_size=0
        last_report_time=$(date +%s)
    fi
    if [ "$restart_tsp" -eq 1 ]; then
        echo "Restarting TSP scraper..."
        kill_scraper $tsp_pid
        tsp_pid=$(start_scraper "$TSP_SCRIPT" "$TSP_LOG")
        last_tsp_size=0
        last_tsp_time=$(date +%s)
    fi

done
