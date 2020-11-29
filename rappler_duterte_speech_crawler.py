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

#Prepare list container
rappler_urls = []
rappler_data = {}

#Click button to load more (rappler's query page does not paginate)
def load_more(driver):
    """
    This function clicks load more button within rappler's search result page
    using an already-instantiated chrome driver.
    """
    xpath = '//*[@id="__next"]/div/div/div[7]/div/div[2]/div[2]/div/button'
    load_more_button = driver.find_element_by_xpath(xpath)
    driver.implicitly_wait(15)
    load_more_button.click()
    driver.implicitly_wait(15)

#Function to get article links from directory
def scrape_from_rappler():
    """
    This function scrapes urls resulting from a search on Rappler. It can
    only scrape articles for year 2016 onwards.
    """
    def extend_global_list(extension):
        """
        This funtion updates global list variable within a function
        """
        global rappler_urls
        rappler_urls.extend(extension)
    years = range(2017,2021) #Not available for 2016
    for year in years:
        domain = 'https://www.rappler.com/'
        query = f'search?q=duterte%20full%20text%20{year}'
        page_url = f'{domain}{query}'
        driver = webdriver.Chrome(executable_path=driver_path)
        driver.get(page_url)
        driver.implicitly_wait(15) #Wait before scraping elements
        #Load additional 19 (total is 20) windows
        for i in range(19):
            try:
                load_more(driver)
            except:
                continue #it will be unclickable at one point

        #Scrape elements
        items = driver.find_elements_by_css_selector('a>h3')
        parents = [item.find_element_by_xpath('./..') for item in items]
        urls = [parent.get_property('href') for parent in parents]
        extend_global_list(urls)
        driver.quit()

#Attempt to scrape 10x
for i in range(10):
    try:
        scrape_from_rappler()
    except:
        pass

#Remove duplicates
rappler_urls = list(set(rappler_urls))

#Isolate full text speeches by duterte
whitelist = r'(full-text[\w\d-]+duterte)|duterte[\w\d-]+sona'
blacklist = r'(locsin)|(robredo)|(sereno)'
rappler_urls = [url for url in rappler_urls
                if re.search(whitelist, url) and not re.search(blacklist, url)]

#Script to extract transcript paragraphs from rappler page
def rappler_page_to_transcript(url):
    """
    This function reads content of a validated rappler page (after taking in
    param url) and returns full article content as string.
    """
    #Validation
    if 'rappler.com' not in url:
        pass
    else:
        #Extract and filter results in soup
        content = requests.get(url) #Extract content
        soup = BeautifulSoup(content.text, 'html.parser') #Parse html
        p_tags = soup.find_all('p') #Find all by <p> tag
        #Build transcipt
        text_lines = [p_tag.text for p_tag in p_tags]
        transcript = ' '.join(text_lines)
        #Replace non-breaking space char
        transcript = re.sub('\xa0', '', transcript)
        return transcript

#Crawl directory using urls
for rappler_url in rappler_urls:
    #Visit each url
    try:
        driver.get(rappler_url)
    except:
        driver = webdriver.Chrome(executable_path=driver_path)
        driver.get(rappler_url)
    driver.implicitly_wait(15) #Wait before scraping elements

    #Close pop up, if it exists
    for i in range(1,8):
        try:
            no_thanks_xpath = f'/html/body/div[{i}]/div/div/div[2]/button[2]'
            driver.find_element_by_xpath(no_thanks_xpath).click()
            break
        except:
            continue

    #Scrape elements
    title = driver.find_element_by_css_selector('h1').text
    for i in range(1,8):
        try:
            date_xpath = f'/html/body/div[1]/div/div/div[5]/div[2]/div[{i}]/div/div/p/time'
            release_date = driver.find_element_by_xpath(date_xpath).text
            break
        except:
            continue
    #For transcript: can either be hard-coded or stored in linked pdf
    try:
        transcript = rappler_page_to_transcript(rappler_url)
    except:
        transcript = driver.find_element_by_class_name('release-content').text
    extract_date = dt.strftime(dt.now(), '%B %d, %Y %H:%M:%S')
    #Close Selenium-controlled window after crawling all pages
    driver.quit()

    #Add to json
    rappler_data[rappler_url] = {'Title' : title,
                                 'Release Date' : release_date,
                                 'Extract Date' : extract_date,
                                 'Transcript' : transcript}
    #print(f'Collected transcript for {title}.')

#Export json
with open('rappler_data.json', 'w') as file:
    json.dump(rappler_data, file)
