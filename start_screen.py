import pygame
import logging

class StartScreenManager:
    def __init__(self, screen, offset_x, offset_y, WIDTH, HEIGHT):
        self.screen = screen
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

        self.font = pygame.font.SysFont(None, 32)
        self.selected_agent_ai1 = "MCTS"
        self.selected_agent_ai2 = "MCTS"
        self.game_mode = "human_vs_ai"
        self.previous_game_mode = self.game_mode

        self.input_boxes = {
            "iterations_ai1": InputBox(offset_x + 150, offset_y + 280, 100, 30, font=self.font),
            "iterations_ai2": InputBox(offset_x + 150, offset_y + 400, 100, 30, font=self.font)
        }

        self.buttons = {
            "human_vs_ai": pygame.Rect(offset_x + 100, offset_y + 160, 20, 20),
            "ai_vs_ai": pygame.Rect(offset_x + 300, offset_y + 160, 20, 20),
            "start": pygame.Rect(WIDTH // 2 - 75, HEIGHT - 100, 150, 50)
        }

    def draw_radio_button(self, label, x, y, selected):
        color = (0, 200, 0) if selected else (200, 200, 200)
        pygame.draw.circle(self.screen, color, (x, y), 10)
        pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 10, 2)
        text = pygame.font.SysFont("Arial", 24).render(label, True, (255, 255, 255))
        self.screen.blit(text, (x + 20, y - 12))

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.screen.blit(self.font.render("Select Game Mode:", True, (255, 255, 255)),
                         (self.offset_x + 100, self.offset_y + 120))

        self.draw_radio_button("Human vs AI", self.buttons["human_vs_ai"].x + 10,
                               self.buttons["human_vs_ai"].y + 10, self.game_mode == "human_vs_ai")
        self.draw_radio_button("AI vs AI", self.buttons["ai_vs_ai"].x + 10,
                               self.buttons["ai_vs_ai"].y + 10, self.game_mode == "ai_vs_ai")

        agents = ["MCTS", "Expectimax", "Markov"]
        for i, agent in enumerate(agents):
            bx = self.offset_x + 120 + i * 150
            selected1 = (agent == self.selected_agent_ai1)
            self.draw_radio_button(agent, bx, self.offset_y + 230, selected1)

            if self.game_mode == "ai_vs_ai":
                selected2 = (agent == self.selected_agent_ai2)
                self.draw_radio_button(agent, bx, self.offset_y + 350, selected2)
                self.screen.blit(self.font.render("Iterations AI 2:", True, (255, 255, 255)),
                                 (self.offset_x - 10, self.offset_y + 400))

        self.screen.blit(self.font.render("Iterations AI 1:", True, (255, 255, 255)),
                         (self.offset_x - 10, self.offset_y + 280))

        self.input_boxes["iterations_ai1"].draw(self.screen)
        if self.game_mode == "ai_vs_ai":
            self.input_boxes["iterations_ai2"].draw(self.screen)

        pygame.draw.rect(self.screen, (0, 255, 0), self.buttons["start"])
        self.screen.blit(self.font.render("Start", True, (0, 0, 0)),
                         (self.buttons["start"].x + 40, self.buttons["start"].y + 10))

        if self.game_mode != self.previous_game_mode:
            logging.debug(f"[WARNING] game_mode changed in draw from {self.previous_game_mode} to {self.game_mode}")
        self.previous_game_mode = self.game_mode

    def handle_event(self, event):
        for box in self.input_boxes.values():
            box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if self.buttons["human_vs_ai"].collidepoint(event.pos):
                self.game_mode = "human_vs_ai"
                logging.debug("Game mode set to Human vs AI")

            elif self.buttons["ai_vs_ai"].collidepoint(event.pos):
                self.game_mode = "ai_vs_ai"
                logging.debug("Game mode set to AI vs AI")

            agents = ["MCTS", "Expectimax", "Markov"]
            for i, agent in enumerate(agents):
                bx = self.offset_x + 120 + i * 150
                ry1 = self.offset_y + 230
                ry2 = self.offset_y + 350

                if bx - 10 <= x <= bx + 10:
                    if ry1 - 10 <= y <= ry1 + 10:
                        self.selected_agent_ai1 = agent
                    elif self.game_mode == "ai_vs_ai" and ry2 - 10 <= y <= ry2 + 10:
                        self.selected_agent_ai2 = agent

            if self.buttons["start"].collidepoint(event.pos):
                return {
                    "game_mode": self.game_mode,
                    "selected_agent_ai1": self.selected_agent_ai1,
                    "selected_agent_ai2": self.selected_agent_ai2,
                    "iterations_ai1": self.input_boxes["iterations_ai1"].get_value(),
                    "iterations_ai2": self.input_boxes["iterations_ai2"].get_value(),
                    "current_player": "Human" if self.game_mode == "human_vs_ai" else "AI1"
                }

        return None