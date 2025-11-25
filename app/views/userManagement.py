# 用户管理模块
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.http import HttpResponse
import datetime
import json
from .tools import *




# ================================
# 1. 用户注册
# ================================
# http://127.0.0.1:8000/user/register/ 
@csrf_exempt
def register(request):
    if request.method not in ["GET", "POST"]:
        return json_cn({"error": "GET or POST required"}, 400)
    
    if request.method == "GET":
        return HttpResponse("""
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
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            # 如果不是 JSON，则从 form-data 获取
            data = request.POST


        # ----------------------------
        # 1. 数据获取
        # ----------------------------
        username = data.get("username")
        password = data.get("password")

        # -------- 可选字段，但要处理默认值 -------- 
        # 需要处理的所有可选字段
        optional_fields = ["gender", "birthday", "region", "email", "profile"]

        # 默认值
        defaults = {
            "gender": "其他",
            "birthday": None,
            "region": None,
            "email": None,
            "profile": None,
        }

        # 解析字段
        cleaned = {}
        for field in optional_fields:
            value = data.get(field, defaults[field])
            if value == "":
                value = defaults[field]
            cleaned[field] = value

        # 获得最终值
        gender = cleaned["gender"]
        birthday = cleaned["birthday"]
        region = cleaned["region"]
        email = cleaned["email"]
        profile = cleaned["profile"]


        # ----------------------------
        # 2. 基础校验
        # ----------------------------
        if not username or not password:
            return HttpResponse("""
                    <h2>请输入用户名和密码</h2>
                    <p><a href="/user/register/">返回重新输入</a></p>
                    """)

        if len(username) < 4:
            return HttpResponse("""
                    <h2>用户名长度至少为4</h2>
                    <p><a href="/user/register/">返回重新输入</a></p>
                    """)

        if len(password) < 6:
            return HttpResponse("""
                    <h2>密码长度至少为6</h2>
                    <p><a href="/user/register/">返回重新输入</a></p>
                    """)

        # ----------------------------
        # 3. 禁止传入账号状态 status 和 register_time
        # ----------------------------
        if "status" in data:
            return json_cn({"error": "status field is not allowed"}, 400)

        if "register_time" in data:
            return json_cn({"error": "register_time cannot be set manually"}, 400)
        # ----------------------------
        # 4. 检查用户名是否已存在
        # ----------------------------
        sql_check_name = "SELECT user_id FROM User WHERE user_name = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check_name, [username])
            if cursor.fetchone():
                return HttpResponse("""
                            <h2>用户名已存在</h2>
                            <p><a href="/user/register/">返回重新输入</a></p>
                            """)

        # ----------------------------
        # 5. 检查邮箱是否唯一
        # ----------------------------
        if email:
            sql_check_email = "SELECT user_id FROM User WHERE email = %s"
            with connection.cursor() as cursor:
                cursor.execute(sql_check_email, [email])
                if cursor.fetchone():
                    return HttpResponse("""
                        <h2>邮箱已存在</h2>
                        <p><a href="/user/register/">返回重新输入</a></p>
                        """)

        # ----------------------------
        # 6. 插入用户（使用原生 SQL）
        # ----------------------------
        hashed_pw = hash_password(password)

        sql_insert = """
            INSERT INTO User (user_name, password, gender, birthday, region, email, profile)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_insert, [
                username, hashed_pw, gender, birthday, region, email, profile
            ])
            
        return HttpResponse("""
                <h2>注册成功</h2>
                <p><a href="/user/login/">登录账号</a></p>
                """)
    
    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 2. 用户登录
