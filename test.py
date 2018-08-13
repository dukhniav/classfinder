# import libraries
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from pandas import DataFrame
import time
import numpy as np
import re

# address of ClassFinder
my_url = 'https://admin.wwu.edu/pls/wwis/wwsktime.SelClass'

# opening client, grabbing page
uClient = uReq(my_url)
# offload content into variable
page_html = uClient.read()
# close connection
uClient.close()

# current subject
CURR_SUBJ = ''

# full list of classes
CLASSES = []

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

# --------------------------
# unselect first option
driver.find_element_by_xpath("//select[@name='sel_subj']/option[text()='All Subjects']").click()

# select wanted subject
driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='" + subj_options[18] + "']").click()
CURR_SUBJ = subj_options[18]

# click submit button
submit = '//input[@type="submit" and @value="Search Now"]'
driver.find_element_by_xpath(submit).click()

time.sleep(.5)

new_soup = soup(driver.page_source, "html.parser")

head_tag = new_soup.head
map_tag = new_soup.map

table_tag = map_tag.contents[11]

new_table = []
crn = []

# list of crns, which are not part of > <, same order
crns = new_soup.find_all('input', {'name': 'sel_crn'})
crn_ctr = 1
for x in crns:
    crn.append(x.get('value'))
    crn_ctr = crn_ctr + 1


def find_between_tags():
    global temp, new_table
    for child in table_tag.children:
        temp = re.findall(r'\>(.*?)\<', repr(child))
        if (len(temp) > 0):
            new_table = temp


# find everythin between > <
find_between_tags()

# removing empty spaces
table = list(filter(None, new_table))

# remove 15 first spots for headers of table
header_table = table[15:]


def remove_duplicates():
    global entry
    for entry in header_table:
        if entry == 'CLOSED                               ':
            header_table.remove(entry)
        if entry == ' ':
            header_table.remove(entry)
        if entry == '\xa0':
            header_table.remove(entry)


# remove "CLOSED" and other elements in list
remove_duplicates()

# make array to preserve element arrangment with duplicates
nptable = np.array(header_table)

counter = 0
crn_counter = 0
temp_counter = 0

stuff = False
prereq = False
new_temp_list = []
prereq_counter = 0
last_class = 0
for entry in nptable:

    if 'Prerequisites' in entry:
        prereq_counter = counter
        prereq = True
    if CURR_SUBJ in entry[:5] and stuff is False and prereq is False and len(entry) < 10 and \
            '.' not in entry and int(entry[-3:]) >= last_class:
        stuff = True
        temp_counter = counter

        print('-----------------------------------------')
        print('=-=============last class: ' + str(last_class))

        print('subject line encountered')
        print("class: " + entry)
        last_class = int(entry[-3:])
        new_temp_list.append(entry)
    if stuff:
        if counter - temp_counter < 9:
            if counter - temp_counter == 1:
                print("title: " + entry)
                new_temp_list.append(entry)
                # CRN after Course title
                print("crn  : " + crn[crn_counter])
                new_temp_list.append(crn[crn_counter])
                if crn_counter < (len(crn) - 1):
                    crn_counter = crn_counter + 1
            if counter - temp_counter == 2:
                print("cap  : " + entry)
                new_temp_list.append(entry)
            if counter - temp_counter == 3:
                print("enrl : " + entry)
                new_temp_list.append(entry)
            if counter - temp_counter == 4:
                print("avail: " + entry)
                new_temp_list.append(entry)
            if counter - temp_counter == 5:
                print("instr: " + entry)
                new_temp_list.append(entry)
            if counter - temp_counter == 6:
                print("dates: " + entry)
                new_temp_list.append(entry)
        else:
            stuff = False
    if prereq_counter < counter:
        prereq = False

    counter = counter + 1

print(new_temp_list)

CLASSES.append(new_temp_list)


# to flatten out the list of Classes


def flatten_list(nested_list):
    temp_list = []
    for sub in nested_list:
        for item in sub:
            temp.append(item)
    return temp_list


# to flatten out the list of Classes
flat_classes = flatten_list(CLASSES)

classes = []
titles = []
crns = []
caps = []
enrls = []
avails = []
instrs = []
dates = []

class_ctr = 0
for c in flat_classes:
    if class_ctr % 8 == 0:
        classes.append(c)
    if class_ctr % 8 == 1:
        titles.append(c)
    if class_ctr % 8 == 2:
        crns.append(c)
    if class_ctr % 8 == 3:
        caps.append(c)
    if class_ctr % 8 == 4:
        enrls.append(c)
    if class_ctr % 8 == 5:
        avails.append(c)
    if class_ctr % 8 == 6:
        instrs.append(c)
    if class_ctr % 8 == 7:
        dates.append(c)
    class_ctr = class_ctr + 1

print(classes)
print(crns)
print(caps)

df = DataFrame({'Class': classes, 'Title': titles, 'CRN': crns,
                'Cap': caps, 'Enrl': enrls, 'Avail': avails,
                'Instructor': instrs, 'Dates': dates})

df.to_csv('test.csv', sep='\t', encoding='utf-8')
