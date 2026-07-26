import pandas as pd                          # data manipulation library
import numpy as np                           # numerical operations
from sklearn.model_selection import train_test_split  # split data into train/test sets
from sklearn.ensemble import RandomForestClassifier   # the ML model we will train
from sklearn.preprocessing import LabelEncoder        # convert text labels to numbers
from sklearn.metrics import (
    accuracy_score, classification_report,   # measure how well the model predicts
    roc_auc_score, confusion_matrix          # additional evaluation metrics
)
import matplotlib.pyplot as plt  # draw charts
import seaborn as sns            # nicer-looking charts built on matplotlib
import pickle                    # save/load Python objects (our trained model)
import os                        # file and folder operations

# ── 1. Load data ────────────────────────────────────────────────────────────
df = pd.read_csv('data/raw/deliveries.csv')  # load CSV into a DataFrame
print(f"Loaded {len(df):,} records")         # :, adds thousands separator e.g. 50,000

# ── 2. Feature engineering ──────────────────────────────────────────────────
# Encode categorical features as numbers (ML needs numbers, not strings)
le_address  = LabelEncoder()  # one encoder per column (each learns its own mapping)
le_window   = LabelEncoder()
le_city     = LabelEncoder()

# fit_transform does two steps in one call:
#   fit()       → scans the column and learns the unique values e.g. ['Apartment','House','Office']
#               → assigns each a number:  Apartment→0, House→1, Office→2
#   transform() → applies that mapping to every row, returning the number column
# fit_transform() = fit() then transform() back to back (shortcut for training data)
# IMPORTANT: only call fit_transform() on training data; call transform() alone on new/test data
#            so the same mapping is applied (not re-learned from scratch)
# → "Apartment" → 0,  "Evening (15-19)" → 1,  "Mumbai" → 3  (exact numbers depend on sort order)
df['address_type_enc']    = le_address.fit_transform(df['address_type'])    # fit = learn mapping, transform = apply it
df['delivery_window_enc'] = le_window.fit_transform(df['delivery_window'])  # e.g. "Morning" → 2
df['city_enc']            = le_city.fit_transform(df['city'])               # e.g. "Mumbai" → 3

# Order value buckets (bucketing reduces noise)
# pd.cut splits a continuous column into labelled ranges (buckets)
# bins=[0, 500, 1500, 3000, 10000] defines 4 ranges (each pair of neighbours is one bucket):
#   bucket 0 → (0, 500]     e.g. order_value=300  → label 0  (Low)
#   bucket 1 → (500, 1500]  e.g. order_value=999  → label 1  (Mid)
#   bucket 2 → (1500, 3000] e.g. order_value=2000 → label 2  (High)
#   bucket 3 → (3000,10000] e.g. order_value=5000 → label 3  (Premium)
# Note: the left edge is exclusive (not included), right edge is inclusive
# → value exactly 500 goes into bucket 0; value 501 goes into bucket 1
df['order_value_bucket'] = pd.cut(
    df['order_value'],
    bins=[0, 500, 1500, 3000, 10000],  # edges of each bucket
    labels=[0, 1, 2, 3]               # label each bucket 0-3 (low to high)
).astype(int)                          # convert to integer so model can use it

FEATURES = [
    'address_type_enc',         # encoded address type (Apartment, House, etc.)
    'delivery_window_enc',      # encoded time window (Morning, Evening, etc.)
    'city_enc',                 # encoded city name
    'order_value_bucket',       # order value group (0=cheapest, 3=most expensive)
    'attempt_number',           # 1st attempt vs re-attempt
    'has_delivery_preference',  # 1 if customer set a preference, 0 if not
    'proximity_alert_sent',     # 1 if customer was alerted before delivery
]
TARGET = 'is_successful'  # what we are trying to predict (1=success, 0=fail)

X = df[FEATURES]  # input columns (what the model sees)
y = df[TARGET]    # output column (what the model predicts)

# y.value_counts() → counts how many rows have each unique value, e.g. {1: 38000, 0: 12000}
# .to_dict()       → converts the Series into a plain Python dict so it prints cleanly
# → tells you if the dataset is imbalanced (many more successes than failures or vice versa)
print(f"Class balance: {y.value_counts().to_dict()}")  # show ratio of 1s to 0s

