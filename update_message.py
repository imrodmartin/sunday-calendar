#!/usr/bin/env python3
"""
update_message.py
Reads the latest "Scripture and Title" email from Gmail and updates index.html.
Requires env vars: GMAIL_USER, GMAIL_APP_PASSWORD
"""
import imaplib
import email
import re
import os

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
SUBJECT_KEYWORD = "Scripture and Title"


def fetch_email_body():
    with imaplib.IMAP4_SSL("imap.gmail.com") as mail:
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        mail.select("inbox")
        _, msg_ids = mail.search(None, f'SUBJECT "{SUBJECT_KEYWORD}"')
        if not msg_ids[0]:
            raise ValueError(f"No emails found with subject containing '{SUBJECT_KEYWORD}'")
        latest_id = msg_ids[0].split()[-1]
        _, msg_data = mail.fetch(latest_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        return msg.get_payload(decode=True).decode("utf-8", errors="ignore")


def parse_title(body):
    # Match text inside straight or curly double quotes
    match = re.search(r'[“"]([^”"\n]+)[”"]', body)
    if not match:
        raise ValueError("No quoted title found in email body")
    return match.group(1).strip()


def parse_scripture(body):
    # Match patterns like "John 11:25", "1 Corinthians 13:4-7", "Song of Solomon 2:1"
    match = re.search(
        r'\b(?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+\d+:\d+(?:[–\-]\d+)?\b',
        body
    )
    if not match:
        raise ValueError("No scripture reference found in email body")
    return match.group(0).strip()


def update_html(title, scripture, html_path="index.html"):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(
        r"<!-- TITLE_START -->.*?<!-- TITLE_END -->",
        f"<!-- TITLE_START -->{title}<!-- TITLE_END -->",
        content, flags=re.DOTALL,
    )
    content = re.sub(
        r"<!-- SCRIPTURE_START -->.*?<!-- SCRIPTURE_END -->",
        f"<!-- SCRIPTURE_START -->{scripture}<!-- SCRIPTURE_END -->",
        content, flags=re.DOTALL,
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated: {title!r} | {scripture!r}")


if __name__ == "__main__":
    body = fetch_email_body()
    title = parse_title(body)
    scripture = parse_scripture(body)
    update_html(title, scripture)
