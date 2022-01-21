Written with Python 3.8.10

The script scrapes photos from https://mamba.ru/ dating site. Search filters
can be configured immediately on the search webpage in a browser window.
The results are saved to a folder ("./img/" - by default).

In order to make things working the Firefox and Selenium Webdriver should be
installed. Both of them can be downloaded from the official Firefox browser
website. Note: after installation the Windows system variable PATH should be
modified manually in order to keep actual path to Firefox Webdriver.

HOW TO USE

For the first run and setting up new search filters:

    python mamba_scraper.py --set-filters

It will open a browser window showing search page. Switch back to console when
all the filters are configured and press ENTER.

For resuming previously interrupted script execution:

    python mamba_scraper.py

Feel free to use and modify it as needed.

For dependencies refer to requirements.txt.
