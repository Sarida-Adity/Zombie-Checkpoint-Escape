#CSE423 Project
#1.Sarida Islam(22201065)
#2.Aishwarja Roy(23201386)
#3.Nazia Nuzhat Esha(23201365)



from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random
import time

#camera
camera_pos = (0, 700, 650)
fovY = 100
GRID_LENGTH = 600
WINDOW_W = 1000
WINDOW_H = 800
orbit_angle = 0.0
BOUNDARY_Z = 105
ARENA_HALF = GRID_LENGTH 

# Gameplay state
player_x = -520.0
player_y = 0.0
player_angle = 0.0
player_speed = 12.0
player_radius = 22.0

camera_angle = 0.0
camera_height = 420.0
camera_side_offset = 0.0
first_person = False

wall_x_positions = [-180.0, 140.0, 420.0]
wall_open_progress = [0.0, 0.0, 0.0]
wall_opening = [False, False, False]
wall_opened = [False, False, False]

checkpoints = [
    {
        "x": -300.0,
        "tiles": ["Red", "Blue", "Green", "Yellow"],
        "mode": "single",
        "answer": ["Yellow"],
        "clue": "Checkpoint 1: Mix of red and green is the key.",
        "cleared": False,
    },
    {
        "x": 60.0,
        "tiles": ["Red", "Blue", "Green", "Yellow"],
        "mode": "sequence",
        "answer": ["Blue", "Green"],
        "clue": "Checkpoint 2: Sky comes before grass.",
        "cleared": False,
    },
    {
        "x": 340.0,
        "tiles": ["Purple", "Yellow", "Blue"],
        "mode": "single",
        "answer": ["Blue"],
        "clue": "Checkpoint 3: Two are mixed, one is pure. Pick the odd one.",
        "cleared": False,
    },
]

current_checkpoint = -1
completed_checkpoints = 0
sequence_progress = []
selected_tile = -1

freeze_active = False
freeze_duration = 30.0
freeze_start_time = 0.0
remaining_freeze = 0.0
penalty_seconds = 5.0

zombies = []
zombie_count = 5
zombie_base_speed = 0.75
zombie_touch_distance = 28.0
zombie_wobble = 0.0

score = 0
lives = 3
wrong_steps = 0
message_text = "Reach the first checkpoint."
message_timer = 0.0
last_update_time = time.time()

game_over = False
win_game = False

def wall_quad(ax, ay, bx, by, col):
    glColor3f(*col)
    glBegin(GL_QUADS)
    glVertex3f(ax, ay, 0)
    glVertex3f(bx, by, 0)
    glVertex3f(bx, by, BOUNDARY_Z)
    glVertex3f(ax, ay, BOUNDARY_Z)
    glEnd()

def draw_boundaries():
    H = ARENA_HALF

    # south wall
    wall_quad(-H, -H, H, -H, (0.3, 1.0, 1.0))

    # north wall
    wall_quad(H, H, -H, H, (0.3, 1.0, 1.0))


    # west wall
    wall_quad(-H, H, -H, -H, (0.0, 1.0, 0.0))


    # east wall
    wall_quad(H, -H, H, H, (1.0, 0.0, 1.0))

TILE_COLOR = {
    "Red": (1.0, 0.2, 0.2),
    "Blue": (0.2, 0.4, 1.0),
    "Green": (0.2, 0.9, 0.3),
    "Yellow": (1.0, 0.9, 0.2),
    "Purple": (0.75, 0.3, 0.95),
}


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def clamp(val, low, high):
    return max(low, min(high, val))


def show_message(text, duration=2.0):
    global message_text, message_timer
    message_text = text
    message_timer = duration


