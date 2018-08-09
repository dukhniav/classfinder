# import libraries
import json
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
import re

# address of ClassFinder
my_url = 'https://admin.wwu.edu/pls/wwis/wwsktime.SelClass'

# opening client, grabbing page
uClient = uReq(my_url)
# offload content into variable
page_html = uClient.read()
# close connection
uClient.close()

# html parser
page_soup = soup(page_html, "html.parser")

# get Subject options
options = page_soup.select('select[name=sel_subj] > option')
string = str(options)
temp = re.findall(r'"([^"]*)"', string)

# make list of all subjects
subj_options = temp[2:]

driver = webdriver.Firefox(executable_path="/home/artem/projects/scrape/drivers/geckodriver")

driver.get("https://admin.wwu.edu/pls/wwis/wwsktime.SelClass")
table = driver.find_element_by_name('sel_subj')

#--------------------------

# unselect first option
driver.find_element_by_xpath("//select[@name='sel_subj']/option[text()='All Subjects']").click()

# select wanted subject
driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='"+subj_options[1]+"']").click()

# click submit button
submit = '//input[@type="submit" and @value="Search Now"]'
driver.find_element_by_xpath(submit).click()

new_soup = soup(driver.page_source, "html.parser")

rows = []

rows = new_soup.find_all("td", class_="dddefault")
print(rows)

new_row = ''.join(str(e) for e in rows)
# list_row = rows.split()

print(new_row)

result = []
for row in rows:
    row.select("td")

####### remove everythin between < ... > like before !!!

# for row in rows:
#     cells = row.find_all("td")
#     rn = cells[0].get_text()

# back button
# driver.execute_script("window.history.go(-1)")
# continiue
