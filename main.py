# Import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests

# 1. NumPy array and mean
arr = np.arange(1, 11)
mean_val = np.mean(arr)
print("NumPy Array:", arr)
print("Mean:", mean_val)

# 2. Pandas DataFrame and summary statistics
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
    'Age': [24, 30, 22, 35, 28],
    'Score': [85, 90, 88, 76, 95]
}
df = pd.DataFrame(data)
print("\nDataFrame:")
print(df)
print("\nSummary Statistics:")
print(df.describe(include='all'))

# 3. Fetch data from public API
import requests, json

def fetch_any():
    urls = [
        # very reliable public APIs with simple JSON
        ("GitHub API status", "https://api.github.com"),
        ("Cat fact", "https://catfact.ninja/fact"),
        ("Coingecko ping", "https://api.coingecko.com/api/v3/ping"),
    ]
    for name, url in urls:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            return name, data
        except Exception as e:
            last_err = e
    # Fallback if all online calls fail
    return "Offline fallback", {"message": "No internet? Using local data.", "demo_value": 42}

label, data = fetch_any()
print("\nAPI Result:", label)
print(json.dumps(data, indent=2))


# 4. Plot with matplotlib
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]
plt.plot(x, y, marker='o')
plt.title("Simple Line Graph")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")
plt.grid(True)
plt.show()
