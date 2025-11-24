# 歌手与音乐模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .tools import *


# ================================
# 1. 新增歌手（管理员权限）
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
                    <input type="radio" name="type" value="男">男
                    <input type="radio" name="type" value="女">女
                    <input type="radio" name="type" value="组合">组合<br><br>
                            
                <label>国家：</label><br>
                <input name="country"><br><br>

                <label>生日：</label><br>
                <input name="type" type="date"><br><br>
                            
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
# 2. 删除歌手（管理员权限）
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
# 3. 查看歌手列表
# ================================
# http://127.0.0.1:8000/singer/list_singers/ 
@csrf_exempt
def list_singers(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)
    
    if request.method == "GET":
        # --------------------------
        # 2. 展示搜索歌手界面
        # --------------------------
        return HttpResponse("""
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
                            
                <p><a href="/user/profile/">返回个人界面</a></p>
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
            SELECT singer_name, type, country
            FROM Singer
            {where_clause}
            ORDER BY singer_name ASC
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        # ------------------------
        # 3. 查询数量
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
        # 4. 输出查找结果
        # --------------------------

        # 转换为 JSON 格式
        result = []
        for r in rows:
            result.append({
                "singer_name": r[0],
                "type": r[1],
                "country": r[2],
            })
        singers_list= "".join(
            f"<li>歌手名：{r['singer_name']} | 类型：{r['type']} | 国家：{r['country']}</li>" 
            for r in result
        )
        return HttpResponse(f"""
            <h2>歌手搜索结构</h2>
            <h2>歌手数:{total}</h2>            
            <ul>
                {singers_list if singers_list else '<li>无符合条件歌手</li>'}
            </ul>
            <p><a href="/user/profile/">返回个人中心</a></p>
        """)
    
    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 4. 新增专辑（管理员权限）
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
# 5. 删除专辑（管理员权限）
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
# 6. 查看专辑详情
# ================================
# http://127.0.0.1:8000/album/album_detail/ 
@csrf_exempt
def album_detail(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h3 style="color:red;">请先登录</h3>
            <a href="/user/login/">去登录</a>
        """)
    
    if request.method == "GET":
        # --------------------------
        # 2. 展示搜索专辑界面
        # --------------------------
        return HttpResponse("""
            <h2>搜索专辑</h2>
            <form method="POST">
                <label>专辑名：(支持模糊搜索)</label><br>
                <input name="album_name"><br><br>
                                                     
                <label>歌手名：(支持模糊搜索)</label><br>
                <input name="singer_name"><br><br>
                            
                <button type="submit">搜索</button>
                            
                <p><a href="/user/profile/">返回个人界面</a></p>
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
        album_name = data.get("album_name", "").strip()
        singer_name = data.get("singer_name", "").strip()

        filters = []
        params = []

        if album_name:
            filters.append("a.album_title LIKE %s")
            params.append(f"%{album_name}%")
        if singer_name:
            filters.append("s.singer_name LIKE %s")
            params.append(f"%{singer_name}%")


        # --------------------------
        # 4. 查询专辑信息
        # --------------------------
        sql_album = """
            SELECT a.album_title, s.singer_name, a.release_date, a.description, 
                   IFNULL(SUM(song.duration), 0) AS total_duration
            FROM Album a
            JOIN Singer s ON a.singer_id = s.singer_id
            LEFT JOIN Song song ON song.album_id = a.album_id
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
                    <p><a href="/user/profile/">返回个人界面</a></p>
                """)


        # --------------------------
        # 5. 将信息转成HTML
        # --------------------------
        albums_html = ""
        for r in rows:
            album_title, singer_name, release_date, description, total_duration = r
            minutes = total_duration // 60
            seconds = total_duration % 60
            albums_html += (
                f"<li>专辑名：{album_title} | 歌手名：{singer_name} | "
                f" 发行日期：{release_date} | 专辑总时长：{minutes}分{seconds}秒 |<br>"
                f" 专辑简介：{description} | </li>"
            )

        return HttpResponse(f"""
            <h2>搜索结果</h2>
            <ul>
                {albums_html}
            </ul>
            <p><a href="/user/profile/">返回个人界面</a></p>
        """)
    
    return json_cn({"error": "GET or POST required"}, 400)




# ================================
# 7. 添加歌曲（管理员权限）
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
                <input name="song_title"><br><br>

                <label>专辑ID：</label><br>
                <input name="album_id" type="number"><br><br>

                <label>时长（分:秒，例如 3:25）：</label><br>
                <input name="duration" type="text" placeholder="mm:ss"><br><br>

                <label>文件URL：</label><br>
                <input name="file_url"><br><br>

                <label>歌手ID（用逗号分隔）：</label><br>
                <input name="singers_id"><br><br>

                <button type="submit">提交</button>
                            
                <p><a href="/Administrator/profile/">返回管理员界面</a></p>
            </form>
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            # 如果不是 JSON，则从 form-data 获取
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
                <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
            """)
        
        if "album_id" in data:
            album_id = data.get("album_id")
        else :
            return HttpResponse("""
                <h2>未检测到所属专辑id</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
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
                    <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
                """)
        else :
            return HttpResponse("""
                <h2>未检测到歌曲时长</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
            """)
        
        if "file_url" in data:
            file_url = data.get("file_url")
        else :
            return HttpResponse("""
                <h2>未检测到歌曲文件路径</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
            """)


        # --------------------------
        # 4. 正式添加歌曲
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


        # --------------------------
        # 5. 完善歌曲-歌手关系
        # --------------------------
        # 获取 singers_id
        if "singers_id" in data:
            singers_id = data.get("singers_id")
        else :
            return HttpResponse("""
                <h2>未检测到歌曲的歌手id</h2>
                <p><a href="/user/login/">重新填写</a></p>
                <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
            """)
        
        # 不是列表则自动改成单元素列表
        if not isinstance(singers_id, list):
            singers_id = [singers_id]


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
                <p><a href="/Administrator/singer/admin_add_song/">返回重新输入</a></p>
            """)

    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 8. 删除歌曲（管理员权限）
# ================================
@csrf_exempt
def admin_delete_song(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    ok, resp = require_admin(request)
    if not ok:
        return resp

    data = json.loads(request.body)

    sql = "DELETE FROM Song WHERE song_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [data["song_id"]])

    return json_cn({"message": "歌曲已删除"})





# ================================
# 9. 查看歌曲详情
# ================================
@csrf_exempt
def song_detail(request, song_id):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    # 查询歌曲信息
    sql_song = "SELECT * FROM Song WHERE song_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_song, [song_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "Song not found"}, 404)

    song = {
        "song_id": row[0],
        "title": row[1],
        "album_id": row[2],
        "duration": row[3],
        "file_url": row[4]
    }

    # 查询演唱歌手
    sql_singers = """
        SELECT Singer.singer_id, Singer.name
        FROM Song_Singer 
        JOIN Singer ON Song_Singer.singer_id = Singer.singer_id
        WHERE Song_Singer.song_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_singers, [song_id])
        rows = cursor.fetchall()

    song["singers"] = [{"singer_id": r[0], "name": r[1]} for r in rows]

    return json_cn(song)


