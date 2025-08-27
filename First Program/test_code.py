# Submarine Arena — Unique Features Edition (Bullet Frenzy Template)
# Implements: Stealth, Power-ups, Minimap, Boss, Currents, Story Timer, Bubble Trail
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random

# --------------- Window & Arena -----------------
window_width, window_height = 1000, 700
arena_size = 18.0  # half-length

# --------------- Player/Submarine ----------------
sub_pos = [0.0, 0.0, -5.0]
sub_vel = [0.0, 0.0, 0.0]
sub_angle = 0.0
base_speed = 7.0     # units/sec
stealth = False
hp_max = 100
hp = 100
shield_charges = 0

# --------------- Torpedoes -----------------------
torpedoes = []  # each: [x,y,z, vx,vy,vz]
torpedo_speed = 25.0  # units/sec
fire_cooldown_ms = 300
boost_active = False
boost_ends_at = 0
last_fire_time = 0

# --------------- Obstacles & Boss ----------------
obstacles = []  # each: dict(x,y,z, vx,vy,vz, r, alive)
num_obstacles = 14
detect_radius = 9.0  # when not stealth, enemies drift toward player
obstacle_speed = 3.0 # base drift speed

boss = None  # dict(x,y,z, vx,vy,vz, r, hp, alive, spawnedMinute)
boss_base_hp = 30
boss_reward = 200
boss_speed = 2.0

# --------------- Power-ups -----------------------
powerups = []  # each: dict(x,y,z, type, ttl_ms)
powerup_spawn_interval_ms = 12000
last_powerup_spawn = 0
POWER_HEALTH, POWER_BOOST, POWER_SHIELD = 0, 1, 2

# --------------- Currents (Wind Zones) -----------
# Each zone: (xmin, xmax, ymin, ymax, zmin, zmax, ax, ay, az)
current_zones = [
    (-12, -2,  -12, 12,  -18, 18,   2.0, 0.0,  0.0),  # gentle push +X
    (  2,  12, -12, 12,  -18, 18,  -2.0, 0.0,  0.0),  # gentle push -X
    (-18, 18,   8,  18,  -18, 18,   0.0,-2.0,  0.0),  # push downwards at top layer
]

# --------------- Story / Escape Mode -------------
story_mode = True
story_total_ms = 180000  # 3 minutes
story_start_ms = 0
story_goal = [12.0, 10.0, 12.0]  # reach this coordinate
story_goal_radius = 2.0
won = False
game_over = False

# --------------- Bubbles (Particle System) -------
bubbles = []  # each: dict(x,y,z, vx,vy,vz, life_ms)
bubble_spawn_accum = 0.0  # for timed emission

# --------------- Input ---------------------------
keys = {}

# --------------- Utility -------------------------
def now_ms():
    return glutGet(GLUT_ELAPSED_TIME)

def clamp(v, a, b):
    return max(a, min(b, v))

def length3(v):
    return math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])

def norm3(v):
    L = length3(v)
    if L < 1e-6: return [0.0,0.0,0.0]
    return [v[0]/L, v[1]/L, v[2]/L]

def rand_pos_inside():
    return [
        random.uniform(-arena_size+1.5, arena_size-1.5),
        random.uniform(-arena_size+1.5, arena_size-1.5),
        random.uniform(-arena_size+1.5, arena_size-1.5),
    ]

