"""
Mamaearth Growth Analytics Pipeline
Part 2: Visualizations Generation Script
"""

import os
import matplotlib.pyplot as plt
import pandas as pd

def generate_visualizations():
    os.makedirs("visualizations", exist_ok=True)

    orders = pd.read_csv(os.path.join("data", "orders.csv"))
    products = pd.read_csv(os.path.join("data", "products.csv"))
    customers = pd.read_csv(os.path.join("data", "customers.csv"))

    orders["payment_method"] = orders["payment_method"].astype(str).str.strip().str.upper()
    natural_key = [
        "customer_id", "product_id", "order_date", "quantity",
        "discount_pct", "payment_method", "rating", "returned"
    ]
    orders = orders.drop_duplicates(subset=natural_key, keep="first").copy()
    orders["discount_pct"] = orders["discount_pct"].fillna(0.0)

    df = orders.merge(products, on="product_id", how="inner")
    df = df.merge(customers, on="customer_id", how="inner")
    df["order_value"] = df["quantity"] * df["price"] * (1 - df["discount_pct"] / 100.0)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["year_month"] = df["order_date"].dt.strftime("%Y-%m")

    # Exclude IQR outliers (quantity > 3.5)
    q1 = df["quantity"].quantile(0.25)
    q3 = df["quantity"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    df_clean = df[df["quantity"] <= upper_bound].copy()

    # Chart 1: Return Rate by Payment Method
    pm_stats = df.groupby("payment_method")["returned"].agg(["count", "mean"]).reset_index()
    pm_stats["return_rate_pct"] = (pm_stats["mean"] * 100).round(1)
    pm_stats = pm_stats.sort_values(by="return_rate_pct", ascending=False)

    plt.figure(figsize=(8, 5))
    bars = plt.bar(
        pm_stats["payment_method"],
        pm_stats["return_rate_pct"],
        color=["#D9534F", "#F0AD4E", "#5CB85C"],
        edgecolor="black",
        width=0.55
    )

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1.0,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold"
        )

    plt.title("COD Returns at 44.4% — 3x Card", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Payment Method", fontsize=11, labelpad=10)
    plt.ylabel("Return Rate (%)", fontsize=11, labelpad=10)
    plt.ylim(0, 52)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    out1 = os.path.join("visualizations", "return_rate_by_payment.png")
    plt.savefig(out1, dpi=300)
    plt.close()
    print(f"Saved: {out1}")

    # Chart 2: Monthly Revenue Trend (Outlier-Corrected)
    monthly_rev = df_clean.groupby("year_month")["order_value"].sum().round(2).reset_index()

    plt.figure(figsize=(9, 5))
    plt.plot(
        monthly_rev["year_month"],
        monthly_rev["order_value"],
        marker="o",
        linewidth=2.5,
        markersize=7,
        color="#0275D8"
    )

    for _, row in monthly_rev.iterrows():
        plt.annotate(
            f"₹{row['order_value']:,.2f}",
            (row["year_month"], row["order_value"]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold"
        )

    plt.title("Outlier-Corrected Monthly Revenue Trend: March Peak at ₹20,318.90", fontsize=13, fontweight="bold", pad=15)
    plt.xlabel("Month (2026)", fontsize=11, labelpad=10)
    plt.ylabel("Net Order Value (INR)", fontsize=11, labelpad=10)
    plt.ylim(7000, 23000)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    out2 = os.path.join("visualizations", "monthly_revenue_trend.png")
    plt.savefig(out2, dpi=300)
    plt.close()
    print(f"Saved: {out2}")

if __name__ == "__main__":
    generate_visualizations()