def reset_game():
    global player_x, player_y, player_angle, current_checkpoint, completed_checkpoints
    global sequence_progress, selected_tile, freeze_active, freeze_start_time
    global remaining_freeze, wall_open_progress, wall_opening, wall_opened
    global score, lives, wrong_steps, game_over, win_game, message_text, message_timer
    global camera_pos, camera_angle, camera_height, camera_side_offset, first_person, last_update_time, checkpoints

    player_x = -520.0
    player_y = 0.0
    player_angle = 0.0
    current_checkpoint = -1
    completed_checkpoints = 0
    sequence_progress = []
    selected_tile = -1
    freeze_active = False
    freeze_start_time = 0.0
    remaining_freeze = 0.0
    wall_open_progress = [0.0, 0.0, 0.0]
    wall_opening = [False, False, False]
    wall_opened = [False, False, False]
    score = 0
    lives = 3
    wrong_steps = 0
    game_over = False
    win_game = False
    message_text = "Reach the first checkpoint."
    message_timer = 0.0
    camera_angle = 0.0
    camera_height = 420.0
    camera_side_offset = 0.0
    first_person = False
    camera_pos = (-760, -420, 520)
    last_update_time = time.time()

    i = 0
    while i < len(checkpoints):
        checkpoints[i]["cleared"] = False
        random.shuffle(checkpoints[i]["tiles"])
        i += 1

    spawn_zombies()



def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18,r=1,g=1,b=1):
    glColor3f(r,g,b)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        #glColor3f(r,g,b)
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_cube(x, y, z, sx, sy, sz, r, g, b, rot=0.0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rot, 0, 0, 1)
    glScalef(sx, sy, sz)
    glColor3f(r, g, b)
    glutSolidCube(1)
    glPopMatrix()


def draw_cylinder(x, y, z, radius, height, r, g, b, rx=0, ry=0, rz=0, angle=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    if angle != 0:
        glRotatef(angle, rx, ry, rz)
    glColor3f(r, g, b)
    gluCylinder(gluNewQuadric(), radius, radius, height, 12, 12)
    glPopMatrix()


def draw_sphere(x, y, z, radius, r, g, b):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(r, g, b)
    gluSphere(gluNewQuadric(), radius, 16, 16)
    glPopMatrix()


def draw_floor():
    tile = 60
    start = -GRID_LENGTH
    end = GRID_LENGTH
    ix = 0
    x = start
    while x < end:
        iy = 0
        y = start
        while y < end:
            glBegin(GL_QUADS)
            if (ix + iy) % 2 == 0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.08, 0.08, 0.08)
            glVertex3f(x, y, 0)
            glVertex3f(x + tile, y, 0)
            glVertex3f(x + tile, y + tile, 0)
            glVertex3f(x, y + tile, 0)
            glEnd()
            y += tile
            iy += 1
        x += tile
        ix += 1

def draw_player():
    body_rot = 90 - player_angle
    lie_rot = 90 if game_over else 0

    glPushMatrix()
    glTranslatef(player_x, player_y, 0)
    glRotatef(body_rot, 0, 0, 1)
    glRotatef(lie_rot, 0, 1, 0)

    # head completely black
    draw_sphere(0, 0, 100, 16,0,0,0)

    # neck
    draw_cylinder(0, 0, 78, 3.0, 8, 0.15, 0.15, 0.15)

    # tors0

    draw_cube(0, 0, 54, 40, 18, 50, 0.282, 0.239, 0.545)
    draw_cube(0, 0, 54, 20, 18, 52, 0.92, 0.92, 0.92)

    # shoulders
    draw_sphere(-15, 0, 70, 4.8, 0.95, 0.95, 0.95)
    draw_sphere(15, 0, 70, 4.8, 0.95, 0.95, 0.95)

    # upper arms - colorful
    draw_cylinder(-15, 0, 66, 3.8, 26, 0.95, 0.25, 0.25, 1, 0, 0, 120)   # red
    draw_cylinder(15, 0, 66, 3.8, 26, 0.95, 0.25, 0.25, 1, 0, 0, 120)    # red

    # elbows
    draw_sphere(-24, 0, 44, 4.2, 0.12, 0.12, 0.12)
    draw_sphere(24, 0, 44, 4.2, 0.12, 0.12, 0.12)

    # lower arms - colorful
    draw_cylinder(-24, 0, 42, 3.3, 22, 0.20, 0.90, 0.35, 1, 0, 0, 120)   # green
    draw_cylinder(24, 0, 42, 3.3, 22, 0.20, 0.90, 0.35, 1, 0, 0, 120)    # green 
    

    # hips
    draw_sphere(-12, 0, 35, 4.2, 1,1,1)
    draw_sphere(12, 0, 35, 4.2, 1,1,1)


    # shins - colorful
    draw_cylinder(-14, 0, 0, 6, 30, 1.00, 0.80, 0.20, 1, 0, 0, 0)    # yellow
    draw_cylinder(14, 0, 0, 6, 30,1.00, 0.80, 0.20 , 1, 0, 0, 0) #yellow

    glPopMatrix()

