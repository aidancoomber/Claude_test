# Claude Dash — a tiny geometry-dash / dino-run style game
#
# FUTURE IDEAS (v2):
#   - Damage instead of instant death: hitting a spike breaks a piece off Claude,
#     and the broken shape changes how it moves. E.g. a 4-legged Claude that loses
#     a leg jumps lower / needs more energy / moves slower; a circle-Claude that
#     takes damage gets a wobblier, more random movement pattern.

import tkinter as tk
import random

# 1. Make the window (the "container")
root = tk.Tk()
root.title("Claude Dash")

# 2. Make the canvas (the "world" we draw on) and put it in the window
canvas = tk.Canvas(root, width=800, height=400, bg="white")
canvas.pack()

# 3. Draw the ground (a horizontal line across the world)
GROUND_Y = 320
ground = canvas.create_line(0, GROUND_Y, 800, GROUND_Y, fill="black", width=3)

# Stars scattered across the sky (drawn as * characters, various sizes)
stars = []
for _ in range(22):
    sx = random.randint(10, 790)
    sy = random.randint(15, 210)
    size = random.choice([10, 14, 18])
    stars.append(canvas.create_text(sx, sy, text="*", font=("Arial", size)))

# 4. Draw the player (Claude) — an orange square sitting on the ground
player = canvas.create_rectangle(100, 290, 130, 320, fill="#DA7756", outline="")

# 5. Physics: our two magic numbers
GRAVITY = 1            # constant downward pull, added every tick
JUMP_VELOCITY = -15    # the upward shove when we jump (negative = up)
velocity = 0           # how fast the player is moving right now

# One full jump lasts this many frames (14 up, the peak, 14 down).
# This is the yardstick for ALL obstacle spacing: a jump carries you
# AIR_FRAMES * speed pixels, so no gap may ever demand less than that.
AIR_FRAMES = 2 * abs(JUMP_VELOCITY) - 1    # = 29

# --- Obstacles -------------------------------------------------------------
SPIKE_SIZE = 30
SPIKE_COLOR = "#e0455f"
BASE_SPEED = 6         # starting speed (pixels/frame)
speed = BASE_SPEED     # current speed — grows the longer you survive

obstacles = []         # every live obstacle on screen lives in this list
spawn_timer = 60       # frames until the next obstacle appears

# --- Ledges (solid platforms — terrain, not death) --------------------------
LEDGE_Y = 240          # the ledge's top surface (jump peak reaches 215 — landable)
LEDGE_THICK = 12       # underside sits at 252, so headroom below is only 38px
LEDGE_LEN = 180
LEDGE_COLOR = "#8888a0"
ledges = []            # separate list: touching these must NOT end the game

# Each builder draws one shape and returns its canvas id
def ground_spike(x):
    # a triangle poking UP from the floor — jump over it
    return canvas.create_polygon(x, GROUND_Y, x + SPIKE_SIZE, GROUND_Y,
                                 x + SPIKE_SIZE / 2, GROUND_Y - SPIKE_SIZE,
                                 fill=SPIKE_COLOR, outline="")

def ceiling_spike(x):
    # a long triangle hanging DOWN from the sky — stay grounded, don't jump into it
    return canvas.create_polygon(x, 0, x + SPIKE_SIZE, 0,
                                 x + SPIKE_SIZE / 2, 240,
                                 fill=SPIKE_COLOR, outline="")

def make_ledge(x):
    # one helper instead of four copies — every ledge pattern starts here
    return canvas.create_rectangle(x, LEDGE_Y, x + LEDGE_LEN,
                                   LEDGE_Y + LEDGE_THICK,
                                   fill=LEDGE_COLOR, outline="")

