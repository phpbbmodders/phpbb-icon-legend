#!/usr/bin/env python3
"""Build the icon legend forum post from its template.

The template (post/template.bbcode.txt) holds the whole post except the
small-icons section, which is marked by {{SMALL_ICONS}}. This script fills
that marker with one "[img]<url> - meaning" line per icon, pointing at the
PNGs in icons/, and writes post/icon-legend.bbcode.txt.

Inputs:  post/template.bbcode.txt, icons/*.png, --base-url.
Outputs: post/icon-legend.bbcode.txt (--write), or exit code 1 when that
         file is out of date or names a PNG that icons/ lacks (--check).
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "post/template.bbcode.txt"
OUTPUT = REPO / "post/icon-legend.bbcode.txt"
ICONS = REPO / "icons"
MARKER = "{{SMALL_ICONS}}"
DEFAULT_BASE_URL = ("https://raw.githubusercontent.com/phpbbmodders/"
                    "phpbb-icon-legend/main/icons")

# (heading, [(png name, meaning), ...]) in post order.
SECTIONS = [
    ("BOARD INDEX AND FORUM LIST", [
        ("subforum_unread", "Subforum has unread posts"),
        ("subforum_read", "Subforum has no unread posts"),
        ("subforum_link", "Subforum is a link to another site"),
        ("last_post", "Go to the last post in the forum"),
        ("feed", "Feed (RSS/Atom) for that forum"),
        ("unapproved", "Topics or posts are waiting for approval "
                       "(moderators only)"),
    ]),
    ("TOPIC LIST", [
        ("first_unread", "Topic has unread posts; click it to jump straight "
                         "to the first one you haven't read"),
        ("last_post", "Go to the last post in the topic"),
        ("attachment", "Topic has attachments"),
        ("poll", "Topic has a poll"),
        ("pagination", "Topic has more than one page; click a number to go "
                       "to that page"),
        ("reported", "Topic has been reported (moderators only)"),
        ("unapproved", "Topic or post is waiting for approval "
                       "(moderators only)"),
        ("deleted", "Topic has been soft deleted (moderators only)"),
        ("locked", "Forum is locked; no new topics can be posted"),
    ]),
    ("INSIDE A TOPIC", [
        ("post_unread", "Unread post"),
        ("post_read", "Read post"),
        ("reply", "Post a reply"),
        ("locked", "Topic is locked; no replies can be posted"),
        ("topic_tools", "Topic tools menu"),
        ("bookmark", "Bookmark this topic"),
        ("email_topic", "Email this topic to a friend"),
        ("bump", "Bump this topic"),
        ("print", "Print view"),
        ("quote", "Reply with a quote"),
        ("edit", "Edit the post"),
        ("delete", "Delete the post"),
        ("report", "Report the post"),
        ("warn", "Warn the poster (moderators only)"),
        ("info", "Post details (moderators only)"),
        ("contact", "Contact the poster"),
        ("reported", "Post has been reported, or is waiting for approval "
                     "(moderators only)"),
        ("back_to_top", "Back to top"),
        ("search", "Search this topic or forum"),
        ("advanced_search", "Advanced search"),
    ]),
    ("TOP OF THE PAGE", [
        ("quick_links", "Quick links menu"),
        ("unread_posts", "Unread posts, or new posts since your last visit"),
        ("active_topics", "Active topics"),
        ("unanswered", "Unanswered topics, or your own posts"),
        ("faq", "FAQ"),
        ("notifications", "Notifications; the number shows how many are "
                          "unread"),
        ("private_messages", "Private messages; the number shows how many "
                             "are unread"),
        ("ucp", "User Control Panel"),
        ("profile", "Your profile"),
        ("members", "Members list"),
        ("team", "The team"),
        ("login_logout", "Log in or log out"),
        ("register", "Register"),
        ("board_index", "Board index"),
    ]),
]


def small_icons(base_url: str) -> str:
    """Return the SMALL ICONS section with an [img] line per icon."""
    parts = ["[size=150][b][u]SMALL ICONS[/u][/b][/size]", ""]
    for heading, rows in SECTIONS:
        parts.append(f"[size=100][b][u]{heading}[/u][/b][/size]")
        parts += [f"[img]{base_url}/{name}.png[/img] - {meaning}"
                  for name, meaning in rows]
        parts.append("")
    return "\n".join(parts)


def missing_icons() -> list[str]:
    """Return icon names the post uses that have no PNG in icons/."""
    names = {name for _, rows in SECTIONS for name, _ in rows}
    return sorted(n for n in names if not (ICONS / f"{n}.png").is_file())


def build(base_url: str) -> str:
    """Return the full post text with the marker filled in."""
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count(MARKER) != 1:
        sys.exit(f"{TEMPLATE}: expected exactly one {MARKER} marker")
    return template.replace(MARKER, small_icons(base_url.rstrip("/")))


def parse_args() -> argparse.Namespace:
    """Parse the command line; show help when run without arguments."""
    parser = argparse.ArgumentParser(
        description="Build post/icon-legend.bbcode.txt from the template.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("-w", "--write", action="store_true",
                      help="write post/icon-legend.bbcode.txt")
    mode.add_argument("-c", "--check", action="store_true",
                      help="exit 1 if the built post is out of date or "
                           "uses an icon with no PNG; writes nothing")
    parser.add_argument("-u", "--base-url", default=DEFAULT_BASE_URL,
                        help="URL of the folder holding the icon PNGs "
                             f"(default: {DEFAULT_BASE_URL})")
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    return parser.parse_args()


def main() -> None:
    """Write or check the built post."""
    args = parse_args()
    missing = missing_icons()
    if missing:
        sys.exit("No PNG in icons/ for: " + ", ".join(missing))
    post = build(args.base_url)
    if args.write:
        OUTPUT.write_text(post, encoding="utf-8")
        print(f"Wrote {OUTPUT}")
        return
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
    if current != post:
        sys.exit(f"{OUTPUT.relative_to(REPO)} is out of date; run "
                 "scripts/build_post.py --write")
    print("Post is up to date and every icon has a PNG.")


if __name__ == "__main__":
    main()
