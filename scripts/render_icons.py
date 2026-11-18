#!/usr/bin/env python3
"""Render phpBB 3.3 prosilver's small Font Awesome icons to transparent PNGs.

prosilver draws its small icons (red "first unread post" page, paperclip,
padlock and so on) with the Font Awesome icon font, so there are no image
files a forum post could link to. This script draws each icon in headless
Chromium with a phpBB board's own font-awesome.min.css, using prosilver's
colours and sizes, and saves one PNG per icon.

Inputs:  --board, the root of a local phpBB 3.3 install (only its
         assets/css/font-awesome.min.css and assets/fonts/ are read).
Outputs: <out>/<name>.png for every entry in ICONS, and, with --sheet,
         a review sheet image showing every icon beside its label.
"""
import argparse
import sys
import tempfile
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent

# Colours from prosilver theme/colours.css; plain icons inherit their context.
RED, BLUE, GREEN = "#BC2A4D", "#196DB5", "#1B9A1B"
ORANGE, GRAY, LIGHTGRAY = "#FF6600", "#777777", "#999999"
TEXT, BUTTON, LINK = "#536482", "#8F8F8F", "#105289"

# Sizes from prosilver theme/icons.css: default 14px, icon-md 10px,
# icon-lg 16px.
DEFAULT, MD, LG = 14, 10, 16

# (file name, Font Awesome class, colour, font size in px, label)
ICONS = [
    ("subforum_unread", "fa-file-o", RED, DEFAULT, "Subforum, unread"),
    ("subforum_read", "fa-file-o", BLUE, DEFAULT, "Subforum, read"),
    ("subforum_link", "fa-external-link", BLUE, DEFAULT, "Subforum link"),
    ("last_post", "fa-external-link-square", LIGHTGRAY, MD, "Go to last post"),
    ("feed", "fa-rss-square", ORANGE, DEFAULT, "Forum feed"),
    ("unapproved", "fa-question", BLUE, DEFAULT, "Awaiting approval"),
    ("first_unread", "fa-file", RED, MD, "Go to first unread post"),
    ("attachment", "fa-paperclip", TEXT, DEFAULT, "Has attachments"),
    ("poll", "fa-bar-chart", TEXT, DEFAULT, "Has a poll"),
    ("pagination", "fa-clone", TEXT, DEFAULT, "Topic pages"),
    ("reported", "fa-exclamation", RED, DEFAULT, "Reported"),
    ("deleted", "fa-recycle", GREEN, DEFAULT, "Soft deleted"),
    ("locked", "fa-lock", BUTTON, DEFAULT, "Locked (button)"),
    ("post_unread", "fa-file", RED, MD, "Unread post"),
    ("post_read", "fa-file", LIGHTGRAY, MD, "Read post"),
    ("reply", "fa-reply", BUTTON, DEFAULT, "Post reply (button)"),
    ("topic_tools", "fa-wrench", BUTTON, DEFAULT, "Topic tools"),
    ("bookmark", "fa-bookmark-o", LINK, DEFAULT, "Bookmark topic"),
    ("email_topic", "fa-envelope-o", LINK, DEFAULT, "Email topic"),
    ("bump", "fa-level-up", LINK, DEFAULT, "Bump topic"),
    ("print", "fa-print", LINK, DEFAULT, "Print view"),
    ("quote", "fa-quote-left", BUTTON, DEFAULT, "Quote"),
    ("edit", "fa-pencil", BUTTON, DEFAULT, "Edit"),
    ("delete", "fa-times", BUTTON, DEFAULT, "Delete"),
    ("report", "fa-exclamation", BUTTON, DEFAULT, "Report"),
    ("warn", "fa-exclamation-triangle", BUTTON, DEFAULT, "Warn"),
    ("info", "fa-info", BUTTON, DEFAULT, "Post details"),
    ("contact", "fa-commenting-o", LINK, LG, "Contact poster"),
    ("back_to_top", "fa-chevron-circle-up", GRAY, DEFAULT, "Back to top"),
    ("search", "fa-search", BUTTON, DEFAULT, "Search"),
    ("advanced_search", "fa-cog", BUTTON, DEFAULT, "Advanced search"),
    ("quick_links", "fa-bars", LINK, DEFAULT, "Quick links"),
    ("unread_posts", "fa-file-o", RED, DEFAULT, "Unread / new posts"),
    ("active_topics", "fa-file-o", BLUE, DEFAULT, "Active topics"),
    ("unanswered", "fa-file-o", GRAY, DEFAULT, "Unanswered / own posts"),
    ("faq", "fa-question-circle", LINK, DEFAULT, "FAQ"),
    ("notifications", "fa-bell", LINK, DEFAULT, "Notifications"),
    ("private_messages", "fa-inbox", LINK, DEFAULT, "Private messages"),
    ("ucp", "fa-sliders", LINK, DEFAULT, "User Control Panel"),
    ("profile", "fa-user", LINK, DEFAULT, "Profile"),
    ("members", "fa-group", LINK, DEFAULT, "Members"),
    ("team", "fa-shield", LINK, DEFAULT, "The team"),
    ("login_logout", "fa-power-off", LINK, DEFAULT, "Log in / log out"),
    ("register", "fa-pencil-square-o", LINK, DEFAULT, "Register"),
    ("board_index", "fa-home", LINK, DEFAULT, "Board index"),
]


