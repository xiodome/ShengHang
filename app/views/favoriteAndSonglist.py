# 收藏与歌单模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .tools import *