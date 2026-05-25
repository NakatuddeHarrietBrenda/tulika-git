import pandas as pd
import numpy as np
import warnings

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import silhouette_score

warnings.filterwarnings('ignore')

#  LOAD & PREPARE DATA 
print("Loading data...")
import os
import joblib

# Check if new files exist, else fallback to old ones
if os.path.exists("data/Final_Updated_Expanded_Users.csv"):
    users = pd.read_csv("data/Final_Updated_Expanded_Users.csv")
    destinations = pd.read_csv("data/Expanded_Destinations.csv")
    reviews = pd.read_csv("data/Final_Updated_Expanded_Reviews.csv")
    history = pd.read_csv("data/Final_Updated_Expanded_UserHistory.csv")
    
    # Clean column names
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
    
    country_translation = {
        "India": "East Africa"
    }
    
    # Save the complete unified dataset before renaming columns
    complete_df = history.merge(users, on="userid", how="outer")
    complete_df = complete_df.merge(destinations, on="destinationid", how="outer", suffixes=('_user', '_dest'))
    complete_df = complete_df.merge(reviews, on=["userid", "destinationid"], how="left", suffixes=('', '_review'))
    complete_df.to_csv("data/Complete_Tulika_Dataset.csv", index=False)
    print(f"Saved complete merged dataset to data/Complete_Tulika_Dataset.csv ({len(complete_df)} records)")
        
    # Simulate 'age' programmatically to make demographics charts work
    import numpy as np
    np.random.seed(42)
    users['age'] = np.random.randint(18, 65, size=len(users))
    
    # Map user columns
    customers = users.rename(columns={
        'userid': 'customer_id',
        'preferences': 'travel_preference',
        'numberofadults': 'number_of_adults',
        'numberofchildren': 'number_of_children'
    })
    
    # Assign prices and price-tiers based on East African destinations
    price_map = {
        "Murchison Falls": 6500,
        "Zanzibar Beaches": 6500,
        "Kampala City": 3350,
        "Lake Bunyonyi": 3350,
        "Mount Rwenzori": 4050
    }
    tier_map = {
        "Murchison Falls": "Luxury",
        "Zanzibar Beaches": "Luxury",
        "Kampala City": "Budget",
        "Lake Bunyonyi": "Budget",
        "Mount Rwenzori": "Medium"
    }
    destinations['price'] = destinations['name'].map(price_map).fillna(4050)
    destinations['price-tier'] = destinations['name'].map(tier_map).fillna('Medium')
    
    # Set East African countries based on destination name
    country_map = {
        "Murchison Falls": "Uganda",
        "Zanzibar Beaches": "Tanzania",
        "Kampala City": "Uganda",
        "Lake Bunyonyi": "Uganda",
        "Mount Rwenzori": "Uganda"
    }
    destinations['country'] = destinations['name'].map(country_map).fillna('Uganda')
    destinations['city'] = destinations['state']
    
    packages = destinations.rename(columns={
        'destinationid': 'package_id',
        'name': 'destination',
        'type': 'package_category'
    })
    
    # Map history columns
    history['visitdate'] = pd.to_datetime(history['visitdate'])
    history['booking_date'] = history['visitdate'] - pd.Timedelta(days=30)
    
    bookings = history.rename(columns={
        'historyid': 'booking_id',
        'userid': 'customer_id',
        'destinationid': 'package_id',
        'visitdate': 'travel_date'
    })
    bookings = bookings.merge(customers[['customer_id', 'number_of_adults', 'number_of_children']], on='customer_id', how='left')
    bookings['number_of_people'] = bookings['number_of_adults'] + bookings['number_of_children']
    bookings['booking_status'] = 'Confirmed'
    
    # Map reviews columns
    reviews = reviews.rename(columns={
        'reviewid': 'review_id',
        'destinationid': 'package_id',
        'userid': 'customer_id',
        'rating': 'rating_review',
        'reviewtext': 'comment'
    })
    
    # Simulate payments based on bookings and prices
    pay_merge = bookings.merge(packages[['package_id', 'price']], on='package_id', how='left')
    methods = ['Mobile Money', 'Credit Card', 'Bank Transfer']
    np.random.seed(42)
    pay_methods = np.random.choice(methods, size=len(pay_merge))
    
    payments = pd.DataFrame({
        'payment_id': [f"PAY{i:03d}" for i in range(len(pay_merge))],
        'booking_id': pay_merge['booking_id'],
        'payment_method': pay_methods,
        'amount_paid': pay_merge['price'],
        'payment_date': pay_merge['travel_date'] - pd.Timedelta(days=15)
    })
    
    # Merge datasets
    df = bookings.merge(customers, on="customer_id", how="left")
    df = df.merge(packages,  on="package_id",  how="left")
    df = df.merge(payments,  on="booking_id",  how="left")
    df = df.merge(reviews[['customer_id', 'package_id', 'comment', 'rating_review']], on=["customer_id", "package_id"], how="left")
    
    df['rating'] = df['rating_review'].combine_first(df['experiencerating'])
    df['comment'] = df['comment'].fillna("No comment")
