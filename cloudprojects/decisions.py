from deuces import Card, Deck, Evaluator
import random
from Card_Lookup import pocket_class, pocket_rank
import os
import pickle
from itertools import combinations
from operator import itemgetter
import boto3
import time
import botocore

with open(os.path.join(os.path.dirname(__file__), 'k1.txt')) as f:
	ids = f.read().strip()
with open(os.path.join(os.path.dirname(__file__), 'k2.txt')) as f:
	keys = f.read().strip()

s3 = boto3.resource('s3', aws_access_key_id=ids, aws_secret_access_key=keys)


evaluator = Evaluator()
all_holes = list(combinations(Deck().draw(52), 2))
all_holes = [frozenset(i) for i in all_holes]

def AI(hand, board, stack, BB, to_call, pot, dealer, bets, VARIABLES):
	
	if len(board) == 0:
		return preflop_decision(hand, board, stack, BB, to_call, pot, dealer, bets)
	
	if len(board) == 3:
		name = "".join(sorted([Card.int_to_str(c) for c in board], key=str.lower))
		KEY = "flop_charts/%s.p" %name
		try:
			print "downloading file"
			s3.Bucket("chartsflopturn").download_file(KEY, os.path.join(os.path.dirname(__file__), 'currentflop.p'))
			print "found and downloaded file"
			with open(os.path.join(os.path.dirname(__file__), 'currentflop.p'), "rb") as f:
				board_rankings = pickle.load(f)
				board_rankings = [i[0] for i in board_rankings]
		except:
			print "pickle loading error!"
			return int(0)
	
	if len(board)==4:
		board_rankings = generate_turn_rankings(board)
		board_rankings = [i[0] for i in board_rankings]
	
	if len(board)==5:
		board_rankings = generate_river_rankings(board)
		board_rankings = [i[0] for i in board_rankings]

	fixed_board_rankings = [i for i in board_rankings if (len(i&set(hand))==0 and len(i&set(board))==0) or (i==frozenset(hand))]
	my_hand_percentile = 1 - (fixed_board_rankings.index(frozenset(hand))/float(len(fixed_board_rankings)))

	strong_bets = len([o for o in bets if o[0]=="bet" and o[1]>BB*3])
	very_strong_bets = len([o for o in bets if o[0]=="bet" and o[1]>pot/2.5 and o[2]>0])
	strong_calls = len([o for o in bets if o[0]=="call" and o[1]>BB*3])
	checks = len([o for o in bets if o[0]=="check"])

	if very_strong_bets > 0:
		V_strength = max(1.0 + strong_bets + strong_calls + very_strong_bets, 1.0)
	else:
		V_strength = max(1.0 + strong_bets + strong_calls - checks, 1.0)

	if to_call > 25*BB:
		V_strength += 2

	if to_call == (2000-stack):
		if len(board)<=3 or pot/1.4 < to_call:
			V_strength += 2
		else:
			V_strength += 1

	if len(board) < 5:

		if to_call > 0:
			EV_CALL = (my_hand_percentile**V_strength)*pot - (1-my_hand_percentile**V_strength)*to_call
			if EV_CALL > 0:
				if EV_CALL > pot/2.0:
					if random.random() > .5:
						return to_call
					else:
						return min(stack, random.choice([to_call+pot/2.0, to_call+pot]))
				elif pot/2.0 >= EV_CALL > pot/3.5:
					return min(stack, to_call+pot)
				else:
					return to_call
			elif to_call<stack/3.0:
				if V_strength < 3:
					if random.random()>.66:
						return min(stack, random.choice([to_call+pot/2.0, to_call+pot]))
				elif V_strength < 5:
					if random.random()>.85:
						return min(stack, random.choice([to_call+pot/2.0, to_call+pot]))
				return int(0)
			return int(0)

		if to_call == 0:
			if dealer == True:
				if my_hand_percentile**V_strength > .8 and len(board) == 3:
					return int(0)
				if my_hand_percentile**V_strength > .66:
					return min(max(pot/2.0, BB*3), stack)
				elif V_strength < 4 and random.random() > .5:
					return min(max(pot/2.0, BB*3), stack)
			else:
				if my_hand_percentile**V_strength > .8:
					return int(0)
				elif my_hand_percentile**V_strength > .66:
					return min(max(pot/2.0, BB*3), stack)
				elif V_strength < 4 and random.random() > .75:
					return min(max(pot/2.0, BB*3), stack)
			return int(0)
	else:
		if my_hand_percentile**V_strength > .95:
			return stack

		if to_call > 0:
			EV_CALL = (my_hand_percentile**V_strength)*pot - (1-my_hand_percentile**V_strength)*to_call
			if EV_CALL > 0:
				if EV_CALL > pot/1.2:
					return min(stack, pot*2+to_call)
				if EV_CALL > pot/2.0:
					return min(stack, random.choice([to_call+pot/2.0, to_call+pot]))
				else:
					return to_call
			if to_call < stack/4.0 and to_call < (2000-stack)/4.0 and strong_bets < 3:
				if random.random() > .15:
					return min(stack, to_call*3)
			return int(0)
		elif to_call == 0:
			if dealer == True:
				if my_hand_percentile**V_strength > .65:
					return min(max(pot/2.0, 6*BB), stack/4.0)
			else:
				if my_hand_percentile**V_strength > .8:
					return min(max(pot/2.0, 6*BB), stack/4.0)
			return int(0)

		return int(0)




	#EV_RAISE_HALF = P_vf*pot + P_vc*(P_hw*(pot*1.5) - P_hl*(pot*0.5+to_call))
	#EV_RAISE_POT = P_vf*pot + P_vc*(P_hw*(pot*2) - P_hl*(pot+to_call))



