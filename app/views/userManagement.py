# 用户管理模块
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import datetime
import hashlib
import json

# ================================
# 工具函数
# ================================
# 密码哈希
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

# 中文输出
def json_cn(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})



# ================================
# 1. 用户注册
# ================================
# 示例： 
# curl -X POST http://127.0.0.1:8000/user/register/ ^
# -H "Content-Type: application/json" ^
# -d "{\"username\":\"miuna\", \"password\":\"111111\"}"
@csrf_exempt
def register(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    # -------- 可选字段，但要处理默认值 --------
    gender = data.get("gender")  
    if not gender:
        gender = "其他"

    birthday = data.get("birthday", None)
    region = data.get("region", None)
    email = data.get("email", None)
    profile = data.get("profile", None)


    # ============================
    # 1. 基础校验
    # ============================
    if not username or not password:
        return json_cn({"error": "请输入用户名和密码"}, 400)

    if len(username) < 4:
        return json_cn({"error": "用户名长度至少为4"}, 400)

    if len(password) < 6:
        return json_cn({"error": "密码长度至少为6"}, 400)

    # ============================
    # 2. 禁止传入账号状态 status 和 register_time
    # ============================
    if "status" in data:
        return json_cn({"error": "status field is not allowed"}, 400)

    if "register_time" in data:
        return json_cn({"error": "register_time cannot be set manually"}, 400)
    # ============================
    # 3. 检查用户名是否已存在
    # ============================
    sql_check_name = "SELECT user_id FROM User WHERE user_name = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_check_name, [username])
        if cursor.fetchone():
            return json_cn({"error": "用户名已存在"}, 400)

    # ============================
    # 4. 检查邮箱是否唯一
    # ============================
    if email:
        sql_check_email = "SELECT user_id FROM User WHERE email = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check_email, [email])
            if cursor.fetchone():
                return json_cn({"error": "邮箱已存在"}, 400)

    # ============================
    # 5. 插入用户（使用原生 SQL）
    # ============================
    hashed_pw = hash_password(password)

    sql_insert = """
        INSERT INTO User (user_name, password, gender, birthday, region, email, profile)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, [
            username, hashed_pw, gender, birthday, region, email, profile
        ])

    return json_cn({"message": "注册成功"})



# ================================
# 2. 用户登录
# ================================
# 示例：
#curl -X POST http://127.0.0.1:8000/user/login/ ^
# -H "Content-Type: application/json" ^
# -d "{\"username\":\"miuna\", \"password\":\"111111\"}" ^
# -c cookie.txt
@csrf_exempt
def login(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)

    username = data.get("username")
    password = hash_password(data.get("password"))

    sql = """SELECT user_id, status FROM User WHERE user_name=%s AND password=%s"""
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [username, password])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户名或密码错误"}, 401)

    uid, status = row

    if status == "封禁中":
        return json_cn({"error": "用户封禁中"}, 403)

    request.session["user_id"] = uid

    return json_cn({"message": "登录成功", "user_id": uid})




# ================================
# 3. 用户退出
# ================================
# 示例：
# curl http://127.0.0.1:8000/user/logout/ ^
# -b cookie.txt 
def logout(request):
    request.session.flush()
    return json_cn({"message": "退出成功"})



# ================================  
# 4. 用户注销
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/user/delete_account/ ^
# -H "Content-Type: application/json" ^
# -d "{\"password\":\"111111\"}" ^
# -b cookie.txt
@csrf_exempt
def delete_account(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录再注销"}, 401)

    data = json.loads(request.body)
    password = hash_password(data.get("password"))

    if not password:
        return json_cn({"error": "请输入密码"}, 400)

    # --------------------------
    # 2. 查询用户真实密码（SQL）
    # --------------------------
    sql_get_user = "SELECT password FROM user WHERE user_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_user, [user_id])
        row = cursor.fetchone()

        if not row:
            # 理论上不会发生，除非用户已被删
            return json_cn({"error": "用户不存在"}, 404)

        real_hashed_pw = row[0]

    # --------------------------
    # 3. 校验密码
    # --------------------------
    if password != real_hashed_pw:
        return json_cn({"error": "密码错误"}, 403)


    # --------------------------
    # 4. 删除用户（SQL）
    # --------------------------
    sql_delete = "DELETE FROM user WHERE user_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_delete, [user_id])

    # --------------------------
    # 5. 注销 session
    # --------------------------
    request.session.flush()

    return json_cn({"message": "账号成功注销"})



# ================================
# 4. 修改密码
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/user/change_password/ ^
# -H "Content-Type: application/json" ^
# -d "{\"old_password\":\"111111\", \"new_password\":\"222222\"}" ^
# -b cookie.txt
@csrf_exempt
def change_password(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    if "user_id" not in request.session:
        return json_cn({"error": "请先登录再修改密码"}, 403)

    uid = request.session["user_id"]
    data = json.loads(request.body)
    old_pw = data.get("old_password")
    new_pw = data.get("new_password")

    if len(new_pw) < 6 :
        return json_cn({"error": "新密码长度至少为6"}, 401)
    
    if new_pw == old_pw :
        return json_cn({"error": "新密码不能与旧密码相同"}, 401)
    
    old_pw = hash_password(old_pw)
    new_pw = hash_password(new_pw)

    sql_check = "SELECT user_id FROM User WHERE user_id=%s AND password=%s"
    sql_update = "UPDATE User SET password=%s WHERE user_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [uid, old_pw])
        if not cursor.fetchone():
            return json_cn({"error": "旧密码错误"})    
        cursor.execute(sql_update, [new_pw, uid])

    return json_cn({"message": "密码修改成功"})


# ================================
# 5. 修改个人信息
# gender, birthday, region, profile 等
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/user/update_profile/ ^
# -H "Content-Type: application/json" ^
# -d "{\"gender\":\"男\", \"birthday\":\"2025-10-10\", \"region\":\"北京\", \"profile\":\"helloworld\", \"email\":\"111111@qq.com\"}" ^
# -b cookie.txt
@csrf_exempt
def update_profile(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    if "user_id" not in request.session:
        return json_cn({"error": "请先登录再修改个人信息"}, 403)

    uid = request.session["user_id"]

    # 解析 JSON
    try:
        data = json.loads(request.body)
    except:
        return json_cn({"error": "数据格式错误"}, 400)

    fields = []
    values = []

    # ========== 1. 性别检查 ==========
    if "gender" in data:
        if data["gender"] not in ["男", "女", "其他"]:
            return json_cn({"error": "非法性别，只能为：男/女/其他"}, 400)

        fields.append("gender=%s")
        values.append(data["gender"])

    # ========== 2. 生日格式检查（YYYY-MM-DD） ==========
    if "birthday" in data:
        try:
            datetime.datetime.strptime(data["birthday"], "%Y-%m-%d")
        except ValueError:
            return json_cn({"error": "生日格式应为 YYYY-MM-DD"}, 400)

        fields.append("birthday=%s")
        values.append(data["birthday"])

    # ========== 3. email 唯一性检查 ==========
    if "email" in data:
        new_email = data["email"]

        sql_check_email = """
            SELECT user_id FROM User 
            WHERE email=%s AND user_id<>%s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql_check_email, [new_email, uid])
            if cursor.fetchone():
                return json_cn({"error": "邮箱已存在"}, 409)

        fields.append("email=%s")
        values.append(new_email)

    # ========== 4. 其他字段：region、profile ==========
    for key in ["region", "profile"]:
        if key in data:
            fields.append(f"{key}=%s")
            values.append(data[key])

    if not fields:
        return json_cn({"error": "请输入修改信息"}, 400)

    # ========== 5. 执行更新 ==========
    sql_update = f"UPDATE User SET {', '.join(fields)} WHERE user_id=%s"
    values.append(uid)

    with connection.cursor() as cursor:
        cursor.execute(sql_update, values)

    return json_cn({"message": "个人信息修改成功"})





