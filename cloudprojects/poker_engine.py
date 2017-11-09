from deuces import Card, Deck, Evaluator
import random
from Card_Lookup import pocket_class
from decisions import AI
import os
import pickle

evaluator = Evaluator()


class Game:

	def __init__(self, p1_name, p1_stack=1000, p2_stack=1000, p1_hand=[], p2_hand=[], pot=0, to_call=0, board=[], deck=Deck().draw(52), dealer=2, action=0, count=0, current_phase=0, MSGS=[], p1_opp_bet_log=[], p2_opp_bet_log=[], hand_number=0, max_hands=100, p2_decision=AI):

		self.p1_name = p1_name

		self.p2_decision = p2_decision

		self.p1_stack = p1_stack
		self.p2_stack = p2_stack
		self.blinds = (5, 10)
		self.hand_number = hand_number ### random choice to start on hand 1 or hand 0 so that first player on button changes.
		self.max_hands = max_hands

		self.current_phase = current_phase
		self.results = False
		self.showdown_occured = False
		self.MSGS = MSGS
		self.p1_opp_bet_log = p1_opp_bet_log
		self.p2_opp_bet_log = p2_opp_bet_log
		self.p1_hand = p1_hand
		self.p2_hand = p2_hand
		self.pot = pot
		self.board = board
		self.to_call = to_call
		self.deck = deck
		self.action = action
		self.count = count
		self.dealer = dealer


	def update_game(self, new_input_value):
		print "got here"
		if new_input_value == None:
			if self.p1_stack > 0 and self.p2_stack > 0 and self.hand_number<self.max_hands:
				return self.new_hand()
			else:
				return self.end()
		else:
			if new_input_value < self.to_call and new_input_value < self.p1_stack:
				new_input_value = 0
				self.MSGS.append("%s folds." %self.p1_name)
				return self.hand_winner(2)
			else:
				self.count += 1
				self.action = 0
				if new_input_value > self.p1_stack:
					new_input_value = self.p1_stack
				if new_input_value > self.p2_stack + self.to_call:
					new_input_value = self.p2_stack + self.to_call

				if new_input_value == self.to_call:
					if new_input_value == 0:
						self.p2_opp_bet_log.append(("check", 0, len(self.board)))
						self.MSGS.append("%s checks." %self.p1_name)
					else:
						self.p2_opp_bet_log.append(("call", self.to_call, len(self.board)))
						self.MSGS.append("%s calls %s." %(self.p1_name, sum([n[1] for n in self.p2_opp_bet_log if n[2]==len(self.board)])))
					self.to_call = 0
					self.p1_stack = self.p1_stack - new_input_value
					self.pot = self.pot + new_input_value
					if self.count > 1:
						self.current_phase += 1
						self.count = 0
						self.action = (self.dealer + 1)%2
				elif new_input_value > self.to_call:
					if self.to_call != 0:
						self.p2_opp_bet_log.append(("call", self.to_call, len(self.board)))
						self.p2_opp_bet_log.append(("bet", new_input_value - self.to_call, len(self.board)))
						self.MSGS.append("%s raises to %s." %(self.p1_name, sum([n[1] for n in self.p2_opp_bet_log if n[2]==len(self.board)])))
					else:
						self.p2_opp_bet_log.append(("bet", new_input_value - self.to_call, len(self.board)))
						if len(self.board) == 0:
							self.MSGS.append("%s raises to %s." %(self.p1_name, sum([n[1] for n in self.p2_opp_bet_log if n[2]==len(self.board)])))
						else:	
							self.MSGS.append("%s bets %s." %(self.p1_name, sum([n[1] for n in self.p2_opp_bet_log if n[2]==len(self.board)])))						
					self.p1_stack = self.p1_stack - new_input_value
					self.to_call = new_input_value - self.to_call
					self.pot = self.pot + new_input_value
				if self.current_phase == 1:
					return self.phase_1()
				if self.current_phase == 2:
					return self.phase_2()
				if self.current_phase == 3:
					return self.phase_3()
				if self.current_phase == 4:
					return self.phase_4()
				if self.current_phase == 5:
					return self.showdown()


	def new_hand(self): ### reset hand information at the top of the hand: post blinds, find dealer, shuffle deck.
		self.p1_hand = []
		self.p2_hand = []
		self.board = []
		self.MSGS = []
		self.pot = 0 
		self.results = False
		self.showdown_occured = False
		self.hand_number += 1
		if self.p1_stack > self.blinds[1] and self.p2_stack > self.blinds[1]:
			if self.hand_number%2 == 0:
				self.p2_stack = self.p2_stack - self.blinds[0]
				self.p1_stack = self.p1_stack - self.blinds[1]
				self.dealer = 2
				self.p2_opp_bet_log = [("blind", 10, 0)]
				self.p1_opp_bet_log = [("blind", 5, 0)]
				self.MSGS.append("Kassandra posts 5. (Dealer)")
				self.MSGS.append("%s posts 10." %self.p1_name)
			else:
				self.p1_stack = self.p1_stack - self.blinds[0]
				self.p2_stack = self.p2_stack - self.blinds[1]
				self.dealer = 1
				self.p1_opp_bet_log = [("blind", 10, 0)]
				self.p2_opp_bet_log = [("blind", 5, 0)]
				self.MSGS.append("%s posts 5. (Dealer)" %self.p1_name)
				self.MSGS.append("Kassandra posts 10.")
			self.pot = self.blinds[0] + self.blinds[1]
			self.to_call = self.blinds[0]
		else:
			if self.p1_stack <= self.blinds[1]:
				self.pot = self.p1_stack*2
				self.p2_stack = self.p2_stack - self.p1_stack
				self.p1_stack = 0
			elif self.p2_stack <= self.blinds[1]:
				self.pot = self.p2_stack*2
				self.p1_stack = self.p1_stack - self.p2_stack
				self.p2_stack = 0
		self.deck = Deck().draw(52)
		random.shuffle(self.deck)
		self.action = self.dealer%2
		self.count = 0
		return self.phase_1()

	def phase_1(self):
		self.current_phase = 1
		self.p1_hand = self.deck[0:2]
		self.p2_hand = self.deck[2:4]
		if (self.p1_stack == 0 or self.p2_stack == 0) and self.to_call == 0:
			return self.phase_2()
		else:
			if self.to_call > 0 or self.count <3:
				if self.action == 1:
					return self.bet_out()
				if self.action == 0:
					return self.bet_in()
			else:
				self.action = (self.dealer + 1)%2
				self.count = 0
				return self.phase_2()

	def phase_2(self):
		self.current_phase = 2
		if len(self.board)==0:
			self.board = self.deck[4:7]
			self.MSGS.append("see FLOP")
		if (self.p1_stack == 0 or self.p2_stack == 0) and self.to_call == 0:
			return self.phase_3()
		else:
			if self.to_call > 0 or self.count <3:
				if self.action == 1:
					return self.bet_out()
				if self.action == 0:
					return self.bet_in()
			else:
				self.action = (self.dealer + 1)%2
				self.count = 0
				return self.phase_3()


	def phase_3(self):
		self.current_phase = 3
		if len(self.board) == 3:
			self.board = self.deck[4:8]
			self.MSGS.append("see TURN")
		if (self.p1_stack == 0 or self.p2_stack == 0) and self.to_call == 0:
			return self.phase_4()
		else:
			if self.to_call > 0 or self.count <3:
				if self.action == 1:
					return self.bet_out()
				if self.action == 0:
					return self.bet_in()
			else:
				self.action = (self.dealer + 1)%2
				self.count = 0
				return self.phase_4()

	def phase_4(self):
		self.current_phase = 4
		if len(self.board) == 4:
			self.board = self.deck[4:9]
			self.MSGS.append("see RIVER")
		if (self.p1_stack == 0 or self.p2_stack == 0) and self.to_call == 0:
			return self.showdown()
		else:
			if self.to_call > 0 or self.count < 3:
				if self.action == 1:
					return self.bet_out()
				if self.action == 0:
					return self.bet_in()
			else:
				return self.showdown()

	def showdown(self):      ### deal next phase of game, then move on to betting. In final phase, evaluate showdown!
		self.showdown_occured = True
		p1_score = evaluator._seven(self.p1_hand+self.board)
		p2_score = evaluator._seven(self.p2_hand+self.board)
		if p1_score < p2_score:
			return self.hand_winner(1)
		elif p1_score > p2_score:
			return self.hand_winner(2)
		elif p1_score == p2_score:
			return self.hand_winner(0)

	def bet_out(self):
		print "my turn"
		if self.dealer == 1:
			dealer = True
		else:
			dealer = False

		self.STATE = ((self.p1_hand, self.board, self.pot, self.to_call, self.p1_stack, self.MSGS, self.p2_stack, self.p2_opp_bet_log, dealer, self.blinds[1], self.hand_number, self.results), (self.p1_name, self.p1_stack, self.p2_stack, self.p1_hand, self.p2_hand, self.pot, self.to_call, self.board, self.deck, self.dealer, self.action, self.count, self.current_phase, self.MSGS, self.p1_opp_bet_log, self.p2_opp_bet_log, self.hand_number))
		return self.STATE

	def bet_in(self):
		print "cpu turn"

		if self.dealer == 2:
			dealer = True
		else:
			dealer = False

		bet = int(self.p2_decision(self.p2_hand, self.board, self.p2_stack, self.p1_stack, self.blinds[1], self.to_call, self.pot, dealer, self.p2_opp_bet_log, ""))
		if bet > self.p1_stack + self.to_call:   ### adjust bet size if it puts other opp all in
			bet = self.p1_stack + self.to_call

		if bet == 0 and self.to_call == 0:
			self.p1_opp_bet_log.append(("check", 0, len(self.board)))
			self.MSGS.append("Kassandra checks.")
		if bet > 0 and self.to_call == bet:
			self.p1_opp_bet_log.append(("call", self.to_call, len(self.board)))
			self.MSGS.append("Kassandra calls %s." %sum([n[1] for n in self.p1_opp_bet_log if n[2]==len(self.board)]))
		if bet > 0 and self.to_call == 0:
			self.p1_opp_bet_log.append(("bet", bet, len(self.board)))
			if len(self.board) == 0:
				self.MSGS.append("Kassandra raises to %s." %sum([n[1] for n in self.p1_opp_bet_log if n[2]==len(self.board)]))
			else:
				self.MSGS.append("Kassandra bets %s." %sum([n[1] for n in self.p1_opp_bet_log if n[2]==len(self.board)]))
		if bet > 0 and self.to_call != 0 and bet>self.to_call:
			self.p1_opp_bet_log.append(("call", self.to_call, len(self.board)))
			self.p1_opp_bet_log.append(("bet", bet-self.to_call, len(self.board)))
			self.MSGS.append("Kassandra raises to %s." %sum([n[1] for n in self.p1_opp_bet_log if n[2]==len(self.board)]))
		
		if self.to_call > bet:  ### to_call negative so someone took the pot
			self.showdown_occured=False
			self.MSGS.append("Kassandra folds.")
			return self.hand_winner(1)

		self.to_call = bet - self.to_call

		self.p2_stack = self.p2_stack - bet  ### take bet out of player stack
		self.pot = self.pot + bet   ### add bet to pot

		self.action = (self.action+1)%2
		self.count += 1

		if self.to_call == 0 and self.count>1:  ### to_call balanced so time to deal next card
			self.action = (self.dealer + 1)%2
			self.count = 0
			if self.current_phase == 1:
				return self.phase_2()
			if self.current_phase == 2:
				return self.phase_3()
			if self.current_phase == 3:
				return self.phase_4()
			if self.current_phase == 4:
				return self.showdown()
		else:
			if self.current_phase == 1:
				return self.phase_1()
			if self.current_phase == 2:
				return self.phase_2()
			if self.current_phase == 3:
				return self.phase_3()
			if self.current_phase == 4:
				return self.phase_4()		


	def hand_winner(self, num):
		### pass the pot to the winner of the hand (or split).
		self.results = True
		if num == 1:           
			self.p1_stack = self.p1_stack + self.pot
		elif num == 2:
			self.p2_stack = self.p2_stack + self.pot
		elif num == 0:
			self.p1_stack = self.p1_stack + (self.pot/2.0)
			self.p2_stack = self.p2_stack + (self.pot/2.0)
		self.STATE = ((self.p1_hand, self.board, self.pot, self.to_call, self.p1_stack, self.p2_hand, self.p2_stack, num, self.MSGS, self.showdown_occured, self.hand_number, self.results), (self.p1_name, self.p1_stack, self.p2_stack, self.p1_hand, self.p2_hand, self.pot, self.to_call, self.board, self.deck, self.dealer, self.action, self.count, self.current_phase, self.MSGS, self.p1_opp_bet_log, self.p2_opp_bet_log, self.hand_number))
		return self.STATE


	def end(self):         #### end of game -- locate winner, output collected stats
		self.output = [(self.p1_stack - 1000)/self.blinds[1], self.hand_number]
		return (self.output, True)