# ================================
# http://127.0.0.1:8000/user/login/ 
@csrf_exempt
def login(request):
    if request.method not in ["GET", "POST"]:
        return json_cn({"error": "GET or POST required"}, 400)

    if request.method == "GET":
        return HttpResponse("""
            <h2>用户登录</h2>
            <form method="POST">
                <label>用户名：</label><br>
                <input name="username" required><br><br>

                <label>密码：</label><br>
                <input name="password" type="password" required><br><br>

                <button type="submit">登录</button>
                            
                <p><a href="/user/register/">注册账号</a></p>
            </form>
        """)

    # ----------------------------
    # 1. 数据获取
    # ----------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # 如果 body 是 JSON
        except:
            data = request.POST              # 如果是 form-data 自动 fall back
        

        username = data.get("username")
        password = hash_password(data.get("password"))


        # ----------------------------
        # 2. 数据校验
        # ----------------------------
        sql = """SELECT user_id, status FROM User WHERE user_name=%s AND password=%s"""
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [username, password])
            row = cursor.fetchone()

        if not row:
            return HttpResponse("""
                <h2>用户名或密码错误</h2>
                <p><a href="/user/login/">返回重新输入</a></p>
            """, status=400)

        uid, status = row

        if status == "封禁中":
            return HttpResponse("""
                <h2>用户封禁中</h2>
                <p><a href="/user/login/">返回登录</a></p>
            """)

        request.session["user_id"] = uid

        # ----------------------------
        # 3. 特判管理员 user_id
        # ----------------------------
        if uid == ADMIN_USER_ID:
            return HttpResponse(f"""
                <h2>管理员登录成功</h2>
                <p>欢迎管理员 {username} 登录！</p>
                <p><a href="/Administrator/profile/">管理员界面</a></p>
            """)
        
        return HttpResponse(f"""
                <h2>登录成功</h2>
                <p><a href="/user/profile/{uid}/">个人界面</a></p>
            """)
    
    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 3. 用户退出
# ================================
# curl http://127.0.0.1:8000/user/logout/ ^
@csrf_exempt
def logout(request):
    # ----------------------------
    # 1. 登录检查
    # ----------------------------
    if "user_id" not in request.session:
        # 未登录，直接返回提示
        return HttpResponse("""
            <h2>您尚未登录</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """, status=403)
    user_id = request.session["user_id"]

    # ----------------------------
    # 2. 显示退出确认页
    # ----------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>退出登录</h2>
            <p>确定要退出吗？</p>
            <form method="POST">
                <button type="submit">确认退出</button>
                            
                <p><a href="/user/profile/{user_id}/">取消</a></p>
            </form>
        """)

    # ----------------------------
    # 3. 执行退出
    # ----------------------------  
    if request.method == "POST":
        request.session.flush()
        return HttpResponse("""
            <h2>退出成功</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)




# ================================  
# 4. 用户注销
# ================================
# http://127.0.0.1:8000/user/delete_account/ ^
@csrf_exempt
def delete_account(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return HttpResponse("""
            <h2>请先登录</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """, status=401)


    # --------------------------
    # 2. 返回确认注销界面
    # --------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>注销账号</h2>
            <p style="color:red;">该操作不可撤销，将永久删除您的账号。</p>
            <form method="POST">
                <label>请输入密码以确认：</label><br>
                <input name="password" type="password" required><br><br>
                <button type="submit" style="color:white;background:red;padding:5px 15px;border:none;border-radius:5px;">
                    确认注销
                </button>
            </form>
            <br>
            <p><a href="/user/profile/{user_id}/">取消</a></p>
        """)


    if request.method == "POST":
        # 兼容 JSON 和 form
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        password_raw = data.get("password")
        if not password_raw:
                return HttpResponse("""
                    <h2>请输入密码</h2>
                    <p><a href="/user/delete_account/">返回重新输入</a></p>
                """)
        password = hash_password(password_raw)

        # --------------------------
        # 3. 查询用户真实密码（SQL）
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
        # 4. 校验密码
        # --------------------------
        if password != real_hashed_pw:
            return HttpResponse("""
                    <h2 style="color:red;">密码错误，无法注销账号。</h2>
                    <p><a href="/user/delete_account/">返回重新输入</a></p>
                """, status=403)


        # --------------------------
        # 5. 删除用户（SQL）
        # --------------------------
        sql_delete = "DELETE FROM user WHERE user_id = %s"

        with connection.cursor() as cursor:
            cursor.execute(sql_delete, [user_id])

        # --------------------------
        # 6. 注销 session
        # --------------------------
        request.session.flush()

        return HttpResponse("""
                <h2>账号已成功注销</h2>
                <p><a href="/user/register/">点击前往注册新账号</a></p>
            """)

    return json_cn({"error": "GET or POST required"}, 400)





# ================================
# 5. 修改密码
# ================================
# 示例：访问
# http://127.0.0.1:8000/user/change_password/
@csrf_exempt
def change_password(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    uid = request.session.get("user_id")
    if not uid:
        return HttpResponse("""
            <h2>请先登录</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """, status=403)

    # --------------------------
    # 2. 修改密码界面
    # --------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>修改密码</h2>
            <form method="POST">
                <label>旧密码：</label><br>
                <input name="old_password" type="password" required><br><br>

                <label>新密码（至少 6 位）：</label><br>
                <input name="new_password" type="password" required><br><br>

                <button type="submit">确认修改</button>
            </form>
            <br>
            <p><a href="/user/profile/{uid}/">取消</a></p>
        """)


    if request.method == "POST":

        # form-data OR x-www-form-urlencoded
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        old_pw_raw = data.get("old_password")
        new_pw_raw = data.get("new_password")

        # --------------------------
        # 3. 密码校验
        # --------------------------
        if not old_pw_raw or not new_pw_raw:
            return HttpResponse("""
                <h2 style="color:red;">旧密码或新密码不能为空</h2>
                <p><a href="/user/change_password/">返回重新输入</a></p>
            """, status=400)

        if len(new_pw_raw) < 6:
            return HttpResponse("""
                <h2 style="color:red;">新密码长度至少为 6 位</h2>
                <p><a href="/user/change_password/">返回重新输入</a></p>
            """, status=400)

        if new_pw_raw == old_pw_raw:
            return HttpResponse("""
                <h2 style="color:red;">新密码不能与旧密码相同</h2>
                <p><a href="/user/change_password/">返回重新输入</a></p>
            """, status=400)

        
        old_pw = hash_password(old_pw_raw)
        new_pw = hash_password(new_pw_raw)

        # --------------------------
        # 4. 旧密码校验
        # --------------------------
        sql_check = "SELECT user_id FROM User WHERE user_id=%s AND password=%s"
        sql_update = "UPDATE User SET password=%s WHERE user_id=%s"

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [uid, old_pw])
            if not cursor.fetchone():
                return HttpResponse("""
                    <h2 style="color:red;">旧密码错误</h2>
                    <p><a href="/user/change_password/">返回重新输入</a></p>
                """, status=403)

            cursor.execute(sql_update, [new_pw, uid])

        return HttpResponse(f"""
            <h2>密码修改成功</h2>
            <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
        """)

    
    return json_cn({"error": "GET or POST required"}, 400)


