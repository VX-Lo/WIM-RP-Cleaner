# WoW RP Log Cleaner

A Python script that converts WIM logs into clean, readable prose — ideal for archiving roleplay scenes.

You should ask your roleplaying partner first before you archive things in a place where anyone else might possibly see them, even if it's unlikely.


## Features

- Concatenates split messages with matching timestamps into a single paragraph
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
python clean-rp.py this-rp-file -o scene.txt

# Filter to a specific conversation
python clean-rp.py RP.lua --convo Jaina

# Pipe from stdin
cat my_log.lua | python clean-rp.py
```

## Input Format

The script expects Lua table entries as saved by WoW whisper-logging addons:

```lua
{
["type"] = 1,
["time"] = 1632642069,
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

Python 3.6+, probably. No external dependencies.