else:
    customers = pd.read_csv("data/Customers.csv")
    packages  = pd.read_csv("data/Packages.csv")
    bookings  = pd.read_csv("data/bookings.csv")
    reviews   = pd.read_csv("data/Reviews.csv")
    payments  = pd.read_csv("data/Payments.csv")
    # Clean column names
    for df_item in [customers, packages, bookings, reviews, payments]:
        df_item.columns = df_item.columns.str.lower().str.replace(" ", "_")
    # Merge all data
    df = bookings.merge(customers, on="customer_id", how="left")
    df = df.merge(packages,  on="package_id",  how="left")
    df = df.merge(payments,  on="booking_id",  how="left")
    df = df.merge(reviews,   on=["customer_id", "package_id"], how="left", suffixes=('', '_review'))

#  DATA PREPROCESSING 
if "price" in df.columns:
    df["price"] = pd.to_numeric(df["price"], errors='coerce').fillna(0)
if "amount_paid" in df.columns:
    df["amount_paid"] = df["amount_paid"].astype(str).str.replace(",", "")
    df["amount_paid"] = pd.to_numeric(df["amount_paid"], errors='coerce').fillna(0)

df["popularity"]       = pd.to_numeric(df["popularity"], errors='coerce').fillna(5)
df["rating"]           = pd.to_numeric(df["rating"],     errors='coerce').fillna(3)
df["number_of_people"] = pd.to_numeric(df["number_of_people"], errors='coerce').fillna(1)
df["comment"]          = df["comment"].fillna("").astype(str)
df["destination"]      = df["destination"].fillna("Unknown")

for date_col in ["booking_date", "travel_date", "review_date", "payment_date"]:
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# Model Cache Configuration
MODEL_DIR = "models_cache"
os.makedirs(MODEL_DIR, exist_ok=True)

kmeans_path = os.path.join(MODEL_DIR, "kmeans_model.joblib")
scaler_path = os.path.join(MODEL_DIR, "scaler.joblib")
lr_path = os.path.join(MODEL_DIR, "lr_model.joblib")
sentiment_path = os.path.join(MODEL_DIR, "sentiment_model.joblib")
tfidf_path = os.path.join(MODEL_DIR, "tfidf.joblib")
metrics_path = os.path.join(MODEL_DIR, "metrics.joblib")

segment_names = { 0: "Budget Travelers", 1: "Medium Clients", 2: "Luxury Clients" }
seg_features = df[["price", "popularity"]].fillna(0)

