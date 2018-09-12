# import libraries
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from pandas import DataFrame
import time
import numpy as np
import re
from tqdm import tqdm

# Global vars

# making firefox headless
fire_options = Options()
fire_options.add_argument("--headless")

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

# "firefox_options=fire_options" --> headless firefox
driver = webdriver.Firefox(firefox_options=fire_options,
                           executable_path="/home/artem/projects/scrape/drivers/geckodriver")

driver.get("https://admin.wwu.edu/pls/wwis/wwsktime.SelClass")
table = driver.find_element_by_name('sel_subj')

# --------------------------

first_go = True
for subj in tqdm(subj_options):
    if first_go:
        # unselect first option
        driver.find_element_by_xpath("//select[@name='sel_subj']/option[text()='All Subjects']").click()

        # select wanted subject
        driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='" + subj + "']").click()
        CURR_SUBJ = subj
        time.sleep(.5)
    else:
        # unselect first option
        driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value= '" + CURR_SUBJ + "']").click()
        time.sleep(.5)
        # select wanted subject
        driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='" + subj + "']").click()
        CURR_SUBJ = subj
        time.sleep(.5)

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

    # find everythin between > <
    for child in table_tag.children:
        temp = re.findall(r'\>(.*?)\<', repr(child))
        if (len(temp) > 0):
            new_table = temp

    # removing empty spaces
    table = list(filter(None, new_table))

    # remove 15 first spots for headers of table
    header_table = table[15:]

    # remove "CLOSED" and other elements in list
    for entry in header_table:
        if entry == 'CLOSED                               ':
            header_table.remove(entry)
        if entry == ' ':
            header_table.remove(entry)
        if entry == '\xa0':
            header_table.remove(entry)

    # make array to preserve element arrangment with duplicates
    nptable = np.array(header_table)

    crn_counter = 0  # counter to keep track of how many CRNs have been assigned
    single_class_list = []  # list of all parts, made up of 'class_parts_list' after loop
    since_prereq_ctr = 0  # counter to keep track how many entries occured since last 'Prerequisite'
    prev_class_num = 0  # previous class number, to make sure the right class is being added
    class_part_list = []  # keeps temporary class parts to be 'dumped' later
    backup_crn = 0  # previous class CRN

    total_ctr = 0  # total counter since start
    class_part_ctr = 0  # counts the parts of the class, normally < 9

    subj_sat = False  # class satisfied with class name -> EX: 'HIST 112'
    prereq = False  # class with 'Prerequisites'
    runaway_class = False  # class with info embedded past 'Prerequisites'

    for entry in nptable:

        if 'Prerequisites' in entry:
            since_prereq_ctr = total_ctr
            prereq = True

        if CURR_SUBJ in entry and subj_sat is True and len(entry) < 10 and \
                '.' not in entry and len(class_part_list) > 0:
            runaway_class = True  # set runaway to True
            class_part_ctr = total_ctr  # reset part_ctr
            class_part_list.clear()  # clear class_part_list
            class_part_list.append(entry)  # add first entry to list

        if CURR_SUBJ in entry[:5] and subj_sat is False and prereq is False and len(entry) < 10 and \
                '.' not in entry and len(class_part_list) == 0:
            try:
                if int(entry[-3:]) >= prev_class_num:  # save last 3 number of class name/num
                    subj_sat = True  # set sub satisfied to True

                    class_part_ctr = total_ctr  # reset part counter
                    prev_class_num = int(entry[-3:])  # update prev class number

                    class_part_list.append(entry)  # add entry to class list

            except ValueError:  # IF letter in class number
                if int(entry[-4:-1]) >= prev_class_num:  # add last 3 before letter
                    subj_sat = True

                    class_part_ctr = total_ctr
                    prev_class_num = int(entry[-4:-1])

                    class_part_list.append(entry)

        if subj_sat:  # subj is satisfied
            if total_ctr - class_part_ctr < 9:  # counter add up to less then 9
                # Title & CRN
                if total_ctr - class_part_ctr == 1:
                    class_part_list.append(entry)  # first one is TITLE, automatically followed by
                    # CRN from CRN LIST
                    # CRN after Course Title
                    if not runaway_class:  # runaway = False
                        class_part_list.append(crn[crn_counter])
                        backup_crn = crn[crn_counter]  # save copy to backup

                        if crn_counter < (len(crn) - 1):  # update crn_counter
                            crn_counter = crn_counter + 1
                    else:  # runaway = True
                        class_part_list.append(backup_crn)
                        runaway_class = False  # set runaway to False

                # Cap
                if total_ctr - class_part_ctr == 2:
                    class_part_list.append(entry)

                # Enrl
                if total_ctr - class_part_ctr == 3:
                    class_part_list.append(entry)

                # Avail
                if total_ctr - class_part_ctr == 4:
                    class_part_list.append(entry)

                # Instructor
                if total_ctr - class_part_ctr == 5:
                    class_part_list.append(entry)

                # Dates
                if total_ctr - class_part_ctr == 6:
                    class_part_list.append(entry)
            else:  # if counter don't add up, set subj to false
                subj_sat = False

        if since_prereq_ctr < total_ctr:
            prereq = False

        if len(class_part_list) == 8:  # add everything from temp list to class list
            for x in class_part_list:
                single_class_list.append(x)
            class_part_list.clear()

        total_ctr = total_ctr + 1  # update total counter

    # needed to check the right options
    first_go = False

    last_class = 0

    CLASSES.append(single_class_list)

    time.sleep(.5)

    # back button
    driver.execute_script("window.history.go(-1)")
    time.sleep(.5)

# to flatten out the list of Classes
flat_classes = []
for x in CLASSES:
    for i in x:
        flat_classes.append(i)

# removing empty spaces
flat_classes_final = list(filter(None, flat_classes))

classes = []
titles = []
crns = []
caps = []
enrls = []
avails = []
instrs = []
dates = []

class_ctr = 0
for c in flat_classes_final:
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

print(flat_classes_final)
print('--------------------------------')
print(classes)
print(titles)
print(crns)
print(caps)
print(enrls)
print(avails)
print(instrs)
print(dates)

df = DataFrame({'Class': classes, 'Title': titles, 'CRN': crns,
                'Cap': caps, 'Enrl': enrls, 'Avail': avails,
                'Instructor': instrs, 'Dates': dates})

df.to_csv('test.csv', sep='\t', encoding='utf-8')