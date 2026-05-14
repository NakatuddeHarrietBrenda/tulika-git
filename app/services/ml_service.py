import pandas as pd
import numpy as np
import warnings

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import silhouette_score

warnings.filterwarnings('ignore')

# ============ LOAD & PREPARE DATA ============
print("Loading data...")
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



# ============ DATA PREPROCESSING ============
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

# ============ CUSTOMER SEGMENTATION (K-MEANS) ============
print("Training segmentation model...")
seg_features = df[["price", "popularity"]].fillna(0)
scaler       = StandardScaler()
seg_scaled   = scaler.fit_transform(seg_features)

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["segment"] = kmeans.fit_predict(seg_scaled)

segment_names = {0: "Budget Travelers", 1: "Luxury Clients", 2: "Frequent Travelers"}

try:
    sil_score_val = float(silhouette_score(seg_scaled, df["segment"]))
except Exception:
    sil_score_val = None

# ============ DEMAND FORECASTING (LINEAR REGRESSION) ============
print("Training demand forecast model...")
demand_df = df[["price", "popularity", "number_of_people"]].dropna()
lr_model   = None
demand_r2  = None

if len(demand_df) >= 5:
    X_d = demand_df[["price", "popularity"]].values
    y_d = demand_df["number_of_people"].values
    lr_model  = LinearRegression()
    lr_model.fit(X_d, y_d)
    demand_r2 = float(lr_model.score(X_d, y_d))

# ============ SENTIMENT ANALYSIS ============
print("Training sentiment model...")

def sentiment_label(rating):
    if pd.isna(rating): return "Neutral"
    if float(rating) >= 4: return "Positive"
    if float(rating) == 3: return "Neutral"
    return "Negative"

df["sentiment"] = df["rating"].apply(sentiment_label)

tfidf           = TfidfVectorizer(max_features=100, stop_words="english")
sentiment_model = None
tfidf_model     = None

valid_comments = df[df["comment"].str.strip() != ""]
if len(valid_comments) > 0 and valid_comments["sentiment"].nunique() >= 2:
    X_s = tfidf.fit_transform(valid_comments["comment"])
    y_s = valid_comments["sentiment"]
    sentiment_model = LogisticRegression(max_iter=1000, random_state=42)
    sentiment_model.fit(X_s, y_s)
    tfidf_model = tfidf
else:
    classes_found = list(valid_comments["sentiment"].unique()) if len(valid_comments) > 0 else []
    print(f"WARNING: Sentiment model skipped. Classes found: {classes_found}")

# ============ ML MODELS & DATA ============
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
            "n_samples":         int(len(seg_scaled)),
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