# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response, jsonify
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm,\
    CommentForm
from .. import db
from ..models import Permission, Role, User, Post, Comment, SzEstate
from ..decorators import admin_required, permission_required
from datetime import datetime,date
import time

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

@main.route('/tools', methods=['GET', 'POST'])
def tools():
    return render_template('tools.html')

@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('你的信息已经更新成功.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('信息已经更新成功.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('你的评论已经发表成功.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('文章更新成功.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注此用户.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('关注 %s 成功.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('你还没有关注此用户.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('取消关注 %s 成功.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))





####################################################################################
#API
####################################################################################
@main.route('/estates/<int:sid>', methods=['GET'])
@login_required
def get_estatea(sid):
    print 'sid,',sid
    #es = SzEstate.query.get()
    es = SzEstate.query.filter_by(sid=sid).all()
    e = {}
    if len(es) > 0:
        e = es[0].toJson()
    return jsonify(e),200

#根据获取所有房源信息
@main.route('/estates', methods=['GET'])
@login_required
def get_estates():
    es = SzEstate.query.all()
    return jsonify([e.toJson() for e in es]),200

@main.route('/search_estates', methods=['POST'])
@login_required
def search_estates():
    rjson = request.json
    if not rjson:
        abort(400)
    print rjson
    type = rjson.get("type")
    objs = []
    if type == "day":
        for index in range(30):
            day = dateToString(getDayDate(-index))
            es = SzEstate.query.filter(SzEstate.pub_date.like("%"+day+"%")).all()
            objs.append({"label":day,"num":len(es),'no_repeat_num':no_repeat_len(es)})
        #objs.reverse()
    elif type == "week":    
        for index in range(24):
            start = dateToString(getWeekDate(0,-index))
            end = dateToString(getWeekDate(6,-index))
            es = SzEstate.query.filter(SzEstate.pub_date>=start).filter(SzEstate.pub_date<=end).all()
            objs.append({"label":start[5:],"num":len(es),'no_repeat_num':no_repeat_len(es)})
        #objs.reverse()
    elif type == "month":
        for index in range(24):
            day = dateToString(getMonthDate(-index))
            sday = day[0:7]
            es = SzEstate.query.filter(SzEstate.pub_date.like("%"+sday+"%")).all()
            objs.append({"label":day,"num":len(es),'no_repeat_num':no_repeat_len(es)})
        #objs.reverse()
    elif type == "year":
        for index in range(12):
            day = dateToString(getYearDate(-index))
            sday = day[0:4]
            es = SzEstate.query.filter(SzEstate.pub_date.like("%"+sday+"%")).all()
            objs.append({"label":day,"num":len(es),'no_repeat_num':no_repeat_len(es)})
        #objs.reverse()

    return jsonify(objs),200

def no_repeat_len(es):
    no_repeat_arr = []
    no_repeat_keys = []
    for e in es:
        esn = e.sn
        if not esn or no_repeat_keys.count(esn) > 0:
            continue
        no_repeat_keys.append(esn)
        no_repeat_arr.append(e)

    return len(no_repeat_arr)

def dateToString(d):
    return '%d-%02d-%02d' % (d.year,d.month,d.day)

def getDayDate(offset = 0):
    today = datetime.today()
    ltime = time.localtime(time.time()+offset*24*3600)
    return date(ltime.tm_year,ltime.tm_mon,ltime.tm_mday)

#day: 0-6,week:0本周, <0本周之前, >0本周之后
def getWeekDate(day,week = 0):
    today = datetime.today()
    num = today.weekday()-day
    ltime = time.localtime(time.time()-(num-week*7)*24*3600)
    return date(ltime.tm_year,ltime.tm_mon,ltime.tm_mday)

def getMonthDate(offset = 0):
    today = datetime.today()
    y = today.year
    m = today.month
    m = m + offset

    cc = 0
    if m < 0:
        cc = int(m/-12)
        m = m % -12
    else:
        cc = int(m/-12)
        m = m % 12

    if m < 1:
        m = m + 12
        y = y - 1 - cc
    if m > 12:
        m = m - 12
        y = y + 1 + cc
    return date(y,m,1)

def getYearDate(offset = 0):
    today = datetime.today()
    y = today.year + offset
    return date(y,1,1)