# ── 3. Train / test split ───────────────────────────────────────────────────
# What train/test split means and why: you cannot evaluate a model on the same
# data it was trained on — it has already "seen" those answers. The split holds
# back 20% of records (test_size=0.2) as an unseen test set. The model trains on
# the 80%, then you measure accuracy on the 20% it never saw. This gives an honest
# estimate of how it will perform on new, real-world deliveries.
#
# What stratify=y does: ensures the train and test sets have the same ratio of
# successes to failures as the full dataset. Without stratify, a random split
# might accidentally put most failures in training and few in test, making
# evaluation misleading. stratify=y preserves the class proportions in both halves.
# train_test_split returns 4 things in this exact order:
#   X_train → 80% of input rows  (model learns from these)
#   X_test  → 20% of input rows  (model is evaluated on these — never seen during training)
#   y_train → matching labels for X_train
#   y_test  → matching labels for X_test
# → if X has 50,000 rows: X_train gets 40,000 rows, X_test gets 10,000 rows
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
    # test_size=0.2 → keep 20% for testing, train on 80%
    # random_state=42 → fixed seed so results are the same every run
    # stratify=y → keep the same success/fail ratio in both halves
)
print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── 4. Train model ──────────────────────────────────────────────────────────
model = RandomForestClassifier(
    n_estimators=100,   # build 100 decision trees and combine their votes
    max_depth=8,        # each tree can be at most 8 levels deep (prevents overfitting)
    random_state=42,    # fixed seed for reproducibility
    n_jobs=-1     # What n_jobs=-1 means: use all available CPU cores in parallel
                  # to train the random forest. -1 is a convention meaning "use
                  # everything available." Training 100 trees is embarrassingly
                  # parallel — each tree is independent — so this gives a significant
                  # speedup on a multi-core machine.
)
# model.fit(X_train, y_train) is where training actually happens:
#   → the model looks at each row in X_train alongside its label in y_train
#   → it builds 100 decision trees, each learning rules like:
#      "if delivery_window_enc == 2 AND has_delivery_preference == 1 → likely success"
#   → after fit() the model object stores all 100 trees internally
#   → fit() changes the model object in-place; it returns self but you don't need to capture it
model.fit(X_train, y_train)  # train: model learns patterns from 80% of data
print("Model trained.")

# ── 5. Evaluate ─────────────────────────────────────────────────────────────
# What predict vs predict_proba is: model.predict() returns a hard decision —
# either 0 (fail) or 1 (success) — for each delivery. model.predict_proba()
# returns a probability between 0 and 1 for each class. [:, 1] takes the
# probability of the positive class (success). Probabilities are more useful
# than hard decisions because you can set your own threshold — e.g. flag any
# delivery with a success probability below 60% for special handling.
#
# What ROC-AUC means in plain terms: ROC-AUC measures how good the model is at
# ranking — does it consistently give high probabilities to deliveries that will
# actually succeed and low probabilities to those that will fail? 0.5 = random
# guessing (useless), 1.0 = perfect. A score above 0.80 is considered strong
# for a real-world prediction problem.
y_pred = model.predict(X_test)           # hard predictions: 0 or 1

# predict_proba(X_test) returns a 2D array with one row per delivery, two columns:
#   column 0 = probability of class 0 (failure)
#   column 1 = probability of class 1 (success)
# example output for 3 rows:
#   [[0.72, 0.28],   ← 28% chance of success
#    [0.15, 0.85],   ← 85% chance of success
#    [0.60, 0.40]]   ← 40% chance of success
#
# [:, 1] is a numpy 2D slice — it means:
#   :   = all rows (every delivery)
#   , 1 = column index 1 (the "success probability" column)
# → result is a 1D array: [0.28, 0.85, 0.40, ...]  — one probability per delivery
y_prob = model.predict_proba(X_test)[:, 1]  # [:, 1] = probability of success (class 1)

# accuracy_score: compares y_test (actual labels) vs y_pred (predicted labels)
# → counts how many predictions matched → divides by total → returns a fraction
# → e.g. 8340 correct out of 10000 → accuracy = 0.834 (print as 83.40% below)
acc    = accuracy_score(y_test, y_pred)       # % of predictions that were correct
# roc_auc_score needs probabilities (y_prob), not hard labels — it measures ranking quality
# → 0.5 = model is no better than random guessing (coin flip)
# → 1.0 = model perfectly ranks every success above every failure
# → 0.88 means: pick any random success and any random failure — 88% of the time
#   the model gave the success a higher probability score
roc    = roc_auc_score(y_test, y_prob)        # ranking quality score (0.5–1.0)

