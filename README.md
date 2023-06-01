# Stuttgart events RSS Generator

This script is a Python script for generating RSS feeds by scraping event data from a website.

## Prerequisites

Before running the script, make sure you have the following prerequisites installed:

- Python 3.x
- `requests` library
- `bs4` library (BeautifulSoup)
- `pytz` library
- `ics` library

You can install the required libraries using pip:

```shell
pip install -r reqs/requirements.txt

```

## Usage

To use the script, follow these steps:

1. Clone the repository or download the script to your local machine.
2. Open the script in a Python IDE or editor.
3. Set up the desired configuration in the script, such as RSS feed name, title, and category.
4. Run the script using Python 3.x.

```shell
python rss_generator.py
```

The script will scrape the event data from the specified website and generate an RSS feed file in the same directory as the script. The generated RSS feed file will be named according to the specified `rss_name` variable.

## Configuration

The script provides several configuration options that you can modify:

- `rss_name`: The name of the generated RSS feed file.
- `rss_title`: The title of the RSS feed.
- `rss_category`: The category ID of the events to scrape.
- `destination_folder`: The folder where the RSS feed file and log files will be moved after generation.

Make sure to update these variables according to your requirements before running the script.

## Logging

The script uses the logging module to log its activities. The log file is named `rss_generator.log` and is generated in the same directory as the script. The log level is set to INFO, which means that informational messages will be logged. You can change the log level or customize the logging configuration as needed.

## Contributing

Contributions to this script are welcome! If you find any issues or have suggestions for improvements, please feel free to create an issue or submit a pull request.

## License

This script is licensed under the GNU General Public License (GPL). Feel free to use, modify, and distribute it as per the terms of the license.
