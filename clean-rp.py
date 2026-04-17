#!/usr/bin/env python3
"""
Clean up WoW whisper RP logs into readable prose.

Designed for addons that persist whisper history as Lua tables, namely
WIM but also maybe Elephant? The saved format interleaves messages from
both participants chronologically, and long pastes get fragmented by
WoW's 255-character whisper limit — so a single RP paragraph often
arrives as 3-5 rapid-fire messages sharing the same timestamp.

This script reassembles those fragments, groups speaker turns, strips
WoW markup, drops OOC chatter within parentheses, and outputs clean prose
suitable for archiving or (consensual) posting. 

Usage:
    python clean_rp_log.py                           # auto-detect input*, write to output.txt
    python clean_rp_log.py input.lua
    python clean_rp_log.py input.lua -o output.txt
    python clean_rp_log.py input.lua --convo Etanna
    python clean_rp_log.py input.lua --latency 2
    cat input.lua | python clean_rp_log.py
"""

import re
import sys
import os
import glob
import argparse


def parse_entries(text):
    """Parse Lua-style table entries from the input text."""
    entries = []

    # Each message lives in a { ... } block. We rely on the fact that WoW
    # saved-variables files don't nest braces inside message entries, so a
    # non-greedy match between braces is safe here without a full Lua parser.
    blocks = re.findall(r'\{(.*?)\}', text, re.DOTALL)

    for block in blocks:
        entry = {}

        # Lua serializes strings as ["key"] = "value". The inner pattern
        # accounts for backslash-escaped characters so we don't break on
        # dialogue containing escaped quotes — common in RP logs.
        for match in re.finditer(r'\["(\w+)"\]\s*=\s*"((?:[^"\\]|\\.)*)"', block):
            key, value = match.group(1), match.group(2)
            value = value.replace('\\"', '"')
            value = value.replace('\\\\', '\\')
            value = value.replace('\\n', '\n')
            entry[key] = value

        for match in re.finditer(r'\["(\w+)"\]\s*=\s*(\d+)', block):
            entry[match.group(1)] = int(match.group(2))

        # "inbound" is the only field we actually use as a boolean — it
        # tells us who spoke without relying on character names, which
        # can change due to server transfers, name changes, or alts.
        for match in re.finditer(r'\["(\w+)"\]\s*=\s*(true|false)', block):
            entry[match.group(1)] = match.group(2) == 'true'

        if 'msg' in entry:
            entries.append(entry)

    return entries


def strip_color_codes(text):
    """Remove WoW UI escape sequences.

    WoW's client uses pipe-prefixed escape codes for inline formatting.
    These show up in saved variables verbatim. The most common ones in
    RP logs come from addons colorizing names or emote text.
    """
    # |cAARRGGBB — start colored text (alpha + RGB, 8 hex digits)
    text = re.sub(r'\|c[0-9a-fA-F]{8}', '', text)
    # Some addons emit |cff directly (implying full alpha), followed by 6 hex
    text = re.sub(r'\|cff[0-9a-fA-F]{6}', '', text)
    # |r — reset to default color
    text = re.sub(r'\|r', '', text)
    # |T...|t — inline texture/icon references (e.g., raid markers)
    text = re.sub(r'\|T[^|]*\|t', '', text)
    # |H...|h — hyperlink data (item links, spell links, etc.)
    text = re.sub(r'\|H[^|]*\|h', '', text)
    text = re.sub(r'\|h', '', text)
    return text

def is_ooc(msg):
    """Detect out-of-character messages, which RPers conventionally wrap
    in parentheses or square brackets. We track nesting depth rather than
    just checking the first and last characters, because IC dialogue can
    contain parenthetical asides — we only want to exclude messages that
    are entirely OOC.
    """
    stripped = msg.strip()

    if stripped.startswith('('):
        open_char, close_char = '(', ')'
    elif stripped.startswith('['):
        open_char, close_char = '[', ']'
    else:
        return False

    depth = 0
    for i, ch in enumerate(stripped):
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                # Same logic as before — if the bracket closes at the very
                # end, the whole message was OOC. Mid-string means IC text
                # with a bracketed aside, like a gesture or stage direction.
                return i == len(stripped) - 1
    return False


def clean_text(msg):
    """Clean a single message string."""
    msg = strip_color_codes(msg)
    msg = msg.strip()
    return msg


