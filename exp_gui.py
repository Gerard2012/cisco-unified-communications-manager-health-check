##############################################################################################
# modules
##############################################################################################

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import logging


##############################################################################################
# Functions
##############################################################################################

def expressway_alarm_cleanup(node, username, password):

    license_alarms = [
        'Room system license limit reached',
        'Capacity warning',
        'Call license limit reached'
    ]

    path_to_webdriver = 'D:\\NetOps Apps\\Scripts\\uc_checks\\WebDrivers\\chromedriver.exe'

    if '-expe-' in str(node) or '-EXPE-' in str(node):
        node_url = f'https://{node}:7443/login'
    else:
        node_url = f'https://{node}/login'


    # create a new Chrome session
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(executable_path=path_to_webdriver)

    # Navigate to the application home page
    driver.get(node_url)

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'save_button')))
        logging.debug('## {} - {}.expressway_alarm_cleanup() -- GUI RESPONDING'.format(__name__, node))
    except:
        driver.quit()

    driver.maximize_window()

    # Authenticate
    username_field = driver.find_element_by_id('username')
    username_field.clear()
    username_field.send_keys(username)

    password_field = driver.find_element_by_id('password')
    password_field.clear()
    password_field.send_keys(password)

    login_button = driver.find_element_by_id('save_button')
    login_button.click()

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'warningicon')))
        logging.debug('## {} - {}.expressway_alarm_cleanup() -- AUTHENTICATION SUCCESSFUL'.format(__name__, node))
    except:
        logging.debug('## {} - {}.expressway_alarm_cleanup() -- NO ALARMS, QUITTING'.format(__name__, node))
        driver.quit()


    # Navigate to alarms page
    try:
        driver.find_element_by_id('warningicon').click()
    except:
        logging.debug('## {} - {}.expressway_alarm_cleanup() -- NO ALARMS, QUITTING'.format(__name__, node))
        driver.quit()

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'warninglist_tbody')))
    except:
        driver.quit()


    # Capture number of alarms
    alarm_rows = len(driver.find_elements_by_xpath('//*[@id="warninglist_tbody"]/tr'))
    logging.debug('## {} - {}.expressway_alarm_cleanup() -- ALARMS == {}'.format(__name__, node, alarm_rows))

    # Action licensing alarms
    alarm_index = 1
    while alarm_index <= alarm_rows:
        alarm_title = driver.find_element_by_xpath(f'//*[@id="warninglist_tbody"]/tr[{alarm_index}]/td[2]')
        alarm_state = driver.find_element_by_xpath(f'//*[@id="warninglist_tbody"]/tr[{alarm_index}]/td[4]')
        alarm_peer = driver.find_element_by_xpath(f'//*[@id="warninglist_tbody"]/tr[{alarm_index}]/td[6]')

        if alarm_title.text in license_alarms and alarm_peer.text == 'This system' and alarm_state.text != 'Acknowledged':
            driver.find_element_by_xpath(f'//*[@id="warninglist_tbody"]/tr[{alarm_index}]/td[1]').click()
            logging.debug('## {} - {}.expressway_alarm_cleanup() -- ALARM {} SELECTED'.format(__name__, node, alarm_index))

            driver.find_element_by_xpath('/html/body/div[2]/div/form/div[2]/input[1]').click()
            logging.debug('## {} - {}.expressway_alarm_cleanup() -- ALARMS ACKNOWLEDGED'.format(__name__, node))
        else:
            pass

        alarm_index += 1

    else:
        driver.quit()


##############################################################################################
# Run
##############################################################################################

if __name__ == '__main__':

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

    pass
