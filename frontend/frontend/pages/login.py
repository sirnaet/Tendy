"""
Reflex Login & Registration View
Editorial layout with deep burgundy & warm parchment aesthetic.
"""

import reflex as rx
from frontend.state import AppState
from frontend.theme import (
    PRIMARY_BURGUNDY,
    PRIMARY_DEEP,
    ACCENT_WINE,
    ACCENT_ROSE,
    ACCENT_MUTED_BORDER,
    BG_PARCHMENT_LIGHT,
    TEXT_PRIMARY_LIGHT,
    TEXT_MUTED_LIGHT
)

def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            # Header Branding
            rx.vstack(
                rx.box(
                    rx.text("A", font_family="var(--font-heading)", font_size="2.2rem", font_weight="bold", color="#FFFFFF"),
                    background=PRIMARY_BURGUNDY,
                    border_radius="12px",
                    width="56px",
                    height="56px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    box_shadow="0 4px 12px rgba(91, 14, 45, 0.25)"
                ),
                rx.heading("Tendy Attendance", font_family="var(--font-heading)", size="8", color=PRIMARY_DEEP, font_weight="normal"),
                rx.text("University Academic Tracker & Absence Guard", size="3", color=TEXT_MUTED_LIGHT),
                spacing="2",
                align="center"
            ),

            # Card Container
            rx.box(
                rx.form(
                    rx.vstack(
                        rx.text("Sign In to Your Workspace", font_weight="700", size="4", color=TEXT_PRIMARY_LIGHT),
                        
                        rx.vstack(
                            rx.text("Email Address", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                            rx.input(
                                name="email",
                                placeholder="student@university.edu",
                                default_value="student@university.edu",
                                type="email",
                                style={
                                    "width": "100%",
                                    "border": f"1px solid {ACCENT_MUTED_BORDER}",
                                    "border_radius": "8px",
                                    "padding": "10px 14px",
                                    "background": "#FAF7F5"
                                }
                            ),
                            width="100%",
                            align="start",
                            spacing="1"
                        ),

                        rx.vstack(
                            rx.text("Password", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                            rx.input(
                                name="password",
                                placeholder="••••••••••••",
                                default_value="password123",
                                type="password",
                                style={
                                    "width": "100%",
                                    "border": f"1px solid {ACCENT_MUTED_BORDER}",
                                    "border_radius": "8px",
                                    "padding": "10px 14px",
                                    "background": "#FAF7F5"
                                }
                            ),
                            width="100%",
                            align="start",
                            spacing="1"
                        ),

                        rx.cond(
                            AppState.auth_error != "",
                            rx.text(AppState.auth_error, color="#8C1D24", size="2", font_weight="600")
                        ),

                        rx.button(
                            "Authenticate with Firebase",
                            type="submit",
                            style={
                                "width": "100%",
                                "background": PRIMARY_BURGUNDY,
                                "color": "#FFFFFF",
                                "font_weight": "600",
                                "border_radius": "8px",
                                "padding": "12px",
                                "margin_top": "8px",
                                "box_shadow": "0 2px 6px rgba(91, 14, 45, 0.2)",
                                "cursor": "pointer"
                            }
                        ),
                        spacing="4",
                        width="100%"
                    ),
                    on_submit=AppState.login_user
                ),
                background="#FFFFFF",
                border=f"1px solid {ACCENT_MUTED_BORDER}",
                border_radius="16px",
                padding="2.5rem",
                width="420px",
                box_shadow="0 6px 24px rgba(74, 14, 23, 0.07)"
            ),
            spacing="6",
            align="center"
        ),
        width="100%",
        min_height="100vh",
        background=BG_PARCHMENT_LIGHT
    )
