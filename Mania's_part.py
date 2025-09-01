treasures = []
treasure_spawn_interval_ms = 15000
last_treasure_spawn = 0
TREASURE_SCORE = 50

darkness_zones = [
    (-20, -10, -20, 20, -20, 20)
]

# --------------- Scoring System ------------------
score = 0
obstacle_points = 10
boss_points = 200
powerup_points = 5

# --------------- Power-ups -----------------------
powerups = []
powerup_spawn_interval_ms = 12000
last_powerup_spawn = 0
POWER_HEALTH, POWER_BOOST, POWER_SHIELD = 0, 1, 2

# --------------- Story / Escape Mode -------------
story_mode = True
story_total_ms = 180000
story_start_ms = 0
story_goal = [12.0, 10.0, 12.0]
story_goal_radius = 2.0
won = False
game_over = False

# --------------- Input ---------------------------
keys = {}

# --------------- Camera Setup --------------------
camera_pos = [0.0, 15, 25.0]
fovY = 45

# --------------- Timing --------------------------
last_frame_time = 0

def trigger_game_over():
    global game_over
    game_over = True

def reset_game():
    global sub_pos, sub_vel, sub_angle, hp, shield_charges, score, won, game_over
    global difficulty_level, last_difficulty_increase, story_start_ms, day_night_cycle
    global torpedoes, obstacles, boss, powerups, bubbles, bubble_trail, water_particles

    # Reset submarine
    sub_pos = [0.0, 0.0, -5.0]
    sub_vel = [0.0, 0.0, 0.0]
    sub_angle = 0.0
    hp = hp_max
    shield_charges = 0

    # Reset game state
    score = 0
    won = False
    game_over = False
    difficulty_level = 1
    last_difficulty_increase = now_ms()
    story_start_ms = now_ms()
    day_night_cycle = 0.0

    # Clear all objects
    torpedoes.clear()
    obstacles.clear()
    powerups.clear()
    bubbles.clear()
    bubble_trail.clear()
    water_particles.clear()
    boss = None

    # Respawn obstacles
    spawn_obstacles()
    
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, window_width/window_height, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Follow the submarine
    cam_x = sub_pos[0] + camera_pos[0]
    cam_y = sub_pos[1] + camera_pos[1]
    cam_z = sub_pos[2] + camera_pos[2]

    gluLookAt(cam_x, cam_y, cam_z,
              sub_pos[0], sub_pos[1], sub_pos[2],
              0, 1, 0)
    
def draw_powerups():
    for p in powerups:
        glPushMatrix()
        glTranslatef(p["x"], p["y"], p["z"])

        if p["type"] == POWER_HEALTH:
            glColor3f(0.2,1.0,0.2)
        elif p["type"] == POWER_BOOST:
            glColor3f(1.0,1.0,0.2)
        else:
            glColor3f(0.2,1.0,1.0)

        glScalef(1.2, 1.2, 1.2)
        glutSolidCube(1.0)
        glPopMatrix()
        
