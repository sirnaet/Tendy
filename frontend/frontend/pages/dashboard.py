"""
Reflex Dashboard View
Displays Today's Roster panel with 3 tactile toggles and Course Overview Cards with burgundy progress bars and safe skip metrics.
"""

import reflex as rx
from frontend.state import AppState
from frontend.components.navbar import navbar
from frontend.theme import (
    PRIMARY_BURGUNDY,
    PRIMARY_DEEP,
    ACCENT_WINE,
    ACCENT_ROSE,
    ACCENT_MUTED_BORDER,
    BG_PARCHMENT_LIGHT,
    STATUS_SAGE,
    STATUS_SAGE_BG,
    STATUS_CRIMSON,
    STATUS_CRIMSON_BG,
    STATUS_MUTED_GRAY,
    STATUS_MUTED_GRAY_BG,
    TEXT_PRIMARY_LIGHT,
    TEXT_MUTED_LIGHT
)

from frontend.state import ClassItem, CourseUnitItem

def render_roster_item(item: ClassItem) -> rx.Component:
    """Renders single class item on Today's Roster with 3 tactile status toggles"""
    return rx.box(
        rx.hstack(
            # Class Details
            rx.hstack(
                rx.box(
                    rx.text(item.unit_code, font_family="var(--font-mono)", font_weight="700", color=PRIMARY_BURGUNDY, size="2"),
                    background="#F4ECEE",
                    padding="6px 10px",
                    border_radius="6px",
                    border=f"1px solid {ACCENT_WINE}22"
                ),
                rx.vstack(
                    rx.text(item.unit_name, font_weight="600", color=TEXT_PRIMARY_LIGHT, size="3"),
                    rx.text(f"{item.start_time} - {item.end_time} ({item.duration_hours} hrs)", size="2", color=TEXT_MUTED_LIGHT, font_family="var(--font-mono)"),
                    spacing="1",
                    align="start"
                ),
                spacing="3",
                align="center"
            ),

            rx.spacer(),

            # Tactile 3-State Toggle Group
            rx.hstack(
                rx.button(
                    "Attended",
                    on_click=AppState.update_class_status(item.id, "Attended"),
                    style={
                        "background": rx.cond(item.status == "Attended", STATUS_SAGE_BG, "#FFFFFF"),
                        "color": rx.cond(item.status == "Attended", STATUS_SAGE, TEXT_MUTED_LIGHT),
                        "border": rx.cond(item.status == "Attended", f"1.5px solid {STATUS_SAGE}", f"1px solid {ACCENT_MUTED_BORDER}"),
                        "font_weight": rx.cond(item.status == "Attended", "700", "500"),
                        "border_radius": "6px",
                        "padding": "6px 14px",
                        "cursor": "pointer"
                    }
                ),
                rx.button(
                    "Missed",
                    on_click=AppState.update_class_status(item.id, "Missed"),
                    style={
                        "background": rx.cond(item.status == "Missed", STATUS_CRIMSON_BG, "#FFFFFF"),
                        "color": rx.cond(item.status == "Missed", STATUS_CRIMSON, TEXT_MUTED_LIGHT),
                        "border": rx.cond(item.status == "Missed", f"1.5px solid {STATUS_CRIMSON}", f"1px solid {ACCENT_MUTED_BORDER}"),
                        "font_weight": rx.cond(item.status == "Missed", "700", "500"),
                        "border_radius": "6px",
                        "padding": "6px 14px",
                        "cursor": "pointer"
                    }
                ),
                rx.button(
                    "Cancelled",
                    on_click=AppState.update_class_status(item.id, "Cancelled"),
                    style={
                        "background": rx.cond(item.status == "Cancelled", STATUS_MUTED_GRAY_BG, "#FFFFFF"),
                        "color": rx.cond(item.status == "Cancelled", STATUS_MUTED_GRAY, TEXT_MUTED_LIGHT),
                        "border": rx.cond(item.status == "Cancelled", f"1.5px solid {STATUS_MUTED_GRAY}", f"1px solid {ACCENT_MUTED_BORDER}"),
                        "font_weight": rx.cond(item.status == "Cancelled", "700", "500"),
                        "border_radius": "6px",
                        "padding": "6px 14px",
                        "cursor": "pointer"
                    }
                ),
                spacing="2"
            ),
            width="100%",
            align="center",
            padding="1rem"
        ),
        border_bottom=f"1px solid {ACCENT_MUTED_BORDER}"
    )

