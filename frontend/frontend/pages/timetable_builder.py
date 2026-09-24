"""
Reflex Timetable & Semester Builder View
Step-by-step editorial form to configure semester boundaries, exclusion dates, and recurring weekly unit time blocks.
"""

import reflex as rx
from frontend.state import AppState
from frontend.components.navbar import navbar
from frontend.theme import (
    PRIMARY_BURGUNDY,
    PRIMARY_DEEP,
    ACCENT_WINE,
    ACCENT_MUTED_BORDER,
    BG_PARCHMENT_LIGHT,
    TEXT_PRIMARY_LIGHT,
    TEXT_MUTED_LIGHT
)

from frontend.state import DraftUnitItem

def render_draft_unit_row(unit: DraftUnitItem) -> rx.Component:
    days_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    day_str = days_map.get(unit.day_of_week, "Mon")
    
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(unit.code, font_family="var(--font-mono)", font_weight="700", color=PRIMARY_BURGUNDY, size="2"),
                background="#F4ECEE",
                padding="4px 8px",
                border_radius="4px",
                border=f"1px solid {ACCENT_WINE}22"
            ),
            rx.vstack(
                rx.text(unit.name, font_weight="600", color=TEXT_PRIMARY_LIGHT, size="2"),
                rx.text(f"Every {day_str} @ {unit.start_time} - {unit.end_time}", size="1", color=TEXT_MUTED_LIGHT, font_family="var(--font-mono)"),
                spacing="0",
                align="start"
            ),
            rx.spacer(),
            rx.button(
                "Remove",
                on_click=AppState.remove_draft_unit(unit.code),
                variant="ghost",
                style={"color": "#8C1D24", "font_size": "0.85rem", "cursor": "pointer"}
            ),
            width="100%",
            align="center"
        ),
        padding="10px 14px",
        border_bottom=f"1px solid {ACCENT_MUTED_BORDER}"
    )