# ================================
# 6. 个人界面
# ================================
# http://127.0.0.1:8000/user/profile/5/
@csrf_exempt
def profile(request, owner_id):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return HttpResponse("""
            <h2>请先登录</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """)
    # 判断是否为本人
    if owner_id != user_id :
        guest = 1
    else :
        guest = 0

    # --------------------------
    # 2. 查询个人信息
    # --------------------------
    sql = """
        SELECT user_name, gender, birthday, region, email, profile 
        FROM User WHERE user_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [owner_id])
        row = cursor.fetchone()

        if not row:
            return HttpResponse("<h2>用户不存在</h2>")

        username, gender, birthday, region, email, profile_text = row

    # --------------------------
    # 3. 处理空值
    # --------------------------
    gender = gender if gender else "无"
    region = region if region else "无"
    email = email if email else "无"
    profile_text = profile_text if profile_text else "无"
    birthday = birthday if birthday else "无"


    # --------------------------
    # 4. 设置可见性
    # --------------------------
    if guest == 1:
        # 游客模式：只显示最基本内容
        function_html = f"""
            <p><em>您当前处于游客模式，仅可浏览基本信息。</em></p>

            <form action="/user/follow_user/" method="post">
            <input type="hidden" name="user_id" value="{ owner_id }">
            <button type="submit">关注这个用户</button>
            </form>

            <p><a href="/user/profile/{user_id}/">返回个人界面</a></p>

        """
    else:
        # 正常用户：显示全部功能
        function_html = f"""
            <p><a href="/music/">音乐中心</a></p>

            <p><a href="/songlist/list_songlists/">我的歌单</a></p>

            <p><a href="/user/{user_id}/get_followers/">查看粉丝列表</a></p>
            <p><a href="/user/{user_id}/get_followsingers/">查看关注歌手列表</a></p>
            <p><a href="/user/{user_id}/get_followings/">查看关注列表</a></p>
            <br>
            <p><a href="/user/update_profile/">修改个人信息</a></p>
            <p><a href="/user/change_password/">修改密码</a></p>
            <p><a href="/user/delete_account/">注销账号</a></p>
            <p><a href="/user/logout/">退出登录</a></p>
        """

    # --------------------------
    # 4. 显示个人信息和功能
    # --------------------------
    return HttpResponse(f"""
        <h2>个人信息</h2>

        <p><strong>用户名：</strong> {username}</p>
        <p><strong>性别：</strong> {gender}</p>
        <p><strong>生日：</strong> {birthday}</p>
        <p><strong>地区：</strong> {region}</p>
        <p><strong>邮箱：</strong> {email}</p>
        <p><strong>个人简介：</strong> {profile_text}</p>
        <br> 
        
        {function_html}
    """)


# ================================
# 7. 修改个人信息
# ================================
# http://127.0.0.1:8000/user/update_profile/ 
@csrf_exempt
def update_profile(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录再修改个人信息。</h3>
            <a href="/user/login/">去登录</a>
        """)
    uid = request.session["user_id"]

    if request.method == "GET":

        # --------------------------
        # 2. 修改个人信息界面
        # --------------------------
        return HttpResponse(f"""
            <h2>修改个人信息</h2>

            <form method="POST">

                <label>性别：</label>
                    <input type="radio" name="gender" value="男">男
                    <input type="radio" name="gender" value="女">女
                    <input type="radio" name="gender" value="其他">其他<br><br>

                <label>生日（YYYY-MM-DD）：</label><br>
                <input type="date" name="birthday"><br><br>

                <label>邮箱：</label><br>
                <input type="email" name="email"><br><br>

                <label>地区：</label><br>
                <input type="text" name="region"><br><br>

                <label>个人简介：</label><br>
                <textarea name="profile"></textarea><br><br>

                <button type="submit">提交修改</button>
                <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
            </form>
        """)

    if request.method == "POST":

        try:
            data = json.loads(request.body)
        except:
            data = request.POST
            

        # --------------------------
        # 3. 获取新个人信息并校验
        # --------------------------   
        fields = []
        values = []
        for key in ["gender", "birthday", "email", "region", "profile"]:
            if key in data and data[key].strip() != "":  # 空字符串不更新
                if key == "gender" and data[key] not in ["男", "女", "其他"]:
                    return json_cn({"error": "非法性别，只能为：男/女/其他"}, 400)
                if key == "birthday":
                    try:
                        datetime.datetime.strptime(data[key], "%Y-%m-%d")
                    except ValueError:
                        return json_cn({"error": "生日格式应为 YYYY-MM-DD"}, 400)
                if key == "email":
                    sql_check_email = "SELECT user_id FROM User WHERE email=%s AND user_id<>%s"
                    with connection.cursor() as cursor:
                        cursor.execute(sql_check_email, [data[key], uid])
                        if cursor.fetchone():
                            return HttpResponse(f"""
                                <h2>邮箱已存在</h2>
                                <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
                            """)
                fields.append(f"{key}=%s")
                values.append(data[key])

        if not fields:
            return HttpResponse(f"""
                <h2>请输入修改信息</h2>
                <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
            """)

        # --------------------------
        # 4. 更新个人信息
        # --------------------------
        sql_update = f"UPDATE User SET {', '.join(fields)} WHERE user_id=%s"
        values.append(uid)

        with connection.cursor() as cursor:
            cursor.execute(sql_update, values)

        return HttpResponse(f"""
            <h2>个人信息修改成功</h2>
            <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)





# ================================
# 8. 关注用户
# ================================
# http://127.0.0.1:8000/user/follow_user/ 
@csrf_exempt
def follow_user(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)

    follower = request.session["user_id"]

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # --------------------------
        # 2. 获取目标用户名并查询
        # --------------------------
        target_user_id = data.get("user_id")

        if not target_user_id:
            return json_cn({"error": "请输入 user_id 参数"}, 400)

    
        sql_get_target = "SELECT 1 FROM User WHERE user_id=%s"

        with connection.cursor() as cursor:
            cursor.execute(sql_get_target, [target_user_id])
            row = cursor.fetchone()

        if not row:
            return HttpResponse(f"""
                <h2>用户不存在</h2>
                <p><a href="/user/profile/{target_user_id}/">返回用户详情页</a></p>
            """)

        # --------------------------
        # 3. 不允许操作自己
        # --------------------------
        if target_user_id == follower:
            return HttpResponse(f"""
                <h2>不能对自己进行操作</h2>
                <p><a href="/user/profile/{target_user_id}/">返回用户详情页</a></p>
            """)

        # --------------------------
        # 4. 关注逻辑
        # --------------------------

        
        # 检查是否已关注
        sql_check = """
            SELECT * FROM UserFollow
            WHERE follower_id=%s AND followed_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [follower, target_user_id])
            if cursor.fetchone():
                return HttpResponse(f"""
                    <h2>已关注该用户</h2>
                    <p><a href="/user/profile/{target_user_id}/">返回用户详情页</a></p>
                """)

        # 插入关注关系
        sql_follow = """INSERT INTO UserFollow(follower_id, followed_id) 
                        VALUES (%s, %s)"""

        with connection.cursor() as cursor:
            cursor.execute(sql_follow, [follower, target_user_id])

        return HttpResponse(f"""
            <h2>关注成功</h2>
            <p><a href="/user/profile/{target_user_id}/">返回用户详情页</a></p>
        """)

    return json_cn({"error": "POST required"}, 400)



