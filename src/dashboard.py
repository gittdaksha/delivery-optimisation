import streamlit as st  # web app framework, turns script into a web page
import pandas as pd  # data tables (DataFrames)
import sqlite3  # built-in Python library for reading SQLite databases
import pickle  # load saved ML model from a .pkl file
import matplotlib.pyplot as plt  # draw charts and graphs
import seaborn as sns  # heatmap and statistical charts

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(  # configure browser tab appearance
    page_title="Delivery Optimisation Dashboard",  # text shown in browser tab
    page_icon="📦",  # icon shown in browser tab
    layout="wide"  # use full screen width instead of narrow default
)

# ── Load data ───────────────────────────────────────────────────────────────
# What @st.cache_data does: this decorator tells Streamlit to run this function
# once, cache the result (the DataFrame) in memory, and return the cached copy
# on every subsequent call — without re-reading from the database. This makes
# the dashboard fast: 50,000 rows are loaded once, not on every user interaction.
# Use @st.cache_data for data (DataFrames, lists, dicts).
@st.cache_data  # cache result; avoid re-querying DB on every interaction
def load_data():  # function to read all deliveries from SQLite
    conn = sqlite3.connect('data/delivery_db.sqlite')  # open the database file
    df = pd.read_sql("SELECT * FROM deliveries", conn)  # run SQL query → DataFrame
    conn.close()  # always close DB connection when done
    return df  # send the DataFrame back to the caller

# What @st.cache_resource does: similar to @st.cache_data but for shared resources
# like database connections, ML models, or API clients that should not be
# recreated for every user interaction. The loaded model is kept in memory and
# reused — loading a pickle file repeatedly would slow the dashboard significantly.
@st.cache_resource  # cache model object in memory, not reloaded on each click
def load_model():  # function to load the saved Random Forest model
    with open('models/fadr_predictor.pkl', 'rb') as f:  # rb = read binary mode
        return pickle.load(f)  # deserialise the .pkl file back to a Python object

df = load_data()  # call the function once; cached result reused after that

# ── Header ──────────────────────────────────────────────────────────────────
st.title("📦 Delivery Optimisation — FADR Analytics")  # large H1 heading at top
# next line: italic subheading shown below the title
st.markdown("*First Attempt Delivery Rate dashboard — identifying where and why deliveries fail*")

# ── KPI Row ─────────────────────────────────────────────────────────────────
# What st.columns() does: divides the page horizontally into N equal columns.
# Each column is an independent layout container. You write content into each
# one using a with block or by calling methods on the column object (col1.metric()).
col1, col2, col3, col4 = st.columns(4)  # split page into 4 equal side-by-side columns

total     = len(df)  # count total delivery attempts
success   = df['is_successful'].sum()  # count rows where delivery succeeded
failed    = total - success  # count rows where delivery failed
# → success = 37,650  |  total = 50,000  |  37,650 / 50,000 * 100 = 75.3
fadr      = success / total * 100  # FADR as a percentage (e.g. 75.3)
# df[df['attempt_number'] > 1] = keep only rows where attempt_number is 2 or higher
# .shape returns a tuple (rows, columns); .shape[0] = just the row count
repeat    = df[df['attempt_number'] > 1].shape[0]  # count rows needing re-delivery

# What st.metric() is: a Streamlit widget that displays a bold headline number
# with an optional delta value shown in green (positive) or red (negative) below it.
# It is designed for KPI (Key Performance Indicator) tiles — the headline numbers
# at the top of a dashboard.
# f"{total:,}" = f-string with :, format spec → adds thousand-separator commas
# e.g. total=50000 → "50,000"
col1.metric("Total Attempts",         f"{total:,}")  # KPI tile 1; :, adds comma separator
# f"{fadr:.1f}%" = :.1f means 1 decimal place → fadr=75.34 → "75.3%"
col2.metric("Overall FADR",           f"{fadr:.1f}%")  # KPI tile 2; :.1f = 1 decimal place
# delta= shows a secondary number below the headline; delta_color="inverse" makes it red
# because for a bad metric (failures), a negative delta is highlighted red not green
# f"-{failed/total*100:.1f}%" builds the string: "-" + failure% rounded to 1 decimal
col3.metric("Failed Deliveries",      f"{failed:,}",  delta=f"-{failed/total*100:.1f}%", delta_color="inverse")
# shows repeat attempts as % of total; red because it indicates wasted cost
col4.metric("Repeat Attempt Required",f"{repeat:,}",  delta=f"{repeat/total*100:.1f}% of total", delta_color="inverse")

# What st.divider() does: draws a horizontal line across the full width of the
# page, visually separating sections of the dashboard so users can distinguish
# different topics at a glance.
st.divider()  # horizontal line to separate sections visually

# ── Two-column analysis ─────────────────────────────────────────────────────
col_a, col_b = st.columns(2)  # split page into 2 side-by-side panels

