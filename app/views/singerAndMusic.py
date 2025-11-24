# 歌手与音乐模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .tools import *


# ================================
# 1. 新增歌手（管理员权限）
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/Administrator/singer/admin_add_singer/ ^
# -H "Content-Type: application/json" ^
# -d "{\"singer_name\":\"周杰伦\", \"type\":\"男\", \"country\":\"中国\", \"birthday\":\"1979-01-18\", \"type\":\"男\", \"introduction\":\"周杰伦（Jay Chou），1979年1月18日出生于台湾省新北市，祖籍福建省永春县，华语流行乐男歌手、音乐人、演员、导演。\"}" ^
# -b cookie.txt
@csrf_exempt
def admin_add_singer(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok :
        return resp

    # --------------------------
    # 2. 获取歌手数据并校验
    # --------------------------
    data = json.loads(request.body)

    if "type" in data:
        singer_name = data.get("singer_name")
    else :
        return json_cn({"error": "未检测到歌手名称"}, 400)
    
    if "type" in data:
        if data["type"] not in ["男", "女", "组合"]:
            return json_cn({"error": "非法类别，只能为：男/女/组合"}, 400)
        else :
            type = data.get("type")
    else :
        return json_cn({"error": "未检测到歌手类别"}, 400)

    # -------- 可选字段，但要处理默认值 --------
    country = data.get("country", None)
    birthday = data.get("birthday", None)
    introduction = data.get("introduction", None)

    # --------------------------
    # 3. 正式添加歌手
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

    return json_cn({"message": "歌手已经添加"})



# ================================
# 1. 删除歌手（管理员权限）
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/Administrator/singer/admin_delete_singer/ ^
# -H "Content-Type: application/json" ^
# -d {\"singer_id\":8} ^
# -b cookie.txt
@csrf_exempt
def admin_delete_singer(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok :
        return resp


    # --------------------------
    # 2. 获取歌手id并校验
    # --------------------------
    data = json.loads(request.body)
    singer_id = data["singer_id"]

    if not singer_id :
        json_cn({"error": "请输入歌手id"})

    name_sql = """
        SELECT singer_name
        FROM Singer 
        WHERE singer_id = %s      
    """
    with connection.cursor() as cursor:
        cursor.execute(name_sql, [singer_id])
        row = cursor.fetchone()
    
    if row is None :
        return json_cn({"error": "歌手不存在"}, 404)
    
    singer_name = row[0]

    # --------------------------
    # 3. 删除对应歌手
    # --------------------------

    delete_sql = """
        DELETE 
        FROM Singer 
        WHERE singer_id = %s   
    """
    with connection.cursor() as cursor:
        cursor.execute(delete_sql, [singer_id])

    return json_cn({
    "message": "歌手删除成功",
    "singer_id": singer_id,
    "singer_name": singer_name
})


# ================================
# 3. 查看歌手列表（支持过滤）
# ================================
# 示例：
# curl -G http://127.0.0.1:8000/singer/list_singers/ ^
# --data-urlencode "country=新加坡" ^
# --data-urlencode "gender=男"
@csrf_exempt
def list_singers(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    # --------------------------
    # 1. 获取筛选标签
    # --------------------------
    filters = []
    params = []

    type = request.GET.get("type")
    country = request.GET.get("country")
    singer_name = request.GET.get("singer_name")

    if type:
        filters.append("type = %s")
        params.append(type)
    if country:
        filters.append("country = %s")
        params.append(country)
    if singer_name:
        filters.append("singer_name LIKE %s")
        params.append("%" + singer_name + "%")

    # --------------------------
    # 2. 正式查找歌手
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
    return json_cn({"total": total, "singers": rows})



# ================================
# 4. 新增专辑（管理员权限）
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/Administrator/singer/admin_add_album/ ^
# -H "Content-Type: application/json" ^
# -d @data.json ^
# -b cookie.txt
@csrf_exempt
def admin_add_album(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp


    # --------------------------
    # 2. 获取专辑数据并校验
    # --------------------------
    data = json.loads(request.body)

    if "album_title" in data:
        album_title = data.get("album_title")
    else :
        return json_cn({"error": "未检测到专辑名称"}, 400)
    
    if "singer_id" in data:
        singer_id = data.get("singer_id")
    else :
        return json_cn({"error": "未检测到歌手id"}, 400)

    release_date = data.get("release_date", "1970-01-01")
    cover_url = data.get("cover_url", "/images/default_album_cover.jpg")
    description = data.get("description", None)


    # --------------------------
    # 3. 正式添加专辑
    # --------------------------

    sql = """
        INSERT INTO Album (album_title, singer_id, release_date, cover_url, description)
        VALUES (%s, %s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [
            album_title, singer_id, release_date, cover_url, description,
            ])

    return json_cn({"message": "专辑已添加"})



# ================================
# 5. 删除专辑（管理员权限）
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/Administrator/singer/admin_add_album/ ^
# -H "Content-Type: application/json" ^
# -d @data.json ^
# -b cookie.txt
@csrf_exempt
def admin_delete_album(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp


    # --------------------------
    # 2. 获取要删除的专辑数据
    # --------------------------
    data = json.loads(request.body)

    if "album_id" in data :
        album_id = data.get("album_id")
    else :
        json_cn({"error": "请输入要删除的专辑id"}, 400)


    # --------------------------
    # 3. 获取专辑标题
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
        return json_cn({"error": "专辑不存在"}, 404)
    
    album_title = row[0]

    # --------------------------
    # 4. 正式删除专辑
    # --------------------------
    sql = "DELETE FROM Album WHERE album_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [album_id])

    return json_cn({
        "message": "专辑删除成功",
        "album_id": album_id,
        "album_title": album_title
    })



# ================================
# 6. 查看专辑详情
# ================================
# 示例：
# curl -G http://127.0.0.1:8000/album/album_detail/ ^
# --data-urlencode "album_id=3" 
@csrf_exempt
def album_detail(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)
    
    # --------------------------
    # 1. 获取专辑id
    # --------------------------
    album_id = request.GET.get("album_id")
    if not album_id :
        return json_cn({"error": "请输入专辑id"}, 400)

    # --------------------------
    # 2. 查询专辑信息
    # --------------------------
    sql_album = """
        SELECT *
        FROM Album 
        WHERE album_id = %s      
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_album, [album_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "未找到专辑", "album_id": album_id}, 404)


    # --------------------------
    # 3. 将信息转成字典
    # --------------------------
    album = {
        "album_id": row[0],
        "title": row[1],
        "singer_id": row[2],
        "release_date": row[3],
        "cover_url": row[4],
        "description": row[5]
    }


    # --------------------------
    # 4. 获取专辑总时长
    # --------------------------
    sql_sum = """
        SELECT SUM(duration) 
        FROM Song 
        WHERE album_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_sum, [album_id])
        total = cursor.fetchone()[0]

    album["total_duration"] = total if total else 0

    return json_cn(album)




# ================================
# 7. 添加歌曲（管理员权限）
# ================================
# 示例：
# curl -X POST http://127.0.0.1:8000/Administrator/singer/admin_add_song/ ^
# -H "Content-Type: application/json" ^
# -d @data.json ^
# -b cookie.txt
@csrf_exempt
def admin_add_song(request):
    if request.method != "POST" and request.method != "GET":
        return json_cn({"error": "POST or GET required"}, 400)
    
    if request.method == "GET":
        # 返回一个简单的 HTML 表单
        return HttpResponse("""
            <h2>添加歌曲</h2>
            <form method="POST">
                <label>歌曲名：</label><br>
                <input name="song_title"><br><br>

                <label>专辑ID：</label><br>
                <input name="album_id" type="number"><br><br>

                <label>时长（秒）：</label><br>
                <input name="duration" type="number"><br><br>

                <label>文件URL：</label><br>
                <input name="file_url"><br><br>

                <label>歌手ID（用逗号分隔）：</label><br>
                <input name="singers_id"><br><br>

                <button type="submit">提交</button>
            </form>
        """)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            # 如果不是 JSON，则从 form-data 获取
            data = request.POST


    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp


    # --------------------------
    # 2. 获取歌曲数据并校验
    # --------------------------
    data = json.loads(request.body)

    if "song_title" in data:
        song_title = data.get("song_title")
    else :
        return json_cn({"error": "未检测到歌曲名称"}, 400)
    
    if "album_id" in data:
        album_id = data.get("album_id")
    else :
        return json_cn({"error": "未检测到所属专辑id"}, 400)
    
    if "duration" in data:
        duration = data.get("duration")
    else :
        return json_cn({"error": "未检测到歌曲时长"}, 400)
    
    if "file_url" in data:
        file_url = data.get("file_url")
    else :
        return json_cn({"error": "未检测到歌曲文件路径"}, 400)


    # --------------------------
    # 3. 正式添加歌曲
    # --------------------------
    sql_insert_song = """
        INSERT INTO Song (song_title, album_id, duration, file_url)
        VALUES (%s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert_song, [
            song_title, album_id, duration, file_url
            ])
    
        # 获取新插入的 song_id
        cursor.execute("SELECT LAST_INSERT_ID()")
        song_id = cursor.fetchone()[0]


    # --------------------------
    # 4. 完善歌曲-歌手关系
    # --------------------------
    # 获取 singers_id
    if "singers_id" in data:
        singers_id = data.get("singers_id")
    else :
        return json_cn({"error": "未检测到歌曲的歌手id"}, 400)
    
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

    return json_cn({"message": "歌曲已添加", 
                    "song_id": song_id,
                    "singers_id": singers_id})



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