# Check if cached models exist
models_loaded = False
if (os.path.exists(kmeans_path) and os.path.exists(scaler_path) and 
    os.path.exists(lr_path) and os.path.exists(sentiment_path) and 
    os.path.exists(tfidf_path) and os.path.exists(metrics_path)):
  try:
    print("Loading saved ML models from cache...")
    kmeans = joblib.load(kmeans_path)
    scaler = joblib.load(scaler_path)
    lr_model = joblib.load(lr_path)
    sentiment_model = joblib.load(sentiment_path)
    tfidf_model = joblib.load(tfidf_path)
    
    metrics = joblib.load(metrics_path)
    sil_score_val = metrics.get("sil_score_val")
    demand_r2 = metrics.get("demand_r2")
    
    # Segment predictions
    df["segment"] = kmeans.predict(scaler.transform(seg_features))
    
    # Sort cluster IDs dynamically by mean price
    if len(df) > 0:
      cluster_mean_prices = df.groupby('segment')['price'].mean()
      sorted_clusters = cluster_mean_prices.sort_values().index
      cluster_mapping = {old_id: new_id for new_id, old_id in enumerate(sorted_clusters)}
      df['segment'] = df['segment'].map(cluster_mapping)
      
    models_loaded = True
    print("Models loaded successfully!")
  except Exception as e:
    print(f"Error loading cached models, retraining: {e}")

# Sentiment label helper
def sentiment_label(rating):
  if pd.isna(rating): return "Neutral"
  if float(rating) >= 4: return "Positive"
  if float(rating) == 3: return "Neutral"
  return "Negative"

df["sentiment"] = df["rating"].apply(sentiment_label)
valid_comments = df[df["comment"].str.strip() != ""]

if not models_loaded:
  print("Training and caching ML models...")
  # CUSTOMER SEGMENTATION (K-MEANS)
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
  
  try:
    sil_score_val = float(silhouette_score(seg_scaled, df["segment"]))
  except Exception:
    sil_score_val = None

  # DEMAND FORECASTING (LINEAR REGRESSION)
  demand_df = df[["price", "popularity", "number_of_people"]].dropna()
  lr_model = None
  demand_r2 = None
  if len(demand_df) >= 5:
    X_d = demand_df[["price", "popularity"]].values
    y_d = demand_df["number_of_people"].values
    lr_model = LinearRegression()
    lr_model.fit(X_d, y_d)
    demand_r2 = float(lr_model.score(X_d, y_d))

  # SENTIMENT ANALYSIS (LOGISTIC REGRESSION + TF-IDF)
  tfidf = TfidfVectorizer(max_features=100, stop_words="english")
  sentiment_model = None
  tfidf_model = None
  
  if len(valid_comments) > 0 and valid_comments["sentiment"].nunique() >= 2:
    X_s = tfidf.fit_transform(valid_comments["comment"])
    y_s = valid_comments["sentiment"]
    sentiment_model = LogisticRegression(max_iter=1000, random_state=42)
    sentiment_model.fit(X_s, y_s)
    tfidf_model = tfidf
  else:
    classes_found = list(valid_comments["sentiment"].unique()) if len(valid_comments) > 0 else []
    print(f"WARNING: Sentiment model training skipped. Classes found: {classes_found}")

  # Cache models to disk
  try:
    joblib.dump(kmeans, kmeans_path)
    joblib.dump(scaler, scaler_path)
    if lr_model:
      joblib.dump(lr_model, lr_path)
    if sentiment_model:
      joblib.dump(sentiment_model, sentiment_path)
    if tfidf_model:
      joblib.dump(tfidf_model, tfidf_path)
        
    metrics = {"sil_score_val": sil_score_val, "demand_r2": demand_r2}
    joblib.dump(metrics, metrics_path)
    print("Models successfully saved to disk!")
  except Exception as e:
    print(f"Error saving models: {e}")

# ML MODELS & DATA 
def get_overview_stats():
    return {
        "total_packages":  int(packages["package_id"].nunique()),
        "total_customers": int(customers["customer_id"].nunique()),
        "total_bookings":  int(bookings["booking_id"].nunique()),
        "total_revenue":   float(df["amount_paid"].sum()) if "amount_paid" in df.columns else 0,
        "average_rating":  float(df["rating"].mean())
    }

