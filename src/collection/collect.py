# Importing all the packages needed
import time
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

# Initialize the WebDriver for Chrome
driver = webdriver.Chrome()

# Navigate to the URL
driver.get('https://kamernet.nl/huren/kamer')

# Accept the cookies, or skip if there is no cookie pop-up
try:
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    ).click()  # Click on the accept button for the cookie pop-up
    print('Cookie pop-up clicked')
except TimeoutException:
    print('No cookie pop-up, skipped the code')  # If there is no cookie pop-up, skip this code
    pass  # Continue execution without taking any action

# Scroll to the bottom of the page to ensure all elements are loaded
driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

# Defining a function that scrapes all the room-url's on the page, and put them in a list
def scrape_room_links():
    room_links = [] # List to store all room links
    try:
        link_elements = WebDriverWait(driver, 10).until( 
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.MuiPaper-root"))
        )  # Wait for all link elements to be present on the page
        for link_element in link_elements: # Loop through all the link elements
            room_link = link_element.get_attribute('href')  # Get the href attribute of the link element
            if room_link: # Check if the room link exists
                room_links.append(room_link)  # Append the room link to the list if it exists
    except StaleElementReferenceException: # check for error in Selenium that occurs when a web element is no longer present.
        pass  # If there is a StaleElementReferenceException, ignore it and continue execution
    return room_links  # Return the list of room links

# Defining a function that checks whether a 'next page' button is present or not
def is_next_page_button_present(): # Function that checks if there is a 'next page' button
    try:
        next_page_button = driver.find_element(By.CLASS_NAME, 'MuiPagination-ul').find_elements(By.TAG_NAME, 'button')[-1] # Find the last button element in the pagination
        return not next_page_button.get_attribute("disabled") # Return True if the button is not disabled, False if it is disabled
    except NoSuchElementException: # Check for error in Selenium that occurs when an element is not found
        return False # Return False if the element is not found

# Make a list that will store all of the room-url's, from all pages
all_room_links = [] 

# Variable to keep track of which page is being scraped
pagecounter = 1
while True: # While loop that keeps going until broken out of
    all_room_links.extend(scrape_room_links()) # Scrape room links from the current page, and add it to the all_room_links list
    # Check whether there is a 'next page' button
    if is_next_page_button_present(): # If there is a button, keep loop going
        next_page_button = WebDriverWait(driver, 10).until( # Wait for the next page button to be clickable
            EC.element_to_be_clickable((By.CLASS_NAME, 'MuiPagination-ul')) 
        ).find_elements(By.TAG_NAME, 'button')[-1] # Find the last button element in the pagination
        try:
            next_page_button.click() # Click next page button
        except ElementClickInterceptedException: # Check for error in Selenium that occurs when an element is not clickable
            WebDriverWait(driver, 10).until_not( # Wait for the loading spinner to disappear
                EC.visibility_of_element_located((By.CLASS_NAME, 'MuiCircularProgress-root')) # Find the loading spinner element
            )
            next_page_button.click()
        # This part updates you how many pages have been scraped, for every 10 pages
        if pagecounter % 10 == 0:
            print(f"Scraped the url's of {pagecounter} pages")
        pagecounter = pagecounter + 1 
        # Wait to ensure the next page has loaded
        time.sleep(2) 
    else: # If there is no button, break the loop
        break

print("Finished scraping. Total room links collected:", len(all_room_links))

# Close the WebDriver
driver.quit()

print("Now starting to scrape all the room pages!")

# Variable to keep track of which room-page is being scraped
roomcounter = 1
# for loop that takes every room-page, scrapes the info we need and stores it in the file
for room_link in all_room_links:
    user_agent = {'User-agent': 'Mozilla/5.0'}
    url = room_link
    res = requests.get(url, headers=user_agent)  # Send a GET request to the room link with the specified user agent
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text)  # Parse the HTML content of the response using BeautifulSoup

    try:
        # Find and name all of the data we want to collect about a room
        price = soup.find(class_='Overview_root__WQi2M').find_all('h6')[0].get_text()  # Get the price of the room. Use beautifulsoup to find the right class and tag and only get the text
        area = soup.find(class_='Overview_root__WQi2M').find_all('h6')[1].get_text()  # Get the area of the room. again use beautifulsoup to find the right class and tag and only get the text
        included = soup.find(class_='Overview_root__WQi2M').find_all('p')[1].get_text()  # Get the included amenities of the room. Use beautifulsoup to find the right class and tag and only get the text
        address = soup.find(class_='Header_details__nRVNP').find('a').get_text()  # Get the address of the room. Use beautifulsoup to find the right class and tag and only get the text
        details_all = soup.find(class_='Details_gridContainer__nBfKx').find_all('p')  # Get all the details of the room. Use beautifulsoup to find the right class and tag and only get the text
        # Make a list with the room 'details': an unstructured list of details that highly differs between rooms. 
        details_list = []
        for details in details_all:
            details_list.append(details.get_text())  # Append each detail to the details_list


        # Fill object with all the scraped data for the room + timestamp
        obj = ({'room_id': url.split('-')[-1],
                        'price': price.split('€')[-1],
                        'included': included,
                        'area': area,
                        'city': address.split(',')[1],
                        'street': address.split(',')[0],
                        'details': details_list,
                        'time of extraction': int(time.time())})

    except AttributeError:
        print(f"Error scraping room at {url}. Element not found.")
        obj = ({'room_id': url.split('-')[-1], 'error': 'Missing data'})
        # If there is an AttributeError while scraping the room, print an error message and create an object with the room ID and an error message

    # Append the room's data list to the JSON file, and start a new line
    with open('room_data.json', 'a', encoding='utf-8') as outfile:
        json.dump(obj, outfile, ensure_ascii=False)
        outfile.write(',\n')

    # This part updates you how many rooms have been scraped, for every 25 rooms
    if roomcounter % 25 == 0:
        print(f"Scraped and stored {roomcounter} rooms.")
    roomcounter = roomcounter + 1

print("Scraping and JSON creation complete!")