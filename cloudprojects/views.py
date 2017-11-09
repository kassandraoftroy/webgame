# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from poker_engine import Game
from Card_Lookup import card_images, convert
from deuces import Evaluator 
from models import Player, User
import random
import pickle
from operator import itemgetter
import os

evaluator = Evaluator()


def home(request):
	return render(request, "home.html")

def start_game(request):
	rand_char = "! # $ ! # $ ! # $ ! # $ Q W R T Y P S D F G H J K L Z X C V B N M q w r t y p s d f g h j k l z x c v b n m ø µ ç Ω ∆ π ∑".split()
	new_user = User()
	new_user.name = "Player %s%s%s" %(random.choice(rand_char),random.choice(rand_char),random.choice(rand_char))
	new_user.password = "0"
	new_user.roi = 0.0
	new_user.save()
	new_id = Player()
	new_id.turns = 0
	new_id.hands = 0
	new_id.stack = 1000
	new_id.user = new_user
	new_id.save()
	next_turn = 1
	GAME = Game(new_user.name)
	state, variables = GAME.update_game(None)
	with open(os.path.join(os.path.dirname(__file__), "game_%s.p" %new_id.id), "wb") as f:
		pickle.dump(variables, f)
	hand = [card_images[c] for c in state[0]]
	board = [card_images[c] for c in state[1]]
	raises = [2,3,4,5,6,7,8]
	fold = 0
	call = 1
	if state[3] == 0:
		call_button = "check"
		fold_attr = 'silver'
		r_attr = 'silver'
	else:
		call_button = "call"
		fold_attr = 'black'
		r_attr = 'black'
	
	if state[2] < 20:
		p_attr = 'silver'
	else:
		p_attr = 'black'
	context = {"hand":hand, "board":board, "pot":state[2], "to_call":state[3], "hand_num":state[-2], "stack": state[4], "ai_stack":state[6], "messages":state[5], "fold":fold, "call":call, "raise":raises,  "alias":new_id, "next":next_turn, "call_button":call_button, "f_button":fold_attr, "p_button":p_attr, "r_button":r_attr, "user":new_user}
	return render(request, "poker_lobby.html", context)

