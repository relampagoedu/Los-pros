import math
import random
import time
import tkinter as tk


WIDTH = 1000
HEIGHT = 650
ROAD_HORIZON_Y = 130
ROAD_BOTTOM_Y = HEIGHT
ROAD_TOP_HALF_WIDTH = 70
ROAD_BOTTOM_HALF_WIDTH = 410
LANE_COUNT = 3
MAX_SPEED = 240
ACCEL = 85
BRAKE = 140
DRAG = 35
STEER_SPEED = 2.6
WORLD_LENGTH = 18000
SEGMENT_LENGTH = 130

CHECKPOINT_DISTANCE = 3500
TIME_BONUS = 28
START_TIME = 55


class CarGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Los Pros Racer 3D - Edición MVP")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#87ceeb", highlightthickness=0)
        self.canvas.pack()

        self.keys = set()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

        self.running = True
        self.game_over = False
        self.win = False

        self.player_x = 0.0
        self.speed = 0.0
        self.distance = 0.0
        self.time_left = float(START_TIME)
        self.score = 0

        self.last_checkpoint = 0

        self.camera_curvature = 0.0
        self.road_segments = self.generate_road()
        self.traffic = self.generate_traffic(80)

        self.last_time = time.perf_counter()
        self.fps_samples = []

        self.loop()

    def generate_road(self):
        segment_count = WORLD_LENGTH // SEGMENT_LENGTH + 200
        segments = []
        curve = 0.0
        target_curve = 0.0
        for i in range(segment_count):
            if i % 24 == 0:
                target_curve = random.uniform(-0.6, 0.6)
            curve += (target_curve - curve) * 0.08
            hill = math.sin(i * 0.09) * 0.35
            scenery = random.choice(["tree", "tree", "rock", "sign", "none"])
            segments.append({"curve": curve, "hill": hill, "scenery": scenery})
        return segments

    def generate_traffic(self, count):
        traffic = []
        for _ in range(count):
            d = random.uniform(600, WORLD_LENGTH - 300)
            lane = random.randint(0, LANE_COUNT - 1)
            speed_factor = random.uniform(0.35, 0.82)
            color = random.choice(["#ff4d4d", "#ffd166", "#4cc9f0", "#b5179e", "#ef476f"])
            traffic.append({
                "distance": d,
                "lane": lane,
                "speed_factor": speed_factor,
                "color": color,
            })
        return traffic

    def on_key_press(self, event):
        self.keys.add(event.keysym.lower())
        if self.game_over and event.keysym.lower() == "r":
            self.restart()

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def restart(self):
        self.player_x = 0.0
        self.speed = 0.0
        self.distance = 0.0
        self.time_left = float(START_TIME)
        self.score = 0
        self.last_checkpoint = 0
        self.camera_curvature = 0.0
        self.game_over = False
        self.win = False
        self.traffic = self.generate_traffic(80)
        self.last_time = time.perf_counter()

    def get_segment(self, world_distance):
        idx = int(world_distance // SEGMENT_LENGTH) % len(self.road_segments)
        return self.road_segments[idx]

    def lane_to_x(self, lane):
        return -0.62 + lane * (1.24 / (LANE_COUNT - 1))

    def update(self, dt):
        if self.game_over:
            return

        accel_pressed = "up" in self.keys or "w" in self.keys
        brake_pressed = "down" in self.keys or "s" in self.keys
        left_pressed = "left" in self.keys or "a" in self.keys
        right_pressed = "right" in self.keys or "d" in self.keys

        if accel_pressed:
            self.speed += ACCEL * dt
        if brake_pressed:
            self.speed -= BRAKE * dt

        self.speed -= DRAG * dt
        self.speed = max(0.0, min(MAX_SPEED, self.speed))

        steer = 0.0
        if left_pressed:
            steer -= 1.0
        if right_pressed:
            steer += 1.0

        local_curve = self.get_segment(self.distance)["curve"]
        grip_penalty = 1.0 - min(0.55, abs(local_curve) * 0.6)
        self.player_x += steer * STEER_SPEED * dt * (0.75 + self.speed / MAX_SPEED) * grip_penalty
        self.player_x -= local_curve * dt * (0.5 + self.speed / MAX_SPEED)

        if abs(self.player_x) > 1.12:
            self.speed -= 85 * dt
            self.time_left -= 12 * dt

        self.player_x = max(-1.35, min(1.35, self.player_x))

        prev_distance = self.distance
        self.distance += self.speed * dt
        self.time_left -= dt

        self.score += int(self.speed * dt * 1.8)

        checkpoint = int(self.distance // CHECKPOINT_DISTANCE)
        if checkpoint > self.last_checkpoint and self.distance < WORLD_LENGTH:
            self.last_checkpoint = checkpoint
            self.time_left += TIME_BONUS
            self.score += 1200

        # tráfico y colisiones
        player_front = self.distance + 14
        for car in self.traffic:
            car["distance"] += self.speed * car["speed_factor"] * dt
            if car["distance"] < self.distance - 600:
                car["distance"] += WORLD_LENGTH + random.uniform(500, 1800)
                car["lane"] = random.randint(0, LANE_COUNT - 1)

            dz = car["distance"] - player_front
            if -10 < dz < 18:
                lane_x = self.lane_to_x(car["lane"])
                if abs(self.player_x - lane_x) < 0.25:
                    self.speed *= 0.35
                    self.time_left -= 5
                    self.score = max(0, self.score - 450)
                    self.player_x += -0.2 if self.player_x > lane_x else 0.2

        if self.time_left <= 0:
            self.game_over = True
            self.win = False

        if self.distance >= WORLD_LENGTH:
            self.game_over = True
            self.win = True
            self.score += int(self.time_left * 150)

        # Suavizado de cámara
        self.camera_curvature += (local_curve - self.camera_curvature) * min(1.0, dt * 5.2)

    def project_point(self, z, x, y):
        perspective = max(0.001, 1.0 - z)
        sx = WIDTH / 2 + x * (ROAD_BOTTOM_HALF_WIDTH / perspective)
        sy = ROAD_HORIZON_Y + y * 210 + z * (ROAD_BOTTOM_Y - ROAD_HORIZON_Y)
        return sx, sy

    def draw_background(self):
        # Cielo degradado simple en bandas
        self.canvas.create_rectangle(0, 0, WIDTH, ROAD_HORIZON_Y, fill="#79b8ff", outline="")
        self.canvas.create_rectangle(0, ROAD_HORIZON_Y - 36, WIDTH, ROAD_HORIZON_Y, fill="#a4d3ff", outline="")
        self.canvas.create_rectangle(0, ROAD_HORIZON_Y, WIDTH, HEIGHT, fill="#3a7a3a", outline="")

    def draw_road(self):
        draw_distance = 1700
        steps = 90
        base = self.distance

        prev_left = prev_right = prev_y = None
        curve_acc = 0.0

        for n in range(steps, 0, -1):
            z0 = (n - 1) / steps
            z1 = n / steps
            d0 = base + z0 * draw_distance
            d1 = base + z1 * draw_distance
            s0 = self.get_segment(d0)
            s1 = self.get_segment(d1)

            curve_acc += s1["curve"] * 0.0009 * (draw_distance / steps)
            cam_shift = (self.camera_curvature * 0.55 + curve_acc) * (1 - z1)

            w = ROAD_TOP_HALF_WIDTH + (ROAD_BOTTOM_HALF_WIDTH - ROAD_TOP_HALF_WIDTH) * z1
            cx = WIDTH / 2 + cam_shift * WIDTH
            y = ROAD_HORIZON_Y + z1 * (ROAD_BOTTOM_Y - ROAD_HORIZON_Y) + (s1["hill"] * 28 * (1 - z1))

            left = cx - w
            right = cx + w

            if prev_left is not None:
                grass_color = "#3f8f3f" if n % 2 == 0 else "#478f47"
                rumble_color = "#f2f2f2" if n % 2 == 0 else "#d10d0d"
                road_color = "#595959" if n % 2 == 0 else "#5e5e5e"

                # césped banda
                self.canvas.create_polygon(
                    0, prev_y,
                    WIDTH, prev_y,
                    WIDTH, y,
                    0, y,
                    fill=grass_color,
                    outline="",
                )

                # arcenes
                rb = 13 + z1 * 28
                self.canvas.create_polygon(
                    prev_left - rb, prev_y,
                    prev_left, prev_y,
                    left, y,
                    left - rb, y,
                    fill=rumble_color,
                    outline="",
                )
                self.canvas.create_polygon(
                    prev_right, prev_y,
                    prev_right + rb, prev_y,
                    right + rb, y,
                    right, y,
                    fill=rumble_color,
                    outline="",
                )

                # carretera
                self.canvas.create_polygon(
                    prev_left, prev_y,
                    prev_right, prev_y,
                    right, y,
                    left, y,
                    fill=road_color,
                    outline="",
                )

                # líneas de carril
                lane_w0 = (prev_right - prev_left) / LANE_COUNT
                lane_w1 = (right - left) / LANE_COUNT
                for lane in range(1, LANE_COUNT):
                    lx0 = prev_left + lane_w0 * lane
                    lx1 = left + lane_w1 * lane
                    if n % 5 in (0, 1):
                        self.canvas.create_line(lx0, prev_y, lx1, y, fill="#f5f5c8", width=max(1, int(4 * z1)))

                # decoración lejana
                if n % 8 == 0:
                    if s1["scenery"] == "tree":
                        side = -1 if (n // 8) % 2 == 0 else 1
                        tx = left - 40 if side < 0 else right + 40
                        h = 24 + z1 * 35
                        self.canvas.create_polygon(
                            tx, y - h,
                            tx - 12, y,
                            tx + 12, y,
                            fill="#145c2a",
                            outline="",
                        )
                    elif s1["scenery"] == "sign":
                        sx = right + 28
                        self.canvas.create_rectangle(sx - 2, y - 18, sx + 2, y, fill="#dcdcdc", outline="")
                        self.canvas.create_rectangle(sx - 12, y - 30, sx + 12, y - 18, fill="#2d6cdf", outline="")

            prev_left, prev_right, prev_y = left, right, y

    def draw_traffic(self):
        for car in self.traffic:
            rel = car["distance"] - self.distance
            if rel < 20 or rel > 1100:
                continue

            z = rel / 1100.0
            seg = self.get_segment(car["distance"])
            cx_offset = (seg["curve"] + self.camera_curvature) * 0.4
            lane_x = self.lane_to_x(car["lane"])
            scale = 1 - z

            road_w = ROAD_TOP_HALF_WIDTH + (ROAD_BOTTOM_HALF_WIDTH - ROAD_TOP_HALF_WIDTH) * scale
            center_x = WIDTH / 2 + cx_offset * WIDTH * (1 - z)
            car_x = center_x + lane_x * road_w * 0.88
            car_y = ROAD_HORIZON_Y + z * (ROAD_BOTTOM_Y - ROAD_HORIZON_Y)

            w = 18 + scale * 42
            h = 10 + scale * 26

            self.canvas.create_rectangle(car_x - w, car_y - h, car_x + w, car_y + h, fill=car["color"], outline="#222")
            self.canvas.create_rectangle(car_x - w * 0.5, car_y - h * 1.25, car_x + w * 0.5, car_y - h * 0.2, fill="#d8f0ff", outline="")

    def draw_player(self):
        px = WIDTH / 2 + self.player_x * 250
        py = HEIGHT - 85

        body_color = "#16a085"
        self.canvas.create_polygon(
            px - 44, py + 30,
            px + 44, py + 30,
            px + 34, py - 26,
            px - 34, py - 26,
            fill=body_color,
            outline="#0c5344",
            width=2,
        )
        self.canvas.create_polygon(
            px - 24, py - 26,
            px + 24, py - 26,
            px + 15, py - 52,
            px - 15, py - 52,
            fill="#cdeeff",
            outline="#5f6a72",
        )
        # ruedas
        self.canvas.create_rectangle(px - 48, py + 8, px - 38, py + 30, fill="#1a1a1a", outline="")
        self.canvas.create_rectangle(px + 38, py + 8, px + 48, py + 30, fill="#1a1a1a", outline="")

    def draw_hud(self, fps):
        speed_kmh = int(self.speed * 1.2)
        dist = int(self.distance)
        remaining = max(0, int(self.time_left))

        self.canvas.create_rectangle(14, 14, 370, 132, fill="#111111", outline="#2e2e2e", width=2)
        self.canvas.create_text(30, 32, anchor="w", text=f"Velocidad: {speed_kmh:03d} km/h", fill="#f2f2f2", font=("Helvetica", 15, "bold"))
        self.canvas.create_text(30, 58, anchor="w", text=f"Distancia: {dist}/{WORLD_LENGTH} m", fill="#f2f2f2", font=("Helvetica", 13))
        self.canvas.create_text(30, 82, anchor="w", text=f"Tiempo: {remaining:02d} s", fill="#ffe066" if remaining < 15 else "#f2f2f2", font=("Helvetica", 13, "bold"))
        self.canvas.create_text(30, 106, anchor="w", text=f"Puntos: {self.score}", fill="#f2f2f2", font=("Helvetica", 13))

        progress = min(1.0, self.distance / WORLD_LENGTH)
        bar_x0, bar_y0, bar_w, bar_h = 400, 24, 560, 20
        self.canvas.create_rectangle(bar_x0, bar_y0, bar_x0 + bar_w, bar_y0 + bar_h, fill="#1c1c1c", outline="#666")
        self.canvas.create_rectangle(bar_x0 + 2, bar_y0 + 2, bar_x0 + 2 + (bar_w - 4) * progress, bar_y0 + bar_h - 2, fill="#00d084", outline="")

        self.canvas.create_text(WIDTH - 14, HEIGHT - 12, anchor="se", text=f"FPS: {fps:.0f}", fill="#dcdcdc", font=("Helvetica", 10))

        if self.game_over:
            overlay = "#1f1f1f"
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=overlay, stipple="gray50", outline="")
            if self.win:
                title = "¡META CONSEGUIDA!"
                subtitle = f"Has terminado con {self.score} puntos"
                c = "#59ffa8"
            else:
                title = "SE ACABÓ EL TIEMPO"
                subtitle = "Pulsa R para reintentar"
                c = "#ff7b7b"
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 24, text=title, fill=c, font=("Helvetica", 34, "bold"))
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text=subtitle, fill="#f2f2f2", font=("Helvetica", 18))

    def loop(self):
        now = time.perf_counter()
        dt = min(0.045, now - self.last_time)
        self.last_time = now

        self.update(dt)

        self.canvas.delete("all")
        self.draw_background()
        self.draw_road()
        self.draw_traffic()
        self.draw_player()

        if dt > 0:
            self.fps_samples.append(1.0 / dt)
            if len(self.fps_samples) > 30:
                self.fps_samples.pop(0)
        fps = sum(self.fps_samples) / len(self.fps_samples) if self.fps_samples else 0.0
        self.draw_hud(fps)

        if self.running:
            self.root.after(16, self.loop)


def main():
    root = tk.Tk()
    game = CarGame(root)

    def on_close():
        game.running = False
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
