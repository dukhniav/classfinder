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
TERM = ''
CRN_TOTAL = 0


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
   global TERM

   print("\n Current term: " + TERM)

   # select term
   driver.find_element_by_xpath("//select[@name='term']/option[@value='" + TERM + "']").click()

   # unselect first option
   driver.find_element_by_xpath("//select[@name='sel_subj']/option[text()='All Subjects']").click()

   # driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='MUS']").click()

   # # select wanted subject
   driver.find_element_by_xpath("//select[@name='sel_subj']/option[@value='" + subj + "']").click()
   CURR_SUBJ = subj


def select_rest_options(driver, subj):
   global CURR_SUBJ
   global TERM

   # select term
   driver.find_element_by_xpath("//select[@name='term']/option[@value='" + TERM + "']").click()

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

   """
   print(str(len(classes)) + ", " + str(len(titles)) + ", " + str(len(crns)) + ", " + str(len(caps)) + ", " + str(len(enrls))
         + ", " + str(len(avails)) + ", " + str(len(instrs)) + ", " + str(len(dates)))
    """
   return avails, caps, classes, crns, dates, enrls, instrs, titles


def flatten_class_lists(flat_class_list):
   for class_list in CLASSES:
       for entry in class_list:
           flat_class_list.append(entry)
   return flat_class_list


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


def get_class(classes, new_soup):
   class_list = new_soup.find_all("font", {'size':'-1'})
   # print(class_list)
   class_list_ctr = 1
   for x in class_list:
       classes.append(x.text)
       # print(str(class_list_ctr) + ": " + x.text)
       class_list_ctr = class_list_ctr + 1
   return classes


def submit_button_click(driver):
   submit = '//input[@type="submit" and @value="Search Now"]'
   driver.find_element_by_xpath(submit).click()


def get_class_list(driver, subjects):
    global CRN_TOTAL

    first_go = True
    for subj in tqdm(subjects):
       crn_counter = 0  # counter to keep track of how many CRNs have been assigned
       crn = []
       classes = []

       flat_classes = []

       if first_go:
           select_first_option(driver, subj)
       else:
           select_rest_options(driver, subj)

       # click submit button
       submit_button_click(driver)

       time.sleep(.5)

       new_soup = soup(driver.page_source, "html.parser")

       # list of crns, which are not part of > <, same order
       get_crns(crn, new_soup)

       CRN_TOTAL += len(crn)

       # print("The number of CRNS in *" + subj + ": " + str(len(crn)))

       parts_list = get_class(classes, new_soup)

       test_ctr = 0
       temp_parts_ctr = 0
       temp_parts_list = []
       class_list = []
       temp_ctr = 1
       for entry in parts_list:
           if test_ctr > 12:
               # subject
               if CURR_SUBJ in entry and len(entry) < 10:  # -> "MUS" = CUR_SUBJ
                   # print(str(temp_ctr) + ": " + entry)
                   temp_ctr += 1
                   temp_parts_ctr = 0
                   temp_parts_list.append(entry)
               # title
               if temp_parts_ctr == 1:
                   temp_parts_list.append(entry)
                   temp_parts_list.append(crn[crn_counter])
                   crn_counter += 1
               # cap
               if temp_parts_ctr == 2:
                   temp_parts_list.append(entry)
               # enrl
               if temp_parts_ctr == 3:
                   temp_parts_list.append(entry)
               # avail
               if temp_parts_ctr == 4:
                   temp_parts_list.append(entry)
               # prof
               if temp_parts_ctr == 5:
                   temp_parts_list.append(entry)
               # dates
               if temp_parts_ctr == 6:
                   temp_parts_list.append(entry)
               temp_parts_ctr += 1


               #print("DB: Parts List -> " + ": " + str(temp_parts_list))
               #print("DB: Parts List Length -> " + ": " + str(len(temp_parts_list)))


               # add parts of single class to overall list of classes for subject
               if temp_parts_ctr == 7 and len(temp_parts_list) == 8:
                   for x in temp_parts_list:
                       class_list.append(x)
                   temp_parts_list.clear()
                   # print(" --done")

           test_ctr += 1


       # needed to check the right options
       first_go = False

       #print(class_list)

       CLASSES.append(class_list)

       time.sleep(.5)

       # back button
       driver.execute_script("window.history.go(-1)")
       time.sleep(.5)

    print(CRN_TOTAL)


    # to flatten out the list of Classes
    new_flat_classes = flatten_class_lists(flat_classes)

    # removing empty spaces
    flat_classes_final = list(filter(None, new_flat_classes))

    avails, caps, classes, crns, dates, enrls, instrs, titles = get_final_class_list(flat_classes_final)

    write_to_file(avails, caps, classes, crns, dates, enrls, instrs, titles, 'test.csv')


def main():
   global TERM
   # address of ClassFinder
   my_url = 'https://admin.wwu.edu/pls/wwis/wwsktime.SelClass'

   # Winter 2019
   TERM = '201910'

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

