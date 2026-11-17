"""Визуальная тема в духе файлового менеджера Google Drive."""

from __future__ import annotations

import streamlit as st


def apply_theme(dark: bool) -> None:
    colors = (
        {
            "bg": "#101214",
            "surface": "#1f1f1f",
            "sidebar": "#151719",
            "text": "#e3e3e3",
            "muted": "#a8c7fa",
            "border": "#444746",
            "hover": "#2c2e30",
            "search": "#282a2c",
            "accent": "#a8c7fa",
        }
        if dark
        else {
            "bg": "#f7f9fc",
            "surface": "#ffffff",
            "sidebar": "#f7f9fc",
            "text": "#1f1f1f",
            "muted": "#5f6368",
            "border": "#e1e5ea",
            "hover": "#f0f4f9",
            "search": "#edf2fc",
            "accent": "#0b57d0",
        }
    )
    primary_text = "#062e6f" if not dark else "#d3e3fd"
    danger = "#c5221f" if not dark else "#f2b8b5"
    danger_text = "#ffffff" if not dark else "#601410"
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: {'dark' if dark else 'light'}; }}
        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            background: {colors['bg']} !important;
            color: {colors['text']} !important;
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] {{
            background: {colors['sidebar']} !important;
            color: {colors['text']} !important;
            border-right: 0;
            min-width: 238px;
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top: 1rem; }}
        .main .block-container {{
            max-width: 1600px;
            padding: .65rem 1.35rem 3rem;
        }}
        h1, h2, h3, h4, h5, h6, p, label,
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p {{
            color: {colors['text']} !important;
        }}
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {{
            color: {colors['muted']} !important;
        }}
        h1 {{ font-size: 1.55rem !important; font-weight: 500 !important; }}
        .drive-brand {{
            display: flex; align-items: center; gap: .75rem;
            font-size: 1.35rem; font-weight: 500; margin: .15rem 0 1.2rem;
            color: {colors['text']} !important;
        }}
        .drive-mark {{
            width: 28px; height: 28px; border-radius: 8px;
            background: conic-gradient(from 30deg, #34a853 0 25%, #4285f4 0 50%, #ea4335 0 75%, #fbbc04 0);
            box-shadow: inset 0 0 0 7px {colors['sidebar']};
        }}
        .storage-status {{
            display: flex; justify-content: flex-end; align-items: center;
            min-height: 48px; color: {colors['muted']}; font-size: .8rem;
        }}
        .test-pill {{
            display: inline-block; padding: .2rem .55rem; border-radius: 999px;
            background: #e6f4ea; color: #137333; font-size: .76rem; font-weight: 600;
        }}
        [data-testid="stTextInput"] [data-baseweb="input"] {{
            border: 1px solid transparent !important;
            border-radius: 28px !important;
            background: {colors['search']} !important;
            box-shadow: none !important;
        }}
        [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {{
            border-color: {colors['accent']} !important;
        }}
        [data-testid="stTextInput"] input {{
            border: 0 !important;
            color: {colors['text']} !important;
            background: transparent !important;
            min-height: 48px; padding-left: 1.15rem;
            -webkit-text-fill-color: {colors['text']} !important;
        }}
        [data-testid="stTextInput"] input::placeholder {{
            color: {colors['muted']} !important;
            opacity: 1 !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border: 1px solid {colors['border']} !important; border-radius: 16px;
            background: {colors['surface']} !important;
        }}
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stPopover"] > button {{
            border-radius: 18px !important;
            border: 1px solid {colors['border']} !important;
            background: {colors['surface']} !important;
            color: {colors['text']} !important;
            min-height: 38px;
            box-shadow: none !important;
        }}
        .stButton > button p,
        .stDownloadButton > button p,
        [data-testid="stPopover"] > button p {{
            color: inherit !important;
        }}
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stPopover"] > button:hover {{
            border-color: {colors['accent']} !important;
            color: {primary_text} !important;
            background: {colors['hover']} !important;
        }}
        .stButton > button:disabled,
        .stDownloadButton > button:disabled {{
            background: {colors['hover']} !important;
            color: {colors['muted']} !important;
            opacity: .55;
        }}
        .stButton > button[kind="primary"] {{
            background: {danger} !important;
            border-color: {danger} !important;
            color: {danger_text} !important;
        }}
        .stButton > button[kind="tertiary"],
        button[data-testid="stBaseButton-tertiary"] {{
            background: transparent !important;
            border-color: transparent !important;
            box-shadow: none !important;
            justify-content: flex-start !important;
            text-align: left !important;
            padding-left: .35rem !important;
            color: {colors['text']} !important;
        }}
        .stButton > button[kind="tertiary"]:hover,
        button[data-testid="stBaseButton-tertiary"]:hover {{
            background: {colors['hover']} !important;
            border-color: transparent !important;
        }}
        button[data-testid="stBaseButton-tertiary"] p {{
            width: 100%; text-align: left !important;
        }}
        button[data-testid="stBaseButton-tertiary"] > div,
        button[data-testid="stBaseButton-tertiary"] > div > span {{
            justify-content: flex-start !important;
            text-align: left !important;
        }}
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] [data-testid="stPopover"] > button {{
            border-radius: 16px; min-height: 46px; text-align: left;
        }}
        [data-testid="stSidebar"] [data-testid="stPopover"] > button {{
            background: {colors['surface']} !important;
            border: 1px solid {colors['border']} !important;
            box-shadow: 0 1px 3px rgba(60,64,67,.22) !important;
            justify-content: flex-start !important;
        }}
        .st-key-go_root button {{
            min-height: 38px !important;
            background: {'#c2e7ff' if not dark else '#004a77'} !important;
            border-color: transparent !important;
            color: {'#001d35' if not dark else '#c2e7ff'} !important;
            justify-content: flex-start !important;
            box-shadow: none !important;
        }}
        [data-testid="stFileUploader"] {{
            border-radius: 14px;
            color: {colors['text']} !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: {colors['hover']} !important;
            border-color: {colors['border']} !important;
        }}
        [data-testid="stPopoverBody"],
        div[data-baseweb="popover"] > div {{
            border-radius: 16px;
            background: {colors['surface']} !important;
            color: {colors['text']} !important;
        }}
        main [data-testid="stPopover"] > button {{
            min-width: 34px !important;
            padding: 0 .45rem !important;
            border-color: transparent !important;
            background: transparent !important;
        }}
        [data-baseweb="select"] > div {{
            min-height: 36px !important;
            border-radius: 9px !important;
            border-color: {colors['border']} !important;
            background: {colors['surface']} !important;
            color: {colors['text']} !important;
            box-shadow: none !important;
        }}
        [data-baseweb="select"] input {{ color: {colors['text']} !important; }}
        [role="listbox"] {{
            background: {colors['surface']} !important;
            color: {colors['text']} !important;
        }}
        [data-testid="stSegmentedControl"] {{ justify-content: flex-end; }}
        [data-testid="stSegmentedControl"] button {{
            min-width: 48px; color: {colors['text']} !important;
            border-color: {colors['border']} !important;
            background: {colors['surface']} !important;
        }}
        [data-testid="stSegmentedControl"] button[aria-pressed="true"] {{
            color: {'#001d35' if not dark else '#c2e7ff'} !important;
            background: {'#c2e7ff' if not dark else '#004a77'} !important;
        }}
        [data-baseweb="radio"] {{ color: {colors['text']} !important; }}
        [data-baseweb="radio"] > div:first-child {{
            background-color: {colors['surface']} !important;
            border-color: {colors['muted']} !important;
        }}
        [data-baseweb="radio"] [aria-checked="true"] > div:first-child {{
            background-color: {colors['accent']} !important;
            border-color: {colors['accent']} !important;
        }}
        button svg {{ fill: currentColor !important; color: inherit !important; }}
        hr {{ border-color: {colors['border']}; }}
        .drive-divider {{
            height: 1px; background: {colors['border']}; margin: .05rem 0;
        }}
        .file-name {{
            font-size: .92rem; font-weight: 500; line-height: 2.35rem;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }}
        .grid-title {{
            height: 2.4rem; font-size: .88rem; font-weight: 600;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            display: flex; align-items: center;
        }}
        .folder-preview, .file-preview {{
            height: 115px; border-radius: 12px; background: {colors['hover']};
            display: flex; align-items: center; justify-content: center;
            font-size: 2.7rem; margin: .35rem 0 .7rem;
        }}
        .safety-note {{
            border-radius: 12px; padding: .65rem .8rem; margin-top: .75rem;
            color: {colors['muted']}; background: {colors['hover']}; font-size: .78rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
