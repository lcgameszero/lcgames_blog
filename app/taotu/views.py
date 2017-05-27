# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from . import taotu
from .. import db
import urllib
import os
import time
import math
from datetime import datetime,date
import requests
from bs4 import BeautifulSoup
import chardet

initCached = False
max_cache_num = 1000
sz_cache = {}
#房源公示
@taotu.route('/meizi', methods=['GET'])
#@login_required
def meizi():
    return render_template("taotu/meizi.html")