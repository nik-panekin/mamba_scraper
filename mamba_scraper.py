import logging
import sys
import os

from requests.cookies import RequestsCookieJar
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from utils.http_request import HttpRequest
from utils.scraping_utils import (
    FATAL_ERROR_STR,

    setup_logging,

    save_items_json,
    load_items_json,
)

SEARCH_URL = 'https://www.mamba.ru/ru/search/list'
API_URL = 'https://www.mamba.ru/api/search'

CURSOR_FILENAME = 'cursor.json'
COOKIES_FILENAME = 'cookies.json'
DUMP_FILENAME = 'dump.json'

IMAGE_DIR = 'img'

SLEEP_TIME = 0

request = None # Global HttpRequest object

def close_driver(driver) -> bool:
    try:
        driver.close()
    except Exception:
        logging.exception('Error while webdriver closing.')
        return False

    return True

def get_selenium_cookies():
    print("Setting up search filters. WARNING: don't close browser window.")

    try:
        driver = webdriver.Firefox()
    except Exception:
        logging.exception('Error while webdriver initializing.')
        return None

    try:
        driver.get(SEARCH_URL)
    except TimeoutException:
        logging.exception(f'Timeout while loading [{SEARCH_URL}] page.')
        close_driver(driver)
        return None

    input('Press ENTER when ready.')

    cookies = driver.get_cookies()

    close_driver(driver)
    return cookies

def get_cookie_jar(cookies: dict) -> RequestsCookieJar:
    jar = RequestsCookieJar()

    for cookie in cookies:
        jar.set(cookie['name'], cookie['value'])

    return jar

def save_cursor(cursor: dict) -> bool:
    return save_items_json(cursor, CURSOR_FILENAME)

def load_cursor() -> dict:
    if os.path.exists(CURSOR_FILENAME):
        cursor = load_items_json(CURSOR_FILENAME)
    else:
        cursor = None

def delete_cursor() -> bool:
    if os.path.exists(CURSOR_FILENAME):
        try:
            os.remove(CURSOR_FILENAME)
        except OSError:
            logging.warning(f"Can't delete the file {CURSOR_FILENAME}.")
            return False

    return True

def scrape_page_items(cursor: dict = None) -> dict:
    global request

    params = {
        'statusNames': 'hasVerifiedPhoto',
        'limit': '56',
    }

    if cursor:
        params['cursor[type]'] = cursor['type'],
        params['cursor[searchId]'] = str(cursor['searchId']),
        params['cursor[searcherOffset]'] = str(cursor['searcherOffset'])
    else:
        params['cursor[searchId]'] = '0'
        params['cursor[searcherOffset]'] = '0'

    r = request.get(API_URL, params=params)

    if not r:
        return None

    try:
        json = r.json()
    except Exception as e:
        logging.exception('Error while getting JSON.')
        return None

    try:
        for item in json['items']:
            # if item['gender'] == 'M':
            #     continue

            image_filename = os.path.join(
                IMAGE_DIR, str(item['profile']['id']) + '.jpg')
            image_url = item['userpic']['huge']

            if request.save_image(image_url, image_filename):
                logging.info(f'Image saved: {image_filename}.')

    except KeyError:
        logging.exception('Error while parsing JSON.')
        save_items_json(json, DUMP_FILENAME)
        return None

    try:
        cursor = json['cursor']
    except KeyError:
        logging.exception("Can't read cursor value from JSON. "
                          'Maybe no items left.')
        save_items_json(json, DUMP_FILENAME)
        return None

    return cursor

def scrape_all_items():
    cursor = load_cursor()
    if cursor:
        logging.info('Continue scraping. '
                     + f"Cursor position: {cursor['searcherOffset']}.")

    while True:
        cursor = scrape_page_items(cursor)
        if cursor is None:
            return False

        save_cursor(cursor)

        logging.info('Page processed. '
                     + f"Cursor position: {cursor['searcherOffset']}.")
    return True

def main():
    global request

    setup_logging()

    logging.info('Starting scraping process.')

    if '--set-filters' in sys.argv:
        cookies = get_selenium_cookies()
        if cookies:
            save_items_json(cookies, 'cookies.json')
        else:
            logging.warning("Can't get cookies for search filters.")

        delete_cursor()
    else:
        cookies = load_items_json(COOKIES_FILENAME)

    if cookies:
        request = HttpRequest(sleep_time=SLEEP_TIME,
                              cookies=get_cookie_jar(cookies))
    else:
        request = HttpRequest(sleep_time=SLEEP_TIME)

    completed = scrape_all_items()
    if not completed:
        logging.error(FATAL_ERROR_STR)
        return

if __name__ == '__main__':
    main()