def play(request, n, bet, turn):
	player = Player.objects.get(id=n) 
	name = player.user.name
	with open(os.path.join(os.path.dirname(__file__), "game_%s.p" %player.id), "rb") as f:
		a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q = pickle.load(f)
	GAME = Game(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q)
	if int(player.turns)+1 == int(turn):
		player.turns += 1
		player.save()
		if int(bet) == 0:
			state, variables = GAME.update_game(0)
		elif int(bet) == 1:
			new_number = GAME.to_call
			state, variables = GAME.update_game(new_number)
		elif int(bet) == 2:
			new_number = GAME.to_call+20
			state, variables = GAME.update_game(new_number)
		elif int(bet)==3:
			new_number = GAME.to_call+30
			state, variables = GAME.update_game(new_number)
		elif int(bet)==4:
			new_number = GAME.to_call+40
			state, variables = GAME.update_game(new_number)
		elif int(bet)==5:
			new_number = GAME.to_call*2
			state, variables = GAME.update_game(new_number)
		elif int(bet)==6:
			new_number = GAME.to_call+GAME.pot*.5
			state, variables = GAME.update_game(new_number)
		elif int(bet)==7:
			new_number = GAME.to_call+GAME.pot
			state, variables = GAME.update_game(new_number)
		elif int(bet)==8:
			new_number = GAME.p1_stack
			state, variables = GAME.update_game(new_number)
		elif int(bet) == 100:
			state, variables = GAME.update_game(None)
	else:
		if GAME.dealer == 1:
			db = True
		else:
			db = False
		state, variables = ((GAME.p1_hand, GAME.board, GAME.pot, GAME.to_call, GAME.p1_stack, GAME.MSGS, GAME.p2_stack, GAME.p2_opp_bet_log, db, GAME.blinds[1], GAME.hand_number, GAME.results), (GAME.p1_name, GAME.p1_stack, GAME.p2_stack, GAME.p1_hand, GAME.p2_hand, GAME.pot, GAME.to_call, GAME.board, GAME.deck, GAME.dealer, GAME.action, GAME.count, GAME.current_phase, GAME.MSGS, GAME.p1_opp_bet_log, GAME.p2_opp_bet_log, GAME.hand_number))

	with open(os.path.join(os.path.dirname(__file__), "game_%s.p" %player.id), "wb") as f:
		pickle.dump(variables, f)	

	if len(state) == 2:
		if state[0] == 100:
			output = "%s WON after %s hands" %(name, state[1])
		elif state[0] == -100:
			output = "%s LOST after %s hands" %(name, state[1])
		else:
			output = "After 100 hands %s averaged %s big blinds" %(name, state[0])
		os.remove(os.path.join(os.path.dirname(__file__), "game_%s.p" %player.id))
		context = {"msg":output, "user":player.user}
		return render(request, "end_game.html", context)


	if state[-1] == False:
		next_turn = player.turns + 1
		hand = [card_images[c] for c in state[0]]
		board = [card_images[c] for c in state[1]]
		raises = [2,3,4,5,6,7,8]
		fold = 0
		call = 1
		try:
			messages = [state[5][-3], state[5][-2], state[5][-1]]
		except:
			messages = [i for i in state[5]]

		if state[3] == 0:
			call_button = "check"
			fold_attr = 'silver'
			r_attr = 'silver'
		else:
			call_button = "call"
			fold_attr = 'black'
			r_attr = 'black'
		
		if state[2] < 20:
			p_attr = 'silver'
		else:
			p_attr = 'black'
		context = {"hand":hand, "board":board, "pot":state[2], "to_call":state[3], "hand_num":state[-2], "stack": state[4], "ai_stack":state[6], "messages":messages, "fold":fold, "call":call, "raise":raises,  "alias":player, "next":next_turn, "call_button":call_button, "f_button":fold_attr, "p_button":p_attr, "r_button":r_attr, "user":player.user}
		return render(request, "poker.html", context)
	else:
		next_turn = player.turns + 1
		hand = [card_images[c] for c in state[0]]
		board = [card_images[c] for c in state[1]]
		cpu_hand = [card_images[c] for c in GAME.p2_hand]

		try:
			messages = [state[8][-2], state[8][-1]]
		except:
			messages = [i for i in state[8]]

		if state[7]==1:
			if state[-3] == True:
				winner = "%s WINS with a" %name, evaluator.class_to_string(evaluator.get_rank_class(evaluator._seven(state[1]+list(state[0]))))
			else:
				winner = "%s WINS" %name, GAME.pot
		elif state[7]==2:
			if state[-3] == True:
				winner = "KASSANDRA WINS with a", evaluator.class_to_string(evaluator.get_rank_class(evaluator._seven(state[1]+list(GAME.p2_hand))))
			else:
				winner = "KASSANDRA WINS", GAME.pot
		elif state[7]==0:
			winner = "tie hand with", evaluator.class_to_string(evaluator.get_rank_class(evaluator._seven(state[1]+list(state[0]))))
		raises = [2,3,4,5,6]
		fold = 0
		call = 1
		if state[3] == 0:
			call_button = "check"
			fold_attr = 'silver'
		else:
			call_button = "call"
			fold_attr = 'black'
		new_hand = 100
		player.hands += 1
		player.stack = int(GAME.p1_stack)
		player.save()
		U = player.user
		U.roi = U.update_roi()
		U.save()
		context = {"hand":hand, "board":board, "cpu_hand":cpu_hand, "winner":winner, "pot":state[2], "to_call":state[3], "hand_num":state[-2], "stack": state[4], "ai_stack":state[6], "messages":messages, "fold":fold, "call":call, "raise":raises,  "alias":player, "next":next_turn, "call_button":call_button, "new_hand":new_hand, "f_button":fold_attr, "user":player.user}
		return render(request, "poker_results.html", context)
	#if bet < current_game.to_call:

def play_again(request, user_id):
	user = User.objects.get(id=user_id)
	new_id = Player()
	new_id.turns = 0
	new_id.hands = 0
	new_id.stack = 1000
	new_id.user = user
	new_id.save()
	next_turn = 1
	GAME = Game(user.name)
	state, variables = GAME.update_game(None)
	with open(os.path.join(os.path.dirname(__file__), "game_%s.p" %new_id.id), "wb") as f:
		pickle.dump(variables, f)
	hand = [card_images[c] for c in state[0]]
	board = [card_images[c] for c in state[1]]
	raises = [2,3,4,5,6,7,8]
	fold = 0
	call = 1
	if state[3] == 0:
		call_button = "check"
		fold_attr = 'silver'
		r_attr = 'silver'
	else:
		call_button = "call"
		fold_attr = 'black'
		r_attr = 'black'
	
	if state[2] < 20:
		p_attr = 'silver'
	else:
		p_attr = 'black'
	context = {"hand":hand, "board":board, "pot":state[2], "to_call":state[3], "hand_num":state[-2], "stack": state[4], "ai_stack":state[6], "messages":state[5], "fold":fold, "call":call, "raise":raises,  "alias":new_id, "next":next_turn, "call_button":call_button, "f_button":fold_attr, "p_button":p_attr, "r_button":r_attr, "user":user}
	return render(request, "poker_lobby.html", context)