def get_dashboard_summary():
    confirmed = len(df[df["booking_status"] == "Confirmed"])
    pending   = len(df[df["booking_status"] == "Pending"])
    canceled  = len(df[df["booking_status"] == "Canceled"])
    return {
        "confirmed_bookings": int(confirmed),
        "pending_bookings":   int(pending),
        "canceled_bookings":  int(canceled),
        "total_customers":    int(df["customer_id"].nunique()),
        "avg_booking_value":  float(df["amount_paid"].mean()) if "amount_paid" in df.columns else 0
    }

def get_booking_trends():
    t = df[["booking_date", "booking_id"]].dropna(subset=["booking_date"]).copy()
    t["month"] = t["booking_date"].dt.to_period("M").astype(str)
    monthly = t.groupby("month")["booking_id"].count().reset_index()
    monthly.columns = ["month", "bookings"]
    return monthly.sort_values("month").to_dict(orient="records")

def get_clusters():
    result = df[["destination", "price", "popularity", "segment"]].copy()
    result["segment_name"] = result["segment"].map(segment_names)
    return result.fillna(0).to_dict(orient="records")

def get_top_destinations():
    pkg = packages.copy()
    pkg["popularity"] = pd.to_numeric(pkg["popularity"], errors="coerce").fillna(0)
    pkg["price"]      = pd.to_numeric(pkg["price"],      errors="coerce").fillna(0)
    top = pkg.sort_values("popularity", ascending=False).head(10)
    cols = ["destination", "country", "package_category", "price", "price-tier", "popularity", "besttimetovisit"]
    available = [c for c in cols if c in top.columns]
    return top[available].fillna("N/A").to_dict(orient="records")

def get_revenue_analysis():
    pay = payments.copy()
    pay["amount_paid"]   = pay["amount_paid"].astype(str).str.replace(",", "")
    pay["amount_paid"]   = pd.to_numeric(pay["amount_paid"], errors="coerce").fillna(0)
    pay["payment_date"]  = pd.to_datetime(pay["payment_date"], errors="coerce")
    pay["month"]         = pay["payment_date"].dt.to_period("M").astype(str)

    monthly = pay.groupby("month")["amount_paid"].sum().reset_index()
    monthly.columns = ["month", "revenue"]

    by_method = pay.groupby("payment_method")["amount_paid"].sum().reset_index()
    by_method.columns = ["method", "revenue"]

    return {
        "total_revenue":      float(pay["amount_paid"].sum()),
        "monthly_revenue":    monthly.sort_values("month").to_dict(orient="records"),
        "by_payment_method":  by_method.to_dict(orient="records")
    }

def get_customer_demographics():
    cust = customers.copy()
    cust["age"] = pd.to_numeric(cust["age"], errors="coerce")
    bins   = [0, 25, 35, 45, 100]
    labels = ["18-25", "26-35", "36-45", "45+"]
    cust["age_group"] = pd.cut(cust["age"], bins=bins, labels=labels)

    age_dist    = {str(k): int(v) for k, v in cust["age_group"].value_counts().sort_index().items()}
    gender_dist = cust["gender"].value_counts().to_dict()
    pref_dist   = cust["travel_preference"].value_counts().head(8).to_dict()

    pkg_col = "package_type" if "package_type" in cust.columns else None
    pkg_type_dist = cust[pkg_col].value_counts().to_dict() if pkg_col else {}

    return {
        "age_distribution":          age_dist,
        "gender_distribution":       gender_dist,
        "travel_preferences":        pref_dist,
        "package_type_distribution": pkg_type_dist
    }

