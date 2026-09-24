"""
Editorial Deep Burgundy Design System Tokens for Reflex UI
"""

import reflex as rx

# Color Tokens
BG_PARCHMENT_LIGHT = "#FAF7F5"
BG_PARCHMENT_DARK = "#1A1215"
SURFACE_CARD_LIGHT = "#FFFFFF"
SURFACE_CARD_DARK = "#24161B"

PRIMARY_BURGUNDY = "#5B0E2D"
PRIMARY_DEEP = "#4A0E17"
ACCENT_WINE = "#801835"
ACCENT_ROSE = "#C97A8E"
ACCENT_MUTED_BORDER = "#E2D9D7"
ACCENT_DARK_BORDER = "#382229"

# Status Accents
STATUS_SAGE = "#4A6B53"
STATUS_SAGE_BG = "#EEF4F0"
STATUS_CRIMSON = "#8C1D24"
STATUS_CRIMSON_BG = "#FDF2F2"
STATUS_MUTED_GRAY = "#5A5255"
STATUS_MUTED_GRAY_BG = "#F4F2F3"

TEXT_PRIMARY_LIGHT = "#2D1B22"
TEXT_MUTED_LIGHT = "#6E5B63"
TEXT_PRIMARY_DARK = "#FAF7F5"
TEXT_MUTED_DARK = "#A8969D"

# Shadow Tokens
SHADOW_SUBTLE = "0 2px 8px rgba(91, 14, 45, 0.06)"
SHADOW_CARD = "0 4px 16px rgba(74, 14, 23, 0.08)"
SHADOW_BUTTON = "0 2px 4px rgba(91, 14, 45, 0.15)"

# Custom Injectable CSS
CUSTOM_STYLE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --font-heading: 'Instrument Serif', 'Georgia', serif;
    --font-body: 'Plus Jakarta Sans', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

body {
    background-color: #FAF7F5;
    color: #2D1B22;
    font-family: var(--font-body);
}

.editorial-title {
    font-family: var(--font-heading);
    letter-spacing: -0.02em;
}

.mono-code {
    font-family: var(--font-mono);
    letter-spacing: -0.03em;
}

.card-editorial {
    background: #FFFFFF;
    border: 1px solid #E2D9D7;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(91, 14, 45, 0.06);
    transition: all 0.2s ease-in-out;
}

.card-editorial:hover {
    box-shadow: 0 4px 16px rgba(74, 14, 23, 0.10);
}

.btn-burgundy {
    background-color: #5B0E2D;
    color: #FFFFFF;
    font-weight: 600;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.btn-burgundy:hover {
    background-color: #801835;
    transform: translateY(-1px);
}

.toggle-attended {
    background-color: #EEF4F0;
    color: #4A6B53;
    border: 1px solid #4A6B53;
    font-weight: 600;
}

.toggle-missed {
    background-color: #FDF2F2;
    color: #8C1D24;
    border: 1px solid #8C1D24;
    font-weight: 600;
}

.toggle-cancelled {
    background-color: #F4F2F3;
    color: #5A5255;
    border: 1px solid #5A5255;
    font-weight: 500;
}
"""