def draw_zombie(z):
    x = z["x"]
    y = z["y"]
    pulse = z["pulse"]
    scale = 1.0 + 0.04 * math.sin(pulse)
    angle = math.degrees(math.atan2(player_y - y, player_x - x))

    glPushMatrix()
    glTranslatef(x, y, 0)
    glRotatef(angle+90, 0, 0, 1)  
    glScalef(scale, scale, scale)

    quad = gluNewQuadric()

    # HEAD (SPHERE)
    glPushMatrix()
    glTranslatef(0, 0, 85)
    glColor3f(0.33, 0.68, 0.46)
    gluSphere(quad, 14, 16, 16)
    glPushMatrix()
    glTranslatef(-5, 9, -1)   # left eye (relative to head center)
    glColor3f(0.6, 0.0, 0.0)
    gluSphere(quad, 3, 10, 10)
    glColor3f(1.0, 0.0, 0.0)
    gluSphere(quad, 2, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(5, 9, -1)    # right eye
    glColor3f(0.6, 0.0, 0.0)
    gluSphere(quad, 3, 10, 10)
    glColor3f(1.0, 0.0, 0.0)
    gluSphere(quad, 2, 10, 10)
    glPopMatrix()
    glPopMatrix()

    #BODY (CUBE)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glColor3f(0.28, 0.68, 0.62)
    glScalef(18, 12, 28)
    glutSolidCube(1)
    glPopMatrix()

    # ARMS
    glPushMatrix()
    glTranslatef(-16, 0, 55)
    glRotatef(90, 1, 0, 0)
    glColor3f(0.33, 0.68, 0.46)
    gluCylinder(quad, 3.5, 3.5, 28, 12, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(16, 0, 55)
    glRotatef(90, 1, 0, 0)
    glColor3f(0.33, 0.68, 0.46)
    gluCylinder(quad, 3.5, 3.5, 28, 12, 12)
    glPopMatrix()

    # LEGS
    glPushMatrix()
    glTranslatef(-6, 0, 20)    
    #glRotatef(-90, 1, 0, 0)     
    glColor3f(0.12, 0.24, 0.55)
    gluCylinder(quad, 4, 4, 15, 12, 12)
    glPopMatrix()

# right leg
    glPushMatrix()
    glTranslatef(6, 0, 20)
    #glRotatef(-90, 1, 0, 0)
    glColor3f(0.12, 0.24, 0.55)
    gluCylinder(quad, 4, 4, 15, 12, 12)
    glPopMatrix()

    #FEET 
    glPushMatrix()
    glTranslatef(-6, 8, -8)
    glColor3f(0.33, 0.68, 0.46)
    glScalef(10, 6, 4)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(6, 8, -8)
    glColor3f(0.33, 0.68, 0.46)
    glScalef(10, 6, 4)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()
    
  

def draw_wall(index):
    if wall_opened[index]:
        return

    x = wall_x_positions[index]

    # wall goes UP when opening
    height = 120.0 - wall_open_progress[index]
    if height < 2:
        height = 2

    glPushMatrix()
    glTranslatef(x, 0, height / 2)   # center of wall

    glScalef(15, GRID_LENGTH * 2, height)

    glColor3f(0.89, 0.45, 0.36)
    glutSolidCube(1)

    glPopMatrix()
    


def draw_checkpoint_visual(index):
    cp = checkpoints[index]

    if cp["cleared"]:
        return

    cx = cp["x"]

    if current_checkpoint != index or not freeze_active:
        # keep the checkpoint wall visible farther ahead
        draw_cube(cx + 170, 0, 28, 22, 170, 56, 0.10, 0.72, 0.92)
        return

    tile_names = cp["tiles"]
    count = len(tile_names)
    total_width = (count - 1) * 64
    start_y = total_width / 2.0
    i = 0
    while i < count:
        ty = start_y - i * 64
        color_name = tile_names[i]
        rr, gg, bb = TILE_COLOR[color_name]
        scale_z = 12 if i == selected_tile else 7
        draw_cube(cx + 90, ty, scale_z * 0.5, 44, 44, scale_z, rr, gg, bb)
        i += 1

    # wall comes after the color tiles
    draw_cube(cx + 170, 0, 28, 22, 170, 56, 0.10, 0.72, 0.92)

def draw_scene_objects():
    draw_floor()
    draw_boundaries()
    draw_player()

    i = 0
    while i < 3:
        draw_wall(i)
        draw_checkpoint_visual(i)
        i += 1

    for z in zombies:
        draw_zombie(z)


# ----------------------------
# Game logic
# ----------------------------
def spawn_zombies():
    global zombies
    zombies = []
    i = 0
    while i < zombie_count:
        zx = random.choice([-1, 1]) * random.randint(220, 540)
        zy = random.choice([-1, 1]) * random.randint(120, 520)
        if distance(zx, zy, player_x, player_y) < 180:
            zx += 200
        zombies.append({"x": zx, "y": zy, "pulse": 0.0, "alive": True})
        i += 1


def checkpoint_index_for_player():
    i = 0
    while i < len(checkpoints):
        if not wall_opened[i] and not checkpoints[i]["cleared"] and abs(player_x - checkpoints[i]["x"]) < 35 and abs(player_y) < 60:
            return i
        i += 1
    return -1


def start_checkpoint(idx):
    global current_checkpoint, freeze_active, freeze_start_time, remaining_freeze
    global sequence_progress, selected_tile
    current_checkpoint = idx
    freeze_active = True
    freeze_start_time = time.time()
    remaining_freeze = freeze_duration
    sequence_progress = []
    selected_tile = -1
    random.shuffle(checkpoints[idx]["tiles"])
    show_message(checkpoints[idx]["clue"], 4.0)


def complete_checkpoint(idx):
    global completed_checkpoints, current_checkpoint, freeze_active, selected_tile, score, win_game
    checkpoints[idx]["cleared"] = True
    wall_opening[idx] = True
    completed_checkpoints += 1
    current_checkpoint = -1
    freeze_active = False
    selected_tile = -1
    score += 10
    show_message("Correct tile! Wall is opening.", 3.0)
    if completed_checkpoints >= 3:
        win_game = True
        zombies.clear()
        show_message("You crossed all 3 checkpoints. You win!", 8.0)


def apply_wrong_tile_penalty():
    global wrong_steps, freeze_start_time, remaining_freeze
    wrong_steps += 1
    if freeze_active:
        freeze_start_time -= penalty_seconds
        remaining_freeze = max(0.0, remaining_freeze - penalty_seconds)
    show_message("Wrong tile! 5 seconds deducted.", 2.0)


def handle_tile_selection(idx):
    global sequence_progress
    if current_checkpoint < 0 or game_over or win_game:
        return

    cp = checkpoints[current_checkpoint]
    tile_name = cp["tiles"][idx]

    if cp["mode"] == "single":
        if tile_name == cp["answer"][0]:
            complete_checkpoint(current_checkpoint)
        else:
            apply_wrong_tile_penalty()
    else:
        sequence_progress.append(tile_name)
        needed = cp["answer"]
        now_len = len(sequence_progress)
        if sequence_progress[now_len - 1] != needed[now_len - 1]:
            sequence_progress = []
            apply_wrong_tile_penalty()
        elif len(sequence_progress) == len(needed):
            complete_checkpoint(current_checkpoint)
        else:
            show_message("Good. Select the next tile in the sequence.", 1.5)



def move_player(step):
    global player_x, player_y

    angle_rad = math.radians(player_angle)

    nx = player_x + math.cos(angle_rad) * step
    ny = player_y + math.sin(-angle_rad) * step

    H = ARENA_HALF - player_radius

    # boundary collision
    nx = clamp(nx, -H, H)
    ny = clamp(ny, -H, H)

    # wall blocking 
    i = 0
    while i < 3:
        if not wall_opened[i]:
            wx = wall_x_positions[i]
            if player_x < wx -18 <= nx + player_radius:
                nx = wx - 18 - player_radius
        i += 1

    player_x = nx
    player_y = ny


def update_zombies(dt):
    global lives, game_over, zombie_wobble
    zombie_wobble += dt * 4.0

    for z in zombies:
        z["pulse"] = abs(math.sin(zombie_wobble)) * 2.5

        if freeze_active or game_over or win_game:
            continue

        dx = player_x - z["x"]
        dy = player_y - z["y"]
        d = math.sqrt(dx * dx + dy * dy)
        if d > 0.01:
            z["x"] += (dx / d) * zombie_base_speed * 60 * dt
            z["y"] += (dy / d) * zombie_base_speed * 60 * dt

        if distance(z["x"], z["y"], player_x, player_y) < zombie_touch_distance:
            lives -= 1
            z["x"] = random.choice([-1, 1]) * random.randint(260, 520)
            z["y"] = random.choice([-1, 1]) * random.randint(120, 480)
            show_message("A zombie caught you! Life -1", 2.0)
            if lives <= 0:
                game_over = True
                show_message("Game Over! Press R to restart.", 8.0)


def update_walls(dt):
    i = 0
    while i < 3:
        if wall_opening[i] and not wall_opened[i]:
            wall_open_progress[i] += 120 * dt
            if wall_open_progress[i] >= 100:
                wall_open_progress[i] = 100
                wall_opening[i] = False
                wall_opened[i] = True
        i += 1


def update_timers():
    global remaining_freeze, freeze_active, game_over, message_timer, current_checkpoint
    if freeze_active:
        remaining_freeze = freeze_duration - (time.time() - freeze_start_time)
        if remaining_freeze <= 0:
            remaining_freeze = 0
            freeze_active = False
            current_checkpoint = -1
            game_over = True

            zombies.clear()

            show_message("Time over.Press R.", 8.0)


    if message_timer > 0:
        message_timer -= 0.016


def update_selection_from_player_position():
    global selected_tile
    selected_tile = -1
    if current_checkpoint < 0 or not freeze_active:
        return

    cp = checkpoints[current_checkpoint]
    count = len(cp["tiles"])
    total_width = (count - 1) * 64
    start_y = total_width / 2.0
    i = 0
    while i < count:
        ty = start_y - i * 64
        if abs(player_x - (cp["x"] + 90)) < 34 and abs(player_y - ty) < 34:
            selected_tile = i
            return
        i += 1


def rotate_camera_horizontal(delta):
    global orbit_angle
    orbit_angle += delta


def update_camera():
    global camera_pos
    if first_person:
        eye_x = player_x - 45
        eye_y = player_y
        eye_z = 78
        camera_pos = (eye_x, eye_y, eye_z)
    
    else:
      radius = 260

      cam_x = player_x - radius * math.cos(math.radians(orbit_angle))
      cam_y = player_y - radius * math.sin(math.radians(orbit_angle))
    

      camera_pos = (cam_x, cam_y, camera_height)


def game_update():
    global last_update_time
    now = time.time()
    dt = now - last_update_time
    if dt > 0.05:
        dt = 0.05
    last_update_time = now

    if not game_over and not win_game:
        idx = checkpoint_index_for_player()
        if idx != -1 and current_checkpoint == -1:
            start_checkpoint(idx)

    update_timers()
    update_walls(dt)
    update_zombies(dt)
    update_selection_from_player_position()
    update_camera()



# Input

def keyboardListener(key, x, y):
    global player_angle, first_person

    if key == b'w' and not game_over and not win_game:
        move_player(player_speed)
    if key == b's' and not game_over and not win_game:
        move_player(-player_speed)
    if key == b'a' and not game_over and not win_game:
        player_angle = (player_angle+8)%360
    if key == b'd' and not game_over and not win_game:
        player_angle = (player_angle-8)%360
    

    if key == b'1':
        handle_tile_selection(0)
    if key == b'2':
        handle_tile_selection(1)
    if key == b'3':
        handle_tile_selection(2)
    if key == b'4':
        handle_tile_selection(3)

    if key == b'r':
        reset_game()


def specialKeyListener(key, x, y):
    global camera_height
    if key == GLUT_KEY_UP:
        camera_height += 20
    if key == GLUT_KEY_DOWN:
        camera_height -= 20
    if key == GLUT_KEY_LEFT:
        rotate_camera_horizontal(-3)
    if key == GLUT_KEY_RIGHT:
        rotate_camera_horizontal(3)

    camera_height = clamp(camera_height, 220, 900)


def mouseListener(button, state, x, y):
    global first_person
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person



# Camera setup

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = camera_pos

    if first_person:
        rad=math.radians(player_angle)
        tx=player_x+math.cos(rad)*100               #where i am looking changer based on angle
        ty=player_y+math.sin(-rad)*100
        gluLookAt(player_x,player_y,160,tx,ty,100,0,0,1)
    else:
        gluLookAt(x, y, z, player_x + 260, player_y, 45, 0, 0, 1)
        


def idle():
    game_update()
    glutPostRedisplay()


def draw_hud():
    draw_text(10, 770, f"Lives: {lives}")
    draw_text(10, 742, f"Checkpoints Cleared: {completed_checkpoints}/3")
    draw_text(10, 714, f"Wrong Tiles: {wrong_steps}")

    if freeze_active:
        draw_text(10, 686, f"Freeze Time Left: {int(math.ceil(remaining_freeze))} sec",GLUT_BITMAP_HELVETICA_18,1,1,0)

    if current_checkpoint >= 0 and freeze_active:
        cp = checkpoints[current_checkpoint]
        draw_text(10, 658, cp["clue"],GLUT_BITMAP_HELVETICA_18,1,0,1)
        tile_labels = " | ".join([f"{i+1}:{cp['tiles'][i]}" for i in range(len(cp['tiles']))])
        draw_text(10, 630, f"Left to right tiles: {tile_labels}",GLUT_BITMAP_HELVETICA_18,1,0,0)

    if message_timer > 0:
        draw_text(10, 602, message_text,GLUT_BITMAP_HELVETICA_18,0,1,0)

    draw_text(400, 770, "W/S move forward-back, A/D rotate, Right click camera, R restart",GLUT_BITMAP_HELVETICA_18,0.3,1,1)
    draw_text(400, 742, "Stand beside the colored tiles, then press 1/2/3/4",GLUT_BITMAP_HELVETICA_18,0.3,1,1)

    if game_over:
        draw_text(500, 600, "GAME OVER",GLUT_BITMAP_HELVETICA_18,1, 0, 0)  
    if win_game:
        draw_text(500, 600, "YOU WIN",GLUT_BITMAP_HELVETICA_18,1.0, 1.0, 1.0)  


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    setupCamera()
    draw_scene_objects()
    draw_hud()
    glutSwapBuffers()



# Main-
def main():
    reset_game()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Zombie Checkpoint Escape - OpenGL")

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()