def draw_story_goal():
    if story_mode and not won and not game_over:
        glColor3f(0.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(*story_goal)
        glScalef(3.0, 3.0, 3.0)
        glutSolidCube(1.0)
        glPopMatrix()
        
def draw_minimap():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    map_size = 160
    margin = 16
    x0 = window_width - map_size - margin
    y0 = window_height - map_size - margin

    glColor3f(1,1,1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0); glVertex2f(x0+map_size, y0)
    glVertex2f(x0+map_size, y0+map_size); glVertex2f(x0, y0+map_size)
    glEnd()

    def world_to_map(wx, wy, wz):
        rx, ry, rz = wx - sub_pos[0], wy - sub_pos[1], wz - sub_pos[2]
        scale = (map_size/2.2) / arena_size
        mx = x0 + map_size/2 + rx*scale
        my = y0 + map_size/2 + rz*scale
        return mx, my

    sx, sy = world_to_map(sub_pos[0], sub_pos[1], sub_pos[2])
    glColor3f(0.5,0.8,1.0)
    glBegin(GL_QUADS)
    glVertex2f(sx-3, sy-3); glVertex2f(sx+3, sy-3); glVertex2f(sx+3, sy+3); glVertex2f(sx-3, sy+3)
    glEnd()

    if story_mode:
        gx, gy = world_to_map(story_goal[0], story_goal[1], story_goal[2])
        glColor3f(0.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(gx-2, gy-2); glVertex2f(gx+2, gy-2); glVertex2f(gx+2, gy+2); glVertex2f(gx-2, gy+2)
        glEnd()

    glColor3f(0.2,1.0,0.2)
    glBegin(GL_POINTS)
    for o in obstacles:
        if not o["alive"]: continue
        mx,my = world_to_map(o["x"],o["y"],o["z"])
        glVertex2f(mx,my)
    glEnd()

    if boss and boss["alive"]:
        glColor3f(1.0,0.2,0.2)
        mx,my = world_to_map(boss["x"],boss["y"],boss["z"])
        glBegin(GL_QUADS)
        glVertex2f(mx-4,my-4); glVertex2f(mx+4,my-4); glVertex2f(mx+4,my+4); glVertex2f(mx-4,my+4)
        glEnd()

    glMatrixMode(GL_MODELVIEW); glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
# -------------------- Treasure Management --------------------
def spawn_treasure():
    global treasures
    x, y, z = rand_pos_inside()
    treasures.append({
        "x": x, "y": y, "z": z,
        "collected": False,
        "size": random.uniform(0.5, 1.2)
    })

def update_treasures(dt):
    global last_treasure_spawn, score
    current_time = now_ms()
    if current_time - last_treasure_spawn > treasure_spawn_interval_ms:
        spawn_treasure()
        last_treasure_spawn = current_time

    # Check if submarine collects treasure
    for t in treasures[:]:
        if not t["collected"] and distance3(sub_pos, [t["x"], t["y"], t["z"]]) < 2.0:
            t["collected"] = True
            score += TREASURE_SCORE

# -------------------- Sonar --------------------
def activate_sonar():
    global sonar_active, sonar_ends_at
    sonar_active = True
    sonar_ends_at = now_ms() + SONAR_DURATION_MS

def update_sonar():
    global sonar_active
    if sonar_active and now_ms() > sonar_ends_at:
        sonar_active = False
        
def draw_hud():
    draw_text(10, window_height-24, f"HP: {hp}/{hp_max}   Shield: {shield_charges}   Score: {score}")
    draw_text(10, window_height-48, f"Difficulty Level: {difficulty_level}   Enemies: {len([o for o in obstacles if o['alive']])}")
    draw_text(10, window_height-72, f"Time: {get_time_of_day()}   Depth: {underwater_depth}m")
    draw_text(10, window_height-96, f"Day/Night Cycle: {day_night_cycle:.3f}")



    if stealth:
        draw_text(10, window_height-120, "[STEALTH] speed halved, undetected")
    if boost_active:
        remaining = max(0, (boost_ends_at - now_ms())//1000)
        draw_text(10, window_height-144, f"[TORPEDO BOOST] {remaining}s")
    if speed_burst_active:
        remaining = max(0, (speed_burst_ends_at - now_ms())//1000)
        draw_text(10, window_height-168, f"[SPEED BURST] {remaining}s")

    if story_mode and not won and not game_over:
        remaining_ms = max(0, story_total_ms - (now_ms() - story_start_ms))
        draw_text(10, window_height-192, f"Escape Timer: {remaining_ms//1000}s")

    if won:
        glColor3f(0.0, 1.0, 0.0)
        draw_text(window_width//2 - 100, window_height//2, "MISSION COMPLETE!")
        draw_text(window_width//2 - 80, window_height//2 - 30, f"Final Score: {score}")
        draw_text(window_width//2 - 80, window_height//2 - 60, "Press R to restart")
    elif game_over:
        glColor3f(1.0, 0.0, 0.0)
        draw_text(window_width//2 - 60, window_height//2, "GAME OVER")
        draw_text(window_width//2 - 80, window_height//2 - 30, f"Final Score: {score}")
        draw_text(window_width//2 - 100, window_height//2 - 60, "Press R to restart")
        
def spawn_powerup():
    t = random.choice([POWER_HEALTH, POWER_BOOST, POWER_SHIELD])
    x,y,z = rand_pos_inside()
    powerups.append({"x":x,"y":y,"z":z,"type":t,"ttl":22000})
    
def update_powerups(dt):
    global last_powerup_spawn
    current_time = now_ms()

    # Spawn new powerups
    if current_time - last_powerup_spawn > powerup_spawn_interval_ms:
        spawn_powerup()
        last_powerup_spawn = current_time

    # Update existing powerups
    for p in powerups[:]:
        p["ttl"] -= dt * 1000
        if p["ttl"] <= 0:
            powerups.remove(p)
            continue

        # Check collection
        if distance3([p["x"], p["y"], p["z"]], sub_pos) < 2.0:
            global hp, shield_charges, boost_active, boost_ends_at,score

            if p["type"] == POWER_HEALTH:
                hp = min(hp_max, hp + 25)
                score += powerup_points
            elif p["type"] == POWER_BOOST:
                boost_active = True
                boost_ends_at = current_time + 10000
                score += powerup_points
            elif p["type"] == POWER_SHIELD:
                shield_charges += 1
                score += powerup_points

            powerups.remove(p)

def check_story_objectives():                           # Function of Mission Complete
    global won
    if story_mode and not won and not game_over:
        # Check if reached goal
        if distance3(sub_pos, story_goal) < story_goal_radius:
            won = True

        # Check time limit
        if now_ms() - story_start_ms > story_total_ms:
            trigger_game_over()
            
# --------------- Template-Compliant Event Handlers ----
def keyboardListener(key, x, y):
    global keys, stealth
    keys[key] = True

    # Fire torpedo (space)
    if key == b' ':
        fire_torpedo()

    # Toggle stealth (T key)
    if key == b'v' or key == b'V':
        stealth = not stealth

    # Activate speed burst (C key)
    if key == b'c' or key == b'C':
        activate_speed_burst()

    # Reset game (R key)
    if key == b'r' or key == b'R':
        reset_game()

def keyboardUpListener(key, x, y):
    global keys
    keys[key] = False

def specialKeyListener(key, x, y):
    pass

def mouseListener(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_torpedo()

# --------------- Main Game Loop Functions ----
def idle():
    glutPostRedisplay()

def showScreen():
    global last_frame_time
    current_time = now_ms()

    if last_frame_time == 0:
        last_frame_time = current_time

    dt = (current_time - last_frame_time) / 1000.0
    last_frame_time = current_time

    # Prevent huge dt values
    dt = min(dt, 0.033)  # Cap at ~30 FPS equivalent

    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_width, window_height)

    # Set background color based on day/night
    lighting = get_current_lighting()
    glClearColor(lighting[0], lighting[1], lighting[2], 1.0)

    # Setup camera
    setupCamera()

    # Update game systems
    if not game_over and not won:
        update_day_night_cycle()  # THIS WAS MISSING!
        update_submarine(dt)
        update_torpedoes(dt)
        update_obstacles(dt)
        update_boss(dt)
        update_powerups(dt)
        update_bubbles(dt)
        update_speed_burst()
        update_difficulty()
        handle_submarine_collisions()
        check_story_objectives()
        ensure_boss()
        update_pressure(dt)

        # Generate bubbles and particles
        if random.random() < 0.1:
            create_trail_bubble()
        spawn_environmental_bubbles()
        spawn_water_particles()

    # Draw everything
    draw_arena()
    draw_light_rays()
    draw_submarine()
    draw_obstacles()
    draw_boss()
    draw_torpedoes()
    draw_powerups()
    draw_enhanced_bubbles()
    draw_water_particles()
    draw_story_goal()
    draw_minimap()
    draw_hud()

    # Swap buffers
    glutSwapBuffers()

# --------------- Main Function (Template-Compliant) ----
def main():
    global story_start_ms

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Submarine Arena - Template Compliant")

    # Enable depth testing
    glEnable(GL_DEPTH_TEST)

    # Initialize game
    story_start_ms = now_ms()
    spawn_obstacles()

    # Register callbacks (template-compliant)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()