def get_demand_forecast():
    trend = df[["travel_date", "number_of_people", "destination"]].dropna(subset=["travel_date"]).copy()
    trend["month"] = trend["travel_date"].dt.to_period("M").astype(str)

    monthly_demand = trend.groupby("month")["number_of_people"].sum().reset_index()
    monthly_demand.columns = ["month", "total_people"]

    dest_demand = trend.groupby("destination")["number_of_people"].sum().sort_values(ascending=False).head(10).reset_index()
    dest_demand.columns = ["destination", "total_people"]

    predictions = []
    if lr_model is not None:
        pkg = packages.copy()
        pkg["price"]      = pd.to_numeric(pkg["price"],      errors="coerce").fillna(0)
        pkg["popularity"] = pd.to_numeric(pkg["popularity"], errors="coerce").fillna(0)
        preds = lr_model.predict(pkg[["price", "popularity"]].values)
        for i, row in pkg.iterrows():
            predictions.append({
                "destination":          str(row.get("destination", "Unknown")),
                "predicted_group_size": max(1, round(float(preds[i]))),
                "price":                float(row.get("price", 0)),
                "popularity":           float(row.get("popularity", 0))
            })

    return {
        "model_r2":              demand_r2,
        "monthly_demand":        monthly_demand.sort_values("month").to_dict(orient="records"),
        "demand_by_destination": dest_demand.to_dict(orient="records"),
        "package_predictions":   predictions[:15]
    }

def get_model_evaluation():
    classes_found = list(valid_comments["sentiment"].unique()) if len(valid_comments) > 0 else []
    return {
        "segmentation": {
            "model":             "K-Means Clustering",
            "status":            "Trained",
            "inertia":           float(kmeans.inertia_),
            "silhouette_score":  sil_score_val,
            "n_clusters":        3,
            "n_samples":         int(len(seg_features)),
            "segments":          list(segment_names.values())
        },
        "demand_forecast": {
            "model":    "Linear Regression",
            "status":   "Trained" if lr_model else "Insufficient data",
            "r2_score": demand_r2,
            "features": ["price", "popularity"],
            "target":   "number_of_people"
        },
        "sentiment_analysis": {
            "model":         "Logistic Regression + TF-IDF",
            "status":        "Trained" if sentiment_model else "Skipped - single class",
            "classes_found": classes_found,
            "n_reviews":     int(len(valid_comments)),
            "note":          "All reviews are 4-5 stars. Add lower-rated reviews to fully train the model."
        },
        "recommendation": {
            "model":      "Filter-Based (Budget + Category)",
            "status":     "Active",
            "n_packages": int(len(packages)),
            "categories": list(packages["package_category"].dropna().unique())
        }
    }

def run_predict_sentiment(text):
    if not text:
        return {"error": "Text is required"}

    if tfidf_model is None:
        text_lower = text.lower()
        pos_words = ["great","amazing","excellent","fantastic","love","best","wonderful","good","perfect","awesome"]
        neg_words = ["bad","terrible","awful","poor","worst","horrible","disappointing","boring","waste"]
        pos = sum(1 for w in pos_words if w in text_lower)
        neg = sum(1 for w in neg_words if w in text_lower)
        sentiment = "Positive" if pos > neg else ("Negative" if neg > pos else "Neutral")
        return {"sentiment": sentiment, "method": "rule-based"}

    vec  = tfidf_model.transform([text])
    pred = sentiment_model.predict(vec)[0]
    return {"sentiment": pred, "method": "ML model"}

def run_recommend(budget, category):
    pkg = packages.copy()
    pkg["price"]      = pd.to_numeric(pkg["price"],      errors="coerce").fillna(0)
    pkg["popularity"] = pd.to_numeric(pkg["popularity"], errors="coerce").fillna(0)

    filtered = pkg[pkg["price"] <= budget]
    if category:
        cat_match = filtered[filtered["package_category"].str.lower() == category.lower()]
        if len(cat_match) > 0:
            filtered = cat_match

    results = filtered.sort_values("popularity", ascending=False).head(5)
    cols    = ["destination", "package_category", "price", "popularity", "besttimetovisit", "country", "price-tier"]
    available = [c for c in cols if c in results.columns]
    return results[available].fillna("N/A").to_dict(orient="records")

print("Data preparation complete!")