# ================================
# 6. 关注/取关用户
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/user/follow_user/ ^
# -H "Content-Type: application/json" ^
# -d "{\"username\":\"miuna1\", \"action\":\"follow\"}" ^
# -b cookie.txt
@csrf_exempt
def follow_user(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    follower = request.session["user_id"]

    # 解析 JSON
    try:
        data = json.loads(request.body)
    except:
        return json_cn({"error": "错误输入格式"}, 400)

    target_username = data.get("username")
    action = data.get("action")  # follow / unfollow

    if not target_username or not action:
        return json_cn({"error": "请输入 username 或 action 参数"}, 400)

    # ======================
    # 1. 确认目标用户存在
    # ======================
    sql_get_target = "SELECT user_id FROM User WHERE user_name=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_target, [target_username])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "目标用户不存在"}, 404)

    target_uid = row[0]

    # ======================
    # 2. 不允许关注自己
    # ======================
    if target_uid == follower:
        return json_cn({"error": "不能对自己进行操作"}, 400)

    # ======================
    # 3. 关注逻辑
    # ======================

    if action == "follow":
        # 检查是否已关注
        sql_check = """
            SELECT * FROM UserFollow
            WHERE follower_id=%s AND followed_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [follower, target_uid])
            if cursor.fetchone():
                return json_cn({"error": "已关注该用户"}, 409)

        # 插入关注关系
        sql_follow = """INSERT INTO UserFollow(follower_id, followed_id) 
                        VALUES (%s, %s)"""

        with connection.cursor() as cursor:
            cursor.execute(sql_follow, [follower, target_uid])

        return json_cn({"message": "关注成功"})

    # ======================
    # 4. 取关逻辑
    # ======================
    elif action == "unfollow":
        sql_unfollow = """
            DELETE FROM UserFollow
            WHERE follower_id=%s AND followed_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_unfollow, [follower, target_uid])
            if cursor.rowcount == 0:
                return json_cn({"error": "未关注该用户不能取关"}, 409)

        return json_cn({"message": "取关成功"})

    else:
        return json_cn({"error": "action必须为 follow 或 unfollow"}, 400)