# --------------- Rendering Helpers ----------------
def draw_quad_cube(cx, cy, cz, sx, sy, sz):
    glBegin(GL_QUADS)
    # Front (+Z)
    glVertex3f(cx-sx, cy-sy, cz+sz); glVertex3f(cx+sx, cy-sy, cz+sz)
    glVertex3f(cx+sx, cy+sy, cz+sz); glVertex3f(cx-sx, cy+sy, cz+sz)
    # Back (-Z)
    glVertex3f(cx-sx, cy-sy, cz-sz); glVertex3f(cx-sx, cy+sy, cz-sz)
    glVertex3f(cx+sx, cy+sy, cz-sz); glVertex3f(cx+sx, cy-sy, cz-sz)
    # Left (-X)
    glVertex3f(cx-sx, cy-sy, cz-sz); glVertex3f(cx-sx, cy-sy, cz+sz)
    glVertex3f(cx-sx, cy+sy, cz+sz); glVertex3f(cx-sx, cy+sy, cz-sz)
    # Right (+X)
    glVertex3f(cx+sx, cy-sy, cz-sz); glVertex3f(cx+sx, cy+sy, cz-sz)
    glVertex3f(cx+sx, cy+sy, cz+sz); glVertex3f(cx+sx, cy-sy, cz+sz)
    # Top (+Y)
    glVertex3f(cx-sx, cy+sy, cz-sz); glVertex3f(cx-sx, cy+sy, cz+sz)
    glVertex3f(cx+sx, cy+sy, cz+sz); glVertex3f(cx+sx, cy+sy, cz-sz)
    # Bottom (-Y)
    glVertex3f(cx-sx, cy-sy, cz-sz); glVertex3f(cx+sx, cy-sy, cz-sz)
    glVertex3f(cx+sx, cy-sy, cz+sz); glVertex3f(cx-sx, cy-sy, cz+sz)
    glEnd()

def draw_cylinder_quads(cx, cy, cz, length=1.0, radius=0.15, slices=14):
    glBegin(GL_QUADS)
    for i in range(slices):
        t1 = (2*math.pi*i)/slices
        t2 = (2*math.pi*(i+1))/slices
        x1, y1 = radius*math.cos(t1), radius*math.sin(t1)
        x2, y2 = radius*math.cos(t2), radius*math.sin(t2)
        # oriented along -Z
        glVertex3f(cx+x1, cy+y1, cz)
        glVertex3f(cx+x1, cy+y1, cz-length)
        glVertex3f(cx+x2, cy+y2, cz-length)
        glVertex3f(cx+x2, cy+y2, cz)
    glEnd()

def draw_arena():
    glColor3f(1,1,1)
    glBegin(GL_LINES)
    # bottom square
    glVertex3f(-arena_size,-arena_size,-arena_size); glVertex3f( arena_size,-arena_size,-arena_size)
    glVertex3f( arena_size,-arena_size,-arena_size); glVertex3f( arena_size,-arena_size, arena_size)
    glVertex3f( arena_size,-arena_size, arena_size); glVertex3f(-arena_size,-arena_size, arena_size)
    glVertex3f(-arena_size,-arena_size, arena_size); glVertex3f(-arena_size,-arena_size,-arena_size)
    # top square
    glVertex3f(-arena_size, arena_size,-arena_size); glVertex3f( arena_size, arena_size,-arena_size)
    glVertex3f( arena_size, arena_size,-arena_size); glVertex3f( arena_size, arena_size, arena_size)
    glVertex3f( arena_size, arena_size, arena_size); glVertex3f(-arena_size, arena_size, arena_size)
    glVertex3f(-arena_size, arena_size, arena_size); glVertex3f(-arena_size, arena_size,-arena_size)
    # verticals
    glVertex3f(-arena_size,-arena_size,-arena_size); glVertex3f(-arena_size, arena_size,-arena_size)
    glVertex3f( arena_size,-arena_size,-arena_size); glVertex3f( arena_size, arena_size,-arena_size)
    glVertex3f( arena_size,-arena_size, arena_size); glVertex3f( arena_size, arena_size, arena_size)
    glVertex3f(-arena_size,-arena_size, arena_size); glVertex3f(-arena_size, arena_size, arena_size)
    glEnd()

def draw_submarine():
    glPushMatrix()
    glTranslatef(*sub_pos)
    glRotatef(sub_angle, 0,1,0)
    # Stealth visual: fade alpha (simulate by color dim)
    if stealth:
        glColor3f(0.4, 0.4, 0.8)
    else:
        glColor3f(0.0, 0.3, 1.0)
    draw_quad_cube(0,0,0, 1.1,0.55,3.2)          # body
    glColor3f(0.6,0.6,0.6); draw_quad_cube(0,0.75,0, 0.12,0.75,0.12)  # periscope
    glColor3f(0.0,0.0,0.5)
    draw_quad_cube(-1.35,0,0, 0.22,0.06,0.55)   # left fin
    draw_quad_cube( 1.35,0,0, 0.22,0.06,0.55)   # right fin
    draw_quad_cube(0,-0.55,-2.7, 0.33,0.06,0.33) # tail
    glPopMatrix()

