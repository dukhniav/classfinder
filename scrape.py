# import libraries
import re
import time
from urllib.request import urlopen as uReq

import numpy as np
from bs4 import BeautifulSoup as soup
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm


CURR_SUBJ = ''                   # current subject
CLASSES = []                     # full list of classes


##########
#
#   v1.3
#
##########


def browser_headless():
    # making firefox headless
    fire_options = Options()
    fire_options.add_argument("--headless")
    return fire_options


def load_page(client):
    html_page = client.read()
    return html_page


def open_url(url):
    client = uReq(url)
    return client


def close_url(client):
    # close connection
    client.close()


def parse_page(page):
    # html parser
    page_soup = soup(page, "html.parser")
    return page_soup


def get_subject_options(page_soup):
    # get Subject options
    options = page_soup.select('select[name=sel_subj] > option')
    string = str(options)
    subj_temp = re.findall(r'"([^"]*)"', string)

    # make list of all subjects
    subj_options = subj_temp[2:]
    return subj_options


def init_browser(url):
    # "firefox_options=fire_options" --> headless firefox
    driver = webdriver.Firefox(firefox_options=browser_headless(),
                               executable_path="/home/artem/projects/scrape/drivers/geckodriver")

    driver.get(url)
    return driver


def get_subjects(driver):
    table = driver.find_element_by_name('sel_subj')
    return table


def select_first_option(driver, subj):
    global CURR_SUBJ

    # unselect first option
    driver.find_element_by_xpath("//select[@name='sel_subj']/option[text()='All Subjects']").click()
    # select wanted subject
    driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='" + subj + "']").click()
    CURR_SUBJ = subj


def select_rest_options(driver, subj):
    global CURR_SUBJ

    # unselect first option
    driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value= '" + CURR_SUBJ + "']").click()
    time.sleep(.5)
    # select wanted subject
    driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='" + subj + "']").click()
    CURR_SUBJ = subj
    time.sleep(.3)


def write_to_file(avails, caps, classes, crns, dates, enrls, instrs, titles, filename):
    df = DataFrame({'Class': classes, 'Title': titles, 'CRN': crns,
                    'Cap': caps, 'Enrl': enrls, 'Avail': avails,
                    'Instructor': instrs, 'Dates': dates})
    df.to_csv(filename, sep='\t', encoding='utf-8')


def get_final_class_list(flat_classes_final):
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
    return avails, caps, classes, crns, dates, enrls, instrs, titles


def flatten_class_lists(flat_classes):
    for x in CLASSES:
        for i in x:
            flat_classes.append(i)


def remove_elements_repeating(header_table):
    for entry in header_table:
        if entry == 'CLOSED                               ':
            header_table.remove(entry)
        if entry == ' ':
            header_table.remove(entry)
        if entry == '\xa0':
            header_table.remove(entry)


def get_crns(crn, new_soup):
    crns = new_soup.find_all('input', {'name': 'sel_crn'})
    crn_ctr = 1
    for x in crns:
        crn.append(x.get('value'))
        crn_ctr = crn_ctr + 1


def submit_button_click(driver):
    submit = '//input[@type="submit" and @value="Search Now"]'
    driver.find_element_by_xpath(submit).click()


def get_class_list(driver, subjects):
    first_go = True
    for subj in tqdm(subjects):
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

        new_table = []
        crn = []

        flat_classes = []

        if first_go:
            select_first_option(driver, subj)
        else:
            select_rest_options(driver, subj)

        # click submit button
        submit_button_click(driver)

        time.sleep(.5)

        new_soup = soup(driver.page_source, "html.parser")

        map_tag = new_soup.map

        table_tag = map_tag.contents[11]

        # list of crns, which are not part of > <, same order
        get_crns(crn, new_soup)

        # find everything between > <
        for child in table_tag.children:
            temp = re.findall(r'>(.*?)<', repr(child))
            if len(temp) > 0:
                new_table = temp

        # removing empty spaces
        table = list(filter(None, new_table))

        # remove 15 first spots for headers of table
        header_table = table[15:]

        # remove "CLOSED" and other elements in list
        remove_elements_repeating(header_table)

        # make array to preserve element arrangment with duplicates
        nptable = np.array(header_table)

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

        CLASSES.append(single_class_list)

        time.sleep(.5)

        # back button
        driver.execute_script("window.history.go(-1)")
        time.sleep(.5)

    # to flatten out the list of Classes
    flatten_class_lists(flat_classes)

    # removing empty spaces
    flat_classes_final = list(filter(None, flat_classes))

    avails, caps, classes, crns, dates, enrls, instrs, titles = get_final_class_list(flat_classes_final)

    write_to_file(avails, caps, classes, crns, dates, enrls, instrs, titles, 'test.csv')


def main():
    # address of ClassFinder
    my_url = 'https://admin.wwu.edu/pls/wwis/wwsktime.SelClass'

    # opening url, grabbing page
    client = open_url(my_url)

    # offload content into variable
    html_page = load_page(client)
    close_url(client)

    # parse contents of html page
    page_soup = parse_page(html_page)

    # retrieve list of subj options
    subjects = get_subject_options(page_soup)

    # init headless browser
    driver = init_browser(my_url)

    get_class_list(driver, subjects)


if __name__ == '__main__':
    main()
