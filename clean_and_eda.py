"""
Mamaearth Returns & Growth Analytics Pipeline
Part 2: Data Wrangling, Outlier Detection, EDA & Metrics Export
"""

import os
import json
import pandas as pd

def main():
    print("=" * 70)
    print("MAMAEARTH DATA WRANGLING & EDA PIPELINE")
    print("=" * 70)

    # Task 1: Load and Inspect
    orders_path = os.path.join("data", "orders.csv")
    customers_path = os.path.join("data", "customers.csv")
    products_path = os.path.join("data", "products.csv")

    orders = pd.read_csv(orders_path)
    customers = pd.read_csv(customers_path)
    products = pd.read_csv(products_path)

    print(f"\n[Task 1] Loaded orders.shape: {orders.shape}")
    assert orders.shape == (180, 9), f"Expected (180, 9), got {orders.shape}"

    # Task 2: Standardize Payment Method Casing
    raw_pm_unique = orders["payment_method"].unique()
    print(f"\n[Task 2] Distinct raw payment_methods ({len(raw_pm_unique)}): {list(raw_pm_unique)}")
    assert len(raw_pm_unique) == 7, "Expected 7 raw payment methods"

    orders["payment_method"] = orders["payment_method"].astype(str).str.strip().str.upper()
    pm_counts = orders["payment_method"].value_counts().to_dict()
    print(f"Cleaned payment_method counts: {pm_counts}")
    assert pm_counts == {"CARD": 70, "UPI": 55, "COD": 55}, f"Unexpected counts: {pm_counts}"

    # Task 3: Remove Duplicate Orders
    natural_key = [
        "customer_id", "product_id", "order_date", "quantity",
        "discount_pct", "payment_method", "rating", "returned"
    ]
    dup_mask = orders.duplicated(subset=natural_key, keep="first")
    dropped_orders = orders.loc[dup_mask, "order_id"].tolist()
    print(f"\n[Task 3] Dropped duplicate order IDs ({len(dropped_orders)}): {dropped_orders}")
    assert dropped_orders == ["O0176", "O0177", "O0178", "O0179", "O0180"], "Mismatch in dropped order IDs"

    orders_clean = orders.loc[~dup_mask].copy()
    print(f"orders_clean.shape after deduplication: {orders_clean.shape}")
    assert orders_clean.shape == (175, 9), f"Expected (175, 9), got {orders_clean.shape}"

    # Task 4: Impute Missing Values
    missing_discount = orders_clean["discount_pct"].isna().sum()
    orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0.0)
    print(f"\n[Task 4] Imputed {missing_discount} missing discount_pct values with 0.0")
    assert missing_discount == 12, f"Expected 12 missing discount_pct, found {missing_discount}"

    median_rating = orders_clean["rating"].median()
    missing_rating = orders_clean["rating"].isna().sum()
    print(f"Rating median before imputation: {median_rating}")
    assert median_rating == 3.0, f"Expected rating median 3.0, got {median_rating}"

    orders_clean["rating"] = orders_clean["rating"].fillna(median_rating)
    print(f"Imputed {missing_rating} missing rating values with {median_rating}")
    assert missing_rating == 15, f"Expected 15 missing ratings, found {missing_rating}"

    null_check = orders_clean[["discount_pct", "rating"]].isnull().sum().to_dict()
    print(f"Remaining null counts: {null_check}")
    assert null_check == {"discount_pct": 0, "rating": 0}

    # Task 5: Merge and Reconcile against Part 1
    merged_clean = orders_clean.merge(products, on="product_id", how="inner")
    merged_clean = merged_clean.merge(customers, on="customer_id", how="inner")

    merged_clean["order_value"] = (
        merged_clean["quantity"] * merged_clean["price"] * (1 - merged_clean["discount_pct"] / 100.0)
    )
    cleaned_total_rev = round(merged_clean["order_value"].sum(), 2)
    print(f"\n[Task 5] Cleaned total revenue (175 rows): ₹{cleaned_total_rev:,.2f}")
    assert cleaned_total_rev == 97358.30, f"Expected 97358.30, got {cleaned_total_rev}"

    dropped_rows = orders.loc[dup_mask].merge(products, on="product_id", how="inner")
    dropped_rev = round((
        dropped_rows["quantity"] * dropped_rows["price"] * (1 - dropped_rows["discount_pct"].fillna(0) / 100.0)
    ).sum(), 2)
    raw_sql_total = 99860.20
    delta = round(raw_sql_total - cleaned_total_rev, 2)
    print(f"Dropped duplicate orders revenue: ₹{dropped_rev:,.2f}")
    print(f"Part 1 Raw Total - Cleaned Total Delta: ₹{delta:,.2f}")
    assert delta == 2501.90 and dropped_rev == 2501.90, "Reconciliation delta mismatch"

    reconciliation_note = (
        f"Reconciliation Note: Part 1 SQL raw total revenue was ₹{raw_sql_total:,.2f}, whereas "
        f"Part 2 cleaned total revenue is ₹{cleaned_total_rev:,.2f}, resulting in an exact delta of "
        f"₹{delta:,.2f}. This difference is entirely attributable to the removal of 5 duplicate "
        f"orders (O0176 through O0180) resulting from an upstream double-submission anomaly, whose "
        f"combined order value is exactly ₹{dropped_rev:,.2f}. Imputation of discount_pct and rating "
        f"introduced zero revenue variance."
    )
    print(f"\n{reconciliation_note}\n")

    # Task 6: IQR Outlier Detection on Quantity
    q1 = merged_clean["quantity"].quantile(0.25)
    q3 = merged_clean["quantity"].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    print(f"[Task 6] Quantity IQR: Q1={q1}, Q3={q3}, IQR={iqr}, lower={lower_bound}, upper={upper_bound}")
    assert (q1, q3, iqr, lower_bound, upper_bound) == (1.0, 2.0, 1.0, -0.5, 3.5)

    merged_clean["is_outlier"] = (merged_clean["quantity"] < lower_bound) | (merged_clean["quantity"] > upper_bound)
    outlier_df = merged_clean[merged_clean["is_outlier"]]
    outlier_ids = sorted(outlier_df["order_id"].tolist())
    print(f"Identified {len(outlier_df)} outliers: {outlier_ids}")
    assert outlier_ids == ["O0011", "O0098"], f"Expected ['O0011', 'O0098'], got {outlier_ids}"

    # Task 7: Hypothesis Testing
    print("\n[Task 7] Hypothesis: Cash on Delivery (COD) orders suffer a significantly higher return rate than prepaid methods.")
    pm_return = merged_clean.groupby("payment_method")["returned"].agg(["count", "mean"]).reset_index()
    pm_return["return_rate_pct"] = (pm_return["mean"] * 100).round(1)
    rates = dict(zip(pm_return["payment_method"], pm_return["return_rate_pct"]))
    print(f"Return rates by payment method: {rates}")
    assert rates == {"CARD": 14.7, "COD": 44.4, "UPI": 18.9}, f"Mismatch in return rates: {rates}"
    print("Hypothesis: Confirmed (COD at 44.4% is ~3x higher than Card at 14.7% and UPI at 18.9%).")

    # Task 8: Multi-level Segmentation
    segmentation = merged_clean.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "mean"]).reset_index()
    segmentation["return_rate_pct"] = (segmentation["mean"] * 100).round(1)
    print("\n[Task 8] Multi-level Segmentation (Payment x City Tier):")
    for _, row in segmentation.iterrows():
        print(f"  {row['payment_method']} Tier-{row['city_tier']}: Count={row['count']}, Return Rate={row['return_rate_pct']}%")

    cod_t1 = segmentation[(segmentation["payment_method"] == "COD") & (segmentation["city_tier"] == 1)].iloc[0]
    cod_t2 = segmentation[(segmentation["payment_method"] == "COD") & (segmentation["city_tier"] == 2)].iloc[0]
    print(f"\nSingle Highest-Risk Segment: COD + Tier-2 Cities at {cod_t2['return_rate_pct']}% ({cod_t2['count']} orders).")
    print(f"Comparison: Tier-1 COD orders return at {cod_t1['return_rate_pct']}% ({cod_t1['count']} orders).")
    assert cod_t2["return_rate_pct"] == 54.5 and cod_t2["count"] == 22
    assert cod_t1["return_rate_pct"] == 37.5 and cod_t1["count"] == 32

    # Task 9: Correlation Analysis
    corr_cols = ["rating", "returned", "discount_pct", "quantity"]
    corr_matrix = merged_clean[corr_cols].corr()
    print("\n[Task 9] Correlation Matrix:")
    print(corr_matrix.round(4))

    def band(val):
        v = abs(val)
        if v < 0.20:
            return "negligible"
        elif v < 0.40:
            return "weak"
        elif v < 0.70:
            return "moderate"
        return "strong"

    pairs = [
        ("rating", "returned"), ("rating", "discount_pct"), ("rating", "quantity"),
        ("returned", "discount_pct"), ("returned", "quantity"), ("discount_pct", "quantity")
    ]
    for c1, c2 in pairs:
        r_val = corr_matrix.loc[c1, c2]
        print(f"  Pair ({c1}, {c2}): r = {r_val:.4f} -> Band: {band(r_val)}")
        assert band(r_val) == "negligible"

    disc_ret_corr = corr_matrix.loc["discount_pct", "returned"]
    print(f"Hypothesis 'higher discounts reduce returns': Busted (r = {disc_ret_corr:.4f} is negligible).")

    # Task 10: Outlier-Corrected Time Series
    merged_clean["order_date"] = pd.to_datetime(merged_clean["order_date"])
    merged_clean["year_month"] = merged_clean["order_date"].dt.strftime("%Y-%m")

    monthly_raw = merged_clean.groupby("year_month")["order_value"].sum().round(2).to_dict()
    monthly_corrected = (
        merged_clean[~merged_clean["is_outlier"]].groupby("year_month")["order_value"].sum().round(2).to_dict()
    )

    print("\n[Task 10] Monthly Revenue Comparison:")
    print(f"  Raw (including outliers): {monthly_raw}")
    print(f"  Corrected (excluding outliers): {monthly_corrected}")

    assert monthly_raw["2026-01"] == 29582.10
    assert monthly_corrected["2026-01"] == 11637.10
    assert monthly_corrected["2026-02"] == 13195.50
    assert monthly_corrected["2026-03"] == 20318.90
    assert monthly_corrected["2026-04"] == 9495.30
    assert monthly_corrected["2026-05"] == 13151.10
    assert monthly_corrected["2026-06"] == 11615.40

    print("Insight: January's apparent revenue lead (₹29,582.10) is an artifact of two bulk B2B-scale orders "
          "(O0011 on 2026-01-28, qty 25; O0098 on 2026-01-10, qty 30). "
          "Once corrected, March is confirmed as the genuine peak sales month at ₹20,318.90.")

    # Export verified findings
    os.makedirs("narrator", exist_ok=True)
    findings_data = {
        "cleaned_total_revenue_inr": cleaned_total_rev,
        "raw_total_revenue_inr": raw_sql_total,
        "duplicate_reconciliation_delta_inr": delta,
        "return_rate_by_payment": {
            "COD": rates["COD"],
            "CARD": rates["CARD"],
            "UPI": rates["UPI"]
        },
        "highest_risk_segment": {
            "payment_method": "COD",
            "city_tier": 2,
            "return_rate_pct": float(cod_t2["return_rate_pct"])
        },
        "true_peak_month": {
            "month": "2026-03",
            "revenue_inr": monthly_corrected["2026-03"]
        },
        "outlier_inflated_month": {
            "month": "2026-01",
            "apparent_revenue_inr": monthly_raw["2026-01"],
            "corrected_revenue_inr": monthly_corrected["2026-01"]
        }
    }

    findings_file = os.path.join("narrator", "findings.json")
    with open(findings_file, "w", encoding="utf-8") as f:
        json.dump(findings_data, f, indent=4)
    print(f"\n[Export] Verified figures successfully written to {findings_file}")

if __name__ == "__main__":
    main()
