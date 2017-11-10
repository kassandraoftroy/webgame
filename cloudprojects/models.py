# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class User(models.Model):
	name=models.CharField(max_length=200)
	password=models.CharField(max_length=200)
	roi=models.DecimalField(max_digits=10, decimal_places=3, default="")
	hands=models.IntegerField()
	num_games=models.IntegerField()

	def update(self):
		my_games = [p for p in Player.objects.filter(user=self) if p.hands != 0]
		if len(my_games) > 0:
			stack_agg = 0
			total_hands = 0
			for i in my_games:
				stack_agg += i.stack
				total_hands += i.hands
			avg_roi = stack_agg/len(my_games) - 1000
			return (len(my_games), total_hands, avg_roi)
		else:
			return (0,0,0)

	def __str__(self):
		return "%s" %self.name.encode("ascii", errors="replace")



class Player(models.Model):
	turns=models.IntegerField()
	stack=models.IntegerField()
	hands=models.IntegerField() 
	user=models.ForeignKey(User)

	def __str__(self):
		return "%s" %self.user.name.encode("ascii", errors="replace")