# Pick a pattern and drop its shape(s) into the obstacle list.
# The menu of possible patterns GROWS as your score climbs, so navigation
# (not just raw speed) is what gets harder over time.
def spawn_obstacle():
    x = 820
    # Physics-aware spacing: one jump travels AIR_FRAMES * speed pixels,
    # so every "land between" gap is built FROM that number — the game can
    # never deal you a jump that isn't possible.
    jump_dist = AIR_FRAMES * speed
    gap = jump_dist + 60        # comfy landing zone between spikes
    tight = jump_dist + 30      # meaner, but still always clearable

    choices = ["single", "single"]          # early game: just lone spikes
    if score > 300:
        choices += ["double"]               # then doubles unlock
    if score > 500:
        choices += ["ledge"]                # then the high-road / low-road fork
    if score > 700:
        choices += ["ceiling"]              # then hanging spikes
    if score > 800:
        choices += ["ledge_block"]          # a ledge you must NOT ride
    if score > 1100:
        choices += ["ledge_forced"]         # a ledge you MUST ride
    if score > 1200:
        choices += ["triple", "ceiling"]    # then triples (and more ceilings)
    if score > 1300:
        choices += ["ledge_spring"]         # a wall only ledge-altitude clears
    if score > 1500:
        choices += ["ledge_leap"]           # ride it AND jump off the end
    if score > 1600:
        choices += ["ledge_dive"]           # ride it and DON'T jump off the end
    if score > 1800:
        choices += ["tight_double"]         # then a mean, narrow gap

    kind = random.choice(choices)
    if kind == "single":
        obstacles.append(ground_spike(x))
        width = SPIKE_SIZE
    elif kind == "double":
        # jump, land in the gap, jump again
        obstacles.append(ground_spike(x))
        obstacles.append(ground_spike(x + gap))
        width = gap + SPIKE_SIZE
    elif kind == "tight_double":
        obstacles.append(ground_spike(x))
        obstacles.append(ground_spike(x + tight))
        width = tight + SPIKE_SIZE
    elif kind == "triple":
        obstacles.append(ground_spike(x))
        obstacles.append(ground_spike(x + gap))
        obstacles.append(ground_spike(x + 2 * gap))
        width = 2 * gap + SPIKE_SIZE
    elif kind == "ceiling":
        obstacles.append(ceiling_spike(x))
        width = SPIKE_SIZE
    elif kind == "ledge":
        # the fork: jump ON TOP and sail over the spike, or duck UNDER —
        # but then the ledge blocks any early jump, so the spike is tight
        ledges.append(make_ledge(x))
        sx = x + LEDGE_LEN + 10 * speed    # ~10 frames to react down low
        obstacles.append(ground_spike(sx))
        width = (sx + SPIKE_SIZE) - x
    elif kind == "ledge_block":
        # a ceiling spike squats ON the ledge — riding it is death.
        # Read it coming and take the low road instead.
        ledges.append(make_ledge(x))
        obstacles.append(ceiling_spike(x + LEDGE_LEN / 2 - 15))
        sx = x + LEDGE_LEN + 10 * speed
        obstacles.append(ground_spike(sx))
        width = (sx + SPIKE_SIZE) - x
    elif kind == "ledge_forced":
        # a spike lurks UNDER the ledge — with 38px of headroom down there
        # it cannot be jumped, so the high road is the only road
        ledges.append(make_ledge(x))
        obstacles.append(ground_spike(x + LEDGE_LEN / 2 - 15))
        width = LEDGE_LEN
    elif kind == "ledge_leap":
        # a spike wall a short fall past the ledge's end: walk off and you
        # drop just short, onto it; jump off too early and you land on it.
        # Only a well-timed jump from the edge sails clear.
        ledges.append(make_ledge(x))
        wx = x + LEDGE_LEN + 10 * speed
        obstacles.append(ground_spike(wx))
        obstacles.append(ground_spike(wx + 30))
        width = (wx + 65) - x
    elif kind == "ledge_spring":
        # a 120px spike wall flush with the end — a ground jump stays high
        # for ~144px of travel but wall + body needs 150: the maths says
        # only the ledge's extra altitude gives enough hang time. Ride it.
        ledges.append(make_ledge(x))
        for i in range(4):
            obstacles.append(ground_spike(x + LEDGE_LEN + 5 + 30 * i))
        width = LEDGE_LEN + 125
    elif kind == "ledge_dive":
        # the mirror of ledge_leap: a ceiling spike waits past the end, so
        # jumping off is death — walk off, freefall under it, stay low,
        # then clear one last tight spike
        ledges.append(make_ledge(x))
        cx = x + LEDGE_LEN + 20 * speed    # far enough to land before it arrives
        obstacles.append(ceiling_spike(cx))
        sx = cx + 30 + 10 * speed          # the tight finale
        obstacles.append(ground_spike(sx))
        width = (sx + SPIKE_SIZE) - x
    return width               # tell the caller how much road we used up

# Game state
game_over = False
game_over_text = None
score = 0

# Load the saved high score from a file (if one exists yet)
HIGH_SCORE_FILE = "high_score.txt"
try:
    with open(HIGH_SCORE_FILE) as f:
        high_score = int(f.read())
except (FileNotFoundError, ValueError):
    high_score = 0     # no file yet, or it held something that isn't a number

# The score readout in the top-left corner
score_text = canvas.create_text(10, 10, anchor="nw", fill="black",
                                font=("Arial", 14),
                                text=f"Score: 0    High: {high_score}")

# Day / night themes (Chrome-dino style). Claude stays orange in both.
DAY   = {"bg": "white",   "ink": "black", "star": "#aaaaaa"}
NIGHT = {"bg": "#12122b", "ink": "white", "star": "#ffffff"}
night = False

def apply_theme(theme):
    canvas.config(bg=theme["bg"])
    canvas.itemconfig(ground, fill=theme["ink"])
    canvas.itemconfig(score_text, fill=theme["ink"])
    for s in stars:
        canvas.itemconfig(s, fill=theme["star"])

apply_theme(DAY)   # start in daytime

# Jump: only if we're standing on something — ground OR a ledge.
# The game loop re-proves `standing` every frame; jump just trusts it.
standing = True

