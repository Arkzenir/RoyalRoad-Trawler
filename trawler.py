import json
import sys
import os
import re
from bs4 import BeautifulSoup
import pyautogui
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load configuration from config.json
with open('user_config.json', 'r') as user_config_file:
    user_config = json.load(user_config_file)
    
with open('dev_config.json', 'r') as dev_config_file:
    dev_config = json.load(dev_config_file)

driver_path_firefox = dev_config['driver_path_firefox']
driver_path_chrome = dev_config['driver_path_chrome']
driver_path_edge = dev_config['driver_path_edge']
browser = user_config.get('browser', 'chrome').lower()  # Default to 'chrome' if not specified

# Define the download directory and the filename
download_dir = os.path.abspath(os.path.dirname(__file__)) + "\\" + user_config["download_directory"]+"\\"
chapter_limit = user_config["chapter_limit"]

# Check if darkmode is requested
dark_mode = user_config['dark_mode']
dark_mode_css_url = dev_config['dark_mode_css_url']
light_mode_css_url = dev_config['light_mode_css_url']

# Configure Firefox WebDriver without setting download options
def configure_firefox():
    options = FirefoxOptions()
    options.binary_location = dev_config["binary_path_firefox"]
    options.add_argument("--headless")  # Run headless Firefox
    service = FirefoxService(executable_path=driver_path_firefox)
    driver = webdriver.Firefox(service=service, options=options)
    return driver

# Configure Chrome WebDriver without setting download options
def configure_chrome():
    options = ChromeOptions()
    options.add_argument("--headless")  # Run headless Chrome
    service = ChromeService(executable_path=driver_path_chrome)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def configure_edge():
    options = EdgeOptions()
    options.add_argument("--guest")
    service = EdgeService(executable_path=driver_path_edge)
    driver = webdriver.Edge(service=service, options=options)
    return driver

# Set up the WebDriver based on the browser specified in the configuration
if browser == 'firefox':
    driver = configure_firefox()
elif browser == 'chrome':
    driver = configure_chrome()
elif browser == 'edge':
    driver = configure_edge()
else:
    print(f"Unsupported browser: {browser}")
    sys.exit(1)

def save_page_as(download_path):

    # Perform the Save As operation
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)  # Wait for the Save As dialog to open

    # Enter the directory path and filename
    pyautogui.typewrite(download_path)
    pyautogui.press('enter')


#def construct_title(title):
#    if "chapter" in title.lower():
#        title = re.sub(r'\b{}\b'.format(re.escape("chapter")), '',title, flags=re.IGNORECASE).strip()
#    valid_title = re.sub(r'[^a-zA-Z0-9]+', '_', title).strip('_')
#    return f"Chapter_{chapter_number}_{valid_title}.html"

def embed_styles(html_page, site_url):
    soup = BeautifulSoup(html_page, 'html.parser')
    css_links = soup.find_all('link', rel='stylesheet')

    # Dictionary to store CSS contents
    css_contents = {}

    for link in css_links:
        css_url = link['href']

        # Check if css is for light-dark mode
        if dark_mode:
            if light_mode_css_url in css_url:
                css_url = dark_mode_css_url
        else:
            if dark_mode_css_url in css_url:
                css_url = light_mode_css_url

        # Check if the URL is absolute or relative
        if not css_url.startswith('http'):
            css_url = site_url + css_url
        # Get the CSS content
        response = requests.get(css_url)
        css_contents[css_url] = response.text
        # Remove the link tag from the soup
        link.decompose()
    

    # Create a new style tag with all the CSS contents
    style_tag = soup.new_tag('style')
    for css in css_contents.values():
        style_tag.append(css)

    # Insert the style tag into the head of the document
    soup.head.append(style_tag)
    return str(soup)

# Function to save the current page as an HTML file
def save_html(full_dir, html_content):
    with open(full_dir, "w", encoding="utf-8") as file:
        file.write(html_content)

def set_prev_next_buttons(html_str, curr_chapter):
    soup = BeautifulSoup(html_str, 'html.parser')
    prev = soup.select_one("div.col-md-4:nth-child(1) > a:nth-child(1)")
    if prev:
        prev['href'] = 'Chapter-' + str(curr_chapter - 1) + ".htm"
    next = soup.select_one(".col-md-offset-4 > a:nth-child(1)")
    if next:
        next['href'] = 'Chapter-' + str(curr_chapter + 1) + ".htm"
    return str(soup)



# Get the start URL from the command-line arguments or fallback to config.json
start_url = user_config.get('start_url')

if len(sys.argv) > 1:
    start_url = sys.argv[1]

if not start_url:
    print("No start URL provided and no default found in config.json.")
    sys.exit(1)


# Start scraping
print("Load: " + start_url)
driver.get(start_url)
chapter_number = 1

fiction_name = re.sub(r'[^a-zA-Z0-9]+', '_', driver.title.split("|")[0][:-1])
download_dir = download_dir + fiction_name
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

download_dir = download_dir + "\\"

try:
    first_chapter_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "tr.chapter-row:nth-child(1) > td:nth-child(1) > a:nth-child(1)")) #Selector for first chapter in chapter list
        )
    first_chapter_button.click()
except TimeoutException:
        print("Could not start at chapter 1")




while True:

    if chapter_limit > 0 and chapter_number < chapter_limit + 1:
        break

    try:
        # Wait for the specific element that indicates the page has fully loaded
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.chapter-content"))
        )
    except TimeoutException:
        print("Page timeout at chapter " + chapter_number)
        break
    # Get the page title
    title = driver.title

    # Save the current page
    page_source = driver.page_source

    #save_html(chapter_number, title, page_source)
    chapter_title = "Chapter-" + str(chapter_number) + ".htm"
    full_dir = download_dir + chapter_title
    #save_page_as(full_dir)
    print("Start saving")
    embedded_chapter = embed_styles(page_source, driver.current_url.partition(".com")[0] + ".com") #Embed styles
    result_chapter = set_prev_next_buttons(embedded_chapter, chapter_number) #Associate prev next buttons
    save_html(full_dir, result_chapter) #Save chapter
    print(f"Saved chapter {chapter_number}: {title} at {full_dir}")

    try:
        # Try to find and click the next button
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".col-md-offset-4 > a:nth-child(1)"))  #Next button selector
        )
        next_button.click()
    except TimeoutException:
        print("End of fiction")
        break
    
    while not os.path.exists(full_dir):
        time.sleep(1)  # Wait for 1 second before checking again
        print("waiting for : " + full_dir)

    # Increment the chapter number
    chapter_number += 1

# Close the browser
driver.quit()

