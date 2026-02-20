#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2",
#   "pydantic",
# ]
# ///
"""
build-report.py — Compile GitHub Copilot metrics + seat data into a markdown report.

Usage:
    uv run build-report.py <metrics.json> <seats.json>

Output:
    Prints the markdown report to stdout.
"""

import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field


TEMPLATE_DIR = Path(__file__).parent
TEMPLATE_NAME = "report.md.j2"


# ── GitHub API models ──────────────────────────────────────────────────────────

class EngagementMetrics(BaseModel):
    total_engaged_users: int = 0


class Language(BaseModel):
    name: str
    total_engaged_users: int = 0
    total_code_suggestions: int = 0
    total_code_acceptances: int = 0
    total_code_lines_suggested: int = 0
    total_code_lines_accepted: int = 0


class CopilotModel(BaseModel):
    name: str
    is_custom_model: bool = False
    total_engaged_users: int = 0
    languages: list[Language] = []


class Editor(BaseModel):
    name: str
    total_engaged_users: int = 0
    models: list[CopilotModel] = []


class IdeCompletions(BaseModel):
    total_engaged_users: int = 0
    editors: list[Editor] = []
    languages: list[Language] = []


class DayMetrics(BaseModel):
    date: str
    total_active_users: int = 0
    total_engaged_users: int = 0
    copilot_ide_chat: EngagementMetrics = Field(default_factory=EngagementMetrics)
    copilot_dotcom_chat: EngagementMetrics = Field(default_factory=EngagementMetrics)
    copilot_dotcom_pull_requests: EngagementMetrics = Field(default_factory=EngagementMetrics)
    copilot_ide_code_completions: IdeCompletions = Field(default_factory=IdeCompletions)


class Assignee(BaseModel):
    login: str


class Seat(BaseModel):
    created_at: datetime
    assignee: Assignee
    last_authenticated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    last_activity_editor: Optional[str] = None
    pending_cancellation_date: Optional[str] = None


class SeatsResponse(BaseModel):
    total_seats: int
    seats: list[Seat]


# ── Helpers ────────────────────────────────────────────────────────────────────

def pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 1) if denominator else 0.0


def days_since(dt: datetime, now: datetime) -> int:
    return (now - dt.astimezone(timezone.utc)).days


def editor_short(raw: Optional[str]) -> str:
    if not raw:
        return "—"
    return raw.split("/")[0] if "/" in raw else raw


# ── Context builder ────────────────────────────────────────────────────────────