def format_conversation(entries, convo_filter=None, latency=0):
    """Group consecutive same-speaker messages and format as prose.

    The latency parameter controls how many seconds apart two consecutive
    messages from the same speaker can be while still being merged into a
    single paragraph. WoW splits pasted text into multiple whispers, and
    under normal conditions they all share the same epoch-second timestamp.
    With server or network latency, fragments from a single paste can land
    across 2-3 different seconds. Setting latency to 2 or 3 accounts for
    this without merging intentionally separate paragraphs.

    The grouping is chain-based: each message is compared to the one
    immediately before it, not to the first message in the group. This
    means a long paste whose fragments trickle in over several seconds
    still gets reassembled correctly, as long as no single gap between
    consecutive fragments exceeds the threshold.
    """
    entries.sort(key=lambda e: e.get('time', 0))

    if convo_filter:
        entries = [e for e in entries if e.get('convo', '').lower() == convo_filter.lower()]

    cleaned = []
    for entry in entries:
        msg = clean_text(entry.get('msg', ''))
        if not msg or is_ooc(msg):
            continue
        entry = dict(entry)
        entry['msg'] = msg
        cleaned.append(entry)

    if not cleaned:
        return ''

    # First pass: group by speaker turn. A "turn" is an unbroken run of
    # messages with the same inbound direction — i.e., one person talking
    # before the other responds.
    speaker_groups = []
    current = [cleaned[0]]
    for entry in cleaned[1:]:
        if entry.get('inbound') == current[0].get('inbound'):
            current.append(entry)
        else:
            speaker_groups.append(current)
            current = [entry]
    speaker_groups.append(current)

    # Second pass: within each turn, sub-group by timestamp proximity.
    # WoW splits a pasted paragraph into multiple whispers that all land
    # on the same epoch second (or within a few seconds under latency),
    # so close timestamps mean "this was one paste." Larger gaps within
    # the same turn mean the player sent separate paragraphs — those get
    # a blank line between them, preserving the original paragraph
    # structure.
    turn_texts = []
    for group in speaker_groups:
        timestamp_groups = []
        current_ts = [group[0]]
        for entry in group[1:]:
            prev_time = current_ts[-1].get('time', 0)
            this_time = entry.get('time', 0)
            if abs(this_time - prev_time) <= latency:
                current_ts.append(entry)
            else:
                timestamp_groups.append(current_ts)
                current_ts = [entry]
        timestamp_groups.append(current_ts)

        paragraphs = []
        for ts_group in timestamp_groups:
            combined = ' '.join(e['msg'] for e in ts_group)
            # Trailing spaces on fragments and re-joining can produce doubles
            combined = re.sub(r' {2,}', ' ', combined)
            combined = combined.strip()
            if combined:
                paragraphs.append(combined)

        if paragraphs:
            turn_texts.append('\n\n'.join(paragraphs))

    # Horizontal rules between turns — reads like scene prose where you
    # can tell the "camera" has shifted to another character.
    return '\n\n---\n\n'.join(turn_texts)


def find_input_file():
    """Find the most recent input* file in the script's directory.

    This lets you just drop your exported Lua beside the script, name it
    something like input.lua or input_2024-12-01.txt, and run the script
    with no arguments.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = glob.glob(os.path.join(script_dir, 'input*'))
    candidates = [f for f in candidates if os.path.isfile(f)]
    if not candidates:
        return None
    # Most recently modified wins, so you can keep old inputs around
    # without worrying about which one gets picked.
    candidates.sort(key=lambda f: os.path.getmtime(f))
    return candidates[-1]


def main():
    parser = argparse.ArgumentParser(description='Clean up WoW whisper RP logs into readable prose.')
    parser.add_argument('input', nargs='?', default=None,
                        help='Input file (default: auto-detect most recent input* in script dir)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output file (default: output.txt in auto mode, stdout otherwise)')
    parser.add_argument('-c', '--convo', default=None,
                        help='Filter to a specific conversation partner name')
    parser.add_argument('-l', '--latency', type=int, default=0,
                        help='Max seconds between consecutive messages to still merge them '
                             'as one paragraph (default: 0, meaning exact timestamp match only)')
    args = parser.parse_args()

    auto_mode = False

    if args.input is None:
        # If stdin is a pipe or redirect, read from it. If it's a terminal,
        # the user probably just double-clicked or ran the script bare, so
        # fall back to auto-detection.
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            auto_mode = True
            input_file = find_input_file()
            if input_file is None:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                print(f"Error: No input* file found in {script_dir}", file=sys.stderr)
                sys.exit(1)
            print(f"Reading from: {input_file}", file=sys.stderr)
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()

    entries = parse_entries(text)

    if not entries:
        print("Warning: No valid entries found in input.", file=sys.stderr)

    result = format_conversation(entries, convo_filter=args.convo, latency=args.latency)

    # In auto mode, default to output.txt so the user doesn't need to
    # touch the terminal at all. In explicit mode, default to stdout
    # so it plays nicely with pipes and redirects.
    output_path = args.output
    if output_path is None and auto_mode:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output.txt')

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
            f.write('\n')
        print(f"Wrote {len(result)} characters to {output_path}", file=sys.stderr)
    else:
        print(result)


if __name__ == '__main__':
    main()
