import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Define the range of years to gather data for Premier League teams
years = list(range(2024, 2020, -1))

# Initialize a list to hold data for all matches across all teams and years
all_matches = []

# Starting URL for fetching Premier League standings from FBRef
standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

# Loop through each year to collect data
for year in years:
    response = requests.get(standings_url)
    soup = BeautifulSoup(response.text, features="lxml")
    standings_table = soup.select('table.stats_table')[0]
    team_links = [link['href'] for link in standings_table.find_all('a', href=True) if '/squads/' in link['href']]

    # Generate full URLs for each team's page by appending the base domain
    team_urls = ["https://fbref.com" + link for link in team_links]

    # Update standings_url to the previous season for the next loop iteration
    previous_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com{previous_season}"

    # Process each team's URL to gather match and shooting data
    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]
        
        soup = BeautifulSoup(data.text, features="lxml")
        links = [l.get("href") for l in soup.find_all("a")]
        shooting_link = [l for l in links if l and "all_comps/shooting/" in l]
        data = requests.get("https://fbref.com" + shooting_link[0])
        shooting = pd.read_html(data.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()

        # Attempt to merge match data with shooting data and handle any exceptions
        try:
            combined_team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "Gls", "PK", "PKatt", "xG", "npxG", "npxG/Sh", "G-xG", "np:G-xG"]], on="Date")
        except ValueError:
            continue  # Skip to the next team if the merge fails

        # Filter the combined data for Premier League competitions only
        team_data = combined_team_data[combined_team_data["Comp"] == "Premier League"]
        team_data["Season"] = year
        team_data["Team"] = team_name
        all_matches.append(team_data)
        time.sleep(4)  # Add delay to prevent rapid requests to the server

# Concatenate all collected data into a single DataFrame and rename columns to lowercase
match_df = pd.concat(all_matches)
match_df.columns = [c.lower() for c in match_df.columns]
# Save the data to a CSV file
match_df.to_csv("matches.csv")

match_df["team"].value_counts()
