# ---Underwater Atmosphere ---
day_night_cycle = 0.0
day_night_speed = 0.00005
underwater_depth = -15.0

darkness_zones = [
    (-20, -10, -20, 20, -20, 20)
]
water_particles = []


def draw_light_rays():
    # Only add very subtle ambient lighting variation, no visible rays
    if day_night_cycle > 0.2 and day_night_cycle < 0.8:
        sun_intensity = max(0.0, math.sin(day_night_cycle * 2.0 * math.pi))

        # Just add a very subtle color tint to the water, no geometric rays
        lighting = get_current_lighting()
        ambient_boost = sun_intensity * 0.05  # Very subtle

        # You can add this to the ocean floor or background if needed
        # But for now, let's just disable the rays completely
        pass
def get_time_of_day():
    if day_night_cycle < 0.25 or day_night_cycle > 0.75:
        return "Night"
    elif day_night_cycle < 0.5:
        return "Morning"
    else:
        return "Evening"
def in_dark_zone(pos):
    for (xmin, xmax, ymin, ymax, zmin, zmax) in darkness_zones:
        if xmin <= pos[0] <= xmax and ymin <= pos[1] <= ymax and zmin <= pos[2] <= zmax:
            return True
    return False

def get_visibility_factor(pos):
    if in_dark_zone(pos):
        return 0.3 if not boost_active else 0.7
    return 1.0

def update_day_night_cycle():
    global day_night_cycle
    day_night_cycle += day_night_speed
    if day_night_cycle > 1.0:
        day_night_cycle = 0.0
def get_current_lighting():
    sun_angle = day_night_cycle * 2.0 * math.pi
    sun_intensity = max(0.0, math.sin(sun_angle))

    base_r, base_g, base_b = 0.05, 0.15, 0.3
    sun_r, sun_g, sun_b = 0.3, 0.5, 0.7

    r = base_r + (sun_r * sun_intensity * 0.4)
    g = base_g + (sun_g * sun_intensity * 0.5)
    b = base_b + (sun_b * sun_intensity * 0.3)

    return [r, g, b, 1.0]
difficulty_level = 1
last_difficulty_increase = 0
difficulty_interval = 30000
max_obstacles = 25

def update_difficulty():
    global difficulty_level, last_difficulty_increase, obstacle_speed
    current_time = now_ms()

    if current_time - last_difficulty_increase > difficulty_interval:
        difficulty_level += 1
        last_difficulty_increase = current_time
        obstacle_speed += 0.5

        alive_count = len([o for o in obstacles if o["alive"]])
        target_count = min(num_obstacles + (difficulty_level - 1) * 2, max_obstacles)

        for _ in range(target_count - alive_count):
            if len(obstacles) < max_obstacles:
                respawn_obstacle()

bubbles = []
bubble_trail = []
bubble_spawn_accum = 0.0
trail_spawn_accum = 0.0