def timetable_builder_page() -> rx.Component:
    return rx.box(
        navbar(),

        rx.container(
            rx.vstack(
                # Title Banner
                rx.vstack(
                    rx.heading("Semester Timetable Builder", font_family="var(--font-heading)", size="8", color=PRIMARY_DEEP, font_weight="normal"),
                    rx.text("Define academic term dates, holiday exclusions, and weekly course blocks to initialize your schedule generator.", color=TEXT_MUTED_LIGHT, size="3"),
                    spacing="1",
                    align_items="flex-start",
                    margin_bottom="1.5rem"
                ),

                # Grid: Form on Left, Draft Units Preview on Right
                rx.grid(
                    # Left Column: Semester Boundaries Form
                    rx.box(
                        rx.vstack(
                            rx.heading("1. Term Parameters & Limits", font_family="var(--font-heading)", size="5", color=PRIMARY_BURGUNDY),
                            
                            rx.vstack(
                                rx.text("Start Date", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                                rx.input(
                                    value=AppState.builder_start_date,
                                    on_change=AppState.set_builder_start_date,
                                    type="date",
                                    style={"width": "100%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "8px", "padding": "8px 12px", "background": "#FAF7F5"}
                                ),
                                width="100%",
                                align="start",
                                spacing="1"
                            ),

                            rx.vstack(
                                rx.text("End Date", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                                rx.input(
                                    value=AppState.builder_end_date,
                                    on_change=AppState.set_builder_end_date,
                                    type="date",
                                    style={"width": "100%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "8px", "padding": "8px 12px", "background": "#FAF7F5"}
                                ),
                                width="100%",
                                align="start",
                                spacing="1"
                            ),

                            rx.vstack(
                                rx.text("Exclusion Holidays (Comma separated YYYY-MM-DD)", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                                rx.input(
                                    value=AppState.builder_holidays,
                                    on_change=AppState.set_builder_holidays,
                                    placeholder="2026-10-12, 2026-11-26",
                                    style={"width": "100%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "8px", "padding": "8px 12px", "background": "#FAF7F5"}
                                ),
                                width="100%",
                                align="start",
                                spacing="1"
                            ),

                            rx.vstack(
                                rx.text("Maximum Allowed Absence Cap (%)", size="2", font_weight="600", color=TEXT_PRIMARY_LIGHT),
                                rx.input(
                                    value=AppState.builder_max_absence_pct,
                                    on_change=AppState.set_builder_max_absence_pct,
                                    type="number",
                                    style={"width": "100%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "8px", "padding": "8px 12px", "background": "#FAF7F5"}
                                ),
                                width="100%",
                                align="start",
                                spacing="1"
                            ),

                            spacing="4",
                            width="100%"
                        ),
                        background="#FFFFFF",
                        border=f"1px solid {ACCENT_MUTED_BORDER}",
                        border_radius="14px",
                        padding="1.75rem",
                        box_shadow="0 4px 16px rgba(74, 14, 23, 0.05)"
                    ),

                    # Right Column: Weekly Course Block Entry & List
                    rx.box(
                        rx.vstack(
                            rx.heading("2. Weekly Course Blocks", font_family="var(--font-heading)", size="5", color=PRIMARY_BURGUNDY),
                            
                            # Inputs for adding course slot
                            rx.vstack(
                                rx.hstack(
                                    rx.input(
                                        placeholder="Course Code",
                                        value=AppState.new_unit_code,
                                        on_change=AppState.set_new_unit_code,
                                        style={"width": "40%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "6px", "padding": "6px 10px"}
                                    ),
                                    rx.input(
                                        placeholder="Course Title",
                                        value=AppState.new_unit_name,
                                        on_change=AppState.set_new_unit_name,
                                        style={"width": "60%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "6px", "padding": "6px 10px"}
                                    ),
                                    width="100%",
                                    spacing="2"
                                ),

                                rx.hstack(
                                    rx.select(
                                        placeholder="Select Day",
                                        items=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                                        value=AppState.new_unit_day,
                                        on_change=AppState.set_new_unit_day,
                                        style={"width": "30%", "border_radius": "6px"}
                                    ),
                                    rx.input(
                                        type="time",
                                        value=AppState.new_unit_start,
                                        on_change=AppState.set_new_unit_start,
                                        style={"width": "35%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "6px", "padding": "6px 8px"}
                                    ),
                                    rx.input(
                                        type="time",
                                        value=AppState.new_unit_end,
                                        on_change=AppState.set_new_unit_end,
                                        style={"width": "35%", "border": f"1px solid {ACCENT_MUTED_BORDER}", "border_radius": "6px", "padding": "6px 8px"}
                                    ),
                                    width="100%",
                                    spacing="2"
                                ),

                                rx.button(
                                    "+ Add Course Slot",
                                    on_click=AppState.add_draft_unit,
                                    variant="outline",
                                    style={
                                        "width": "100%",
                                        "color": PRIMARY_BURGUNDY,
                                        "border": f"1px solid {PRIMARY_BURGUNDY}",
                                        "font_weight": "600",
                                        "border_radius": "6px",
                                        "cursor": "pointer"
                                    }
                                ),
                                spacing="3",
                                width="100%",
                                background="#FAF7F5",
                                padding="1rem",
                                border_radius="10px",
                                border=f"1px solid {ACCENT_MUTED_BORDER}"
                            ),

                            # Configured Course Blocks List
                            rx.vstack(
                                rx.text("Configured Course Schedule:", font_weight="700", size="2", color=TEXT_PRIMARY_LIGHT),
                                rx.foreach(
                                    AppState.draft_units,
                                    render_draft_unit_row
                                ),
                                spacing="0",
                                width="100%"
                            ),

                            # Generate Engine Button
                            rx.button(
                                "Generate Full Semester Schedule",
                                on_click=AppState.generate_schedule,
                                style={
                                    "width": "100%",
                                    "background": PRIMARY_BURGUNDY,
                                    "color": "#FFFFFF",
                                    "font_weight": "700",
                                    "font_size": "1rem",
                                    "border_radius": "8px",
                                    "padding": "14px",
                                    "margin_top": "1rem",
                                    "box_shadow": "0 2px 8px rgba(91, 14, 45, 0.2)",
                                    "cursor": "pointer"
                                }
                            ),

                            spacing="4",
                            width="100%"
                        ),
                        background="#FFFFFF",
                        border=f"1px solid {ACCENT_MUTED_BORDER}",
                        border_radius="14px",
                        padding="1.75rem",
                        box_shadow="0 4px 16px rgba(74, 14, 23, 0.05)"
                    ),
                    columns="2",
                    spacing="5",
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
