# Streamlit Dashboard

Interactive dashboard developed with Streamlit for data visualization and metrics monitoring.

## Project Structure

```
streamlit-dashboard/
├── app.py                      # Main application file
├── pages/                      # Dashboard pages
│   ├── __init__.py
│   ├── home.py                # Home page
│   ├── analytics.py           # Analytics page
│   ├── reports.py             # Reports page
│   └── settings.py            # Settings page
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── data_loader.py         # Data loading functions
│   └── charts.py              # Chart creation functions
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## Features

* 🏠 **Home**: Overview with key metrics and summary charts
* 📈 **Analytics**: Detailed analysis with filters and advanced visualizations
* 📄 **Reports**: Report generation and export to CSV/Excel
* ⚙️ **Settings**: Customization of appearance, notifications, and user profile

## Installation

1. Clone the repository or navigate to the project folder

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

Run the dashboard with the command:

```bash
streamlit run app.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

## Customization

### Add a New Page

1. Create a new file inside `pages/`, for example: `pages/new_page.py`
2. Implement the `show()` function:

```python
import streamlit as st

def show():
    st.title("New Page")
    st.write("Page content")
```

3. Import and register it in `app.py`

### Change Theme

Edit the `.streamlit/config.toml` file to customize colors and appearance

### Connect Real Data Sources

Update the functions in `utils/data_loader.py` to load data from:

* Databases (PostgreSQL, MySQL, MongoDB)
* APIs
* Files (CSV, Excel, JSON)
* Data warehouses

## Technologies

* **Streamlit**: Main framework
* **Pandas**: Data manipulation
* **Plotly**: Interactive visualizations
* **NumPy**: Numerical operations