def jump(event):
    global velocity
    if standing:
        velocity = JUMP_VELOCITY

# The game loop — the heartbeat
def game_loop():
    global velocity, score, speed, spawn_timer, night, standing

    # Score climbs every frame; speed climbs slowly and gently, then caps
    score += 1
    speed = min(BASE_SPEED + score // 600, 11)
    canvas.itemconfig(score_text, text=f"Score: {score}    High: {high_score}")

    # Day/night cycle — flip every 2000 points: rare enough to feel like a
    # milestone reward, dino-style, not a strobe light
    want_night = (score // 2000) % 2 == 1
    if want_night != night:
        night = want_night
        apply_theme(NIGHT if night else DAY)

    # Remember where we were BEFORE moving — ledge collisions need to know
    # which side we came from (falling onto the top vs rising into the bottom)
    prev_top = canvas.coords(player)[1]
    prev_bottom = prev_top + 30

    velocity += GRAVITY                 # rule 1: gravity nudges velocity
    canvas.move(player, 0, velocity)    # rule 2: velocity moves the square

    standing = False                    # assume airborne until proven otherwise

    # Don't fall through the floor
    bottom = canvas.coords(player)[3]
    if bottom > GROUND_Y:
        canvas.move(player, 0, GROUND_Y - bottom)   # snap back onto the ground
        velocity = 0
        standing = True

    # Spawn a new obstacle when the timer runs out; the gap shrinks as you score
    spawn_timer -= 1
    if spawn_timer <= 0:
        width = spawn_obstacle()
        # Wait until this pattern has fully passed the spawn point, PLUS one
        # full jump, PLUS a reaction window — so a landing spot always exists.
        breather = max(10, 22 - score // 400)      # reaction time shrinks slowly
        spawn_timer = width // speed + AIR_FRAMES + breather + random.randint(0, 20)

    # Ledges: solid terrain. Which side did we come from?
    for ledge in ledges[:]:
        canvas.move(ledge, -speed, 0)
        lx1, ly1, lx2, ly2 = canvas.coords(ledge)
        if lx2 < 0:                            # scrolled off — retire it
            canvas.delete(ledge)
            ledges.remove(ledge)
            continue
        px1, py1, px2, py2 = canvas.coords(player)
        if px1 < lx2 and lx1 < px2:            # only if we're over/under it
            if velocity >= 0 and prev_bottom <= ly1 and py2 >= ly1:
                canvas.move(player, 0, ly1 - py2)   # was above, falling: LAND on top
                velocity = 0
                standing = True
            elif velocity < 0 and prev_top >= ly2 and py1 < ly2:
                canvas.move(player, 0, ly2 - py1)   # was below, rising: BONK, no passing through
                velocity = 0

    # Move every obstacle left, delete ones that scroll off, check each for a hit
    px1, py1, px2, py2 = canvas.bbox(player)
    for obj in obstacles[:]:               # loop over a COPY so we can edit the real list
        canvas.move(obj, -speed, 0)
        ox1, oy1, ox2, oy2 = canvas.bbox(obj)
        if ox2 < 0:                        # fully off the left edge — retire it
            canvas.delete(obj)
            obstacles.remove(obj)
            continue
        # same overlap-in-both-x-and-y test, now against this obstacle
        if px1 < ox2 and ox1 < px2 and py1 < oy2 and oy1 < py2:
            end_game()
            return                         # stop the loop — we're dead

    root.after(20, game_loop)           # do it all again in 20ms (~50x/second)

# Freeze the game and show the Game Over message
def end_game():
    global game_over, game_over_text, high_score
    game_over = True

    # Beat the record? Save it to the file so it survives after we quit.
    if score > high_score:
        high_score = score
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(high_score))

    ink = NIGHT["ink"] if night else DAY["ink"]
    game_over_text = canvas.create_text(400, 160,
                                        text=f"GAME OVER — score {score} — press R to retry",
                                        fill=ink, font=("Arial", 20))

# Reset everything and start again
def restart(event):
    global game_over, velocity, score, speed, spawn_timer, night, standing
    if not game_over:
        return
    game_over = False
    velocity = 0
    standing = True
    score = 0
    speed = BASE_SPEED
    spawn_timer = 60
    night = False
    apply_theme(DAY)
    canvas.delete(game_over_text)
    canvas.coords(player, 100, 290, 130, 320)   # put Claude back home
    for obj in obstacles:                        # wipe every leftover obstacle
        canvas.delete(obj)
    obstacles.clear()
    for ledge in ledges:                         # and every leftover ledge
        canvas.delete(ledge)
    ledges.clear()
    game_loop()                                  # restart the heartbeat

# 6. Bind the keys
root.bind("<space>", jump)
root.bind("<r>", restart)
root.bind("<Escape>", lambda event: root.destroy())

# 7. Start the heartbeat
game_loop()

# 4. Keep the window open and listening
root.mainloop()
