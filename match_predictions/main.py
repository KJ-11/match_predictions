import requests
import pandas as pd

from bs4 import BeautifulSoup

standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

data = requests.get(standings_url)

soup = BeautifulSoup(data.text, features="lxml")
standings_table = soup.select('table.stats_table')[0]
links = standings_table.find_all('a')
links = [l.get('href') for l in links]
links = [l for l in links if '/squads/' in l]

team_urls = ["https://fbref.com" + l for l in links]

team_url = team_urls[0]
team_data = requests.get(team_url)

matches = pd.read_html(team_data.text, match="Scores & Fixtures")