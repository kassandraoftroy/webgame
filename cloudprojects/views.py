# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from poker_engine import Game
from Card_Lookup import card_images, convert
from deuces import Evaluator 
from models import Player, User
import random
import zipfile
from operator import itemgetter
import os

evaluator = Evaluator()
games = {}


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
	games[new_id.id] = Game(new_user.name)
	state = games[new_id.id].update_game(None)
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
	if int(player.turns)+1 == int(turn):
		player.turns += 1
		player.save()
		if int(bet) == 0:
			state = games[player.id].update_game(0)
		elif int(bet) == 1:
			new_number = games[player.id].to_call
			state = games[player.id].update_game(new_number)
		elif int(bet) == 2:
			new_number = games[player.id].to_call+20
			state = games[player.id].update_game(new_number)
		elif int(bet)==3:
			new_number = games[player.id].to_call+30
			state = games[player.id].update_game(new_number)
		elif int(bet)==4:
			new_number = games[player.id].to_call+40
			state = games[player.id].update_game(new_number)
		elif int(bet)==5:
			new_number = games[player.id].to_call*2
			state = games[player.id].update_game(new_number)
		elif int(bet)==6:
			new_number = games[player.id].to_call+games[player.id].pot*.5
			state = games[player.id].update_game(new_number)
		elif int(bet)==7:
			new_number = games[player.id].to_call+games[player.id].pot
			state = games[player.id].update_game(new_number)
		elif int(bet)==8:
			new_number = games[player.id].p1_stack
			state = games[player.id].update_game(new_number)
		elif int(bet) == 100:
			state = games[player.id].update_game(None)
	else:
		state = games[player.id].STATE

	if len(state) == 2:
		if state[0] == 100:
			output = "%s WON after %s hands" %(name, state[1])
		elif state[0] == -100:
			output = "%s LOST after %s hands" %(name, state[1])
		else:
			output = "After 100 hands %s averaged %s big blinds" %(name, state[0])
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
		cpu_hand = [card_images[c] for c in games[player.id].p2_hand]

		try:
			messages = [state[8][-2], state[8][-1]]
		except:
			messages = [i for i in state[8]]

		if state[7]==1:
			if state[-3] == True:
				winner = "%s WINS with a" %name, evaluator.class_to_string(evaluator.get_rank_class(evaluator._seven(state[1]+list(state[0]))))
			else:
				winner = "%s WINS" %name, games[player.id].pot
		elif state[7]==2:
			if state[-3] == True:
				winner = "KASSANDRA WINS with a", evaluator.class_to_string(evaluator.get_rank_class(evaluator._seven(state[1]+list(games[player.id].p2_hand))))
			else:
				winner = "KASSANDRA WINS", games[player.id].pot
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
		player.stack = int(games[player.id].p1_stack)
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
	games[new_id.id] = Game(user.name)
	state = games[new_id.id].update_game(None)
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
	rois = [user.roi for user in User.objects.all()]
	Kassandra_ROI = 0 - round(sum(rois)/len(rois), 3)
	if Kassandra_ROI > 0:
		k_color = "green"
	else:
		k_color = "red"
	total_hands = 0
	total_games = 0
	for u in User.objects.all():
		x = u.hands_and_games()
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
	else:
		u_color = "red"
	context = {"level":level, "user_index":user_index, "gold":gold, "silver":silver, "bronze":bronze, "K_ROI":Kassandra_ROI, "user":this_user, "games_hands":this_user.hands_and_games(), "total_hands":total_hands, "total_games":total_games, "u_color":u_color, "k_color":k_color}
	return render(request, "stats.html", context)
		