def draw_enhanced_bubbles():
    for b in bubbles:
        if b["life_ms"] <= 0: continue
        glColor3f(0.8, 0.9, 1.0)
        glPushMatrix()
        glTranslatef(b["x"], b["y"], b["z"])
        gluSphere(gluNewQuadric(), b["size"], 6, 6)
        glPopMatrix()

    for b in bubble_trail:
        if b["life_ms"] <= 0: continue
        glColor3f(0.9, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(b["x"], b["y"], b["z"])
        gluSphere(gluNewQuadric(), b["size"], 4, 4)
        glPopMatrix()
def create_impact_bubble(x, y, z):
    bubbles.append({
        "x": x + random.uniform(-0.5, 0.5),
        "y": y + random.uniform(-0.5, 0.5),
        "z": z + random.uniform(-0.5, 0.5),
        "vx": random.uniform(-2, 2),
        "vy": random.uniform(1, 4),
        "vz": random.uniform(-2, 2),
        "life_ms": random.uniform(2000, 4000),
        "size": random.uniform(0.1, 0.3),
        "alpha": 0.8
    })

def create_trail_bubble():
    rear_offset = -5.0
    radians = math.radians(sub_angle)
    rear_x = sub_pos[0] + rear_offset * math.sin(radians)
    rear_z = sub_pos[2] + rear_offset * math.cos(radians)

    bubble_trail.append({
        "x": rear_x + random.uniform(-0.3, 0.3),
        "y": sub_pos[1] + random.uniform(-0.2, 0.2),
        "z": rear_z + random.uniform(-0.3, 0.3),
        "vx": random.uniform(-0.5, 0.5) - sub_vel[0] * 0.1,
        "vy": random.uniform(0.5, 1.5),
        "vz": random.uniform(-0.5, 0.5) - sub_vel[2] * 0.1,
        "life_ms": random.uniform(3000, 6000),
        "size": random.uniform(0.05, 0.15),
        "alpha": 0.6
    })
def spawn_environmental_bubbles():
    if random.random() < 0.02:
        x, y, z = rand_pos_inside()
        bubbles.append({
            "x": x,
            "y": y,
            "z": z,
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(0.2, 1.0),
            "vz": random.uniform(-0.3, 0.3),
            "life_ms": random.uniform(8000, 15000),
            "size": random.uniform(0.05, 0.2),
            "alpha": 0.4
        })

def spawn_water_particles():
    if len(water_particles) < 50 and random.random() < 0.05:
        x, y, z = rand_pos_inside()
        water_particles.append({
            "x": x,
            "y": y,
            "z": z,
            "vx": random.uniform(-0.1, 0.1),
            "vy": random.uniform(-0.1, 0.1),
            "vz": random.uniform(-0.1, 0.1),
            "life_ms": random.uniform(20000, 40000),
            "type": random.randint(0, 2),
            "size": random.uniform(0.02, 0.08)
        })
def update_bubbles(dt):
    current_time = now_ms()

    # Update regular bubbles
    for b in bubbles[:]:
        b["x"] += b["vx"] * dt
        b["y"] += b["vy"] * dt
        b["z"] += b["vz"] * dt
        b["life_ms"] -= dt * 1000
        if b["life_ms"] <= 0:
            bubbles.remove(b)

    # Update trail bubbles
    for b in bubble_trail[:]:
        b["x"] += b["vx"] * dt
        b["y"] += b["vy"] * dt
        b["z"] += b["vz"] * dt
        b["life_ms"] -= dt * 1000
        if b["life_ms"] <= 0:
            bubble_trail.remove(b)

    # Update water particles
    for p in water_particles[:]:
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["z"] += p["vz"] * dt
        p["life_ms"] -= dt * 1000
        if p["life_ms"] <= 0:
            water_particles.remove(p)

obstacles = []
num_obstacles = 14
detect_radius = 9.0
obstacle_speed = 3.0
obstacle_respawn_delay = 2000

def draw_sea_creature(cx, cy, cz, creature_type, size_mult=1.0):
    glPushMatrix()
    glTranslatef(cx, cy, cz)

    if creature_type == 0:  # Fish
        glColor3f(0.0, 0.7, 0.3)
        glPushMatrix()
        glScalef(1.6*size_mult, 0.8*size_mult, 2.4*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glColor3f(0.0, 0.5, 0.2)
        glPushMatrix()
        glTranslatef(0, 0, -1.5*size_mult)
        glScalef(0.6*size_mult, 1.2*size_mult, 0.6*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glColor3f(0.0, 0.6, 0.25)
        glPushMatrix()
        glTranslatef(-1.0*size_mult, 0, 0.2*size_mult)
        glScalef(0.8*size_mult, 0.04*size_mult, 0.8*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(1.0*size_mult, 0, 0.2*size_mult)
        glScalef(0.8*size_mult, 0.04*size_mult, 0.8*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

    elif creature_type == 1:  # Jellyfish
        glColor3f(0.8, 0.3, 0.8)
        glPushMatrix()
        glTranslatef(0, 0.5*size_mult, 0)
        glScalef(2.0*size_mult, 0.6*size_mult, 2.0*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glColor3f(0.6, 0.2, 0.6)
        for i in range(4):
            angle = i * 90
            x = 0.5 * math.cos(math.radians(angle)) * size_mult
            z = 0.5 * math.sin(math.radians(angle)) * size_mult
            glPushMatrix()
            glTranslatef(x, -0.8*size_mult, z)
            glScalef(0.1*size_mult, 1.6*size_mult, 0.1*size_mult)
            glutSolidCube(1.0)
            glPopMatrix()

    elif creature_type == 2:  # Shark
        glColor3f(0.4, 0.4, 0.5)
        glPushMatrix()
        glScalef(1.2*size_mult, 1.0*size_mult, 3.6*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glColor3f(0.3, 0.3, 0.4)
        glPushMatrix()
        glTranslatef(0, 0.7*size_mult, 0.5*size_mult)
        glScalef(0.1*size_mult, 0.8*size_mult, 0.6*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0.3*size_mult, -2.2*size_mult)
        glScalef(0.1*size_mult, 1.6*size_mult, 0.8*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-0.8*size_mult, -0.2*size_mult, 0.8*size_mult)
        glScalef(0.8*size_mult, 0.04*size_mult, 0.6*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.8*size_mult, -0.2*size_mult, 0.8*size_mult)
        glScalef(0.8*size_mult, 0.04*size_mult, 0.6*size_mult)
        glutSolidCube(1.0)
        glPopMatrix()

    glPopMatrix()

def draw_water_particles():
    for p in water_particles:
        if p["type"] == 0:
            glColor3f(0.4, 0.3, 0.2)
        elif p["type"] == 1:
            glColor3f(0.2, 0.8, 0.6)
        else:
            glColor3f(0.6, 0.7, 0.3)

        glPushMatrix()
        glTranslatef(p["x"], p["y"], p["z"])
        glScalef(p["size"], p["size"], p["size"])
        glutSolidCube(1.0)
        glPopMatrix()


def draw_obstacles():
    for o in obstacles:
        if not o["alive"]: continue
        creature_type = o.get("enemy_type", 0)
        size_variation = o.get("size_mult", 1.0)
        draw_sea_creature(o["x"], o["y"], o["z"], creature_type, size_variation)
# --------------- Spawning -------------------------
def spawn_obstacles():
    obstacles.clear()
    current_num = min(num_obstacles + (difficulty_level - 1) * 2, max_obstacles)
    for _ in range(current_num):
        x,y,z = rand_pos_inside()
        obstacles.append({
            "x": x, "y": y, "z": z,
            "vx": random.uniform(-0.5,0.5),
            "vy": random.uniform(-0.5,0.5),
            "vz": random.uniform(-0.5,0.5),
            "r": 1.0,
            "alive": True,
            "respawn_timer": 0,
            "enemy_type": random.randint(0, 2),
            "size_mult": random.uniform(0.8, 1.3)
        })

def respawn_obstacle():
    x, y, z = rand_pos_inside()
    obstacles.append({
        "x": x, "y": y, "z": z,
        "vx": random.uniform(-0.5, 0.5) * (1 + difficulty_level * 0.2),
        "vy": random.uniform(-0.5, 0.5) * (1 + difficulty_level * 0.2),
        "vz": random.uniform(-0.5, 0.5) * (1 + difficulty_level * 0.2),
        "r": 1.0,
        "alive": True,
        "respawn_timer": 0,
        "enemy_type": random.randint(0, 2),
        "size_mult": random.uniform(0.8, 1.3)
    })
def update_obstacles(dt):
    current_time = now_ms()

    for o in obstacles[:]:
        if o["alive"]:
            # Move obstacles
            o["x"] += o["vx"] * obstacle_speed * dt
            o["y"] += o["vy"] * obstacle_speed * dt
            o["z"] += o["vz"] * obstacle_speed * dt

            # Keep in bounds
            for coord in ["x", "y", "z"]:
                if o[coord] < -arena_size + 1:
                    o[coord] = -arena_size + 1
                    o["v" + coord] *= -1
                elif o[coord] > arena_size - 1:
                    o[coord] = arena_size - 1
                    o["v" + coord] *= -1
        else:
            # Check for respawn
            if o["respawn_timer"] > 0 and current_time >= o["respawn_timer"]:
                o["alive"] = True
                o["respawn_timer"] = 0
                x, y, z = rand_pos_inside()
                o["x"], o["y"], o["z"] = x, y, z

boss = None
boss_base_hp = 30
boss_reward = 200
boss_speed = 2.0

def draw_boss():
    global boss
    if boss and boss["alive"]:
        glPushMatrix()
        glTranslatef(boss["x"], boss["y"], boss["z"])

        glColor3f(0.7, 0.1, 0.1)
        glPushMatrix()
        glScalef(5.0, 3.6, 6.0)
        glutSolidCube(1.0)
        glPopMatrix()

        glColor3f(1.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(-1.8, 0.8, 2.5)
        gluSphere(gluNewQuadric(), 0.3, 8, 8)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(1.8, 0.8, 2.5)
        gluSphere(gluNewQuadric(), 0.3, 8, 8)
        glPopMatrix()

        glColor3f(0.5, 0.0, 0.0)
        for i in range(6):
            angle = i * 60
            x = 2.5 * math.cos(math.radians(angle))
            z = 2.5 * math.sin(math.radians(angle))
            glPushMatrix()
            glTranslatef(x, -1.0, z)
            glScalef(0.4, 3.0, 0.4)
            glutSolidCube(1.0)
            glPopMatrix()

        glColor3f(0.3, 0.0, 0.0)
        for i in range(5):
            x_pos = -2.0 + i * 1.0
            glPushMatrix()
            glTranslatef(x_pos, 2.2, 0)
            glScalef(0.2, 1.6, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()

        glPopMatrix()
def ensure_boss():
    global boss
    minutes = now_ms() // 60000
    if minutes == 0: return
    if minutes % 5 == 0:
        if (not boss) or (boss and (not boss["alive"] or boss["spawnedMinute"] != minutes)):
            bx, by, bz = (arena_size-2, 0.0, arena_size-2)
            boss_hp = boss_base_hp + (difficulty_level - 1) * 10
            boss = {"x":bx,"y":by,"z":bz,"vx":0,"vy":0,"vz":0,"r":2.5,"hp":boss_hp,"alive":True,"spawnedMinute":minutes}
def update_boss(dt):
    global boss
    if boss and boss["alive"]:
        dx = sub_pos[0] - boss["x"]
        dy = sub_pos[1] - boss["y"]
        dz = sub_pos[2] - boss["z"]

        dist = distance3([boss["x"], boss["y"], boss["z"]], sub_pos)
        if dist > 0:
            boss["x"] += (dx / dist) * boss_speed * dt
            boss["y"] += (dy / dist) * boss_speed * dt
            boss["z"] += (dz / dist) * boss_speed * dt