# How To Use WIM RP Log Cleaner

If you are not used to GitHub, Python, or command lines, that is okay. This guide walks you through the basics without assuming technical experience.

## What you need

You need:

- this project folder
- Python 3
- your `WIM.lua` file

## 1. Download the tool

If the project is on GitHub:

1. Open the project page
2. Click the green **Code** button
3. Click **Download ZIP**
4. Unzip it somewhere easy to find

You should end up with a folder containing files like:

- `clean-rp.py`
- `README.md`
- `HOW_TO_USE.md`

## 2. Install Python 3

### Windows

Download Python 3 from the official Python website and run the installer.

If you see a checkbox for **Add Python to PATH**, turn it on before installing.

### Mac

Install Python 3 from the official Python website.

### Linux

Many Linux systems already have Python 3. Check with:

```bash
python3 --version
```

If needed, install it with your package manager.

Examples:

```bash
sudo apt install python3
```

```bash
sudo dnf install python3
```

```bash
sudo pacman -S python
```

## 3. Find your WIM file

Inside your World of Warcraft folder, WIM usually stores its saved data here:

```text
WTF/Account/<account>/SavedVariables/WIM.lua
```

Copy `WIM.lua` somewhere safe before doing anything else.

It is best to work on a **copy**, not the original.

### Optional but recommended: trim the copy

If you have a lot of old conversation history, `WIM.lua` can get very large.

If you want, make a second copy and trim out old or unrelated sections before running the script. This can make the file easier to work with.

If you are not comfortable editing it, you can skip this and try the full file first.

## 4. Put the copied file next to the script

Put your copied `WIM.lua` file in the same folder as `clean-rp.py`.

For the easiest possible use, rename it to:

```text
input.lua
```

That lets the script find it automatically.

## 5. Run the script

Use the command for your operating system.

### Windows

Open the folder with `clean-rp.py`, click the address bar, type:

```text
cmd
```

and press **Enter**.

Then run:

```bash
python clean-rp.py
```

If that does not work, try:

```bash
py clean-rp.py
```

### Mac

Open Terminal, change into the folder containing `clean-rp.py`, then run:

```bash
python3 clean-rp.py
```

### Linux

Open a terminal, change into the folder containing `clean-rp.py`, then run:

```bash
python3 clean-rp.py
```

## 6. Find your cleaned file

If everything worked, the script will create:

```text
output.txt
```

in the same folder.

That is your cleaned RP log.

## Useful examples

### Use a specific file

```bash
python clean-rp.py my_log.lua
```

Mac/Linux users may need:

```bash
python3 clean-rp.py my_log.lua
```

### Save to a specific output filename

```bash
python clean-rp.py my_log.lua -o scene.txt
```

### Filter to one conversation

```bash
python clean-rp.py my_log.lua --convo Jaina
```

### Merge messages sent a few seconds apart

```bash
python clean-rp.py my_log.lua -l 2
```

This tells the script to merge consecutive fragments that arrived within 2 seconds of each other.

## Troubleshooting

### “python is not recognized” on Windows

Try:

```bash
py clean-rp.py
```

If that still does not work, Python may not be installed correctly.

### “python3: command not found” on Mac or Linux

Python 3 may not be installed yet.

### “No input* file found”

The script could not find a file beginning with `input`.

Either:

- rename your copied file to `input.lua`, or
- give the filename directly:

```bash
python clean-rp.py my_log.lua
```

### “It opened and closed immediately”

Do not double-click the Python file. Open Command Prompt or Terminal first, then run it there.

## Privacy and consent

Please ask your RP partner before archiving, posting, or sharing logs anywhere another person could see them.
