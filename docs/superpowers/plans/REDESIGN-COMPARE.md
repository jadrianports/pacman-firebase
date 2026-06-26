# Redesign Comparison Workflow

Both visual branches fork from `redesign/base` and are checked out as sibling
worktrees so they can run side by side.

## Create the worktrees (after the two branch plans are executed)

```bash
git worktree add ../pacman-brand-match redesign/brand-match
git worktree add ../pacman-bold-reinvention redesign/bold-reinvention
```

Each worktree needs its own venv (deps differ — pygame_gui on both; zengl on Bold):

```bash
# in each worktree dir
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Run both at once

Open two terminals:

```bash
# terminal 1
cd ../pacman-brand-match && .venv/Scripts/python.exe main.py
# terminal 2
cd ../pacman-bold-reinvention && .venv/Scripts/python.exe main.py
```

## Generate the combined contact sheet

```bash
# from each worktree
SDL_VIDEODRIVER=dummy .venv/Scripts/python.exe tools/contact_sheet.py --label brand-match
SDL_VIDEODRIVER=dummy .venv/Scripts/python.exe tools/contact_sheet.py --label bold-reinvention
```

Then montage `brand-match.png` + `bold-reinvention.png` into a single before/after.

## Ship the winner

```bash
git switch main
git merge --no-ff redesign/<winner>
git worktree remove ../pacman-brand-match
git worktree remove ../pacman-bold-reinvention
git branch -D redesign/<loser>
```
