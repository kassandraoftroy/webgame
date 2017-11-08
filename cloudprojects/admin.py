# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import User, Player

admin.site.register(User)
admin.site.register(Player)

# Register your models here.
