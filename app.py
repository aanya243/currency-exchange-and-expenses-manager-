from flask import Flask, render_template, request, redirect, url_for
import requests, csv, os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import os
os.makedirs("static/charts", exist_ok=True)

if not os.path.exists("static/charts"):
    os.makedirs("static/charts")


app = Flask(__name__)
EXPENSE_FILE = "expenses.csv"
DATE_FMT = "%d-%m-%Y"

# Ensure expenses file exists
def ensure_expense_file():
    if not os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Category", "Amount", "Note"])

@app.route("/")
def index():
    return render_template("index.html")

# ---------------- Currency Converter ----------------
@app.route("/convert", methods=["GET", "POST"])
def convert():
    result = None
    error = None

    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            source = request.form["source"].upper()
            target = request.form["target"].upper()

            url = "https://api.freecurrencyapi.com/v1/latest"
            params = {
    "apikey": "fca_live_rKPiyy5jNq8ItcyC6QH0k5QpcGJXTzsRQRRYGdty",  # API  key
    "base_currency": source,
    "currencies": target
}
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            print("API response:", data)
            print("Requesting:", requests.Request('GET', url, params=params).prepare().url)


            if "data" in data and target in data["data"]:
                rate = data["data"][target]
                converted = rate * amount
                result = {
                    "amount": amount,
                    "source": source,
                    "target": target,
                    "converted": converted,
                    "rate": rate,
                    "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }
            else:
                error = "Conversion failed. Please check currency codes or API response."


        except Exception as e:
            error = f"Error: {e}"
    return render_template("convert.html", result=result, error=error)


# ---------------- Add Expense ----------------
@app.route("/add", methods=["GET", "POST"])
def add_expense():
    ensure_expense_file()
    if request.method == "POST":
        category = request.form["category"]
        amount = float(request.form["amount"])
        note = request.form["note"]
        date_str = datetime.now().strftime(DATE_FMT)

        with open(EXPENSE_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([date_str, category, amount, note])
        return redirect(url_for("index"))
    return render_template("add_expense.html")

# ---------------- Insights ----------------
@app.route("/insights")
def insights():
    ensure_expense_file()
    df = pd.read_csv(EXPENSE_FILE)
    if df.empty:
        return "No expenses recorded yet."

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], format=DATE_FMT, errors="coerce")

    summary = df.groupby("Category")["Amount"].sum()

    # Pie chart
    pie_path = "static/charts/pie.png"
    plt.figure(figsize=(6,6))
    summary.plot.pie(autopct="%1.1f%%")
    plt.ylabel("")
    plt.title("Expense Distribution")
    plt.savefig(pie_path)
    plt.close()

    # Line chart
    line_path = "static/charts/line.png"
    trend = df.groupby("Date")["Amount"].sum()
    plt.figure(figsize=(8,4))
    trend.plot.line(marker="o")
    plt.title("Spending Trend Over Time")
    plt.xlabel("Date")
    plt.ylabel("Amount (INR)")
    plt.grid(True)
    plt.savefig(line_path)
    plt.close()

    return render_template("insights.html", summary=summary.to_dict(),
                           pie_chart=pie_path, line_chart=line_path)

if __name__ == "__main__":
    app.run(debug=True)
