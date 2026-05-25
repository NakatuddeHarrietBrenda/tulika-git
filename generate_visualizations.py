import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for high-quality, modern, dark-themed dashboard look
plt.style.use('dark_background')
sns.set_theme(style="dark", rc={
    "grid.color": "#334155",
    "axes.facecolor": "#0f172a",
    "figure.facecolor": "#0f172a",
    "text.color": "#e2e8f0",
    "axes.labelcolor": "#94a3b8",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "axes.edgecolor": "#1e293b"
})

# Path configurations
react_images_dir = "../tulika_updated_ML_dashboard/public/images"
os.makedirs(react_images_dir, exist_ok=True)

# Load the datasets
users = pd.read_csv("data/Final_Updated_Expanded_Users.csv")
destinations = pd.read_csv("data/Expanded_Destinations.csv")
reviews = pd.read_csv("data/Final_Updated_Expanded_Reviews.csv")
history = pd.read_csv("data/Final_Updated_Expanded_UserHistory.csv")

# Clean columns
for df_item in [users, destinations, reviews, history]:
    df_item.columns = df_item.columns.str.lower().str.replace(" ", "_")

# Translate Indian destinations to beautiful East African equivalents
destination_translation = {
    "Taj Mahal": "Murchison Falls",
    "Goa Beaches": "Zanzibar Beaches",
    "Jaipur City": "Kampala City",
    "Kerala Backwaters": "Lake Bunyonyi",
    "Leh Ladakh": "Mount Rwenzori"
}
destinations['name'] = destinations['name'].map(destination_translation).fillna(destinations['name'])

state_translation = {
    "Uttar Pradesh": "Masindi",
    "Goa": "Zanzibar",
    "Rajasthan": "Kampala",
    "Kerala": "Kabale",
    "Jammu & Kashmir": "Kasese"
}
destinations['state'] = destinations['state'].map(state_translation).fillna(destinations['state'])

# Map/Merge just like ml_service does
price_map = {
    "Murchison Falls": 6500,
    "Zanzibar Beaches": 6500,
    "Kampala City": 3350,
    "Lake Bunyonyi": 3350,
    "Mount Rwenzori": 4050
}
destinations['price'] = destinations['name'].map(price_map).fillna(4050)

# Merge
df = history.merge(users, on="userid", how="left")
df = df.merge(destinations, on="destinationid", how="left")
df = df.merge(reviews[['userid', 'destinationid', 'rating', 'reviewtext']], on=["userid", "destinationid"], how="left")
df['rating'] = df['rating'].combine_first(df['experiencerating'])

# 1. VISITOR PREFERENCES EDA
plt.figure(figsize=(8, 5))
color_palette = ["#6366f1", "#22c55e", "#d4af37", "#ef4444", "#a855f7"]
sns.countplot(data=df, x='preferences', palette=color_palette, order=df['preferences'].value_counts().index)
plt.title("Traveler Preference Distribution (New Dataset)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Category Preference", fontsize=12, labelpad=10)
plt.ylabel("Number of Visits", fontsize=12, labelpad=10)
plt.tight_layout()
plt.savefig(os.path.join(react_images_dir, "eda_preferences.png"), dpi=150, facecolor='#0f172a')
plt.close()

# 2. SENTIMENT DISTRIBUTION
def get_sentiment(rating):
    if pd.isna(rating): return "Neutral"
    if float(rating) >= 4: return "Positive"
    if float(rating) == 3: return "Neutral"
    return "Negative"
df['sentiment'] = df['rating'].apply(get_sentiment)

plt.figure(figsize=(8, 5))
sentiment_colors = {"Positive": "#22c55e", "Neutral": "#d4af37", "Negative": "#ef4444"}
sns.countplot(data=df, x='sentiment', palette=sentiment_colors, order=["Positive", "Neutral", "Negative"])
plt.title("Customer Sentiment Distribution", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Sentiment Class", fontsize=12, labelpad=10)
plt.ylabel("Count", fontsize=12, labelpad=10)
plt.tight_layout()
plt.savefig(os.path.join(react_images_dir, "sentiment_distribution.png"), dpi=150, facecolor='#0f172a')
plt.close()

# 3. K-MEANS SEGMENTATION CLUSTERS PLOT
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
seg_features = df[["price", "popularity"]].fillna(0)
scaler = StandardScaler()
seg_scaled = scaler.fit_transform(seg_features)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["segment"] = kmeans.fit_predict(seg_scaled)

# Sort cluster IDs dynamically by mean price to guarantee 0=Budget, 1=Medium, 2=Luxury
if len(df) > 0:
    cluster_mean_prices = df.groupby('segment')['price'].mean()
    sorted_clusters = cluster_mean_prices.sort_values().index
    cluster_mapping = {old_id: new_id for new_id, old_id in enumerate(sorted_clusters)}
    df['segment'] = df['segment'].map(cluster_mapping)

plt.figure(figsize=(8, 5))
# 0 = Budget Travelers (Green), 1 = Medium Clients (Purple), 2 = Luxury Clients (Yellow)
segment_colors_map = {0: "#22c55e", 1: "#a855f7", 2: "#facc15"}
segment_labels = { 0: "Budget Travelers", 1: "Medium Clients", 2: "Luxury Clients" }

for seg_id, color in segment_colors_map.items():
    seg_data = df[df["segment"] == seg_id]
    plt.scatter(seg_data["price"], seg_data["popularity"], c=color, label=segment_labels[seg_id], alpha=0.7, edgecolors='none', s=40)

plt.title("Customer Segments: Price vs Popularity", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Package Price (UGX / Scaled)", fontsize=12, labelpad=10)
plt.ylabel("Popularity Index", fontsize=12, labelpad=10)
plt.legend(frameon=True, facecolor="#1e293b", edgecolor="#334155")
plt.tight_layout()
plt.savefig(os.path.join(react_images_dir, "segmentation_clusters.png"), dpi=150, facecolor='#0f172a')
plt.close()

# 4. DEMAND FORECAST PLOT
df['visitdate'] = pd.to_datetime(df['visitdate'])
df['month'] = df['visitdate'].dt.to_period('M').astype(str)
df['number_of_people'] = df['numberofadults'] + df['numberofchildren']
monthly_demand = df.groupby('month')['number_of_people'].sum().reset_index()

plt.figure(figsize=(8, 5))
plt.plot(monthly_demand['month'], monthly_demand['number_of_people'], color='#22c55e', marker='o', linewidth=3, markersize=8)
plt.title("Monthly Travel Volume (Historical Demand)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Month", fontsize=12, labelpad=10)
plt.ylabel("Total Visitors (People)", fontsize=12, labelpad=10)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(react_images_dir, "demand_forecast.png"), dpi=150, facecolor='#0f172a')
plt.close()

print("All visualisations generated successfully!")
