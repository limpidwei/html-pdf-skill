#!/usr/bin/env python3
"""UserPromptSubmit hook for the html-pdf skill.

Claude Code invokes this script with the user prompt as JSON on stdin:
    {"session_id": "...", "prompt": "...", ...}

If the prompt looks like an HTML-to-PDF request, it prints a JSON object
with additionalContext telling Claude to use the html-pdf skill. Otherwise
it prints nothing.

Register in ~/.claude/settings.json:

    {
      "hooks": {
        "UserPromptSubmit": [
          {
            "matcher": "",
            "hooks": [
              {
                "type": "command",
                "command": "python \"<SKILL_DIR>/scripts/hook_trigger.py\""
              }
            ]
          }
        ]
      }
    }
"""

import json
import re
import sys

PATTERN = re.compile(
    r"(\.html?\b|\.htm\b"
    r"|html.{0,8}(转|转成|转换|导出|变成|save|export|print|to).{0,8}pdf"
    r"|pdf\s*(版本|格式|文件).{0,10}html"
    r"|convert\s+.{0,30}html.{0,30}pdf"
    r"|webpage\s+to\s+pdf"
    r"|slides?.{0,20}pdf"
    r"|presentation.{0,20}pdf"
    r"|演示(稿|文稿).{0,10}pdf"
    r"|网页.{0,10}(转|导出|保存).{0,10}pdf"
    r"|保存.{0,10}pdf)",
    re.IGNORECASE,
)


def main() -> int:
    try:
        # Read raw bytes and decode as UTF-8 explicitly: on Windows the
        # console codepage (e.g. GBK) would otherwise mangle CJK prompts.
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return 0

    prompt = payload.get("prompt", "") if isinstance(payload, dict) else ""
    if not PATTERN.search(prompt):
        return 0

    context = (
        "The user's prompt mentions an HTML file or HTML-to-PDF conversion. "
        "Use the html-pdf skill: convert the HTML file or URL to PDF by running "
        "`python -m html_pdf --input <path-or-url> [--hd]` (run "
        "scripts/setup_env.py from the skill directory first if dependencies "
        "may be missing)."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