# ================================
# 7. 关注/取关歌手
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/user/follow_singer/ ^
# -H "Content-Type: application/json" ^
# -d "{\"singer_name\":\"singer_miuna\", \"action\":\"follow\"}" ^
# -b cookie.txt
@csrf_exempt
def follow_singer(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    follower = request.session["user_id"]

    # 解析 JSON
    try:
        data = json.loads(request.body)
    except:
        return json_cn({"error": "错误输入格式"}, 400)
    
    singer = data.get("singer_name")
    action = data.get("action") # follow / unfollow

    if not singer or not action:
        return json_cn({"error": "请输入 singer_name 或 action 参数"}, 400)

    # ======================
    # 1. 确认目标歌手存在
    # ======================
    sql_get_target = "SELECT singer_id FROM Singer WHERE singer_name=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_target, [singer])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "目标歌手不存在"}, 404)

    target_uid = row[0]

    # ======================
    # 2. 关注逻辑
    # ======================
    if action == "follow":
        # 检查是否已关注
        sql_check = """
            SELECT * FROM SingerFollow
            WHERE user_id=%s AND singer_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [follower, target_uid])
            if cursor.fetchone():
                return json_cn({"error": "已关注该歌手"}, 409)

        # 插入关注关系
        sql_follow = """INSERT INTO SingerFollow(user_id, singer_id) 
                        VALUES (%s, %s)"""

        with connection.cursor() as cursor:
            cursor.execute(sql_follow, [follower, target_uid])

        return json_cn({"message": "关注成功"})

    # ======================
    # 3. 取关逻辑
    # ======================
    elif action == "unfollow":
        sql_unfollow = """
            DELETE FROM SingerFollow
            WHERE user_id=%s AND singer_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_unfollow, [follower, target_uid])
            if cursor.rowcount == 0:
                return json_cn({"error": "未关注该歌手不能取关"}, 409)

        return json_cn({"message": "取关成功"})

    else:
        return json_cn({"error": "action必须为 follow 或 unfollow"}, 400)



