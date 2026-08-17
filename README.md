# match_predictions

Predicts whether a Premier League team wins a given match, using a random forest over rolling form.

Small project, two scripts. One scrapes the data, one trains and evaluates the model.

## What it predicts

A binary target per team per match: did this team win (`result == "W"`), yes or no. Every fixture appears twice in the data, once from each team's perspective, which matters for the last step below.

## Where the data comes from

`scrape.py` pulls from [FBref](https://fbref.com), starting at the Premier League stats page (`/en/comps/9/Premier-League-Stats`) and walking backwards through the "previous season" link.

For each team in each season it fetches two tables and merges them on date:

- Scores & Fixtures (result, goals for and against, venue, opponent, possession, attendance, formation, referee)
- Shooting (shots, shots on target, average shot distance, free kicks, penalties, xG, npxG)

Non Premier League competitions are filtered out, so cup and European fixtures do not leak in. There is a 4 second sleep between teams to stay polite to the server. Output is written to `matches.csv`.

The committed `matches.csv` covers four seasons (2020/21 through 2023/24) at 3,040 rows.

## The features

`analysis.py` builds two groups of predictors.

Straightforward categorical and time encodings:

| Feature | What it is |
|---|---|
| `venue_code` | home or away, as a category code |
| `opp_code` | which opponent, as a category code |
| `hour` | kickoff hour, parsed off the front of the time string |
| `day_code` | day of week |

Rolling form, which is the part doing the real work. For each of `gf`, `ga`, `sh`, `sot`, `dist`, `fk`, `pk`, `pkatt`, the script groups by team, sorts by date, and takes a 3 match rolling mean:

```python
rolling_stats = group[cols].rolling(3, closed='left').mean()
```

`closed='left'` is the important argument. It excludes the current match from its own rolling window, so the model only sees form from the three matches *before* the one it is predicting. Rows without a full window are dropped.

## The model

`RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)`.

The split is by date rather than random, so it is a clean forward looking holdout: everything before 2023-06-06 trains, everything after tests. In practice that trains on the 2020/21 through 2022/23 seasons and tests on 2023/24.

The script computes `precision_score` on the test set and prints it. Precision is the metric of interest here rather than accuracy, since the useful question is how often a predicted win is actually a win.

The final step merges the table onto itself on date and opponent to line up both halves of each fixture, using a small name mapping (`MissingDict`) to reconcile FBref's inconsistent club naming ("Manchester United" vs "Manchester Utd"). It then reports outcomes for fixtures where the model predicted one side to win and the other side not to win, which is the subset where the two per team predictions actually agree.

## Running it

Needs Python 3.9+.

```bash
git clone https://github.com/KJ-11/match_predictions.git
cd match_predictions/match_predictions

pip install pandas scikit-learn requests beautifulsoup4 lxml
```

Both scripts use relative paths, so run them from inside the `match_predictions/match_predictions` directory.

Train and evaluate on the committed data:

```bash
python analysis.py
```

Re-scrape from FBref (slow, roughly 4 seconds per team per season, and it overwrites `matches.csv`):

```bash
python scrape.py
```

## Honest scope

This is a small project, around 130 lines across two files. The feature set is basic, there is no hyperparameter search, no cross validation, and no calibration. The one thing it does carefully is avoid leaking the current match into its own form features.