def draw_torpedoes():
    glColor3f(1,0.25,0.25)
    for t in torpedoes:
        draw_cylinder_quads(t[0],t[1],t[2], length=0.9, radius=0.11, slices=12)

def draw_obstacles():
    glColor3f(0.0, 0.9, 0.0)
    for o in obstacles:
        if not o["alive"]: continue
        draw_quad_cube(o["x"],o["y"],o["z"], 1.0,1.0,1.0)

def draw_boss():
    global boss
    if boss and boss["alive"]:
        # boss is a big sea monster "chunk" – larger cube
        glColor3f(0.85, 0.1, 0.1)
        draw_quad_cube(boss["x"], boss["y"], boss["z"], 2.2, 1.7, 2.2)

def draw_currents_debug():
    # optional: visualize zones as wire boxes (dim)
    glColor3f(0.5, 0.5, 1.0)
    glBegin(GL_LINES)
    for (xmin,xmax,ymin,ymax,zmin,zmax,ax,ay,az) in current_zones:
        # draw rectangle edges (just a few lines for hint)
        glVertex3f(xmin,ymin,zmin); glVertex3f(xmax,ymin,zmin)
        glVertex3f(xmax,ymin,zmin); glVertex3f(xmax,ymax,zmin)
        glVertex3f(xmax,ymax,zmin); glVertex3f(xmin,ymax,zmin)
        glVertex3f(xmin,ymax,zmin); glVertex3f(xmin,ymin,zmin)
        glVertex3f(xmin,ymin,zmax); glVertex3f(xmax,ymin,zmax)
        glVertex3f(xmax,ymin,zmax); glVertex3f(xmax,ymax,zmax)
        glVertex3f(xmax,ymax,zmax); glVertex3f(xmin,ymax,zmax)
        glVertex3f(xmin,ymax,zmax); glVertex3f(xmin,ymin,zmax)
    glEnd()

def draw_powerups():
    for p in powerups:
        if p["type"] == POWER_HEALTH: glColor3f(0.2,1.0,0.2)
        elif p["type"] == POWER_BOOST: glColor3f(1.0,1.0,0.2)
        else: glColor3f(0.2,1.0,1.0)
        draw_quad_cube(p["x"],p["y"],p["z"], 0.6,0.6,0.6)

def draw_bubbles():
    glColor3f(0.8,0.9,1.0)
    glBegin(GL_POINTS)
    for b in bubbles:
        glVertex3f(b["x"], b["y"], b["z"])
    glEnd()