# f-string format spec :.2% multiplies by 100 and appends %, with 2 decimal places
# → acc = 0.834  →  f"{acc:.2%}"  →  "83.40%"
print(f"\nAccuracy : {acc:.2%}")   # format as percentage e.g. 83.40%
# f-string format spec :.4f means fixed-point with 4 decimal places
# → roc = 0.88214  →  f"{roc:.4f}"  →  "0.8821"
print(f"ROC-AUC  : {roc:.4f}")    # format to 4 decimal places
# classification_report prints a table with per-class precision, recall, and F1-score
# → precision: of all predictions of class X, what fraction were actually X?
# → recall: of all actual class X rows, what fraction did the model catch?
# → F1: harmonic mean of precision and recall (single balanced score)
print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")  # precision, recall, F1

# ── 6. Feature importance ───────────────────────────────────────────────────
# What feature importance means: the model measures how much each input feature
# contributed to making correct predictions. A high importance score means
# "when this feature changes, the prediction changes a lot." This tells you which
# factors most affect delivery success — useful for deciding where to invest
# (e.g. if delivery_window is the top feature, optimising time slots matters most).
# model.feature_importances_ is a numpy array of floats, one per feature, summing to 1.0
# → e.g. [0.31, 0.27, 0.08, 0.14, 0.09, 0.07, 0.04]
# pd.Series(..., index=FEATURES) wraps those numbers into a Series labelled with feature names
# → delivery_window_enc: 0.31,  address_type_enc: 0.27,  city_enc: 0.08, ...
# .sort_values(ascending=False) reorders highest → lowest so the most important is first
importance = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
# sort_values(ascending=False) = highest importance at the top
print(f"\nFeature Importance:\n{importance}")

# ── 7. Save charts ──────────────────────────────────────────────────────────
os.makedirs('data/processed', exist_ok=True)  # exist_ok=True = don't error if folder exists

# plt.subplots(rows, cols, figsize=(width_inches, height_inches))
# → (1, 2) creates a grid with 1 row and 2 columns = two side-by-side chart panels
# → figsize=(14, 5) = the whole figure is 14 inches wide and 5 inches tall
# → fig = the overall canvas;  axes = array of 2 Axes objects: axes[0] (left), axes[1] (right)
# → pass ax=axes[0] or ax=axes[1] to each plot call to control which panel it draws into
fig, axes = plt.subplots(1, 2, figsize=(14, 5))  # 1 row, 2 charts side-by-side, 14x5 inches

# Confusion matrix
# confusion_matrix returns a 2x2 array:
#                  Predicted Failed  Predicted Success
#   Actual Failed  [ TN (true neg),   FP (false pos) ]
#   Actual Success [ FN (false neg),  TP (true pos)  ]
# → large TN and TP = model is mostly right
# → large FP = model wrongly predicts success (over-optimistic)
# → large FN = model misses real successes (under-confident)
cm = confusion_matrix(y_test, y_pred)  # rows=actual, cols=predicted
# sns.heatmap draws the 2x2 array as a coloured grid
# annot=True  → write the number from cm into each coloured cell
# fmt='d'     → format those numbers as plain integers (d = decimal integer), not 1.2e3 notation
# cmap='Blues'→ colour scale: low count = light blue, high count = dark blue
# ax=axes[0]  → draw this chart into the LEFT panel of the figure
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
            xticklabels=['Failed', 'Success'], yticklabels=['Failed', 'Success'])
axes[0].set_title('Confusion Matrix')  # chart title
axes[0].set_ylabel('Actual')           # y-axis label
axes[0].set_xlabel('Predicted')        # x-axis label

# Feature importance
# importance is already sorted highest→lowest, but plot() draws the first item at the BOTTOM
# of a horizontal bar chart (matplotlib draws Series from top to bottom in reverse)
# kind='barh' = horizontal bars (h = horizontal); makes long feature names easier to read
# ax=axes[1]  = draw into the RIGHT panel
# color='steelblue' = all bars are the same steel-blue colour
importance.plot(kind='barh', ax=axes[1], color='steelblue')  # barh = horizontal bar chart
axes[1].set_title('Feature Importance')
axes[1].set_xlabel('Importance Score')
# invert_yaxis() flips the y-axis so the highest-importance feature (sorted first)
# appears at the TOP of the chart instead of the bottom
axes[1].invert_yaxis()  # put the most important feature at the top