def render_course_card(unit: CourseUnitItem) -> rx.Component:
    """Renders Editorial Course Card with attendance ratio bar, safe skips badge, and status flag"""
    return rx.box(
        rx.vstack(
            # Top row: Course Code & Status Badge
            rx.hstack(
                rx.vstack(
                    rx.text(unit.code, font_family="var(--font-mono)", font_weight="700", font_size="1.2rem", color=PRIMARY_BURGUNDY),
                    rx.text(unit.name, font_weight="600", size="3", color=TEXT_PRIMARY_LIGHT),
                    spacing="0",
                    align="start"
                ),
                rx.spacer(),
                rx.cond(
                    unit.is_critical,
                    rx.badge(
                        "CRITICAL",
                        style={
                            "background": STATUS_CRIMSON_BG,
                            "color": STATUS_CRIMSON,
                            "border": f"1px solid {STATUS_CRIMSON}",
                            "font_weight": "700",
                            "padding": "4px 10px",
                            "border_radius": "4px",
                            "font_family": "var(--font-mono)"
                        }
                    ),
                    rx.badge(
                        "OKAY",
                        style={
                            "background": STATUS_SAGE_BG,
                            "color": STATUS_SAGE,
                            "border": f"1px solid {STATUS_SAGE}",
                            "font_weight": "700",
                            "padding": "4px 10px",
                            "border_radius": "4px",
                            "font_family": "var(--font-mono)"
                        }
                    )
                ),
                width="100%",
                align="start"
            ),

            rx.divider(border_color=ACCENT_MUTED_BORDER),

            # Progress Bar & Rate
            rx.vstack(
                rx.hstack(
                    rx.text("Attendance Rate", size="2", color=TEXT_MUTED_LIGHT, font_weight="500"),
                    rx.spacer(),
                    rx.text(f"{unit.attendance_rate}%", font_family="var(--font-mono)", font_weight="700", color=PRIMARY_DEEP),
                    width="100%"
                ),
                # Burgundy Horizontal Progress Bar
                rx.box(
                    rx.box(
                        width=f"{unit.attendance_rate}%",
                        height="100%",
                        background=f"linear-gradient(90deg, {PRIMARY_BURGUNDY} 0%, {ACCENT_WINE} 100%)",
                        border_radius="4px",
                        transition="width 0.3s ease"
                    ),
                    width="100%",
                    height="10px",
                    background="#F4ECEE",
                    border_radius="4px",
                    overflow="hidden"
                ),
                width="100%",
                spacing="1"
            ),

            # Bottom Metrics Grid: Absence % and Safe Skips Badge
            rx.hstack(
                # Absence Rate
                rx.vstack(
                    rx.text("Absence Rate", size="1", color=TEXT_MUTED_LIGHT),
                    rx.text(f"{unit.absence_rate}% / max {unit.allowed_absence}%", font_family="var(--font-mono)", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                    spacing="0"
                ),
                rx.spacer(),
                # Safe Skips Remaining Badge
                rx.box(
                    rx.hstack(
                        rx.text("Safe Skips Left:", size="2", color=TEXT_PRIMARY_LIGHT, font_weight="600"),
                        rx.badge(
                            f"{unit.safe_skips_left} classes",
                            style={
                                "background": PRIMARY_BURGUNDY,
                                "color": "#FFFFFF",
                                "font_family": "var(--font-mono)",
                                "font_weight": "700",
                                "padding": "4px 8px",
                                "border_radius": "6px"
                            }
                        ),
                        spacing="2",
                        align="center"
                    ),
                    background="#FAF7F5",
                    padding="6px 12px",
                    border_radius="8px",
                    border=f"1px solid {ACCENT_MUTED_BORDER}"
                ),
                width="100%",
                align="center",
                margin_top="6px"
            ),
            spacing="3",
            width="100%"
        ),
        background="#FFFFFF",
        border=f"1px solid {ACCENT_MUTED_BORDER}",
        border_radius="12px",
        padding="1.25rem",
        box_shadow="0 2px 8px rgba(91, 14, 45, 0.06)",
        width="100%"
    )

def dashboard_page() -> rx.Component:
    return rx.box(
        navbar(),

        rx.container(
            rx.vstack(
                # Dashboard Section Header
                rx.hstack(
                    rx.vstack(
                        rx.heading("Academic Dashboard", font_family="var(--font-heading)", size="8", color=PRIMARY_DEEP, font_weight="normal"),
                        rx.text("Track real-time class attendance, absence safety limits, and daily schedule.", color=TEXT_MUTED_LIGHT, size="3"),
                        spacing="1",
                        align="start"
                    ),
                    rx.spacer(),
                    rx.button(
                        "+ Setup New Timetable",
                        on_click=AppState.set_active_tab("builder"),
                        style={
                            "background": PRIMARY_BURGUNDY,
                            "color": "#FFFFFF",
                            "font_weight": "600",
                            "border_radius": "8px",
                            "padding": "10px 16px",
                            "box_shadow": "0 2px 6px rgba(91, 14, 45, 0.15)",
                            "cursor": "pointer"
                        }
                    ),
                    width="100%",
                    align="center",
                    margin_bottom="1.5rem"
                ),

                # Today's Roster Panel
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.heading("Today's Roster", font_family="var(--font-heading)", size="6", color=PRIMARY_BURGUNDY),
                            rx.badge("3 Scheduled Classes", color_scheme="crimson", variant="soft"),
                            width="100%",
                            align="center",
                            padding="1.25rem 1.5rem",
                            border_bottom=f"1px solid {ACCENT_MUTED_BORDER}"
                        ),

                        rx.foreach(
                            AppState.today_roster,
                            render_roster_item
                        ),
                        spacing="0",
                        width="100%"
                    ),
                    background="#FFFFFF",
                    border=f"1px solid {ACCENT_MUTED_BORDER}",
                    border_radius="14px",
                    box_shadow="0 4px 16px rgba(74, 14, 23, 0.06)",
                    margin_bottom="2rem",
                    width="100%"
                ),

                # Course Overview Section
                rx.vstack(
                    rx.heading("Course Absence Limits & Metrics", font_family="var(--font-heading)", size="6", color=PRIMARY_BURGUNDY),
                    rx.text("Dynamic Safe Skips remaining computed based on 20% max allowed absence cap.", color=TEXT_MUTED_LIGHT, size="2"),
                    
                    rx.grid(
                        rx.foreach(
                            AppState.units_data,
                            render_course_card
                        ),
                        columns="2",
                        spacing="4",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                spacing="4",
                padding_y="2rem",
                width="100%"
            ),
            max_width="1140px"
        ),
        background=BG_PARCHMENT_LIGHT,
        min_height="100vh"
    )