def icons_page(css_uri: str) -> str:
    """Return HTML holding every icon, each in its own padded box."""
    boxes = "\n".join(
        f'<span class="box" id="{name}"><i class="fa {cls} fa-fw" '
        f'style="color:{colour};font-size:{size}px"></i></span>'
        for name, cls, colour, size, _ in ICONS)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{css_uri}">
<style>
html, body {{ background: transparent; margin: 0; }}
.box {{ display: inline-flex; align-items: center; justify-content: center;
        padding: 1px; margin: 4px; line-height: 1; }}
.fa {{ line-height: 1; }}
</style></head><body>{boxes}</body></html>"""


def sheet_page(out_dir: Path) -> str:
    """Return HTML showing every rendered PNG beside its label."""
    rows = "\n".join(
        f'<tr><td><img src="{(out_dir / f"{name}.png").as_uri()}"></td>'
        f'<td>{escape(label)}</td><td><code>{name}.png</code></td></tr>'
        for name, _, _, _, label in ICONS)
    return ("<!doctype html><meta charset='utf-8'><style>body{font:13px "
            "Verdana,sans-serif;background:#F5F7FA;color:#536482;margin:8px}"
            "td{padding:3px 10px}</style><table>" + rows + "</table>")


def parse_args() -> argparse.Namespace:
    """Parse the command line; show help when run without arguments."""
    parser = argparse.ArgumentParser(
        description="Render prosilver's small Font Awesome icons to PNGs.")
    parser.add_argument(
        "-b", "--board", type=Path, required=True,
        help="root folder of a local phpBB 3.3 install to take "
             "font-awesome.min.css and its fonts from")
    parser.add_argument(
        "-o", "--out", type=Path, default=REPO / "icons",
        help="folder to write the PNGs to (default: the repo's icons/)")
    parser.add_argument(
        "-s", "--sheet", type=Path,
        help="also write a review sheet PNG of every icon to this path")
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    return parser.parse_args()


def main() -> None:
    """Render each icon to its own PNG, and the review sheet if asked."""
    args = parse_args()
    css = args.board / "assets/css/font-awesome.min.css"
    if not css.is_file():
        sys.exit(f"--board: {css} not found; give the root of a phpBB 3.3 "
                 "install")
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        page_file = Path(tmp) / "icons.html"
        page_file.write_text(icons_page(css.resolve().as_uri()),
                             encoding="utf-8")
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        page.goto(page_file.as_uri())
        page.evaluate("document.fonts.ready")
        for name, *_ in ICONS:
            page.locator(f"#{name}").screenshot(
                path=str(args.out / f"{name}.png"), omit_background=True)
        if args.sheet:
            sheet_file = Path(tmp) / "sheet.html"
            sheet_file.write_text(sheet_page(args.out.resolve()),
                                  encoding="utf-8")
            sheet = browser.new_page(device_scale_factor=2,
                                     viewport={"width": 420, "height": 400})
            sheet.goto(sheet_file.as_uri())
            sheet.screenshot(path=str(args.sheet), full_page=True)
        browser.close()
    print(f"Rendered {len(ICONS)} icons to {args.out}")


if __name__ == "__main__":
    main()