def preflop_decision(hand, board, stack, BB, to_call, pot, dealer, bets, VARS=[.35, .5, .25, .1]):

	STAT_VARS = VARS
	rank = pocket_class[frozenset(hand)]

	raises = len([o for o in bets if o[0]=="bet"])

	if dealer == True:
		if to_call <= BB/2.0:
			if 5 < rank < 8:
				if random.random() < STAT_VARS[0] and stack > 50*BB:
					return min(stack, to_call+BB*random.choice([2,2,3,3,4,5]))
				else:
					return to_call
			if rank <= 5:
				return min(stack, to_call+BB*random.choice([2,3,4,4,5,5]))
		else:
			if raises == 1:
				if rank >= 6:
					if to_call <= 5*BB and (rank==6 or random.random() > STAT_VARS[1]):
						return to_call
					else:
						return int(0)
				if 3 < rank < 6:
					if to_call < stack/2.5:
						return to_call
					elif stack < 50*BB:
						return stack
				if rank == 3:
					if to_call <= stack/4:
						return min(stack, to_call*random.choice([2,2.5,3,pot/float(to_call)]))
					if to_call <= stack/2.0:
						return to_call
					elif stack < 80*BB:
						return to_call
				if rank <= 2:
					if to_call < stack/3.0:
						return min(stack, to_call*random.choice([2,2.5,3,pot/float(to_call)]))
					else:
						return to_call
			if raises >= 2:
				if rank >= 6:
					return int(0)
				else:
					if pocket_rank[frozenset(hand)] < 5 or stack<12*BB:
						return stack
					else:
						if to_call < stack/2.5:
							return to_call
						elif rank < 3:
							return to_call
						elif rank < 5 and stack < 40*BB:
							return stack
						elif rank < 4 and stack < 70*BB:
							return stack
						else:
							return int(0)

	else:
		if to_call == 0:
			if rank <= 5:
				return min(stack, BB*random.choice([2,3,4,5]))
			elif random.random() < STAT_VARS[2] and stack > 60*BB:
				return min(stack, BB*random.choice([2,3,4,5]))
			else:
				return int(0)
		if to_call > 0:
			if raises == 1:
				if rank >= 6:
					if to_call <= 5*BB and (rank == 6 or random.random() > STAT_VARS[3]):
						return to_call
					else:
						return int(0)
				if 3 < rank < 6:
					if to_call < stack/3.0:	
						return to_call
					elif stack < 50*BB:
						return stack
					else:
						return int(0)
				if rank == 3:
					if to_call <= stack/2.0:
						return to_call
					elif stack<80*BB:
						return stack
				if rank <= 3:
					return min(stack, to_call*random.choice([2,2.5,3,pot/float(to_call)]))
			if raises >= 2:
				if rank >= 5:
					return int(0)
				else:
					if pocket_rank[frozenset(hand)] < 5 or stack<12*BB:
						return stack
					else:
						if to_call < stack/3.5:
							return to_call
						elif to_call < stack/2.5 and rank < 4:
							return to_call
						elif rank < 3:
							return to_call
						elif rank<5 and stack < 40*BB:
							return stack
						elif rank < 4 and stack < 70*BB:
							return stack
						else:
							return int(0)
	return int(0)

def generate_turn_rankings(board):
	ranked_hands = []
	possibles = [i for i in all_holes if len(i&set(board))==0]
	for h in possibles:
		new_hand = list(h)
		cards_left = [[i] for i in Deck().draw(52) if i not in (list(board)+list(new_hand))]
		avg_rank = sum([evaluator._seven(new_hand+board+i) for i in cards_left])/len(cards_left)
		ranked_hands.append((h, avg_rank))
	out = sorted(ranked_hands, key=itemgetter(1))
	return out

def generate_river_rankings(board):
	ranked_hands = []
	possibles = [i for i in all_holes if len(i&set(board))==0]
	for h in possibles:
		new_hand = list(h)
		rank = evaluator._seven(new_hand+board)
		ranked_hands.append((h, rank))
	out = sorted(ranked_hands, key=itemgetter(1))
	return out

