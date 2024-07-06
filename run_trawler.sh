#!/bin/bash

# Function to prompt the user for input
read -p "Enter the starting page URL (leave blank to use default from config.json): " START_URL

# Check if the user provided a URL
if [ -z "$START_URL" ]; then
    # Run the Python script without the URL argument
    python3 path_to_your_script.py
else
    # Run the Python script with the provided URL
    python3 path_to_your_script.py "$START_URL"
fi