def build_context(metrics: list[DayMetrics], seats: SeatsResponse) -> dict:
    now = datetime.now(timezone.utc)

    # ── Aggregate metrics ──────────────────────────────────────────────────────
    total_active = total_engaged = 0
    total_sugg = total_accept = total_lines_sugg = total_lines_accept = 0
    ide_chat = dotcom_chat = pr_days = 0
    editors: dict[str, int] = {}
    languages: dict[str, dict] = {}

    for day in metrics:
        total_active  += day.total_active_users
        total_engaged += day.total_engaged_users
        ide_chat      += day.copilot_ide_chat.total_engaged_users
        dotcom_chat   += day.copilot_dotcom_chat.total_engaged_users
        pr_days       += day.copilot_dotcom_pull_requests.total_engaged_users

        for editor in day.copilot_ide_code_completions.editors:
            editors[editor.name] = editors.get(editor.name, 0) + editor.total_engaged_users
            for model in editor.models:
                for lang in model.languages:
                    total_sugg         += lang.total_code_suggestions
                    total_accept       += lang.total_code_acceptances
                    total_lines_sugg   += lang.total_code_lines_suggested
                    total_lines_accept += lang.total_code_lines_accepted
                    if lang.name not in languages:
                        languages[lang.name] = {"s": 0, "a": 0, "ls": 0, "la": 0}
                    languages[lang.name]["s"]  += lang.total_code_suggestions
                    languages[lang.name]["a"]  += lang.total_code_acceptances
                    languages[lang.name]["ls"] += lang.total_code_lines_suggested
                    languages[lang.name]["la"] += lang.total_code_lines_accepted

    # ── Weekly trend ───────────────────────────────────────────────────────────
    weekly_raw: dict[str, dict] = defaultdict(lambda: {"active": 0, "engaged": 0, "sugg": 0, "accept": 0})
    for day in metrics:
        week = datetime.strptime(day.date, "%Y-%m-%d").strftime("%Y-W%V")
        weekly_raw[week]["active"]  += day.total_active_users
        weekly_raw[week]["engaged"] += day.total_engaged_users
        for editor in day.copilot_ide_code_completions.editors:
            for model in editor.models:
                for lang in model.languages:
                    weekly_raw[week]["sugg"]   += lang.total_code_suggestions
                    weekly_raw[week]["accept"] += lang.total_code_acceptances

    # ── Per-user seats ─────────────────────────────────────────────────────────
    user_rows = []
    for seat in seats.seats:
        if seat.last_activity_at:
            ago     = days_since(seat.last_activity_at, now)
            act_str = f"{seat.last_activity_at.date()} ({ago}d ago)"
        else:
            ago, act_str = 9999, "Never"

        auth_str = (
            f"{seat.last_authenticated_at.date()} ({days_since(seat.last_authenticated_at, now)}d ago)"
            if seat.last_authenticated_at else "Never"
        )

        status = (
            "❌ Never Used" if ago == 9999
            else "✅ Active"   if ago <= 7
            else "⚠️ Inactive" if ago <= 30
            else "🔴 Stale"
        )

        user_rows.append({
            "sort_key":    ago,
            "login":       seat.assignee.login,
            "seat_since":  seat.created_at.date(),
            "last_auth":   auth_str,
            "last_active": act_str,
            "editor":      editor_short(seat.last_activity_editor),
            "status":      status,
        })

    return {
        "generated":  now.strftime("%Y-%m-%d"),
        "date_start": metrics[0].date,
        "date_end":   metrics[-1].date,
        "days":       len(metrics),
        "summary": {
            "total_active":       total_active,
            "total_engaged":      total_engaged,
            "total_sugg":         total_sugg,
            "total_accept":       total_accept,
            "accept_rate":        pct(total_accept, total_sugg),
            "total_lines_sugg":   total_lines_sugg,
            "total_lines_accept": total_lines_accept,
            "line_accept_rate":   pct(total_lines_accept, total_lines_sugg),
            "ide_chat":           ide_chat,
            "dotcom_chat":        dotcom_chat,
            "pr_days":            pr_days,
        },
        "editors": [
            {"name": k, "count": v}
            for k, v in sorted(editors.items(), key=lambda x: x[1], reverse=True)
        ],
        "top_langs": [
            {
                "name":             name,
                "sugg":             v["s"],
                "accept":           v["a"],
                "accept_rate":      pct(v["a"], v["s"]),
                "lines_sugg":       v["ls"],
                "lines_accept":     v["la"],
                "line_accept_rate": pct(v["la"], v["ls"]),
            }
            for name, v in sorted(languages.items(), key=lambda x: x[1]["s"], reverse=True)[:10]
        ],
        "weekly": [
            {
                "label":       week,
                "active":      v["active"],
                "engaged":     v["engaged"],
                "sugg":        v["sugg"],
                "accept":      v["accept"],
                "accept_rate": pct(v["accept"], v["sugg"]),
            }
            for week, v in sorted(weekly_raw.items())
        ],
        "users": sorted(user_rows, key=lambda x: x["sort_key"]),
    }


# ── Renderer ───────────────────────────────────────────────────────────────────

def render(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        keep_trailing_newline=True,
    )
    env.filters["commafy"] = lambda v: f"{v:,}"
    return env.get_template(TEMPLATE_NAME).render(**context)


# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run build-report.py <metrics.json> <seats.json>", file=sys.stderr)
        sys.exit(1)

    raw_metrics = Path(sys.argv[1]).read_text()
    raw_seats   = Path(sys.argv[2]).read_text()

    import json
    metrics = [DayMetrics.model_validate(d) for d in json.loads(raw_metrics)]
    seats   = SeatsResponse.model_validate(json.loads(raw_seats))

    print(render(build_context(metrics, seats)))