# ================================
# 9. 取关用户
# ================================
# http://127.0.0.1:8000/user/unfollow_user/ 
@csrf_exempt
def unfollow_user(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)

    follower = request.session["user_id"]

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # --------------------------
        # 2. 获取目标用户名并查询
        # --------------------------
        target_user_id = data.get("user_id")

        if not target_user_id:
            return json_cn({"error": "请输入 user_id 参数"}, 400)

    
        sql_get_target = "SELECT 1 FROM User WHERE user_id=%s"

        with connection.cursor() as cursor:
            cursor.execute(sql_get_target, [target_user_id])
            row = cursor.fetchone()

        if not row:
            return HttpResponse(f"""
                <h2>用户不存在</h2>
                <p><a href="/user/{follower}/get_followings/">返回关注列表</a></p>
            """)

        # --------------------------
        # 3. 不允许操作自己
        # --------------------------
        if target_user_id == follower:
            return HttpResponse(f"""
                <h2>不能对自己进行操作</h2>
                <p><a href="/user/{follower}/get_followings/">返回关注列表</a></p>
            """)

        # --------------------------
        # 4. 取关逻辑
        # --------------------------
        # 检查是否未关注
        sql_check = """
            SELECT * FROM UserFollow
            WHERE follower_id=%s AND followed_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [follower, target_user_id])
            if not cursor.fetchone():
                return HttpResponse(f"""
                    <h2>未关注该用户，不能取关</h2>
                    <p><a href="/user/{follower}/get_followings/">返回关注列表</a></p>
                """)

        # 插入关注关系
        sql_follow = """DELETE FROM UserFollow 
                    WHERE follower_id = %s AND followed_id = %s
                """

        with connection.cursor() as cursor:
            cursor.execute(sql_follow, [follower, target_user_id])

        return HttpResponse(f"""
            <h2>取关成功</h2>
            <p><a href="/user/{follower}/get_followings/">返回关注列表</a></p>
        """)

    return json_cn({"error": "POST required"}, 400)



# ================================
# 10. 关注歌手
# ================================
# http://127.0.0.1:8000/user/follow_singer/ ^
@csrf_exempt
def follow_singer(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)

    follower = request.session["user_id"]
    
    if request.method == "POST":
        
        try:
            data = json.loads(request.body)
        except:
            data = request.POST
        
        singer_id = data.get("singer_id")

        if not singer_id:
            return json_cn({"error": "请输入 singer_id"}, 400)


        # --------------------------
        # 2. 查找目标歌手
        # --------------------------
        sql_get_target = "SELECT 1 FROM Singer WHERE singer_id = %s"

        with connection.cursor() as cursor:
            cursor.execute(sql_get_target, [singer_id])
            exist = cursor.fetchone()

        if not exist:
            return HttpResponse(f"""
                        <h2>目标歌手不存在</h2>
                        <p><a href="/singer/profile/{singer_id}/">返回详情页</a></p>
                    """)

        # --------------------------
        # 3. 关注逻辑
        # --------------------------
        # 检查是否已关注
        sql_check = """
            SELECT * FROM SingerFollow
            WHERE user_id=%s AND singer_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [follower, singer_id])
            if cursor.fetchone():
                return HttpResponse(f"""
                    <h2>已关注该歌手</h2>
                    <p><a href="/singer/profile/{singer_id}/">返回详情页</a></p>
                """)

        # 插入关注关系
        sql_follow = """INSERT INTO SingerFollow(user_id, singer_id) 
                        VALUES (%s, %s)"""

        with connection.cursor() as cursor:
            cursor.execute(sql_follow, [follower, singer_id])

        return HttpResponse(f"""
                    <h2>关注成功</h2>
                    <p><a href="/singer/profile/{singer_id}/">返回详情页</a></p>
                """)
        
    return json_cn({"error": "POST required"}, 400)