plt.tight_layout()  # automatically adjust spacing so charts don't overlap
# dpi = dots per inch (resolution); 72 is screen default, 150 is sharp for reports/presentations
# → higher dpi = larger file size but crisper image when zoomed in
plt.savefig('data/processed/model_evaluation.png', dpi=150)  # dpi=150 = good resolution
print("Saved chart: data/processed/model_evaluation.png")

# ── 8. Save model ───────────────────────────────────────────────────────────
# What pickle is: pickle is Python's built-in way to serialise (convert to bytes)
# and save any Python object — including a trained ML model — to a file. Later,
# another script (like the dashboard) can load the .pkl file and use the trained
# model directly without retraining. The 'wb' mode means "write binary."
os.makedirs('models', exist_ok=True)          # create models/ folder if it doesn't exist
model_path = 'models/fadr_predictor.pkl'      # .pkl = pickle file extension by convention
# open(model_path, 'wb') opens the file in write-binary mode
# → 'w' = write (create or overwrite)  'b' = binary (not text) — pickle needs binary mode
# → 'as f' gives us a file handle f; the 'with' block auto-closes the file when done
with open(model_path, 'wb') as f:             # 'wb' = write binary mode
    # pickle.dump(object, file) serialises the Python object into bytes and writes to f
    # we save a dict containing both the model AND its encoders because:
    # → when new data arrives the dashboard must encode it with the SAME le_address mapping
    #   (if you re-ran fit_transform on new data, "Apartment" might get a different number)
    pickle.dump({'model': model, 'encoders': {  # save model AND encoders together
        'address': le_address,  # need these to encode new input data the same way
        'window': le_window,
        'city': le_city,
    }}, f)
print(f"Model saved to {model_path}")

# ── 9. Sample prediction ────────────────────────────────────────────────────
print("\n--- Sample Prediction ---")
# pd.DataFrame([{...}]) wraps a single-row dict into a 1-row DataFrame
# → the model expects a DataFrame with the same column names as X_train, not a plain dict
#
# le_address.transform(['Apartment']) — note: transform() not fit_transform()
# → transform() reuses the mapping learned during fit_transform() on the training data
# → ['Apartment'] must be a list (not a string); returns a 1-element array e.g. [0]
# → [0] at the end extracts the scalar integer 0 from that array
# → same logic for le_window and le_city
sample = pd.DataFrame([{
    'address_type_enc':    le_address.transform(['Apartment'])[0],   # [0] = get scalar not array
    'delivery_window_enc': le_window.transform(['Morning (9-12)'])[0],
    'city_enc':            le_city.transform(['Mumbai'])[0],
    'order_value_bucket':  2,               # medium-high value order
    'attempt_number':      1,               # first attempt
    'has_delivery_preference': 0,           # no preference set
    'proximity_alert_sent':    0,           # no alert sent
}])

# model.predict_proba(sample) returns a 2D array even for a single row:
#   [[0.48, 0.52]]   ← outer list is rows, inner list is [prob_fail, prob_success]
# [0]   → selects the first (only) row:  [0.48, 0.52]
# [1]   → selects index 1 from that row:  0.52  (the success probability)
# combined [0][1] extracts a single float you can print with f"{prob:.1%}"
prob = model.predict_proba(sample)[0][1]  # [0] = first row, [1] = success probability
print(f"Apartment + Morning window + No preferences → Success probability: {prob:.1%}")

sample2 = sample.copy()                    # copy so we don't modify the original
sample2['has_delivery_preference'] = 1     # now customer HAS set a preference
sample2['proximity_alert_sent']    = 1     # and was alerted before delivery
sample2['delivery_window_enc']     = le_window.transform(['Evening (15-19)'])[0]  # better window
prob2 = model.predict_proba(sample2)[0][1]
print(f"Apartment + Evening window + Preferences set → Success probability: {prob2:.1%}")
# (prob2 - prob) is the raw difference e.g. 0.781 - 0.523 = 0.258
# multiply by 100 to convert to percentage points e.g. 0.258 × 100 = 25.8
# :.1f formats to 1 decimal place  →  "25.8"
print(f"\nImprovement from preferences + better window: +{(prob2-prob)*100:.1f} percentage points")
