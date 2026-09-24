"""
Reflex Navigation Header Bar Component
Displays Editorial Burgundy branding, current week, overall attendance health badge, and term progress.
"""

import reflex as rx
from frontend.state import AppState
from frontend.theme import (
    PRIMARY_BURGUNDY,
    ACCENT_WINE,
    ACCENT_MUTED_BORDER,
    BG_PARCHMENT_LIGHT,
    STATUS_SAGE,
    STATUS_SAGE_BG,
    STATUS_CRIMSON,
    STATUS_CRIMSON_BG,
    TEXT_PRIMARY_LIGHT,
    TEXT_MUTED_LIGHT
)

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Brand Title
            rx.hstack(
                rx.box(
                    rx.text("A", font_family="var(--font-heading)", font_size="1.5rem", font_weight="bold", color="#FFFFFF"),
                    background=PRIMARY_BURGUNDY,
                    border_radius="8px",
                    width="36px",
                    height="36px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    box_shadow="0 2px 6px rgba(91, 14, 45, 0.2)"
                ),
                rx.vstack(
                    rx.heading("Tendy", font_family="var(--font-heading)", size="5", color=TEXT_PRIMARY_LIGHT, line_height="1.1"),
                    rx.text("University Attendance Tracker", size="1", color=TEXT_MUTED_LIGHT, font_weight="500"),
                    spacing="0"
                ),
                spacing="3",
                align="center"
            ),

            rx.spacer(),

            # Health Badge & Term Progress Metrics
            rx.hstack(
                # Current Week Indicator
                rx.badge(
                    AppState.current_week_str,
                    variant="soft",
                    color_scheme="crimson",
                    style={
                        "background": "#F4ECEE",
                        "color": PRIMARY_BURGUNDY,
                        "border": f"1px solid {ACCENT_WINE}22",
                        "font_family": "var(--font-mono)",
                        "font_weight": "600",
                        "padding": "6px 12px",
                        "border_radius": "20px"
                    }
                ),

                # Overall Attendance Health Status Badge
                rx.cond(
                    AppState.overall_attendance_rate >= 80.0,
                    rx.badge(
                        "HEALTH: OKAY (91.5%)",
                        style={
                            "background": STATUS_SAGE_BG,
                            "color": STATUS_SAGE,
                            "border": f"1px solid {STATUS_SAGE}",
                            "font_weight": "700",
                            "padding": "6px 12px",
                            "border_radius": "20px"
                        }
                    ),
                    rx.badge(
                        "HEALTH: CRITICAL",
                        style={
                            "background": STATUS_CRIMSON_BG,
                            "color": STATUS_CRIMSON,
                            "border": f"1px solid {STATUS_CRIMSON}",
                            "font_weight": "700",
                            "padding": "6px 12px",
                            "border_radius": "20px"
                        }
                    )
                ),

                # Nav Action Buttons
                rx.button(
                    "Dashboard",
                    on_click=AppState.set_active_tab("dashboard"),
                    variant="ghost",
                    style={
                        "color": PRIMARY_BURGUNDY,
                        "font_weight": "600"
                    }
                ),
                rx.button(
                    "Timetable Builder",
                    on_click=AppState.set_active_tab("builder"),
                    variant="ghost",
                    style={
                        "color": TEXT_MUTED_LIGHT,
                        "font_weight": "600"
                    }
                ),
                rx.button(
                    "Sign Out",
                    on_click=AppState.logout_user,
                    variant="outline",
                    style={
                        "border": f"1px solid {ACCENT_MUTED_BORDER}",
                        "color": TEXT_MUTED_LIGHT,
                        "border_radius": "6px"
                    }
                ),
                spacing="3",
                align="center"
            ),
            width="100%",
            align="center",
            padding_x="2rem",
            padding_y="1rem"
        ),
        background="#FFFFFF",
        border_bottom=f"1px solid {ACCENT_MUTED_BORDER}",
        box_shadow="0 1px 3px rgba(91, 14, 45, 0.03)",
        position="sticky",
        top="0",
        z_index="100"
    )