# ================================
# 11. 取关歌手
# ================================
# http://127.0.0.1:8000/user/unfollow_singer/ ^
@csrf_exempt
def unfollow_singer(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)

    follower = request.session["user_id"]
    
    if request.method == "POST":
        
        try:
            data = json.loads(request.body)
        except:
            data = request.POST
        
        singer_id = data.get("singer_id")

        if not singer_id:
            return json_cn({"error": "请输入 singer_id"}, 400)


        # --------------------------
        # 2. 查找目标歌手
        # --------------------------
        sql_get_target = "SELECT 1 FROM Singer WHERE singer_id = %s"

        with connection.cursor() as cursor:
            cursor.execute(sql_get_target, [singer_id])
            exist = cursor.fetchone()

        if not exist:
            return HttpResponse(f"""
                        <h2>目标歌手不存在</h2>
                        <p><a href="/user/{follower}/get_followsingers/">返回关注页</a></p>
                    """)

        # --------------------------
        # 3. 取关逻辑
        # --------------------------
        # 检查是否已关注
        sql_check = """
            SELECT * FROM SingerFollow
            WHERE user_id=%s AND singer_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [follower, singer_id])
            if not cursor.fetchone():
                return HttpResponse(f"""
                    <h2>未关注该歌手</h2>
                    <p><a href="/user/{follower}/get_followsingers/">返回关注页</a></p>
                """)

        # 删除关注关系
        sql_follow = """DELETE FROM SingerFollow
                    WHERE user_id = %s AND singer_id = %s        
                """

        with connection.cursor() as cursor:
            cursor.execute(sql_follow, [follower, singer_id])

        return HttpResponse(f"""
                    <h2>取关成功</h2>
                    <p><a href="/user/{follower}/get_followsingers/">返回关注页</a></p>
                """)
        
    return json_cn({"error": "POST required"}, 400)




# ================================
# 12. 查看关注用户列表
# ================================
# curl -X GET http://127.0.0.1:8000/user/10/get_followings/ 
@csrf_exempt
def get_followings(request, uid):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)

    login_user_id = request.session["user_id"]
    

    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人关注用户列表"}, status=403)

    
    # --------------------------
    # 2. 查询关注列表和总数
    # --------------------------
    sql = """
        SELECT u.user_name, u.user_id
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
        total_count = cursor.fetchone()[0]
    if not total_count :
        total_count = 0

    # --------------------------
    # 3. 展示关注列表和总数
    # --------------------------
    if request.method == "GET":
        following_html = ""
        for username, user_id in rows :
            following_html += f"""
                <p>{username} <a href="/user/profile/{user_id}/">用户信息</a></p>
                <form action="/user/unfollow_user/" method="post">
                <input type="hidden" name="user_id" value="{ user_id }">
                <button type="submit">取关</button>
                </form>
            """
        if following_html == "":
            following_html = "<li>暂无关注用户</li>" 

        return HttpResponse(f"""
            <h2>关注列表</h2>
            <p>关注数：{total_count}</p>
            <ul>
                {following_html}
            </ul>
            <p><a href="/user/profile/{login_user_id}/">返回个人中心</a></p>
        """)

    return json_cn({"关注数：": total_count,
                    "关注者用户名":[r[0] for r in rows]})


