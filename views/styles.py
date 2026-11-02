"""Minimal modern UI styles for NER Logistics Streamlit application."""
import streamlit as st


def inject_styles():
    """Inject modern, minimal styling for a clean professional SaaS look."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        /* Global typography & clean canvas */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            background-color: #f8fafc;
            color: #0f172a;
        }

        /* Streamlit main block container spacing */
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            max-width: 1380px !important;
        }

        /* Hide unnecessary Streamlit chrome */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        #MainMenu, footer {
            visibility: hidden;
        }

        /* Headings */
        h1 {
            font-size: 1.75rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.025em !important;
            color: #0f172a !important;
            margin-bottom: 0.35rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            color: #1e293b !important;
            margin-top: 0.5rem !important;
            margin-bottom: 0.4rem !important;
        }
        h3 {
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            letter-spacing: -0.015em !important;
            color: #334155 !important;
            margin-top: 0.4rem !important;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02) !important;
            transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stMetric"]:hover {
            border-color: #cbd5e1 !important;
            box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.07) !important;
            transform: translateY(-1px) !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
            color: #64748b !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.65rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
            line-height: 1.2 !important;
        }

        /* Clean card containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 18px 20px !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
            margin-bottom: 12px !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #cbd5e1 !important;
            box-shadow: 0 3px 6px -1px rgba(15, 23, 42, 0.06) !important;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
            padding-left: 1.15rem !important;
            padding-right: 1.15rem !important;
        }
        [data-testid="stSidebar"] hr {
            margin: 0.9rem 0 !important;
            border-color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] > div {
            gap: 4px !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            border-radius: 8px !important;
            padding: 7px 12px !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
            color: #334155 !important;
            transition: all 0.15s ease !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
        }

        /* Primary action buttons */
        button[kind="primary"], .stButton > button[kind="primary"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 18px !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            box-shadow: 0 1px 2px rgba(37, 99, 235, 0.25) !important;
            transition: all 0.15s ease-in-out !important;
        }
        button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
            background-color: #1d4ed8 !important;
            box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3) !important;
            transform: translateY(-1px) !important;
        }

        /* Secondary buttons */
        button[kind="secondary"], .stButton > button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #334155 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            padding: 7px 16px !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            transition: all 0.15s ease-in-out !important;
        }
        button[kind="secondary"]:hover, .stButton > button[kind="secondary"]:hover {
            background-color: #f8fafc !important;
            border-color: #94a3b8 !important;
            color: #0f172a !important;
        }

        /* Form elements */
        .stSelectbox div[data-baseweb="select"], .stTextInput input, .stTextArea textarea, .stDateInput input, .stTimeInput input {
            border-radius: 8px !important;
            border: 1px solid #cbd5e1 !important;
            font-size: 0.92rem !important;
        }
        .stSelectbox div[data-baseweb="select"]:hover, .stTextInput input:hover, .stTextArea textarea:hover {
            border-color: #94a3b8 !important;
        }

        /* Folium maps frame */
        iframe {
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        }

        /* Dataframe styling */
        [data-testid="stDataFrame"] {
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            overflow: hidden !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            border-radius: 10px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #f8fafc !important;
        }

        /* Alert and message boxes */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
            font-size: 0.9rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