with col_a:  # everything indented here appears in the left panel
    st.subheader("FADR by Delivery Window")  # bold H3 section heading
    # .groupby('delivery_window') = group rows by each window value (morning, afternoon, etc.)
    # ['is_successful'].mean() = average of 0/1 column = fraction that succeeded
    # .sort_values() = sort ascending so worst window appears at the bottom of the chart
    # * 100 = convert 0.75 fraction to 75.0 percent
    window_fadr = df.groupby('delivery_window')['is_successful'].mean().sort_values() * 100
    fig, ax = plt.subplots(figsize=(7, 4))  # create a 7x4 inch figure
    # barh = horizontal bar chart; colours go red→orange→green→blue
    bars = ax.barh(window_fadr.index, window_fadr.values, color=['#d62728','#ff7f0e','#2ca02c','#1f77b4'])
    ax.set_xlabel("FADR (%)")  # label the x-axis
    # draw a vertical dashed line at the overall average for reference
    ax.axvline(fadr, color='black', linestyle='--', linewidth=1, label=f'Overall avg: {fadr:.1f}%')
    ax.legend()  # show the legend label for the average line
    # zip(bars, window_fadr.values) pairs each bar object with its numeric value
    # so in each iteration: bar = the rectangle shape, val = the % number
    for bar, val in zip(bars, window_fadr.values):  # loop over bars + values together
        # bar.get_y() = bottom edge of bar  |  bar.get_height()/2 = half the bar height
        # together they calculate the vertical midpoint of each bar
        # val + 0.3 = nudge the label 0.3 units to the right of the bar tip
        ax.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center')
    # What plt.tight_layout() does: automatically adjusts the spacing between
    # chart elements (title, axis labels, tick marks) so nothing overlaps or gets
    # cut off. Always call it before saving or displaying a matplotlib chart.
    plt.tight_layout()  # auto-fix spacing so labels don't get cut off
    st.pyplot(fig)  # render the matplotlib figure in Streamlit

with col_b:  # everything indented here appears in the right panel
    st.subheader("FADR by Address Type")  # bold H3 section heading
    # same pattern as col_a: groupby → mean → sort → scale
    addr_fadr = df.groupby('address_type')['is_successful'].mean().sort_values() * 100
    fig2, ax2 = plt.subplots(figsize=(7, 4))  # new 7x4 inch figure
    bars2 = ax2.barh(addr_fadr.index, addr_fadr.values, color='steelblue')  # horizontal bars
    ax2.set_xlabel("FADR (%)")  # label the x-axis
    ax2.axvline(fadr, color='black', linestyle='--', linewidth=1)  # overall average line
    for bar, val in zip(bars2, addr_fadr.values):  # loop to add value labels
        # bar.get_y() + bar.get_height()/2 = vertical midpoint of the bar
        ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center')
    plt.tight_layout()  # prevent labels from being clipped
    st.pyplot(fig2)  # render chart in Streamlit

st.divider()  # horizontal line separator

# ── Preference & Alert Impact ───────────────────────────────────────────────
st.subheader("Impact of Data-Driven Features")  # section heading
col_c, col_d = st.columns(2)  # two side-by-side panels

with col_c:  # left panel: preference impact chart
    pref_data = df.groupby('has_delivery_preference')['is_successful'].mean() * 100  # FADR by preference flag
    labels = ['No Preference Set', 'Preference Set']  # x-axis bar labels
    fig3, ax3 = plt.subplots(figsize=(5, 3))  # smaller figure for side panel
    ax3.bar(labels, pref_data.values, color=['#ff7f0e', '#2ca02c'])  # orange=no pref, green=pref set
    ax3.set_ylabel("FADR (%)")  # y-axis label
    ax3.set_title("Delivery Preference Profile Impact")  # chart title
    for i, v in enumerate(pref_data.values):  # loop to add labels above each bar
        ax3.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')  # label above bar
    st.pyplot(fig3)  # render chart

with col_d:  # right panel: proximity alert impact chart
    alert_data = df.groupby('proximity_alert_sent')['is_successful'].mean() * 100  # FADR by alert flag
    labels2 = ['No Alert Sent', 'Alert Sent']  # x-axis bar labels
    fig4, ax4 = plt.subplots(figsize=(5, 3))  # figure for alert impact chart
    ax4.bar(labels2, alert_data.values, color=['#ff7f0e', '#2ca02c'])  # orange=no alert, green=alert sent
    ax4.set_ylabel("FADR (%)")  # y-axis label
    ax4.set_title("Proximity Alert Impact")  # chart title
    for i, v in enumerate(alert_data.values):  # loop to add labels above each bar
        ax4.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')  # label above bar
    st.pyplot(fig4)  # render chart

st.divider()  # section separator

# ── Cost Calculator ─────────────────────────────────────────────────────────
st.subheader("Business Impact Calculator")  # section heading
st.markdown("Estimate the operational cost of failed deliveries and the savings from improving FADR.")  # description text

