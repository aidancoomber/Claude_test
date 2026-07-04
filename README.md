# Claude Dash 🟧

A geometry-dash / Chrome-dino style runner built in pure Python (tkinter — no
libraries to install), starring a small orange square with places to be.

Built from scratch as my first real project, pair-programming with Claude —
every line explained before it was written.

## Play in your browser

**[▶ Play it live](https://aidancoomber.github.io/Claude_test/)** — or open `index.html` locally.

Works on phones too: tap to jump.

## Play the Python original

```
python3 claude_dash.py
```

- **Space** — jump
- **R** — retry after a wipeout
- **Escape** — quit

## Features

- Real jump physics (gravity + velocity) with a 29-frame airtime that every
  obstacle gap is mathematically derived from — the game can never deal you
  an impossible jump
- 10+ obstacle patterns that unlock as your score climbs: doubles, triples,
  ceiling spikes, and seven ledge variants that force you to *read* the
  pattern and pick a route — over, under, jump off the end, or drop off it
- Solid platforms you can land on (and bonk your head on — no jumping
  through)
- Day/night theme flip every 2000 points, dino-style
- Persistent high score saved between sessions

## Ideas for v2

- Damage instead of instant death: hits break pieces off the character and
  change how it moves