def login_lobby(request):
	msg = "Create a User or Sign in"
	context = {"msg": msg}
	return render(request, "login.html", context)

def login_new_user(request):
	name = "%s" %request.POST["new_name"]
	code = request.POST["new_pass"]
	if code == None or code == "":
		code = "0"
	overlap = [i for i in User.objects.all() if i.name==name]
	if len(overlap)==0:
		new_user = User()
		new_user.name = name
		new_user.password = code
		new_user.roi = 0.0
		new_user.save()
		context = {"user":new_user}
		return render(request, "login_success.html",context)
	else:
		msg = "Username is already taken! If yours, log in with other form."
		context = {"msg":msg}
		return render(request, "login.html", context)

def login_user(request):
	name = request.POST["user_name"]
	code = request.POST["user_pass"]
	if code==None or code=="":
		code = "0"
	user = [i for i in User.objects.all() if i.name==name]
	if len(user)==0:
		msg = "Username does not exist! Create a new user with other form."
		context = {"msg":msg}
		return render(request, "login.html", context)
	if code==user[0].password:
		context = {"user":user[0]}
		return render(request, "login_success.html", context)
	else:
		msg = "Password does not match!"
		context = {"msg":msg}
		return render(request, "login.html", context)

def stats(request, user_id):
	this_user = User.objects.get(id=user_id)
	above_200 = []
	above_1000 = []
	above_2500 = []
	my_hands = sum([p.hands for p in Player.objects.all() if p.user==this_user])
	total_hands = 0
	total_games = 0
	rois = 0
	users = 0
	for u in User.objects.all():
		x = u.hands_and_games()
		if x[1] > 0:
			rois += u.roi
			users += 1
		total_hands += x[1]
		total_games += x[0]
		if x[0] > 20 or x[1] > 200:
			if u.roi > 0:
				above_200.append((u.name, u.roi, "green"))
			else:
				above_200.append((u.name, u.roi, "red"))
		if x[0] > 100 or x[1] > 1000:
			if u.roi > 0:
				above_200.append((u.name, u.roi, "green"))
			else:
				above_200.append((u.name, u.roi, "red"))
		if x[0] > 200 or x[1] > 2500:
			if u.roi > 0:
				above_200.append((u.name, u.roi, "green"))
			else:
				above_200.append((u.name, u.roi, "red"))
	Kassandra_ROI = 0 - round(rois/float(users), 3)
	if Kassandra_ROI > 0:
		k_color = "green"
	else:
		k_color = "red"
	gold = sorted(above_2500, key=itemgetter(1), reverse=True)
	silver = sorted(above_1000, key=itemgetter(1), reverse=True)
	bronze = sorted(above_200, key=itemgetter(1), reverse=True)
	if len(gold) >= 10:
		gold = gold[0:10]
	if len(silver) >= 10:
		silver = silver[0:10]
	if len(bronze) >= 10:
		bronze = bronze[0:10]
	level = "NOVICE"
	user_index = "None"
	if (this_user.name, this_user.roi) in bronze:
		level = "BRONZE"
		user_index = silver.index((this_user.name, this_user.roi)) + 1
	if (this_user.name, this_user.roi) in silver:
		level = "SILVER"
		user_index = silver.index((this_user.name, this_user.roi)) + 1
	if (this_user.name, this_user.roi) in gold:
		level = "GOLD"
		user_index = gold.index((this_user.name, this_user.roi)) + 1
	if this_user.roi > 0:
		u_color = "green"
		opposite = "red"
	else:
		u_color = "red"
		opposite = "green"
	opposite_roi = -1*this_user.roi
	context = {"level":level, "user_index":user_index, "gold":gold, "silver":silver, "bronze":bronze, "K_ROI":Kassandra_ROI, "user":this_user, "opp_color":opposite, "opp_roi":opposite_roi, "games_hands":this_user.hands_and_games(), "total_hands":total_hands, "total_games":total_games, "u_color":u_color, "k_color":k_color}
	return render(request, "stats.html", context)
		