col_e, col_f = st.columns(2)  # inputs on left, calculated outputs on right

with col_e:  # left panel: user input controls
    # number_input: text box with up/down arrows; value=default shown, step=increment
    daily_vol     = st.number_input("Daily delivery volume", value=100000, step=10000)
    # cost of each failed delivery in rupees (default ₹45)
    cost_per_fail = st.number_input("Cost per failed attempt (₹)", value=45, step=5)
    # st.slider(label, min, max, default, step)
    # float(f"{fadr:.1f}") converts the calculated fadr float to exactly 1 decimal place
    # so the slider default matches the data (e.g. 75.3) not a long float like 75.3142...
    current_fadr  = st.slider("Current FADR (%)", 60.0, 95.0, float(f"{fadr:.1f}"), step=0.1)
    # min(current_fadr + 5.0, 99.0) = add 5% to current, but cap at 99.0 so slider stays valid
    # if current_fadr is 96.0, then 96.0+5=101.0 which is above max=99.0, so min() gives 99.0
    target_fadr   = st.slider("Target FADR (%) after improvement", current_fadr, 99.0, min(current_fadr + 5.0, 99.0), step=0.1)

with col_f:  # right panel: calculated results update automatically
    # (1 - current_fadr / 100) = failure rate as a decimal
    # e.g. FADR=75% → failure rate = 1 - 0.75 = 0.25 → 100,000 * 0.25 = 25,000 failures/day
    current_failures = daily_vol * (1 - current_fadr / 100)  # failures per day at current FADR
    target_failures  = daily_vol * (1 - target_fadr / 100)  # failures per day at target FADR
    # difference in failures × cost per fail = money saved per day
    daily_savings    = (current_failures - target_failures) * cost_per_fail  # rupees saved per day
    annual_savings   = daily_savings * 365  # rupees saved per year

    st.metric("Current daily failures",    f"{int(current_failures):,}")  # KPI tile
    st.metric("Target daily failures",     f"{int(target_failures):,}")  # KPI tile
    st.metric("Daily cost saving",         f"₹{daily_savings:,.0f}")  # KPI tile
    st.metric("Annual cost saving",        f"₹{annual_savings:,.0f}", delta="per year")  # KPI tile

st.divider()  # section separator

# ── Failure Reason Breakdown ────────────────────────────────────────────────
st.subheader("Why Deliveries Fail")  # section heading
fail_df = df[df['is_successful'] == 0]['failure_reason'].value_counts()  # count each failure reason
fig5, ax5 = plt.subplots(figsize=(8, 3))  # wide, short figure
fail_df.plot(kind='barh', ax=ax5, color='crimson')  # horizontal bar chart in red
ax5.set_xlabel("Number of failures")  # x-axis label
ax5.set_title("Top Failure Reasons")  # chart title
st.pyplot(fig5)  # render chart

st.divider()  # section separator

# ── City Filter ─────────────────────────────────────────────────────────────
st.subheader("Explore by City")  # section heading
# sorted(df['city'].unique()) = get all unique city values, then sort alphabetically
# this ensures the dropdown always shows cities in A→Z order
city = st.selectbox("Select city", sorted(df['city'].unique()))  # dropdown of all unique cities
# df['city'] == city creates a True/False column; df[...] keeps only True rows
city_df = df[df['city'] == city]  # filter rows for the selected city only
city_fadr = city_df['is_successful'].mean() * 100  # FADR % for this city
# f"**text**" = bold in Markdown; {len(city_df):,} adds comma separator to the count
st.markdown(f"**{city} FADR: {city_fadr:.1f}%** across {len(city_df):,} attempts")  # bold summary

# .groupby(['address_type', 'delivery_window']) = group by two columns simultaneously
# .mean() = FADR fraction for each combination
# .unstack() = pivot the inner groupby level (delivery_window) from rows into columns
# result: a 2D table where rows = address_type, columns = delivery_window, values = FADR
# * 100 = convert fractions to percentages
city_segment = city_df.groupby(['address_type', 'delivery_window'])['is_successful'].mean().unstack() * 100
fig6, ax6 = plt.subplots(figsize=(10, 4))  # wide figure for the heatmap
# annot=True = show the number in each cell
# fmt='.0f' = format numbers as integers (no decimals) inside cells
# cmap='RdYlGn' = Red (low FADR) → Yellow (mid) → Green (high FADR) colour scale
# vmin/vmax = pin the colour scale so 50% is always red and 95% is always green
sns.heatmap(city_segment, annot=True, fmt='.0f', cmap='RdYlGn', ax=ax6,
            vmin=50, vmax=95, linewidths=0.5)
ax6.set_title(f"{city}: FADR Heatmap by Address Type × Delivery Window")  # chart title
st.pyplot(fig6)  # render heatmap

st.caption("Built by Daksha Kurhade | Delivery Optimisation Data Engineering Project")  # small footer text