# --------------- Minimap (Top-Right HUD) ----------
def draw_minimap():
    # Ortho HUD
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    # Minimap square
    map_size = 160
    margin = 16
    x0 = window_width - map_size - margin
    y0 = window_height - map_size - margin

    # Frame
    glColor3f(1,1,1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0); glVertex2f(x0+map_size, y0)
    glVertex2f(x0+map_size, y0+map_size); glVertex2f(x0, y0+map_size)
    glEnd()

    # Map submarine center as origin; scale arena -> square
    def world_to_map(wx, wy, wz):
        # relative to sub
        rx, ry, rz = wx - sub_pos[0], wy - sub_pos[1], wz - sub_pos[2]
        # use X/Z plane; ignore Y
        scale = (map_size/2.2) / arena_size
        mx = x0 + map_size/2 + rx*scale
        my = y0 + map_size/2 + rz*scale   # use Z for vertical on minimap
        return mx, my

    # Sub marker
    sx, sy = world_to_map(sub_pos[0], sub_pos[1], sub_pos[2])
    glColor3f(0.5,0.8,1.0)
    glBegin(GL_QUADS)
    glVertex2f(sx-3, sy-3); glVertex2f(sx+3, sy-3); glVertex2f(sx+3, sy+3); glVertex2f(sx-3, sy+3)
    glEnd()

    # Obstacles
    glColor3f(0.2,1.0,0.2)
    glBegin(GL_POINTS)
    for o in obstacles:
        if not o["alive"]: continue
        mx,my = world_to_map(o["x"],o["y"],o["z"])
        glVertex2f(mx,my)
    glEnd()

    # Torpedoes
    glColor3f(1.0,0.5,0.5)
    glBegin(GL_POINTS)
    for t in torpedoes:
        mx,my = world_to_map(t[0],t[1],t[2])
        glVertex2f(mx,my)
    glEnd()

    # Boss
    if boss and boss["alive"]:
        glColor3f(1.0,0.2,0.2)
        mx,my = world_to_map(boss["x"],boss["y"],boss["z"])
        glBegin(GL_QUADS)
        glVertex2f(mx-4,my-4); glVertex2f(mx+4,my-4); glVertex2f(mx+4,my+4); glVertex2f(mx-4,my+4)
        glEnd()

    glMatrixMode(GL_MODELVIEW); glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --------------- HUD / Text -----------------------
def draw_text(x,y,text):
    glRasterPos2f(x,y)
    for c in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

