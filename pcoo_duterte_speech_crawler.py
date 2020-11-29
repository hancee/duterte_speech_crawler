#Load libraries
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
import os
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#Driver instance
project_root = os.path.abspath(os.getcwd())
driver_path = os.path.join(project_root, 'chromedriver')
try:
    driver = webdriver.Chrome(executable_path=driver_path)
#Install if not available
except:
    from webdriver_manager.chrome import ChromeDriverManager
    driver = webdriver.Chrome(ChromeDriverManager().install())

#Get article links from directory
post_urls = []
domain = 'https://pcoo.gov.ph/'
directory = 'presidential-speech/'
print(f'Scraping post urls from {domain}(directory)...')
for i in range(1,23): #Page 24 onwards doesn't have content
    page = f'page/{i}'
    page_url = f'{domain}{directory}{page}'
    driver.get(page_url)
    driver.implicitly_wait(10) #Wait before scraping elements
    items = driver.find_elements_by_tag_name('h3')
    urls = [item.find_element_by_css_selector('h3>a').get_property('href') \
            for item in items]
    post_urls.extend(urls)

#Prepare data container
pcoo_data = {}

#Crawl directory
print('Crawling directory...')
for post_url in post_urls[:236]: #transcripts were stored in pdf beyond 236
    #Visit each url
    try:
        driver.get(post_url)
    except:
        driver = webdriver.Chrome(executable_path=driver_path)
        driver.get(post_url)
    driver.implicitly_wait(15) #Wait before scraping elements

    #Scrape elements
    title = driver.find_element_by_css_selector('h3').text
    release_date = driver.find_element_by_css_selector('small').text
    #For transcript: can either be hard-coded or stored in linked pdf
    try:
        transcript = driver.find_element_by_class_name('release-content').text
    except:
        driver.find_element_by_xpath("//*[text()='Write and Earn']")
        #driver.findElement(By.xpath("//*[text()='Write and Earn']"));
    extract_date = dt.strftime(dt.now(), '%B %d, %Y %H:%M:%S')

    #Add to json
    pcoo_data[post_url] = {'Title' : title,
                           'Release Date' : release_date,
                           'Extract Date' : extract_date,
                           'Transcript' : transcript}
    print(f'Collected transcript for {title}.')

    #Back up json for every 20th entry
    if post_urls.index(post_url)//20==0:
        with open('pcoo_data.json', 'w') as file:
            json.dump(pcoo_data, file)

#Close Selenium-controlled window after crawling all pages
driver.quit()

#Export json
with open('pcoo_data.json', 'w') as file:
    json.dump(pcoo_data, file)