# ================================
# 8. 查看关注用户列表
# ================================
# 示例：
# curl -X GET http://127.0.0.1:8000/user/5/get_followings/ ^
# -b cookie.txt
def get_followings(request, uid):
    # =========================
    # 1. 登录检查
    # =========================
    login_user_id = request.session.get("user_id")
    if not login_user_id:
        return json_cn({"error": "请先登录"}, status=401)
    

    # =========================
    # 2. 权限检查
    # =========================
    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人关注用户列表"}, status=403)

    # =========================
    # 3. 查询关注列表和总数
    # =========================
    sql = """
        SELECT u.user_name
        FROM UserFollow uf
        JOIN User u ON uf.followed_id = u.user_id
        WHERE uf.follower_id = %s
    """
    sql_count = """
        SELECT COUNT(*)
        FROM UserFollow
        WHERE follower_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        rows = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute(sql_count, [uid])
        total_count = cursor.fetchall()[0]
    if not total_count :
        total_count = 0

    return json_cn({"关注数：": total_count,
                    "关注者用户名":[r[0] for r in rows]})


# ================================
# 9. 查看粉丝列表
# ================================
# 示例：
# curl -X GET http://127.0.0.1:8000/user/1/get_followers/ ^
# -b cookie.txt
def get_followers(request, uid):
    # =========================
    # 1. 登录检查
    # =========================
    login_user_id = request.session.get("user_id")
    if not login_user_id:
        return json_cn({"error": "请先登录"}, status=401)
    

    # =========================
    # 2. 权限检查
    # =========================
    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人粉丝列表"}, status=403)

    # =========================
    # 3. 查询粉丝列表和总数
    # =========================
    sql = """
        SELECT u.user_name
        FROM UserFollow uf
        JOIN User u ON uf.follower_id = u.user_id
        WHERE uf.followed_id = %s
    """
    sql_count = """
        SELECT COUNT(*)
        FROM UserFollow
        WHERE followed_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        rows = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute(sql_count, [uid])
        total_count = cursor.fetchall()[0]
    if not total_count :
        total_count = 0

    return json_cn({"粉丝数：": total_count,
                    "粉丝用户名":[r[0] for r in rows]})


# ================================
# 10. 查看关注歌手列表
# ================================
# 示例：
# curl -X GET http://127.0.0.1:8000/user/5/get_followsingers/ ^
# -b cookie.txt
def get_followsingers(request, uid):
    # =========================
    # 1. 登录检查
    # =========================
    login_user_id = request.session.get("user_id")
    if not login_user_id:
        return json_cn({"error": "请先登录"}, status=401)
    

    # =========================
    # 2. 权限检查
    # =========================
    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人关注歌手列表"}, status=403)

    # =========================
    # 3. 查询关注歌手列表和总数
    # =========================
    sql = """
        SELECT s.singer_name
        FROM SingerFollow sf
        JOIN Singer s ON sf.singer_id = s.singer_id
        WHERE sf.user_id = %s
    """
    sql_count = """
        SELECT COUNT(*)
        FROM SingerFollow
        WHERE user_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        rows = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute(sql_count, [uid])
        total_count = cursor.fetchall()[0]
    if not total_count :
        total_count = 0

    return json_cn({"关注歌手数：": total_count,
                    "关注歌手名":[r[0] for r in rows]})



# ================================
# 11. 查看他人信息
# ================================
# 示例：
#
def get_user_info(request, uid):
    sql = """
        SELECT user_name, gender, birthday, region, profile 
        FROM User
        WHERE user_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户不存在"}, 404)

    username, gender, birthday, region, profile = row
    return json_cn({
        "username": username,
        "gender": gender,
        "birthday": birthday,
        "region": region,
        "profile": profile
    })
