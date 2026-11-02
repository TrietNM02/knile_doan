import json
import os
import pygame

SAVE_FILE_PATH = "savegame.json"

class SaveManager:
    @staticmethod
    def save_game(player, level=None, current_level_index=1):
        """Lưu chính xác thông số Player & Enemy"""
        if not player:
            return False

        # 1. Lưu thông tin Player (Bao gồm steps và skill_slots)
        player_data = {
            "health": player.health,
            "energy": player.energy,
            "pos_x": player.pos.x,
            "pos_y": player.pos.y,
            "steps": getattr(player, "steps", getattr(player, "step_count", 0)),
            "exp": getattr(player, "exp", 0),
            "skill_points": getattr(player, "skill_points", 0),
            # Lưu cấu trúc skill slots (chứa string hoặc list các skill)
            "skill_slots": getattr(player, "skill_slots", {}),
            "unlocked_active_skills": list(getattr(player, "unlocked_active_skills", set())),
            "unlocked_skill_nodes": list(getattr(player, "unlocked_skill_nodes", {'root'}))
        }

        # 2. Lưu thông tin Enemy
        enemies_data = []
        if level and hasattr(level, 'enemy_sprites'):
            for enemy in level.enemy_sprites.sprites():
                is_alive = enemy.alive() if callable(getattr(enemy, 'alive', None)) else getattr(enemy, 'alive', True)
                if is_alive:
                    tile_size = getattr(enemy, 'tile_size', 48)
                    
                    if hasattr(enemy, 'hitbox'):
                        cx, cy = enemy.hitbox.centerx, enemy.hitbox.centery
                    else:
                        cx, cy = enemy.rect.centerx, enemy.rect.centery

                    gx = getattr(enemy, 'grid_x', int(cx // tile_size))
                    gy = getattr(enemy, 'grid_y', int(cy // tile_size))

                    enemies_data.append({
                        "name": getattr(enemy, 'monster_name', getattr(enemy, 'name', 'slime')),
                        "grid_x": gx,
                        "grid_y": gy,
                        "pos_x": cx,
                        "pos_y": cy,
                        "health": getattr(enemy, 'health', getattr(enemy, 'hp', 10))
                    })

        save_data = {
            "level": current_level_index,
            "player": player_data,
            "enemies": enemies_data
        }
        
        try:
            with open(SAVE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            print("[SAVE]: Lưu Game, Map, Bước đi & Skill Slots thành công!")
            return True
        except Exception as e:
            print(f"[SAVE ERROR]: {e}")
            return False

    @staticmethod
    def load_game():
        if not os.path.exists(SAVE_FILE_PATH):
            return None
        try:
            with open(SAVE_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[LOAD ERROR]: {e}")
            return None

    @staticmethod
    def apply_save_to_level(level, save_data):
        if not level or not save_data:
            return

        player_data = save_data.get('player')
        player = getattr(level, 'player', None)

        # --- 1. KHÔI PHỤC PLAYER ---
        if player and player_data:
            player.health = min(player.max_health, player_data.get("health", player.health))
            player.energy = min(player.max_energy, player_data.get("energy", player.energy))
            
            saved_steps = player_data.get("steps", 0)
            if hasattr(player, 'steps'):
                player.steps = saved_steps
            if hasattr(player, 'step_count'):
                player.step_count = saved_steps

            if hasattr(player, 'exp'): player.exp = player_data.get("exp", player.exp)
            if hasattr(player, 'skill_points'): player.skill_points = player_data.get("skill_points", player.skill_points)

            if "pos_x" in player_data and "pos_y" in player_data:
                px = float(player_data["pos_x"])
                py = float(player_data["pos_y"])

                player.pos = pygame.math.Vector2(px, py)
                player.target_pos = pygame.math.Vector2(px, py)
                player.is_moving = False
                player.direction = pygame.math.Vector2()

                player.hitbox.center = (round(px), round(py))
                player.rect.centerx = player.hitbox.centerx
                player.rect.bottom = player.hitbox.bottom

            # 🟢 KHÔI PHỤC SKILL SLOTS (Chuyển key "1", "2"... trong JSON về lại số int 1, 2...)
            if "skill_slots" in player_data and hasattr(player, 'skill_slots'):
                raw_slots = player_data["skill_slots"]
                player.skill_slots = {int(k): v for k, v in raw_slots.items()}

            if "unlocked_active_skills" in player_data and hasattr(player, 'unlocked_active_skills'):
                player.unlocked_active_skills = set(player_data["unlocked_active_skills"])
            if "unlocked_skill_nodes" in player_data and hasattr(player, 'unlocked_skill_nodes'):
                player.unlocked_skill_nodes = set(player_data["unlocked_skill_nodes"])

        # --- 2. CẬP NHẬT TRẠNG THÁI QUÁI ---
        enemies_data = save_data.get('enemies')
        if enemies_data is not None and hasattr(level, 'enemy_sprites'):
            tile_size = 48
            saved_enemies = []
            
            for e in enemies_data:
                name = e.get("name", "slime")
                hp = e.get("health", 10)
                px = e.get("pos_x", 0)
                py = e.get("pos_y", 0)
                
                if "grid_x" in e and "grid_y" in e:
                    gx, gy = e["grid_x"], e["grid_y"]
                else:
                    gx = int(px // tile_size)
                    gy = int(py // tile_size)
                    
                saved_enemies.append({"name": name, "gx": gx, "gy": gy, "px": px, "py": py, "hp": hp})
            
            for enemy in level.enemy_sprites.sprites()[:]:
                e_tile_size = getattr(enemy, 'tile_size', tile_size)
                e_name = getattr(enemy, 'monster_name', getattr(enemy, 'name', 'slime'))
                
                cx = enemy.hitbox.centerx if hasattr(enemy, 'hitbox') else enemy.rect.centerx
                cy = enemy.hitbox.centery if hasattr(enemy, 'hitbox') else enemy.rect.centery
                
                gx = getattr(enemy, 'grid_x', int(cx // e_tile_size))
                gy = getattr(enemy, 'grid_y', int(cy // e_tile_size))
                
                is_boss = "boss" in e_name.lower() or getattr(enemy, 'is_boss', False)
                tolerance = 6 if is_boss else 3 

                matched_index = -1
                for i, s_enemy in enumerate(saved_enemies):
                    if s_enemy["name"] == e_name and abs(s_enemy["gx"] - gx) <= tolerance and abs(s_enemy["gy"] - gy) <= tolerance:
                        matched_index = i
                        break
                
                if matched_index == -1 and is_boss:
                    for i, s_enemy in enumerate(saved_enemies):
                        if s_enemy["name"] == e_name:
                            matched_index = i
                            break

                if matched_index != -1:
                    s_data = saved_enemies[matched_index]
                    
                    if hasattr(enemy, 'health'): enemy.health = s_data["hp"]
                    elif hasattr(enemy, 'hp'): enemy.hp = s_data["hp"]

                    new_x = float(s_data["px"])
                    new_y = float(s_data["py"])

                    if hasattr(enemy, 'pos'):
                        enemy.pos.x = new_x
                        enemy.pos.y = new_y
                    if hasattr(enemy, 'target_pos'):
                        enemy.target_pos.x = new_x
                        enemy.target_pos.y = new_y
                    if hasattr(enemy, 'is_moving'):
                        enemy.is_moving = False

                    if hasattr(enemy, 'hitbox'):
                        enemy.hitbox.center = (round(new_x), round(new_y))
                        if hasattr(enemy, 'rect'):
                            enemy.rect.centerx = enemy.hitbox.centerx
                            enemy.rect.bottom = enemy.hitbox.bottom
                    elif hasattr(enemy, 'rect'):
                        enemy.rect.center = (round(new_x), round(new_y))

                    saved_enemies.pop(matched_index)
                else:
                    enemy.kill()