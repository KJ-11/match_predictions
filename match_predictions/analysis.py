import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score

# Load data
matches = pd.read_csv("./matches.csv", index_col=0)
matches["date"] = pd.to_datetime(matches["date"])
matches["venue_code"] = matches["venue"].astype("category").cat.codes
matches["opp_code"] = matches["opponent"].astype("category").cat.codes
matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype(int)
matches["day_code"] = matches["date"].dt.dayofweek
matches["target"] = (matches['result'] == "W").astype(int)

# Initialize RandomForestClassifier
rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)
predictors = ["venue_code", "opp_code", "hour", "day_code"]

# Function to calculate rolling averages
def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3, closed='left').mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
new_cols = [f"{c}_rolling" for c in cols]

# Apply rolling averages
matches_rolling = matches.groupby("team", group_keys=False).apply(lambda x: rolling_averages(x, cols, new_cols))
matches_rolling.index = range(matches_rolling.shape[0])

# Function to make predictions
def make_predictions(data, predictors):
    train = data[data["date"] < "2023-06-06"]
    test = data[data["date"] >= "2023-06-06"]
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], prediction=preds), index=test.index)
    precision = precision_score(test["target"], preds)
    return combined, precision

# Make predictions
combined, precision = make_predictions(matches_rolling, predictors + new_cols)

combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

class MissingDict(dict):
    __missing__ = lambda self, key: key

map_values = {
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcastle United": "Newcastle Utd",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves"
}

mapping = MissingDict(**map_values)

combined["new_team"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on = ["date", "new_team"], right_on = ["date", "opponent"])
print(merged[(merged["prediction_x"] == 1) & (merged["prediction_y"] == 0)]["actual_x"].value_counts())