# ================================
# 13. 查看粉丝列表
# ================================
# http://127.0.0.1:8000/user/10/get_followers/
@csrf_exempt
def get_followers(request, uid):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)
    
    login_user_id = request.session.get("user_id")
    

    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人粉丝列表"}, status=403)

    # --------------------------
    # 2. 查询粉丝列表和总数
    # --------------------------
    sql = """
        SELECT u.user_name, u.user_id
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
        total_count = cursor.fetchone()[0]
    if not total_count :
        total_count = 0

    # --------------------------
    # 3. 展示粉丝列表和总数
    # --------------------------
    if request.method == "GET":
        fan_html = ""
        for username, user_id in rows :
            fan_html += f"""
                <p>{username} <a href="/user/profile/{user_id}/">用户信息</a></p>
            """
        if fan_html == "" :
            fan_html = "<li>暂无粉丝</li>"
        return HttpResponse(f"""
            <h2>粉丝列表</h2>
            <p>粉丝数：{total_count}</p>
            <ul>
                {fan_html}
            </ul>
            <p><a href="/user/profile/{login_user_id}/">返回个人中心</a></p>
        """)

    return json_cn({"粉丝数：": total_count,
                    "粉丝用户名":[r[0] for r in rows]})


# ================================
# 14. 查看关注歌手列表
# ================================
# http://127.0.0.1:8000/user/10/get_followsingers/
@csrf_exempt 
def get_followsingers(request, uid):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)
    
    login_user_id = request.session.get("user_id")
    

    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人关注歌手列表"}, status=403)

    # --------------------------
    # 2. 查询关注歌手列表和总数
    # --------------------------
    sql = """
        SELECT s.singer_name, s.singer_id
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
        total_count = cursor.fetchone()[0]
    if not total_count :
        total_count = 0

    # --------------------------
    # 3. 展示关注歌手列表和总数
    # --------------------------
    if request.method == "GET":
        follow_singers_html = ""
        for singer_name, singer_id in rows :
            follow_singers_html += f"""
                <p>
                {singer_name} 
                <a href="/singer/profile/{singer_id}/">歌手详情</a> 
                <form action="/user/unfollow_singer/" method="post">
                <input type="hidden" name="singer_id" value="{ singer_id }">
                <button type="submit">取关</button>
                </form>
                </p>
            """
        if follow_singers_html == "":
            follow_singers_html = "<li>暂无关注歌手</li>"
        return HttpResponse(f"""
            <h2>关注歌手列表</h2>
            <p>关注歌手数：{total_count}</p>
            <ul>
                {follow_singers_html}
            </ul>
            <p><a href="/user/profile/{login_user_id}/">返回个人中心</a></p>
        """)

    return json_cn({"关注歌手数：": total_count,
                    "关注歌手名":[r[0] for r in rows]})



