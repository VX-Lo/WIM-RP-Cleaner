# WoW RP Log Cleaner

A Python script that converts WIM logs into clean, readable prose — ideal for archiving roleplay scenes.

You should ask your roleplaying partner first before you archive things in a place where anyone else might possibly see them, even if it's unlikely. Don't assume consent.


## Features

- Reassembles fragmented messages within a configurable time window (default: same timestamp)
- Separates paragraphs from the same speaker by blank lines
- Separates different speakers with `---` dividers
- Strips WoW color codes (`|cffRRGGBB`, `|r`, etc.)
- Skips out-of-character messages wrapped in parentheses
- Handles escaped characters (e.g. `\"` in dialogue)
- Auto-detects the most recent `input*` file in the script directory

## Usage

```bash
# Auto mode: reads most recent input* file, writes to output.txt
python clean-rp.py

# Specify input file
python clean-rp.py my_log.lua

# Specify input and output
python clean-rp.py my_log.lua -o scene.txt

# Filter to a specific conversation
python clean-rp.py RP.lua --convo Jaina

# Pipe from stdin
cat my_log.lua | python clean-rp.py

# Merge messages sent within 2 seconds of each other (useful for high-latency connections)
python clean-rp.py my_log.lua -l 2
```

Use `-l` or `--latency` to set the maximum gap in seconds the script will tolerate between consecutive fragments before treating them as separate paragraphs. Defaults to `0`, meaning only messages with identical timestamps are merged.


## Input Format

The script expects Lua table entries as saved by WIM:

```lua
{
["type"] = 1,
["time"] = 420133769,
["from"] = "Me",
["msg"] = "This message is super in-character, and it's one paragraph. ",
["inbound"] = false,
["convo"] = "Someone Else",
},
```


## Output Format

```
This is one paragraph from a speaker.

This is a second paragraph from the same speaker, sent a few seconds later.

---

And now the other speaker's turn.
```

## Requirements

Python 3.6+. No external dependencies.