def draw_hud():
    # Ortho
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    # Basic HUD
    glColor3f(1,1,1)
    draw_text(10, window_height-24, f"HP: {hp}/{hp_max}   Shield: {shield_charges}   Score: {score}")
    if stealth:
        draw_text(10, window_height-48, "[STEALTH] speed halved, undetected")
    if boost_active:
        remaining = max(0, (boost_ends_at - now_ms())//1000)
        draw_text(10, window_height-72, f"[TORPEDO BOOST] {remaining}s")

    # Story timer
    if story_mode and not won and not game_over:
        remaining_ms = max(0, story_total_ms - (now_ms() - story_start_ms))
        draw_text(10, window_height-96, f"Escape Timer: {remaining_ms//1000}s  Goal: {story_goal}")

    # Win/Lose
    if won:
        draw_text(window_width/2 - 60, window_height/2, "MISSION COMPLETE!")
    if game_over and not won:
        draw_text(window_width/2 - 40, window_height/2, "GAME OVER")

    glMatrixMode(GL_MODELVIEW); glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --------------- Spawning -------------------------
def spawn_obstacles():
    obstacles.clear()
    for _ in range(num_obstacles):
        x,y,z = rand_pos_inside()
        obstacles.append({
            "x": x, "y": y, "z": z,
            "vx": random.uniform(-0.5,0.5),
            "vy": random.uniform(-0.5,0.5),
            "vz": random.uniform(-0.5,0.5),
            "r": 1.0,
            "alive": True
        })

def spawn_powerup():
    t = random.choice([POWER_HEALTH, POWER_BOOST, POWER_SHIELD])
    x,y,z = rand_pos_inside()
    powerups.append({"x":x,"y":y,"z":z,"type":t,"ttl":22000})  # 22s lifetime

def ensure_boss():
    # Spawn every 5th minute mark if not already spawned for that minute
    global boss
    minutes = now_ms() // 60000
    if minutes == 0: return
    if minutes % 5 == 0:
        if (not boss) or (boss and (not boss["alive"] or boss["spawnedMinute"] != minutes)):
            # spawn boss at a far corner
            bx, by, bz = (arena_size-2, 0.0, arena_size-2)
            boss = {"x":bx,"y":by,"z":bz,"vx":0,"vy":0,"vz":0,"r":2.2,"hp":boss_base_hp,"alive":True,"spawnedMinute":minutes}

# --------------- Physics & Logic ------------------
def apply_currents(dt):
    # dt in seconds
    for (xmin,xmax,ymin,ymax,zmin,zmax,ax,ay,az) in current_zones:
        if xmin <= sub_pos[0] <= xmax and ymin <= sub_pos[1] <= ymax and zmin <= sub_pos[2] <= zmax:
            sub_vel[0] += ax*dt
            sub_vel[1] += ay*dt
            sub_vel[2] += az*dt

def move_player(dt):
    # Input-driven velocity
    speed = base_speed * (0.5 if stealth else 1.0)
    vx = vy = vz = 0.0
    if keys.get(b'w', False): vy += 1
    if keys.get(b's', False): vy -= 1
    if keys.get(b'd', False): vx += 1
    if keys.get(b'a', False): vx -= 1
    if keys.get(b'e', False): sub_angle -= 90*dt
    if keys.get(b'q', False): sub_angle += 90*dt

    mv = [vx, vy, 0.0]
    n = norm3(mv)
    sub_vel[0] += n[0] * speed * dt
    sub_vel[1] += n[1] * speed * dt
    # No forward/back along z here; submarine aims torpedoes with rotation & can drift in currents.

    # Currents
    apply_currents(dt)

    # Damping
    sub_vel[0] *= (1.0 - 2.2*dt)
    sub_vel[1] *= (1.0 - 2.2*dt)
    sub_vel[2] *= (1.0 - 2.2*dt)

    # Integrate
    sub_pos[0] += sub_vel[0]*dt
    sub_pos[1] += sub_vel[1]*dt
    sub_pos[2] += sub_vel[2]*dt

    # Clamp to arena
    sub_pos[0] = clamp(sub_pos[0], -arena_size+1.3, arena_size-1.3)
    sub_pos[1] = clamp(sub_pos[1], -arena_size+1.3, arena_size-1.3)
    sub_pos[2] = clamp(sub_pos[2], -arena_size+1.3, arena_size-1.3)

def update_obstacles(dt):
    global game_over, hp, shield_charges
    for o in obstacles:
        if not o["alive"]: continue

        # If sub not in stealth and within detect radius, move toward sub
        to_sub = [sub_pos[0]-o["x"], sub_pos[1]-o["y"], sub_pos[2]-o["z"]]
        dist = length3(to_sub)
        if (not stealth) and dist < detect_radius:
            d = norm3(to_sub)
            o["vx"] += d[0]*obstacle_speed*dt
            o["vy"] += d[1]*obstacle_speed*dt
            o["vz"] += d[2]*obstacle_speed*dt
        else:
            # gentle drift
            o["vx"] *= (1.0 - 1.2*dt)
            o["vy"] *= (1.0 - 1.2*dt)
            o["vz"] *= (1.0 - 1.2*dt)

        # integrate
        o["x"] += o["vx"]*dt
        o["y"] += o["vy"]*dt
        o["z"] += o["vz"]*dt

        # keep in arena
        o["x"] = clamp(o["x"], -arena_size+1.0, arena_size-1.0)
        o["y"] = clamp(o["y"], -arena_size+1.0, arena_size-1.0)
        o["z"] = clamp(o["z"], -arena_size+1.0, arena_size-1.0)

        # Collision with sub
        if abs(o["x"]-sub_pos[0])<1.2 and abs(o["y"]-sub_pos[1])<1.2 and abs(o["z"]-sub_pos[2])<1.2:
            o["alive"] = False
            if shield_charges > 0:
                shield_charges -= 1
            else:
                hp -= 25
                if hp <= 0:
                    game_over = True

def update_boss(dt):
    global boss, game_over, hp, shield_charges
    if not (boss and boss["alive"]): return
    # Boss ignores stealth; always hunts
    to_sub = [sub_pos[0]-boss["x"], sub_pos[1]-boss["y"], sub_pos[2]-boss["z"]]
    d = norm3(to_sub)
    boss["x"] += d[0]*boss_speed*dt
    boss["y"] += d[1]*boss_speed*dt
    boss["z"] += d[2]*boss_speed*dt
    boss["x"] = clamp(boss["x"], -arena_size+2.2, arena_size-2.2)
    boss["y"] = clamp(boss["y"], -arena_size+2.2, arena_size-2.2)
    boss["z"] = clamp(boss["z"], -arena_size+2.2, arena_size-2.2)
    # Collision with sub is devastating
    if abs(boss["x"]-sub_pos[0])<2.3 and abs(boss["y"]-sub_pos[1])<2.3 and abs(boss["z"]-sub_pos[2])<2.3:
        if shield_charges > 0:
            shield_charges -= 1
        else:
            hp -= 50
            if hp <= 0:
                game_over = True

def update_torpedoes(dt):
    # Move
    for t in torpedoes:
        t[0] += t[3]*dt
        t[1] += t[4]*dt
        t[2] += t[5]*dt
    # Remove out-of-arena
    torpedoes[:] = [t for t in torpedoes if -arena_size < t[0] < arena_size and -arena_size < t[1] < arena_size and -arena_size < t[2] < arena_size]

def torpedo_hits():
    global score, boss
    # Hit obstacles
    for t in list(torpedoes):
        for o in obstacles:
            if not o["alive"]: continue
            if abs(t[0]-o["x"])<1.2 and abs(t[1]-o["y"])<1.2 and abs(t[2]-o["z"])<1.2:
                o["alive"] = False
                score += 10
                try: torpedoes.remove(t)
                except: pass
                break
    # Hit boss
    if boss and boss["alive"]:
        for t in list(torpedoes):
            if abs(t[0]-boss["x"])<2.4 and abs(t[1]-boss["y"])<2.4 and abs(t[2]-boss["z"])<2.4:
                boss["hp"] -= 3
                try: torpedoes.remove(t)
                except: pass
                if boss["hp"] <= 0:
                    boss["alive"] = False
                    score += boss_reward

def update_powerups(dt_ms):
    global hp, hp_max, boost_active, boost_ends_at, shield_charges
    # TTL
    for p in list(powerups):
        p["ttl"] -= dt_ms
        if p["ttl"] <= 0:
            powerups.remove(p)
            continue
        # pickup
        if abs(p["x"]-sub_pos[0])<1.1 and abs(p["y"]-sub_pos[1])<1.1 and abs(p["z"]-sub_pos[2])<1.1:
            if p["type"] == POWER_HEALTH:
                hp = clamp(hp+20, 0, hp_max)
            elif p["type"] == POWER_BOOST:
                boost_active = True
                boost_ends_at = now_ms() + 8000  # 8s rapid fire
            else:
                shield_charges += 1
            powerups.remove(p)

    # boost timeout
    if boost_active and now_ms() >= boost_ends_at:
        boost_active = False

def fire_torpedo():
    global last_fire_time
    tnow = now_ms()
    cd = 120 if boost_active else fire_cooldown_ms
    if tnow - last_fire_time < cd: return
    last_fire_time = tnow
    # Torpedo goes forward in the -Z of sub's facing? We'll map rotation to X axis sweep:
    # Use sub_angle yaw to compute local forward on XZ plane. We'll shoot along -Z in *world* by rotating local forward.
    yaw = math.radians(sub_angle)
    forward = [math.sin(yaw), 0.0, -math.cos(yaw)]
    vx, vy, vz = [forward[0]*torpedo_speed, forward[1]*torpedo_speed, forward[2]*torpedo_speed]
    spawn = [sub_pos[0] + forward[0]*1.8, sub_pos[1], sub_pos[2] + forward[2]*1.8]
    torpedoes.append([spawn[0], spawn[1], spawn[2], vx, vy, vz])

def update_bubbles(dt):
    global bubble_spawn_accum
    # spawn rate ~ 35 per second
    bubble_spawn_accum += dt*35.0
    count = int(bubble_spawn_accum)
    bubble_spawn_accum -= count
    # spawn behind sub (opposite of forward)
    yaw = math.radians(sub_angle)
    back = [-math.sin(yaw), 0.0, math.cos(yaw)]
    for _ in range(count):
        jitter = [random.uniform(-0.2,0.2), random.uniform(-0.2,0.2), random.uniform(-0.2,0.2)]
        pos = [sub_pos[0] + back[0]*1.6 + jitter[0],
               sub_pos[1] - 0.2 + jitter[1],
               sub_pos[2] + back[2]*1.6 + jitter[2]]
        vel = [random.uniform(-0.2,0.2), random.uniform(0.9,1.4), random.uniform(-0.2,0.2)]
        bubbles.append({"x":pos[0],"y":pos[1],"z":pos[2],"vx":vel[0],"vy":vel[1],"vz":vel[2],"life":1800})
    # update & cull
    for b in list(bubbles):
        b["x"] += b["vx"]*dt
        b["y"] += b["vy"]*dt
        b["z"] += b["vz"]*dt
        b["life"] -= dt*1000.0
        if b["life"] <= 0 or b["y"] > arena_size-0.5:
            bubbles.remove(b)

def check_story():
    global won, game_over
    if not story_mode or game_over or won: return
    # win condition
    dx = sub_pos[0]-story_goal[0]
    dy = sub_pos[1]-story_goal[1]
    dz = sub_pos[2]-story_goal[2]
    if dx*dx+dy*dy+dz*dz <= story_goal_radius*story_goal_radius:
        won = True
    # lose on timeout
    if now_ms() - story_start_ms >= story_total_ms and not won:
        game_over = True

# --------------- GLUT callbacks -------------------
score = 0
last_time_ms = 0

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    # Chase camera
    cam_dist = 32.0
    cam_height = 18.0
    yaw = math.radians(sub_angle)
    cam_x = sub_pos[0] - math.sin(yaw)*cam_dist
    cam_y = sub_pos[1] + cam_height
    cam_z = sub_pos[2] + math.cos(yaw)*cam_dist
    gluLookAt(cam_x, cam_y, cam_z, sub_pos[0], sub_pos[1], sub_pos[2], 0,1,0)

    draw_arena()
    # draw_currents_debug()  # uncomment to see zones
    draw_submarine()
    draw_torpedoes()
    draw_obstacles()
    draw_boss()
    draw_powerups()
    draw_bubbles()

    draw_minimap()
    draw_hud()

    glutSwapBuffers()

def update():
    global last_time_ms, last_powerup_spawn
    if last_time_ms == 0:
        last_time_ms = now_ms()
    tnow = now_ms()
    dt = (tnow - last_time_ms) / 1000.0
    last_time_ms = tnow

    if game_over or won:
        glutPostRedisplay()
        return

    # Spawn boss on schedule
    ensure_boss()

    # Power-ups spawn timer
    if tnow - last_powerup_spawn >= powerup_spawn_interval_ms:
        spawn_powerup()
        last_powerup_spawn = tnow

    move_player(dt)
    update_obstacles(dt)
    update_boss(dt)
    update_torpedoes(dt)
    torpedo_hits()
    update_powerups((tnow - last_time_ms) if last_time_ms else 16)
    update_bubbles(dt)
    check_story()

    glutPostRedisplay()

def keyboard_down(key, x, y):
    global stealth
    keys[key] = True
    if key == b' ':
        fire_torpedo()
    elif key == b'v' or key == b'V':
        stealth = not stealth

def keyboard_up(key, x, y):
    keys[key] = False

def reshape(w, h):
    global window_width, window_height
    window_width, window_height = w, h
    glViewport(0,0,w,h)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60.0, w/float(h if h>0 else 1), 0.5, 200.0)
    glMatrixMode(GL_MODELVIEW)

def init():
    glClearColor(0.0, 0.02, 0.15, 1.0) # deep ocean
    glEnable(GL_DEPTH_TEST)
    glPointSize(3.0)  # bubbles & minimap dots

# --------------- Main -----------------------------
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(window_width, window_height)
glutInitWindowPosition(100, 80)
glutCreateWindow(b"Submarine Arena Unique Features Edition")

init()
spawn_obstacles()
story_start_ms = now_ms()
last_powerup_spawn = now_ms()

glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutKeyboardFunc(keyboard_down)
glutKeyboardUpFunc(keyboard_up)
glutIdleFunc(update)
glutMainLoop()
