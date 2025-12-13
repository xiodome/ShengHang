# 用户管理模块 (User Management Module)
# Consolidated from userManagement.py
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.http import HttpResponse, JsonResponse
import datetime
import json
from .tools import *


# ================================
# 1. 用户注册 (User Registration)
# ================================
@csrf_exempt
def register(request):
    if request.method not in ["GET", "POST"]:
        return json_cn({"error": "GET or POST required"}, 400)
    
    if request.method == "GET":
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>用户注册</title>
            </head>
            <body>
                <h2>用户注册</h2>
                <form method="POST">
                    <label>用户名：</label><br>
                    <input name="username" required><br><br>

                    <label>密码：</label><br>
                    <input name="password" type="password" required><br><br>

                    <label>性别：(男/女/其他)</label><br>
                    <input name="gender"><br><br>

                    <label>生日：</label><br>
                    <input name="birthday" type="date"><br><br>

                    <label>地区：</label><br>
                    <input name="region"><br><br>
                            
                    <label>邮箱：</label><br>
                    <input name="email" type="email"><br><br>
                            
                    <label>个人简介：</label><br>
                    <textarea name="profile"></textarea><br><br>

                    <button type="submit">提交</button>
                </form>
            </body>
            </html>
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        username = data.get("username")
        password = data.get("password")

        optional_fields = ["gender", "birthday", "region", "email", "profile"]
        defaults = {
            "gender": "其他",
            "birthday": None,
            "region": None,
            "email": None,
            "profile": None,
        }

        cleaned = {}
        for field in optional_fields:
            value = data.get(field, defaults[field])
            if value == "":
                value = defaults[field]
            cleaned[field] = value

        gender = cleaned["gender"]
        birthday = cleaned["birthday"]
        region = cleaned["region"]
        email = cleaned["email"]
        profile = cleaned["profile"]

        if not username or not password:
            return json_cn({"error": "请输入用户名和密码"}, 400)

        # 检查用户名是否已存在
        sql_check = "SELECT 1 FROM User WHERE user_name = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check, [username])
            if cursor.fetchone():
                return json_cn({"error": "用户名已被占用"}, 400)

        # 哈希密码并插入
        hashed_pw = hash_password(password)
        sql_insert = """
            INSERT INTO User (user_name, password, gender, birthday, region, email, profile, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, '正常')
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_insert, [username, hashed_pw, gender, birthday, region, email, profile])

        return json_cn({"message": "注册成功"})


# ================================
# 2. 用户登录 (User Login)
# ================================
@csrf_exempt
def login(request):
    if request.method not in ["GET", "POST"]:
        return json_cn({"error": "GET or POST required"}, 400)
    
    if request.method == "GET":
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>用户登录</title>
            </head>
            <body>
                <h2>用户登录</h2>
                <form method="POST">
                    <label>用户名：</label><br>
                    <input name="username" required><br><br>

                    <label>密码：</label><br>
                    <input name="password" type="password" required><br><br>

                    <button type="submit">登录</button>
                </form>
                <p><a href="/user/register/">还没有账号？点击注册</a></p>
            </body>
            </html>
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return json_cn({"error": "请输入用户名和密码"}, 400)

        hashed_pw = hash_password(password)

        sql = "SELECT user_id, status FROM User WHERE user_name = %s AND password = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [username, hashed_pw])
            row = cursor.fetchone()

        if not row:
            return json_cn({"error": "用户名或密码错误"}, 401)

        user_id, status = row

        if status == '封禁中':
            return json_cn({"error": "账号已被封禁"}, 403)

        # 设置 session
        request.session["user_id"] = user_id
        request.session["user_name"] = username

        return json_cn({"message": "登录成功", "user_id": user_id})


# ================================
# 3. 用户登出 (User Logout)
# ================================
@csrf_exempt
def logout(request):
    request.session.flush()
    return json_cn({"message": "已登出"})


# ================================
# 4. 删除账户 (Delete Account)
# ================================
@csrf_exempt
def delete_account(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 401)

    sql = "DELETE FROM User WHERE user_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [user_id])

    request.session.flush()
    return json_cn({"message": "账户已删除"})


# ================================
# 5. 修改密码 (Change Password)
# ================================
@csrf_exempt
def change_password(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 401)

    data = json.loads(request.body)
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return json_cn({"error": "参数缺失"}, 400)

    # 验证旧密码
    old_hashed = hash_password(old_password)
    sql_check = "SELECT 1 FROM User WHERE user_id = %s AND password = %s"
    
    with connection.cursor() as cursor:
        cursor.execute(sql_check, [user_id, old_hashed])
        if not cursor.fetchone():
            return json_cn({"error": "旧密码错误"}, 400)

        # 更新密码
        new_hashed = hash_password(new_password)
        sql_update = "UPDATE User SET password = %s WHERE user_id = %s"
        cursor.execute(sql_update, [new_hashed, user_id])

    return json_cn({"message": "密码修改成功"})


# ================================
# 6. 用户资料页面 (User Profile)
# ================================
@csrf_exempt
def profile(request, owner_id):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    sql = """
        SELECT user_id, user_name, gender, birthday, region, email, profile, register_time, status
        FROM User
        WHERE user_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [owner_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户不存在"}, 404)

    user_data = {
        "user_id": row[0],
        "user_name": row[1],
        "gender": row[2],
        "birthday": str(row[3]) if row[3] else None,
        "region": row[4],
        "email": row[5],
        "profile": row[6],
        "register_time": str(row[7]),
        "status": row[8]
    }

    return json_cn({"user": user_data})


# ================================
# 7. 更新用户资料 (Update Profile)
# ================================
@csrf_exempt
def update_profile(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 401)

    data = json.loads(request.body)

    allowed_fields = ["gender", "birthday", "region", "email", "profile"]
    updates = []
    params = []

    for field in allowed_fields:
        if field in data:
            updates.append(f"{field} = %s")
            params.append(data[field])

    if not updates:
        return json_cn({"error": "没有可更新的字段"}, 400)

    params.append(user_id)
    sql = f"UPDATE User SET {', '.join(updates)} WHERE user_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)

    return json_cn({"message": "资料更新成功"})


# ================================
# 8. 关注用户 (Follow User)
# ================================
@csrf_exempt
def follow_user(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    follower_id = request.session.get("user_id")
    if not follower_id:
        return json_cn({"error": "请先登录"}, 401)

    data = json.loads(request.body)
    followed_id = data.get("followed_id")

    if not followed_id:
        return json_cn({"error": "参数缺失"}, 400)

    if follower_id == followed_id:
        return json_cn({"error": "不能关注自己"}, 400)

    # 检查是否已关注
    sql_check = "SELECT 1 FROM UserFollow WHERE follower_id = %s AND followed_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_check, [follower_id, followed_id])
        if cursor.fetchone():
            return json_cn({"error": "已经关注过了"}, 400)

        sql_insert = "INSERT INTO UserFollow (follower_id, followed_id) VALUES (%s, %s)"
        cursor.execute(sql_insert, [follower_id, followed_id])

    return json_cn({"message": "关注成功"})


# ================================
# 9. 取消关注用户 (Unfollow User)
# ================================
@csrf_exempt
def unfollow_user(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    follower_id = request.session.get("user_id")
    if not follower_id:
        return json_cn({"error": "请先登录"}, 401)

    data = json.loads(request.body)
    followed_id = data.get("followed_id")

    if not followed_id:
        return json_cn({"error": "参数缺失"}, 400)

    sql = "DELETE FROM UserFollow WHERE follower_id = %s AND followed_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [follower_id, followed_id])

    return json_cn({"message": "取消关注成功"})


# ================================
# 10. 关注歌手 (Follow Singer)
# ================================
@csrf_exempt
def follow_singer(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 401)

    data = json.loads(request.body)
    singer_id = data.get("singer_id")

    if not singer_id:
        return json_cn({"error": "参数缺失"}, 400)

    sql_check = "SELECT 1 FROM SingerFollow WHERE user_id = %s AND singer_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_check, [user_id, singer_id])
        if cursor.fetchone():
            return json_cn({"error": "已经关注过了"}, 400)

        sql_insert = "INSERT INTO SingerFollow (user_id, singer_id) VALUES (%s, %s)"
        cursor.execute(sql_insert, [user_id, singer_id])

    return json_cn({"message": "关注歌手成功"})


# ================================
# 11. 取消关注歌手 (Unfollow Singer)
# ================================
@csrf_exempt
def unfollow_singer(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 401)

    data = json.loads(request.body)
    singer_id = data.get("singer_id")

    if not singer_id:
        return json_cn({"error": "参数缺失"}, 400)

    sql = "DELETE FROM SingerFollow WHERE user_id = %s AND singer_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [user_id, singer_id])

    return json_cn({"message": "取消关注成功"})


# ================================
# 12. 获取粉丝列表 (Get Followers)
# ================================
@csrf_exempt
def get_followers(request, uid):
    sql = """
        SELECT u.user_id, u.user_name, u.profile, uf.follow_time
        FROM UserFollow uf
        JOIN User u ON uf.follower_id = u.user_id
        WHERE uf.followed_id = %s
        ORDER BY uf.follow_time DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        followers = dictfetchall(cursor)

    return json_cn({"followers": followers, "count": len(followers)})


# ================================
# 13. 获取关注列表 (Get Followings)
# ================================
@csrf_exempt
def get_followings(request, uid):
    sql = """
        SELECT u.user_id, u.user_name, u.profile, uf.follow_time
        FROM UserFollow uf
        JOIN User u ON uf.followed_id = u.user_id
        WHERE uf.follower_id = %s
        ORDER BY uf.follow_time DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        followings = dictfetchall(cursor)

    return json_cn({"followings": followings, "count": len(followings)})


# ================================
# 14. 获取关注的歌手列表 (Get Followed Singers)
# ================================
@csrf_exempt
def get_followsingers(request, uid):
    sql = """
        SELECT s.singer_id, s.singer_name, s.type, s.country, sf.follow_time
        FROM SingerFollow sf
        JOIN Singer s ON sf.singer_id = s.singer_id
        WHERE sf.user_id = %s
        ORDER BY sf.follow_time DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        singers = dictfetchall(cursor)

    return json_cn({"followed_singers": singers, "count": len(singers)})


# ================================
# 15. 获取用户信息 (Get User Info) - API接口
# ================================
@csrf_exempt
def get_user_info(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    user_id = request.GET.get("user_id")
    if not user_id:
        return json_cn({"error": "参数缺失"}, 400)

    sql = """
        SELECT user_id, user_name, gender, birthday, region, email, profile, register_time, status
        FROM User
        WHERE user_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [user_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户不存在"}, 404)

    user_data = {
        "user_id": row[0],
        "user_name": row[1],
        "gender": row[2],
        "birthday": str(row[3]) if row[3] else None,
        "region": row[4],
        "email": row[5],
        "profile": row[6],
        "register_time": str(row[7]),
        "status": row[8]
    }

    return json_cn({"user": user_data})


# ================================
# 16. 管理员界面 (Admin Profile)
# ================================
@csrf_exempt
def admin_profile(request):
    ok, resp = require_admin(request)
    if not ok:
        return resp
    
    return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>管理员界面</title>
        </head>
        <body>
            <h1>管理员界面</h1>
            <p><a href="/Administrator/singer/admin_add_singer/">添加歌手</a></p>
            <p><a href="/Administrator/singer/admin_delete_singer/">删除歌手</a></p>
            <p><a href="/Administrator/album/admin_add_album/">添加专辑</a></p>
            <p><a href="/Administrator/album/admin_delete_album/">删除专辑</a></p>
            <p><a href="/Administrator/song/admin_add_song/">添加歌曲</a></p>
            <p><a href="/Administrator/song/admin_delete_song/">删除歌曲</a></p>
        </body>
        </html>
    """)
