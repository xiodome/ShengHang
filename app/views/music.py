# 歌手与音乐模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .tools import *


# ================================
# 1. 音乐中心
# ================================
# http://127.0.0.1:8000/music/
@csrf_exempt
def music(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行查看操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    return HttpResponse(f"""
        
        <p><a href="/user/profile/{uid}/">返回个人界面</a></p>

        <p><a href="/singer/search_singer/">搜索歌手</a></p>
        <p><a href="/album/search_album/">搜索专辑</a></p>
        <p><a href="/song/search_song/">搜索歌曲</a></p>
        <p><a href="/songlist/search_songlist/">搜索歌单</a></p>
    
    """)


# ================================
# 2. 新增歌手（管理员权限）
# ================================
# http://127.0.0.1:8000/Administrator/singer/admin_add_singer/ 
@csrf_exempt
def admin_add_singer(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok :
        return resp
    
    if request.method == "GET":
        # --------------------------
        # 2. 展示添加歌手界面
        # --------------------------
        return HttpResponse("""
            <h2>添加歌手</h2>
            <form method="POST">
                <label>歌手名：</label><br>
                <input name="singer_name" required><br><br>

                <label>歌手类别：</label>
                    <input type="radio" name="type" value="男" required>男
                    <input type="radio" name="type" value="女" required>女
                    <input type="radio" name="type" value="组合" required>组合<br><br>
                            
                <label>国家：</label><br>
                <input name="country"><br><br>

                <label>生日：</label><br>
                <input name="birthday" type="date"><br><br>
                            
                <label>歌手简介：</label><br>
                <textarea name="introduction"></textarea><br><br>                            

                <button type="submit">添加</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)

    # --------------------------
    # 3. 获取歌手数据并校验
    # --------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        if "singer_name" in data:
            singer_name = data.get("singer_name")
        else :
            return HttpResponse("""
                <h2>未检测到歌手名称</h2>
                <p><a href="/Administrator/singer/admin_add_singer/">返回重新输入</a></p>
            """)
        

        if "type" in data:
            type = data.get("type")     
        else :
            return HttpResponse("""
            <h2>错误歌手类别</h2>
            <p><a href="/Administrator/singer/admin_add_singer/">返回重新输入</a></p>
        """)

        # -------- 可选字段，但要处理默认值 -------- 
        # 需要处理的所有可选字段
        optional_fields = ["country", "birthday", "introduction"]

        # 默认值
        defaults = {
            "country": None,
            "birthday": None,
            "introduction": None,
        }

        # 解析字段
        cleaned = {}
        for field in optional_fields:
            value = data.get(field, defaults[field])
            if value == "":
                value = defaults[field]
            cleaned[field] = value

        # 获得最终值
        country = cleaned["country"]
        birthday = cleaned["birthday"]
        introduction = cleaned["introduction"]


        # --------------------------
        # 4. 正式添加歌手
        # --------------------------
        sql = """
            INSERT 
            INTO Singer (singer_name, type, country, birthday, introduction)
            VALUES(%s, %s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [
                singer_name, type, country, birthday, introduction
                ])

        return HttpResponse(f"""
                <h2>成功添加歌手：{singer_name}</h2>
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            """)
    
    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 3. 删除歌手（管理员权限）
# ================================
# http://127.0.0.1:8000/Administrator/singer/admin_delete_singer/
@csrf_exempt
def admin_delete_singer(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok :
        return resp


    if request.method == "GET":
        # --------------------------
        # 2. 展示删除歌手界面
        # --------------------------
        return HttpResponse("""
            <h2>删除歌手</h2>
            <form method="POST">
                <label>歌手名：</label><br>
                <input name="singer_name" required><br><br>
                            
                <label>歌手id：</label><br>
                <input name="singer_id" required><br><br>                          

                <button type="submit">删除</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)

    # --------------------------
    # 3. 获取歌手id并校验
    # --------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST   


    if "singer_id" in data :
        singer_id = data.get("singer_id")
    else :
        return HttpResponse("""
                <h2>未检测到歌手id</h2>
                <p><a href="/Administrator/singer/admin_delete_singer/">返回重新输入</a></p>
            """)
    
    if "singer_name" in data :
        singer_name = data.get("singer_name")
    else :
        return HttpResponse("""
                <h2>未检测到歌手名字</h2>
                <p><a href="/Administrator/singer/admin_delete_singer/">返回重新输入</a></p>
            """)
    
    # --------------------------
    # 4. 检验歌手名字
    # --------------------------
    name_sql = """
        SELECT singer_name
        FROM Singer 
        WHERE singer_id = %s      
    """
    with connection.cursor() as cursor:
        cursor.execute(name_sql, [singer_id])
        row = cursor.fetchone()
    
    if row is None :
        return HttpResponse("""
                <h2>歌手不存在</h2>
                <p><a href="/Administrator/singer/admin_delete_singer/">返回重新输入</a></p>
            """)
    elif singer_name != row[0] :
        return HttpResponse("""
                <h2>歌手名与要删除的歌手不匹配</h2>
                <p><a href="/Administrator/singer/admin_delete_singer/">返回重新输入</a></p>
            """)

    # --------------------------
    # 5. 删除对应歌手
    # --------------------------

    delete_sql = """
        DELETE 
        FROM Singer 
        WHERE singer_id = %s   
    """
    with connection.cursor() as cursor:
        cursor.execute(delete_sql, [singer_id])

    return HttpResponse(f"""
                <h2>歌手删除成功</h2><br>
                <h2>歌手id:{singer_id} 歌手名:{singer_name}</h2>
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            """)


# ================================
# 4. 搜索歌手
# ================================
# http://127.0.0.1:8000/singer/search_singer/ 
@csrf_exempt
def search_singer(request):
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
        # 2. 展示搜索歌手界面
        # --------------------------
        return HttpResponse(f"""
            <h2>搜索歌手</h2>
            <form method="POST">
                <label>歌手名：(支持模糊搜索)</label><br>
                <input name="singer_name"><br><br>
                            
                <label>歌手类别</label><br>
                <input type="radio" name="type" value="">不限
                <input type="radio" name="type" value="男">男
                <input type="radio" name="type" value="女">女
                <input type="radio" name="type" value="组合">组合<br><br>                         

                <label>国家：</label><br>
                <input type="text" name="country" placeholder="输入国家"><br><br>
                            
                <button type="submit">搜索</button>
                            
                <p><a href="/music/">返回音乐中心</a></p>
            </form>
        """)


    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # --------------------------
        # 3. 获取筛选标签
        # --------------------------
        filters = []
        params = []

        type = data.get("type")
        country = data.get("country")
        singer_name = data.get("singer_name")

        if type and type != "":
            filters.append("type = %s")
            params.append(type)
        if country and country != "":
            filters.append("country = %s")
            params.append(country)
        if singer_name and singer_name != "":
            filters.append("singer_name LIKE %s")
            params.append("%" + singer_name + "%")

        # --------------------------
        # 4. 正式查找歌手
        # --------------------------

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        sql = f"""
            SELECT singer_id, singer_name, type, country
            FROM Singer
            {where_clause}
            ORDER BY singer_name ASC
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        # ------------------------
        # 5. 查询数量
        # ------------------------
        sql_count = f"""
            SELECT COUNT(*)
            FROM Singer
            {where_clause}
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_count, params)
            total = cursor.fetchone()[0]


        # --------------------------
        # 6. 生成歌手 HTML
        # --------------------------
        singers_html = ""
        for (singer_id, singer_name, type, country) in rows:
            singers_html += f"""
                <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                    <h4>{singer_name}</h4>
                    <p>类型：{type}</p>
                    <p>国籍：{country}</p>
                    <p>
                        {f"<a href='/singer/profile/{singer_id}/'>歌手详情</a>"}
                    </p>
                </div>
            """

        # --------------------------
        # 7. 输出查找结果
        # --------------------------
        return HttpResponse(f"""
            <h2>歌手搜索结果</h2>
            <p>符合条件歌手数:<strong>{total}</strong></p>
            <p><a href="/music/">返回音乐中心</a></p>

            <hr>
            {singers_html}
            <hr>
        """)
    
    return json_cn({"error": "GET or POST required"}, 400)




# ================================
# 5. 歌手详情
# ================================
# http://127.0.0.1:8000/singer/profile/3/
@csrf_exempt
def singer_profile(request, singer_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行查看操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    user_id = request.session["user_id"]

    # --------------------------
    # 2. 查询歌手信息
    # --------------------------
    sql_list = """
        SELECT singer_name, type, country, birthday, introduction
        FROM Singer
        WHERE singer_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_list, [singer_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>歌手不存在</h2>
            <p><a href="/singer/search_singer/">返回歌手列表</a></p>
        """, status=404)

    singer_name, type, country, birthday, introduction = row


    # --------------------------
    # 3. 查询歌手的歌曲列表
    # --------------------------
    sql_songs = """
        SELECT 
            s.song_title,
            s.duration,
            a.album_title
        FROM Song s
        JOIN Album a ON s.album_id = a.album_id
        JOIN Song_Singer ss ON s.song_id = ss.song_id
        WHERE ss.singer_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songs, [singer_id])
        song_rows = cursor.fetchall()

    # --------------------------
    # 4. 生成歌手歌曲 HTML
    # --------------------------
    songs_html = ""
    for (song_title, duration, album_title) in song_rows:
        songs_html += f"""
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h4>{song_title}</h4>
                <p>所属专辑：{album_title}</p>
                <p>时长：{format_time(duration)}</p>


            </div>
        """

    if not songs_html:
        songs_html = "<p>该歌手还没有任何歌曲。</p>"


    # --------------------------
    # 5. 查询歌手的专辑列表
    # --------------------------
    sql_albums = """
        SELECT 
            a.album_id,
            a.album_title,
            a.release_date
        FROM Album a
        JOIN Singer s ON s.singer_id = a.singer_id
        WHERE s.singer_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_albums, [singer_id])
        album_rows = cursor.fetchall()

    # --------------------------
    # 6. 生成歌手专辑 HTML
    # --------------------------
    albums_html = ""
    for (album_id, album_title, release_date) in album_rows:
        albums_html += f"""
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h4>{album_title}</h4>
                <p>发行日期：{release_date}</p>
                <p><a href="/album/profile/{album_id}/">详情</a></p>
            </div>
        """

    if not albums_html:
        albums_html = "<p>该歌手还没有任何专辑。</p>"

    # --------------------------
    # 7. 生成最终 HTML
    # --------------------------
    return HttpResponse(f"""
        <h2>歌手详情：{singer_name}</h2>
        <p>歌手类别：{type}</p>
        <p>歌手国籍：{country or "无"}</p>
        <p>歌手生日：{birthday or "无"}</p>
        <p>歌手介绍：{introduction or "无"}</p>
        <p>歌曲数量：{len(song_rows)}</p>


        <form action="/user/follow_singer/" method="post">
        <input type="hidden" name="singer_id" value="{ singer_id }">
        <button type="submit">关注这个歌手</button>
        </form>


        <p><a href="/singer/search_singer/">返回歌手列表</a></p>

        <hr>
        <h3>歌手歌曲列表</h3>
        {songs_html}
        <hr>

        <hr>
        <h3>歌手专辑列表</h3>
        {albums_html}
        <hr>
    """)


# ================================
# 6. 新增专辑（管理员权限）
# ================================
# http://127.0.0.1:8000/Administrator/album/admin_add_album/ ^
@csrf_exempt
def admin_add_album(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok :
        return resp


    if request.method == "GET":
        # --------------------------
        # 2. 展示添加专辑界面
        # --------------------------
        return HttpResponse("""
            <h2>添加专辑</h2>
            <form method="POST">
                <label>专辑名：</label><br>
                <input name="album_title" required><br><br>
                            
                <label>歌手id：</label><br>
                <input name="singer_id" required><br><br>  
                            
                <label>发行日期：</label><br>
                <input name="release_date" type = "date"><br><br>
                            
                <label>封面url：</label><br>
                <input name="cover_url"><br><br> 
                                                    
                <label>专辑介绍：</label><br>
                <textarea name="description"></textarea><br><br>
                            
                <button type="submit">添加</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)


    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # --------------------------
        # 3. 获取专辑数据并校验
        # --------------------------
        if "album_title" in data:
            album_title = data.get("album_title")
        else :
            return HttpResponse("""
                <h2>未检测到专辑名称</h2>
                <p><a href="/Administrator/album/admin_add_album/">返回重新输入</a></p>
                """)
        
        if "singer_id" in data:
            singer_id = data.get("singer_id")
        else :
            return HttpResponse("""
                <h2>未检测到歌手id</h2>
                <p><a href="/Administrator/album/admin_add_album/">返回重新输入</a></p>
                """)
        
        sql_singer = """
            SELECT singer_name FROM Singer WHERE singer_id = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_singer, [singer_id])
            row = cursor.fetchone()

        if not row:
            return HttpResponse("""
                <h2>歌手不存在</h2>
                <p><a href="/Administrator/album/admin_add_album/">返回重新输入</a></p>
            """)
        else : 
            singer_name = row[0]


        # -------- 可选字段，但要处理默认值 -------- 
        # 需要处理的所有可选字段
        optional_fields = ["release_date", "cover_url", "description"]

        # 默认值
        defaults = {
            "release_date": "1970-01-01",
            "cover_url": "/images/default_album_cover.jpg",
            "description": None,
        }

        # 解析字段
        cleaned = {}
        for field in optional_fields:
            value = data.get(field, defaults[field])
            if value == "":
                value = defaults[field]
            cleaned[field] = value

        # 获得最终值
        release_date = cleaned["release_date"]
        cover_url = cleaned["cover_url"]
        description = cleaned["description"]


        # --------------------------
        # 4. 正式添加专辑
        # --------------------------

        sql = """
            INSERT INTO Album (album_title, singer_id, release_date, cover_url, description)
            VALUES (%s, %s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [
                album_title, singer_id, release_date, cover_url, description,
                ])

        return HttpResponse(f"""
                <h2>专辑已添加</h2><br>
                <h2>专辑名称:{album_title} 歌手名:{singer_name}</h2>           
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            """)
    
    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 7. 删除专辑（管理员权限）
# ================================
# http://127.0.0.1:8000/Administrator/album/admin_delete_album/ 
@csrf_exempt
def admin_delete_album(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok :
        return resp


    if request.method == "GET":
        # --------------------------
        # 2. 展示删除专辑界面
        # --------------------------
        return HttpResponse("""
            <h2>添加专辑</h2>
            <form method="POST">
                <label>专辑id：</label><br>
                <input name="album_id" required><br><br>
                            
                <button type="submit">删除</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)


    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST


        # --------------------------
        # 3. 获取要删除的专辑数据
        # --------------------------
        if "album_id" in data :
            album_id = data.get("album_id")
        else :
            return HttpResponse("""
                    <h2>未检测到专辑id</h2>
                    <p><a href="/Administrator/album/admin_delete_album/">返回重新输入</a></p>
                """)

        # --------------------------
        # 4. 获取专辑标题
        # --------------------------
        name_sql = """
            SELECT album_title
            FROM Album 
            WHERE album_id = %s      
        """
        with connection.cursor() as cursor:
            cursor.execute(name_sql, [album_id])
            row = cursor.fetchone()
        
        if row is None :
            return HttpResponse("""
                    <h2>专辑不存在</h2>
                    <p><a href="/Administrator/album/admin_delete_album/">返回重新输入</a></p>
                """)
        
        album_title = row[0]

        # --------------------------
        # 5. 正式删除专辑
        # --------------------------
        sql = "DELETE FROM Album WHERE album_id = %s"

        with connection.cursor() as cursor:
            cursor.execute(sql, [album_id])

        return HttpResponse(f"""
                    <h2>专辑已删除</h2><br>
                    <h2>专辑id:{album_id} 专辑名称:{album_title}</h2>           
                    <p><a href="/Administrator/profile/">返回管理员界面</a></p>
                """)

    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 8. 搜索专辑
# ================================
# http://127.0.0.1:8000/album/search_album/ 
@csrf_exempt
def search_album(request):
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
        # 2. 展示搜索专辑界面
        # --------------------------
        return HttpResponse(f"""
            <h2>搜索专辑</h2>
            <form method="POST">
                <label>专辑名：(支持模糊搜索)</label><br>
                <input name="album_title"><br><br>
                                                     
                <label>歌手名：(支持模糊搜索)</label><br>
                <input name="singer_name"><br><br>
                            
                <button type="submit">搜索</button>
                            
                <p><a href="/music/">返回音乐中心</a></p>
            </form>
        """)


    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST
    
        # --------------------------
        # 3. 获取搜索标签
        # --------------------------
        album_title = data.get("album_title", "").strip()
        singer_name = data.get("singer_name", "").strip()

        filters = []
        params = []

        if album_title:
            filters.append("a.album_title LIKE %s")
            params.append(f"%{album_title}%")
        if singer_name:
            filters.append("s.singer_name LIKE %s")
            params.append(f"%{singer_name}%")


        # --------------------------
        # 4. 查询专辑信息
        # --------------------------
        sql_album = """
            SELECT a.album_title, sg.singer_name, a.release_date, a.album_id
            FROM Album a
            JOIN Singer sg ON a.singer_id = sg.singer_id
        """

        if filters:
            sql_album += " WHERE " + " AND ".join(filters)

        sql_album += " GROUP BY a.album_id"

        with connection.cursor() as cursor:
            cursor.execute(sql_album, params)
            rows = cursor.fetchall()


        if not rows:
            HttpResponse(f"""
                    <h2>未找到符合条件专辑</h2><br>          
                    <p><a href="/user/profile/{user_id}/">返回个人界面</a></p>
                """)


        # --------------------------
        # 5. 将信息转成HTML
        # --------------------------
        albums_html = ""
        for (album_title, singer_name, release_date, album_id) in rows:
            albums_html += f"""
                <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                    <h4>{album_title}</h4>
                    <p>歌手名：{singer_name}</p>
                    <p>发行日期：{release_date}</p>
                    <p><a href="/album/profile/{album_id}/">详情</a></p>
                </div>
            """

        return HttpResponse(f"""
            <p><a href="/music/">返回音乐中心</a></p>
                            
            <h2>搜索结果</h2>
            <ul>
                {albums_html}
            </ul>
        """)
    
    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 9. 专辑详情
# ================================
# http://127.0.0.1:8000/album/profile/3/
@csrf_exempt
def album_profile(request, album_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行查看操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    user_id = request.session["user_id"]

    # --------------------------
    # 2. 查询专辑信息
    # --------------------------
    sql_list = """
        SELECT album_title, release_date, cover_url, description, sg.singer_name, sg.singer_id
        FROM Album a
        JOIN Singer sg ON sg.singer_id = a.singer_id
        WHERE a.album_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_list, [album_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>专辑不存在</h2>
            <p><a href="/album/search_album/">返回专辑列表</a></p>
        """, status=404)

    album_title, release_date, cover_url, descprition, singer_name, singer_id = row


    # --------------------------
    # 3. 查询专辑的歌曲列表
    # --------------------------
    sql_albums = """
        SELECT 
            s.song_id,
            s.song_title,
            s.duration
        FROM Album a
        JOIN Song s ON s.album_id = a.album_id       
        WHERE a.album_id = %s
    """

    sql_total_duration = """
        SELECT 
            IFNULL(SUM(s.duration), 0) AS total_duration
        FROM Album a
        JOIN Song s ON s.album_id = a.album_id
        WHERE a.album_id = %s
    """

    sql_singers = """
        SELECT
            sg.singer_name
        FROM Singer sg
        JOIN Song_Singer ss ON ss.singer_id = sg.singer_id
        WHERE ss.song_id = %s
    """

    sql_comment = """
        SELECT 
            u.user_id, u.user_name, c.comment_id, c.content, c.like_count, c.comment_time
        FROM Comment c 
        JOIN User u ON u.user_id = c.user_id
        WHERE target_id = %s AND target_type = 'album'
        ORDER BY comment_time DESC
    """

    # --------------------------
    # 4. 查询并生成专辑 HTML
    # --------------------------
    songs_html = ""

    with connection.cursor() as cursor:
        cursor.execute(sql_albums, [album_id])
        song_rows = cursor.fetchall()

        cursor.execute(sql_total_duration, [album_id])
        total_duration = cursor.fetchone()[0]
        min = total_duration // 60
        sec = total_duration % 60
        
        for (song_id, song_title, duration) in song_rows :
            cursor.execute(sql_singers , [song_id])
            singer_rows = cursor.fetchall()
            singer_names = "、".join([row[0] for row in singer_rows]) if singer_rows else "未知"

            songs_html += f"""
                <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                    <h4>{song_title}</h4>
                    <p>时长：{format_time(duration)}</p>
                    <p>歌手：{singer_names}</p>


                </div>
            """
        if songs_html == "" :
            songs_html = (f"<p>该专辑没有任何歌曲</p>")

        cursor.execute(sql_comment, [album_id])
        comment_rows = cursor.fetchall()
        comment_count = len(comment_rows)


    # --------------------------
    # 5. 专辑评论
    # --------------------------
    comment_html = f"""
        <h2>专辑评论（{comment_count} 个）</h2>
        <ul>
    """
    if comment_count == 0:
        comment_html += "<p>暂无评论。</p>"
    else:
        for user_id, user_name, comment_id, content, like_count, comment_time in comment_rows:
            comment_html += f"""
                <li>
                    <p>用户：<a href="/user/profile/{user_id}/">{user_name}</a><p>
                    内容：<strong>{content}</strong>

                    <form action="/comment/like_comment/{comment_id}/" method="post">
                        <input type="hidden" name="type" value="album">
                        <input type="hidden" name="id" value="{ album_id }">
                        <button type="submit">点赞</button>
                    </form>

                    <p>点赞数：{like_count}<p>
                    <p>评论时间：{comment_time.strftime("%Y-%m-%d %H:%M")}</p>

                </form>

                </li>
            """
    comment_html += "</ul><hr>"

    # --------------------------
    # 6. 生成最终 HTML
    # --------------------------
    return HttpResponse(f"""
        <h2>专辑详情：{album_title}</h2>
        <img src="{cover_url}" style="width:180px;height:180px;">
        <p>歌手：{singer_name} <a href="/singer/profile/{singer_id}/">详情</a></p>
        <p>发行日期：{release_date}</p>
        <p>专辑描述：{descprition or "无"}</p>
        <p>歌曲数量：{len(song_rows)}</p>
        <p>专辑总时长：{min}:{sec}</p>

        <form action="/favorite/add_favorite/" method="post">
            <input type="hidden" name="type" value="album">
            <input type="hidden" name="id" value="{ album_id }">
            <button type="submit">收藏这个专辑</button>
        </form>


        <p><a href="/album/search_album/">返回专辑列表</a></p>

        <hr>
        <h3>专辑歌曲列表</h3>
        {songs_html}
        <hr>

        {comment_html}

        <h3>发表评论</h3>
        <form action="/comment/add_comment/" method="post">
            <input type="hidden" name="target_type" value="album">
            <input type="hidden" name="target_id" value="{ album_id }">

            <textarea name="content" rows="4" cols="50" required></textarea>
            <br>
            <button type="submit">提交评论</button>
        </form>
    """)




# ================================
# 10. 添加歌曲（管理员权限）
# ================================
# http://127.0.0.1:8000/Administrator/song/admin_add_song/ 
@csrf_exempt
def admin_add_song(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

      
    if request.method == "GET":
        # --------------------------
        # 2. 展示添加歌曲界面
        # --------------------------
        return HttpResponse("""
            <h2>添加歌曲</h2>
            <form method="POST">
                <label>歌曲名：</label><br>
                <input name="song_title" required><br><br>

                <label>专辑ID：</label><br>
                <input name="album_id" type="number" required><br><br>

                <label>时长（分:秒）：</label><br>
                <input name="duration" type="text" placeholder="mm:ss" required><br><br>

                <label>文件URL：</label><br>
                <input name="file_url" required><br><br>

                <label>歌手ID（用逗号分隔）：</label><br>
                <input name="singers_id" required><br><br>

                <button type="submit">添加</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST


        # --------------------------
        # 3. 获取歌曲数据并校验
        # --------------------------
        if "song_title" in data:
            song_title = data.get("song_title")
        else :
            return HttpResponse("""
                <h2>未检测到歌曲名称</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/song/admin_add_song/">返回重新输入</a></p>
            """)
        
        if "album_id" in data:
            album_id = data.get("album_id")
        else :
            return HttpResponse("""
                <h2>未检测到所属专辑id</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/song/admin_add_song/">返回重新输入</a></p>
            """)
        
        if "duration" in data:
            try:
                # 支持 mm:ss 或 m:ss
                minutes, seconds = map(int, data.get("duration").strip().split(":"))
                duration_seconds = minutes * 60 + seconds
            except Exception:
                return HttpResponse("""
                    <h2>歌曲时长格式错误</h2>
                    <p><a href="/user/login/">重新填写</a></p>
                    <p><a href="/Administrator/song/admin_add_song/">返回重新输入</a></p>
                """)
        else :
            return HttpResponse("""
                <h2>未检测到歌曲时长</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/song/admin_add_song/">返回重新输入</a></p>
            """)
        
        if "file_url" in data:
            file_url = data.get("file_url")
        else :
            return HttpResponse("""
                <h2>未检测到歌曲文件路径</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/song/admin_add_song/">返回重新输入</a></p>
            """)


        # --------------------------
        # 4. 获取歌曲-歌手关系
        # --------------------------
        # 获取 singers_id
        if "singers_id" in data:
            singers_id = data.get("singers_id")
        else :
            return HttpResponse("""
                <h2>未检测到歌曲的歌手id</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/song/admin_add_song/">返回重新输入</a></p>
            """)
        
        # 不是列表则自动改成单元素列表
        if not isinstance(singers_id, list):
            singers_id = [singers_id]


        # --------------------------
        # 5. 正式添加歌曲
        # --------------------------
        sql_insert_song = """
            INSERT INTO Song (song_title, album_id, duration, file_url)
            VALUES (%s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_insert_song, [
                song_title, album_id, duration_seconds, file_url
                ])
        
            # 获取新插入的 song_id
            cursor.execute("SELECT LAST_INSERT_ID()")
            song_id = cursor.fetchone()[0]


        # 插入多对多关系
        sql_insert_m2m = """
            INSERT INTO Song_Singer (song_id, singer_id)
            VALUES (%s, %s)
        """

        with connection.cursor() as cursor:
            for singer_id in singers_id:
                cursor.execute(sql_insert_m2m, [song_id, singer_id])

        singers_str = ", ".join(str(sid) for sid in singers_id)
        return HttpResponse(f"""
                <h2>歌曲已添加</h2>
                <p><strong>歌曲名：</strong> {song_title}</p>
                <p><strong>歌曲id：</strong> {song_id}</p>
                <p><strong>歌手id：</strong> {singers_str}</p>
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            """)

    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 11. 删除歌曲（管理员权限）
# ================================
# http://127.0.0.1:8000/Administrator/song/admin_delete_song/ 
@csrf_exempt
def admin_delete_song(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

      
    if request.method == "GET":
        # --------------------------
        # 2. 展示删除歌曲界面
        # --------------------------
        return HttpResponse("""
            <h2>删除歌曲</h2>
            <form method="POST">
                <label>歌曲id：</label><br>
                <input name="song_id" required><br><br>

                <button type="submit">删除</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        if "song_id" not in data :
            return HttpResponse(f"""
                <h2>未检测到要删除的歌曲id</h2>
                <p><a href="/Administrator/song/admin_delete_song/">返回重新输入</a></p>
            """)
        else :
            song_id = data.get("song_id")


        # --------------------------
        # 3. 获取歌曲名、所属专辑和歌手
        # --------------------------
        sql_song = """
            SELECT s.song_title, a.album_title
            FROM Song s
            JOIN Album a ON a.album_id = s.album_id
            WHERE s.song_id = %s
        """

        sql_singers = """
            SELECT si.singer_name
            FROM Singer si
            JOIN Song_Singer ss ON si.singer_id = ss.singer_id
            WHERE ss.song_id = %s
        """

        with connection.cursor() as cursor:

            # 查询歌曲 + 专辑
            cursor.execute(sql_song, song_id)
            song_row = cursor.fetchone()

            if not song_row:
                return HttpResponse(f"""
                <h2>要删除的歌曲不存在</h2>
                <p><a href="/Administrator/song/admin_delete_song/">返回重新输入</a></p>
            """)
            
            song_title, album_title = song_row

            # 查询歌手列表
            cursor.execute(sql_singers, [song_id])
            singer_rows = cursor.fetchall()
            singers = [row[0] for row in singer_rows]
            singers_str = ", ".join(str(sid) for sid in singers)



        # --------------------------
        # 3. 正式删除歌曲
        # --------------------------
        # 先删除外键
        sql_delete_Song_Singer = "DELETE FROM Song_Singer WHERE song_id = %s"

        # 再删除本体
        sql_delete_Song = "DELETE FROM Song WHERE song_id=%s"

        with connection.cursor() as cursor:
            cursor.execute(sql_delete_Song_Singer, song_id)
            cursor.execute(sql_delete_Song, song_id)

        return HttpResponse(f"""
                <h2>歌曲已删除</h2>
                <p><strong>歌曲名：</strong> {song_title}</p>
                <p><strong>专辑名：</strong> {album_title}</p>
                <p><strong>歌手名：</strong> {singers_str}</p>
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            """)

    return json_cn({"error": "GET or POST required"}, 400)




# ================================
# 12. 搜索歌曲
# ================================
# http://127.0.0.1:8000/song/search_song/ 
@csrf_exempt
def search_song(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return HttpResponse("""
            <h2>请先登录</h2>
            <p><a href="/user/login/">点击前往登录</a></p>
        """)

    if request.method == "GET":
        # --------------------------
        # 2. 展示搜索歌曲界面
        # --------------------------
        return HttpResponse(f"""
            <h2>搜索歌曲</h2>
            <form method="POST">
                <label>歌曲名：(支持模糊搜索)</label><br>
                <input name="song_title"><br><br>

                <label>专辑名：(支持模糊搜索)</label><br>
                <input name="album_title"><br><br>
                                                     
                <label>歌手名：(支持模糊搜索)</label><br>
                <input name="singer_name"><br><br>
                            
                <button type="submit">搜索</button>
                            
                <p><a href="/music/">返回音乐中心</a></p>
            </form>
        """)


    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST    

            
        # --------------------------
        # 3. 获取搜索标签
        # --------------------------
        song_title = data.get("song_title", "").strip()
        album_title = data.get("album_title", "").strip()
        singer_name = data.get("singer_name", "").strip()

        filters = []
        params = []

        if song_title:
            filters.append("s.song_title LIKE %s")
            params.append(f"%{song_title}%")
        if album_title:
            filters.append("a.album_title LIKE %s")
            params.append(f"%{album_title}%")
        if singer_name:
            filters.append("si.singer_name LIKE %s")
            params.append(f"%{singer_name}%")


        # --------------------------
        # 4. 查询歌曲信息
        # --------------------------
        sql_song = """
            SELECT s.song_id, s.song_title, s.duration, a.album_title
            FROM Song s
            JOIN Album a ON a.album_id = s.album_id
        """
        
        sql_singers = """
            SELECT si.singer_name 
            FROM Singer si
            JOIN Song_Singer ss ON si.singer_id = ss.singer_id
            WHERE ss.song_id = %s
        """

        if filters:
            sql_song += " WHERE " + " AND ".join(filters)

 

        with connection.cursor() as cursor:
            cursor.execute(sql_song, params)
            rows = cursor.fetchall()

            if not rows:
                HttpResponse(f"""
                        <h2>未找到符合歌曲</h2><br>          
                        <p><a href="/song/search_song/">返回搜索界面</a></p>
                    """)
                
            # --------------------------
            # 5. 将信息转成HTML
            # --------------------------
            songs_html = ""
            for (song_id, song_title, duration, album_title) in rows :
                cursor.execute(sql_singers, [song_id])
                singer_rows = cursor.fetchall()
                singer_names = "、".join([row[0] for row in singer_rows]) if singer_rows else "未知"

                songs_html += f"""
                    <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                        <h4>歌曲名：{song_title}</h4> 
                        <p>歌手：{singer_names}</p>
                        <p>专辑：{album_title}</p>
                        <p>时长：{format_time(duration)}</p>

                        <p><a href="/song/profile/{song_id}/">详情</a></p>
                    </div>
                """

        return HttpResponse(f"""
            <p><a href="/music/">返回音乐中心</a></p>
                            
            <h2>搜索结果</h2>
            <ul>
                {songs_html}
            </ul>
        """)
    
    return json_cn({"error": "GET or POST required"}, 400)




# ================================
# 13. 歌曲详情
# ================================
# http://127.0.0.1:8000/song/profile/3/
@csrf_exempt
def song_profile(request, song_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行查看操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    user_id = request.session["user_id"]

    # --------------------------
    # 2. 查询歌曲信息
    # --------------------------
    sql_song = """
        SELECT s.song_id, s.song_title, s.duration, a.album_title
        FROM Song s
        JOIN Album a ON a.album_id = s.album_id
        WHERE s.song_id = %s
    """

    sql_singer = """
        SELECT sg.singer_id, sg.singer_name
        FROM Singer sg
        JOIN Song_Singer ss ON ss.singer_id = sg.singer_id
        WHERE ss.song_id = %s
    """

    sql_comment = """
        SELECT 
            u.user_id, u.user_name, c.comment_id, c.content, c.like_count, c.comment_time
        FROM Comment c 
        JOIN User u ON u.user_id = c.user_id
        WHERE target_id = %s AND target_type = 'song'
        ORDER BY comment_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_song, [song_id])
        song_row = cursor.fetchone()
        song_id, song_title, duration, album_title = song_row

        cursor.execute(sql_singer, [song_id])
        singer_rows = cursor.fetchall()
        singer_names = "、".join([row[1] for row in singer_rows]) if singer_rows else "未知"

        cursor.execute(sql_comment, [song_id])
        comment_rows = cursor.fetchall()
        comment_count = len(comment_rows)


    # --------------------------
    # 3. 歌曲评论
    # --------------------------
    comment_html = f"""
        <h2>歌曲评论（{comment_count} 个）</h2>
        <ul>
    """
    if comment_count == 0:
        comment_html += "<p>暂无评论。</p>"
    else:
        for user_id, user_name, comment_id, content, like_count, comment_time in comment_rows:
            comment_html += f"""
                <li>
                    <p>用户：<a href="/user/profile/{user_id}/">{user_name}</a><p>
                    内容：<strong>{content}</strong>

                    <form action="/comment/like_comment/{comment_id}/" method="post">
                        <input type="hidden" name="type" value="song">
                        <input type="hidden" name="id" value="{ song_id }">
                        <button type="submit">点赞</button>
                    </form>

                    <p>点赞数：{like_count}<p>
                    <p>评论时间：{comment_time.strftime("%Y-%m-%d %H:%M")}</p>

                </form>

                </li>
            """
    comment_html += "</ul><hr>"


    # --------------------------
    # 4. 生成最终 HTML
    # --------------------------
    return HttpResponse(f"""
        <h2>歌名：{song_title}</h2>
        <p>歌手：{singer_names}</a></p>
        <p>所属专辑：{album_title}</p>
        <p>时长：{format_time(duration)}</p>
        <p><a href="/song/search_song/">返回歌曲列表</a></p>

        <form action="/favorite/add_favorite/" method="post">
            <input type="hidden" name="type" value="song">
            <input type="hidden" name="id" value="{ song_id }">
            <button type="submit">收藏这首歌曲</button>
        </form>

        {comment_html}
        
        <h3>发表评论</h3>
        <form action="/comment/add_comment/" method="post">
            <input type="hidden" name="target_type" value="song">
            <input type="hidden" name="target_id" value="{ song_id }">

            <textarea name="content" rows="4" cols="50" required></textarea>
            <br>
            <button type="submit">提交评论</button>
        </form>

    """)