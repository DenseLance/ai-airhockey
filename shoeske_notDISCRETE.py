""" Player module

This is a template/example class for your player.
This is the only file you should modify.

The logic of your hockey robot will be implemented in this class.
Please implement the interface next_move().

The only restrictions here are:
 - to implement a class constructor with the args: paddle_pos, goal_side
 - set self.my_display_name with your team's name, max. 15 characters
 - to implement the function next_move(self, current_state),
    returning the next position of your paddle
"""

# No discrete states (but we round off both states and actions to nearest integer)
# Scoring system uses greedy policy
# Finding best action to take at each state uses thrifty policy
# When using supervised learning to exploit, no need to avg

import copy
import utils
import sqlite3
from random import choice, random
import traceback

class Player:
    def __init__(self, paddle_pos, goal_side):

        # set your team's name, max. 15 chars
        self.my_display_name = "Oi Shoeske"

        # these belong to my solution,
        # you may erase or change them in yours
        self.my_goal = goal_side
        self.my_goal_center = None
        self.opponent_goal_center = None
        self.my_paddle_pos = paddle_pos
        self.paddle_ori_pos = None
        self.ROI = None
        self.puck_towards_opponent = True
        self.start_shooting_position = None

        self.puck_pos = None # state
        self.puck_speed = None # state
        self.next_pos = None # action (dont use this when inserting)
        self.action = None # action (use this when inserting)

        self.goals = {"left": 0, "right": 0}
        self.rewards = {"self_score": 10, "block": 8, "opponent_score": -10} # if score, dont give block reward
##        self.epsilon = self.get_epsilon()
##        self.epsilon_decay = 0.9999

##    def update_epsilon(self, old_epsilon):
##        db = sqlite3.connect("state_action_table.db")
##
##        query = """
##                UPDATE Exploration
##                SET epsilon = ?
##                WHERE my_goal = ?
##                """
##
##        db.execute(query, (old_epsilon * self.epsilon_decay, self.my_goal))
##        db.commit()
##        db.close()

##    def get_epsilon(self):
##        db = sqlite3.connect("state_action_table.db")
##
##        query = """
##                SELECT epsilon
##                FROM Exploration
##                WHERE my_goal = ?
##                """
##
##        result = list(db.execute(query, (self.my_goal, )))[0][0]
##        db.close()
##        
##        return result

    def insert_score(self, reward):
        db = sqlite3.connect("state_action_table.db")

        query = """
                INSERT INTO SAR
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """

        db.execute(query, (self.puck_pos["x"], self.puck_pos["y"], self.puck_speed["x"], self.puck_speed["y"], self.action["x"], self.action["y"], reward))
        db.commit()
        db.close()