# ================================
# 15. 查看他人信息
# ================================
# http://127.0.0.1:8000/user/get_user_info/ 
@csrf_exempt
def get_user_info(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)
    user_id = request.session["user_id"]
    
    if request.method == "GET":

        # --------------------------
        # 2. 展示操作界面
        # --------------------------
        return HttpResponse(f"""
            <h2>查看用户信息</h2>

            <form method="POST">

                <label>用户名：</label><br>
                <input name="user_name" required><br><br>
                            
                <button type="submit">查找</button>
                <p><a href="/user/profile/">返回个人中心</a></p>
            </form>
        """)
    
    if request.method == "POST":
        # 解析 JSON
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # --------------------------
        # 3. 根据用户名查找用户信息
        # --------------------------
        user_name = data.get("user_name")

        sql = """
            SELECT user_name, user_id
            FROM User
            WHERE user_name=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [user_name])
            row = cursor.fetchone()

        if not row:
            return HttpResponse(f"""
                <h2>用户不存在</h2>
                <p><a href="/user/profile/{user_id}/">返回个人中心</a></p>
            """)

        username, target_user_id = row

        # --------------------------
        # 4. 展示用户信息
        # --------------------------
        return HttpResponse(f"""
                <p><strong>用户名：</strong> {username}</p>
                <p><a href="/user/profile/{target_user_id}/">用户个人中心</a></p>
            """)
    
    return json_cn({"error": "GET or POST required"}, 400)

# ================================
# 16. 管理员界面
# ================================
# http://127.0.0.1:8000/Administrator/profile/
ADMIN_USER_ID = 1  # 你可以改成实际管理员 id
@csrf_exempt
def admin_profile(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return HttpResponse("""
            <h2>请先登录</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """)
    elif user_id != ADMIN_USER_ID :
        return HttpResponse("""
            <h2>不是管理员账号！</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """)
    
    # --------------------------
    # 2. 显示管理员功能
    # --------------------------
    return HttpResponse(f"""
        <h2>管理员界面</h2>
        <ul>
                <li><a href="/Administrator/singer/admin_add_singer/">添加歌手</a></li>
                <li><a href="/Administrator/singer/admin_delete_singer/">删除歌手</a></li>
                <li><a href="/Administrator/album/admin_add_album/">添加专辑</a></li>
                <li><a href="/Administrator/album/admin_delete_album/">删除专辑</a></li>
                <li><a href="/Administrator/song/admin_add_song/">添加歌曲</a></li>
                <li><a href="/user/logout/">退出登录</a></li>
        </ul>
        """)