##    def select_best_action(self): ## TO BE CHECKED WITH PRINT STATEMENTS
##        db = sqlite3.connect("state_action_table.db")
##
##        query = """
##                SELECT next_pos_x, next_pos_y, AVG(reward) AS avg_reward
##                FROM SAR
##                WHERE puck_pos_x = ?
##                AND puck_pos_y = ?
##                AND puck_speed_x = ?
##                AND puck_speed_y = ?
##                GROUP BY puck_pos_x, puck_pos_y, puck_speed_x, puck_speed_y, next_pos_x, next_pos_y
##                ORDER BY avg_reward DESC
##                """
##
##        result = list(db.execute(query, (self.puck_pos["x"], self.puck_pos["y"], self.puck_speed["x"], self.puck_speed["y"])))
##        db.close()
##
##        if len(result) == 0:
##            return choice(self.ROI)
##        else:
##            if result[0][2] < 0: # not best action as avg_reward in SAR is negative, find alternative
##                bad_actions = []
##                alternative_actions = []
##                for item in result:
##                    bad_actions.append({"x": item[0], "y": item[1]})
##                for point in self.ROI:
##                    if point not in bad_actions:
##                        alternative_actions.append(point)
##                if alternative_actions:
##                    return choice(alternative_actions) # {next_pos_x, next_pos_y}
##
##        return {"x": result[0][0], "y": result[0][1]} # {next_pos_x, next_pos_y}

    def find_points_along_line(self, point_1, point_2): # since puck is big (32 pixels) and GameCore has random movement, we can afford to approximate action spaces
        points = []
        direction_vector = {"x": point_1["x"] - point_2["x"], "y": point_1["y"] - point_2["y"]}
        magnitude = utils.vector_l2norm(direction_vector)
        direction_vector = {key: direction_vector[key] / magnitude for key in direction_vector} # convert to unit vector

        initial_point_2 = point_2.copy()
        while ((point_2["x"] <= point_1["x"]) ^ (initial_point_2["x"] > point_1["x"])) and\
              ((point_2["y"] <= point_1["y"]) ^ (initial_point_2["y"] > point_1["y"])) and\
              ((point_2["x"] >= point_1["x"]) ^ (initial_point_2["x"] < point_1["x"])) and\
              ((point_2["y"] >= point_1["y"]) ^ (initial_point_2["y"] < point_1["y"])):
            points.append({key: int(point_2[key]) for key in point_2})
            point_2 = {key: point_2[key] + direction_vector[key] for key in point_2}
        return points

    def find_center_of_2_points(self, point_1, point_2): # integer as it is faster and easier to compute
        return {"x": (point_1["x"] + point_2["x"]) // 2, "y": (point_1["y"] + point_2["y"]) // 2}

    def next_move(self, current_state):
        """ Function that computes the next move of your paddle

        Implement your algorithm here. This will be the only function
        used by the GameCore. Be aware of abiding all the game rules.

        Returns:
            dict: coordinates of next position of your paddle.
        """
        try:
            # Reset pointers
            if self.goals != current_state["goals"]:
                if (self.my_goal == "left" and current_state["goals"]["left"] > self.goals["left"]) or\
                   (self.my_goal == "right" and current_state["goals"]["right"] > self.goals["right"]):
                    if self.puck_speed: # time violation by opponent does not give reward
                        reward = self.rewards["self_score"]
                        self.insert_score(reward)                        
##                        self.update_epsilon(self.epsilon)
                elif (self.my_goal == "right" and current_state["goals"]["left"] > self.goals["left"]) or\
                     (self.my_goal == "left" and current_state["goals"]["right"] > self.goals["right"]):
                    reward = self.rewards["opponent_score"]
                    self.insert_score(reward)
##                    self.update_epsilon(self.epsilon)
                self.puck_towards_opponent = True
                self.puck_pos = None
                self.puck_speed = None
                self.action = None
                self.goals = current_state["goals"].copy()

            # Computing both goal centers
            if self.my_goal_center == None:
                self.my_goal_center = {"x": 0 if self.my_goal == "left" else current_state["board_shape"][1], "y": current_state["board_shape"][0] / 2}
            if self.opponent_goal_center == None:
                self.opponent_goal_center = {"x": 0 if self.my_goal == "right" else current_state["board_shape"][1], "y": current_state["board_shape"][0] / 2}

            # Computing region of interest (ROI)
            if self.ROI == None:
                ROI_point_1 = {"x": self.my_goal_center["x"], "y": 0.15 * current_state["board_shape"][0]}
                ROI_point_2 = {"x": self.my_goal_center["x"], "y": 0.85 * current_state["board_shape"][0]}
                ROI_point_3 = {"x": current_state["board_shape"][1] * 0.25 if self.my_goal == "left" else current_state["board_shape"][1] * 0.75, "y": current_state["board_shape"][0] / 2}
                self.ROI = self.find_points_along_line(ROI_point_3, ROI_point_1) + self.find_points_along_line(ROI_point_3, ROI_point_2)
                self.start_shooting_position = max(self.ROI, key = lambda point: point["x"]) if self.my_goal == "left" else min(self.ROI, key = lambda point: point["x"])

            # Computing starting position of paddle
            if self.paddle_ori_pos == None: # always return to this position when x direction of puck is towards opponent
                if self.my_goal == "left":
                    self.paddle_ori_pos = {"x": current_state["board_shape"][0] * current_state["goal_size"] / 2 + 1, "y": current_state["board_shape"][0] / 2}
                else:
                    self.paddle_ori_pos = {"x": current_state["board_shape"][1] - current_state["board_shape"][0] * current_state["goal_size"] / 2 - 1, "y": current_state["board_shape"][0] / 2}
                self.paddle_ori_pos = self.find_center_of_2_points(self.paddle_ori_pos, self.start_shooting_position)
                self.next_pos = self.paddle_ori_pos.copy()

            # Update paddle position to match GameCore random movement
            self.my_paddle_pos = current_state["paddle1_pos"] if self.my_goal == "left" else current_state["paddle2_pos"]

            # Hardcode starting shooting position (no need if model already can exploit existing knowledge)
            if abs(current_state["puck_speed"]["x"]) == 0:
                if (self.my_goal == "left" and current_state["puck_pos"]["x"] < current_state["board_shape"][1] / 2) or\
                   (self.my_goal == "right" and current_state["puck_pos"]["x"] > current_state["board_shape"][1] / 2):
                    self.puck_pos = {key: int(current_state["puck_pos"][key]) for key in current_state["puck_pos"]} # state: puck_pos, puck_speed
                    self.puck_speed = {key: int(current_state["puck_speed"][key]) for key in current_state["puck_speed"]}
                    
                    self.next_pos = self.start_shooting_position.copy() # action: next_pos
                    self.action = self.next_pos.copy()
            # Puck is moving towards opponent, move back to original pos
            elif self.puck_towards_opponent == False and ((self.my_goal == "left" and current_state["puck_speed"]["x"] > 0) or (self.my_goal == "right" and current_state["puck_speed"]["x"] < 0)):
                self.puck_towards_opponent = True
                self.next_pos = self.paddle_ori_pos.copy()
            # Puck is moving towards self, take action; insert reward for blocking first
            elif self.puck_towards_opponent == True and ((self.my_goal == "left" and current_state["puck_speed"]["x"] < 0) or (self.my_goal == "right" and current_state["puck_speed"]["x"] > 0)):
                if self.puck_pos and self.puck_speed and self.action:
                    reward = self.rewards["block"]
                    self.insert_score(reward)
##                    self.update_epsilon(self.epsilon)
                
                self.puck_towards_opponent = False
                self.puck_pos = {key: int(current_state["puck_pos"][key]) for key in current_state["puck_pos"]} # state: puck_pos, puck_speed
                self.puck_speed = {key: int(current_state["puck_speed"][key]) for key in current_state["puck_speed"]}

##                self.epsilon = self.get_epsilon()
##                if random() < self.epsilon: # explore
##                    self.next_pos = choice(self.ROI) # action: next_pos
##                else: # exploit
##                    self.next_pos = self.select_best_action() # action: next_pos
                self.next_pos = choice(self.ROI) # action: next_pos
                self.action = self.next_pos.copy()

            # Move to next_pos, taking into account maximum paddle speed
            if self.next_pos != self.my_paddle_pos:
                direction_vector = {"x": self.next_pos["x"] - self.my_paddle_pos["x"], "y": self.next_pos["y"] - self.my_paddle_pos["y"]}
                magnitude = utils.vector_l2norm(direction_vector)
                direction_vector = {key: direction_vector[key] / magnitude for key in direction_vector}

                movement_dist = min(current_state["paddle_max_speed"] * current_state["delta_t"], utils.distance_between_points(self.next_pos, self.my_paddle_pos))
                direction_vector = {key: direction_vector[key] * movement_dist for key in direction_vector}
                new_paddle_pos = {"x": self.my_paddle_pos["x"] + direction_vector["x"],
                                  "y": self.my_paddle_pos["y"] + direction_vector["y"]}

                # Check if computed new position is valid
                if utils.is_inside_goal_area_paddle(new_paddle_pos, current_state) is False and utils.is_out_of_boundaries_paddle(new_paddle_pos, current_state) is None:
                    self.my_paddle_pos = new_paddle_pos

            return self.my_paddle_pos
        except:
            print(traceback.format_exc())
