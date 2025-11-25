# 收藏与歌单模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .tools import *


# ================================
# 1. 歌单中心
# ================================
# http://127.0.0.1:8000/songlist/list_songlists/
@csrf_exempt
def list_songlists(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再查看歌单</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 解析筛选参数
    # --------------------------
    is_public = request.GET.get("is_public")     # 可为 None / "1" / "0"
    sort_by = request.GET.get("sort_by", "create_time") # 默认按时间排序

    # --------------------------
    # 3. 构建 SQL
    # --------------------------
    sql = """
        SELECT songlist_id, songlist_title, description, create_time, cover_url, like_count, is_public
        FROM Songlist
        WHERE user_id = %s
    """

    params = [uid]

    # ---- 筛选公开性 ----
    if is_public in ["0", "1"]:
        sql += " AND is_public = %s"
        params.append(int(is_public))

    # ---- 排序 ----
    if sort_by == "likes":
        sql += " ORDER BY like_count DESC"
    else:
        sql += " ORDER BY create_time DESC"

    # --------------------------
    # 4. 执行 SQL 查询
    # --------------------------
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # --------------------------
    # 5. 渲染 HTML
    # --------------------------
    html_rows = ""
    for r in rows:
        sid, title, desc, ctime, cover, likes, public = r
        html_rows += f"""
            <div style='border:1px solid #ccc; padding:12px; margin-bottom:10px;'>
                <h3>{title}</h3>
                <img src="{cover}" style="width:120px;height:120px;">
                <p>{desc or ''}</p>
                <p>创建时间：{ctime.strftime("%Y-%m-%d %H:%M")}</p>
                <p>点赞数：{likes}</p>
                <p>公开性：{"公开" if public else "私密"}</p>
                <p>
                    <a href="/songlist/profile/{sid}/">查看详情</a> |
                    <a href="/songlist/edit_songlist/{sid}/">编辑</a> |
                    <a href="/songlist/delete_songlist/{sid}/">删除</a>
                </p>
            </div>
        """

    return HttpResponse(f"""
        <h2>我的歌单</h2>

        <form method="GET" action="/songlist/list_songlists/">
            <p>
                筛选公开性：
                <select name="is_public">
                    <option value="">全部</option>
                    <option value="1" {'selected' if is_public=='1' else ''}>公开</option>
                    <option value="0" {'selected' if is_public=='0' else ''}>私密</option>
                </select>
            </p>

            <p>
                排序方式：
                <select name="sort_by">
                    <option value="time" {'selected' if sort_by=='time' else ''}>按创建时间</option>
                    <option value="likes" {'selected' if sort_by=='likes' else ''}>按点赞数</option>
                </select>
            </p>

            <button type="submit">筛选结果</button>

            <p><a href="/songlist/create_songlist/">创建歌单</a></p>

            <p><a href="/user/profile/">返回用户中心</a></p>
        </form>

        <hr>
        {html_rows if html_rows else "<p>暂无歌单</p>"}
    """)

# ================================
# 2. 创建歌单
# ================================
# http://127.0.0.1:8000/songlist/create_songlist/
@csrf_exempt
def create_songlist(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再创建歌单</h2>
            <p><a href="/login/">返回登录</a></p>
        """, status=403)
    
    uid = request.session["user_id"]

    # --------------------------
    # 2. 展示创建歌单界面
    # --------------------------
    if request.method == "GET":
        return HttpResponse("""
            <h2>创建新的歌单</h2>
            <form method="POST" action="/songlist/create_songlist/">
                <p>歌单名称：<input name="songlist_title" required></p>
                <p>封面地址：<input name="cover_url"></p>
                <p>简介：<textarea name="description"></textarea></p>
                <p>是否公开：
                    <select name="is_public">
                        <option value="1">公开</option>
                        <option value="0">私密</option>
                    </select>
                </p>
                <button type="submit">创建</button>
                
                <p><a href="/songlist/list_songlists/">返回歌单中心</a></p>
            </form>
        """)

    # --------------------------
    # 3. 接收数据并校验
    # --------------------------
    if request.method == "POST":
        # 允许 JSON + Form 两种格式
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # ----------- 必填字段 -----------
        if "songlist_title" in data:
            songlist_title = data.get("songlist_title").strip()
        else:
            return HttpResponse("""
                <h2>缺少歌单名称</h2>
                <p><a href="/songlist/create_songlist/">返回创建页面</a></p>
            """)

        # ----------- 可选字段 + 默认值处理 -----------
        optional_fields = ["description", "is_public", "cover_url"]
        defaults = {
            "description": None,
            "is_public": 1,
            "cover_url": "/images/default_songlist_cover.jpg"
        }

        cleaned = {}
        for field in optional_fields:
            value = data.get(field, defaults[field])
            if value == "":
                value = defaults[field]
            cleaned[field] = value

        description = cleaned["description"]
        is_public = int(cleaned["is_public"])
        cover_url = cleaned["cover_url"]

        # --------------------------
        # 4. 正式创建歌单
        # --------------------------
        sql = """
            INSERT INTO Songlist (user_id, songlist_title, description, is_public, cover_url)
            VALUES (%s, %s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [uid, songlist_title, description, is_public, cover_url])

        return HttpResponse(f"""
            <h2>成功创建歌单：{songlist_title}</h2>
            <p><a href="/songlist/list_songlists/">返回歌单中心</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)


# ================================
# 3. 编辑歌单
# ================================
# http://127.0.0.1:8000/songlist/edit_songlist/1/
@csrf_exempt
def edit_songlist(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再编辑歌单</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_select = """
        SELECT user_id, songlist_title, description, is_public, cover_url
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_select, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>歌单不存在</h2>
            <p><a href="/user/profile/">返回用户中心</a></p>
        """, status=404)

    owner_id, old_title, old_desc, old_public, old_cover = row

    if owner_id != uid:
        return HttpResponse("""
            <h2>无权限：你不是该歌单的创建者</h2>
            <p><a href="/user/profile/">返回用户中心</a></p>
        """, status=403)
    

    # --------------------------
    # 3. GET：展示编辑页面
    # --------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>编辑歌单</h2>
            <form method="POST" action="/songlist/edit_songlist/{songlist_id}/">
                <p>歌单名称：<input name="songlist_title" value="{old_title}" required></p>
                <p>简介：<textarea name="description">{old_desc or ""}</textarea></p>
                <p>是否公开：
                    <select name="is_public">
                        <option value="1" {'selected' if old_public else ''}>公开</option>
                        <option value="0" {'selected' if not old_public else ''}>私密</option>
                    </select>
                </p>
                <p>封面 URL：<input name="cover_url" value="{old_cover}"></p>
                <button type="submit">保存修改</button>

                <p><a href="/songlist/list_songlists/">返回歌单中心</a></p>
            </form>
        """)
 

    # --------------------------
    # 4. POST：接收并校验数据
    # --------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # ----------- 必填字段 -----------
        if "songlist_title" in data:
            songlist_title = data.get("songlist_title").strip()
        else:
            return HttpResponse(f"""
                <h2>修改失败：缺少歌单名称</h2>
                <p><a href="/songlist/edit_songlist/{songlist_id}/">返回编辑页面</a></p>
            """, status=400)

        # ----------- 可选字段 -----------
        optional_fields = ["description", "is_public", "cover_url"]
        defaults = {
            "description": old_desc,
            "is_public": old_public,
            "cover_url": old_cover,
        }

        cleaned = {}
        for field in optional_fields:
            value = data.get(field, defaults[field])
            if value == "":
                value = defaults[field]
            cleaned[field] = value

        description = cleaned["description"]
        is_public = int(cleaned["is_public"])
        cover_url = cleaned["cover_url"]

        # --------------------------
        # 5. SQL 更新操作
        # --------------------------
        sql_update = """
            UPDATE Songlist
            SET songlist_title = %s, description = %s, is_public = %s, cover_url = %s
            WHERE songlist_id = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_update, [
                songlist_title, description, is_public, cover_url, songlist_id
            ])

        return HttpResponse(f"""
            <h2>歌单修改成功：{songlist_title}</h2>
            <p><a href="/songlist/profile/{songlist_id}/">前往歌单详情</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)


# ================================
# 4. 歌单详情
# ================================
# http://127.0.0.1:8000/singer/profile/2/
@csrf_exempt
def songlist_profile(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行查看操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单信息
    # --------------------------
    sql_list = """
        SELECT user_id, songlist_title, description, create_time, cover_url,
               like_count, is_public
        FROM Songlist
        WHERE songlist_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_list, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>歌单不存在</h2>
            <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
        """, status=404)

    owner_id, title, desc, ctime, cover, likes, is_public = row

    # --------------------------
    # 3. 私密歌单权限判断
    # --------------------------
    if is_public == 0:
        if uid != owner_id:
            return HttpResponse("""
                <h2>这是一个私密歌单，你无权查看</h2>
                <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
            """, status=403)

    # --------------------------
    # 4. 查询歌单中的歌曲列表
    # --------------------------
    sql_songs = """
        SELECT 
            s.song_id,
            s.song_title,
            s.duration,
            a.album_title AS album_title,
            sg.singer_name
        FROM Songlist_Song ss
        JOIN Song s ON ss.song_id = s.song_id
        JOIN Album a ON s.album_id = a.album_id
        JOIN Song_Singer ss2 ON s.song_id = ss2.song_id
        JOIN Singer sg ON ss2.singer_id = sg.singer_id
        WHERE ss.songlist_id = %s
        ORDER BY ss.add_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songs, [songlist_id])
        song_rows = cursor.fetchall()

    # --------------------------
    # 5. 计算总时长
    # --------------------------
    total_duration = sum([row[2] for row in song_rows])  # row[2] 是 duration

    total_duration_fmt = format_time(total_duration)

    # --------------------------
    # 6. 生成歌曲 HTML
    # --------------------------
    songs_html = ""
    for (sid, stitle, dur, album_title, singer_name) in song_rows:
        songs_html += f"""
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h4>{stitle}</h4>
                <p>歌手：{singer_name}</p>
                <p>所属专辑：{album_title}</p>
                <p>时长：{format_time(dur)}</p>
                <p>
                    {"<a href='/songlist/%d/delete_song/%d/'>从歌单移除</a>" % (songlist_id, sid) if uid == owner_id else ""}
                </p>
            </div>
        """

    if not songs_html:
        songs_html = "<p>该歌单还没有添加任何歌曲。</p>"

    # --------------------------
    # 7. 生成最终 HTML
    # --------------------------
    return HttpResponse(f"""
        <h2>歌单详情：{title}</h2>
        <img src="{cover}" style="width:180px;height:180px;">
        <p>歌单介绍：{desc or ''}</p>
        <p>创建时间：{ctime.strftime("%Y-%m-%d %H:%M")}</p>
        <p>点赞数：{likes}</p>
        <p>公开性：{"公开" if is_public else "私密"}</p>
        <p>歌曲数量：{len(song_rows)}</p>
        <p>总时长：{total_duration_fmt}</p>

        <p>
            {"<a href='/songlist/%d/add_song/'>添加歌曲到歌单</a>" % songlist_id if uid == owner_id else ""}
        </p>

        <p>
            {"<a href='/songlist/sort_songlist/%d/'>对歌曲排序</a>" % songlist_id if uid == owner_id else ""}
        </p>
        
        <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>

        <hr>
        <h3>歌曲列表</h3>
        {songs_html}

        <hr>
    """)




# ================================
# 5. 删除歌单
# ================================
# http://127.0.0.1:8000/songlist/delete_songlist/1/
@csrf_exempt
def delete_songlist(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行删除操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_select = """
        SELECT user_id, songlist_title
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_select, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>删除失败：该歌单不存在</h2>
            <p><a href="/songlist/list_songlists/">返回歌单中心</a></p>
        """, status=404)

    owner_id, title = row

    if owner_id != uid:
        return HttpResponse("""
            <h2>无权限删除：你不是该歌单的创建者</h2>
            <p><a href="/songlist/list_songlists/">返回歌单中心</a></p>
        """, status=403)

    # --------------------------
    # 3. GET：展示确认页面
    # --------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>确认删除歌单：{title}</h2>
            <p>删除后不可恢复，包含的歌曲关系也将全部删除。</p>
            <form method="POST" action="/songlist/delete_songlist/{songlist_id}/">
                <button type="submit">确认删除</button>
            </form>
            <p><a href="/songlist/list_songlists/">取消并返回歌单中心</a></p>
        """)

    # --------------------------
    # 4. POST：执行删除
    # --------------------------
    if request.method == "POST":
        sql_delete = """
            DELETE FROM Songlist
            WHERE songlist_id = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_delete, [songlist_id])

        return HttpResponse(f"""
            <h2>成功删除歌单：{title}</h2>
            <p><a href="/songlist/list_songlists/">返回歌单中心</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 6. 向歌单插入歌曲
# ================================
# http://127.0.0.1:8000/songlist/2/add_song
@csrf_exempt
def songlist_add_song(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再添加歌曲到歌单</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_select = """
        SELECT user_id, songlist_title
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_select, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>该歌单不存在</h2>
            <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
        """, status=404)

    owner_id, songlist_title = row

    if owner_id != uid:
        return HttpResponse("""
            <h2>无权限：你不是该歌单的创建者</h2>
            <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
        """, status=403)

    # --------------------------
    # 3. GET：展示添加歌曲页面
    # --------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>向歌单：{songlist_title} 添加歌曲</h2>
            <form method="POST" action="/songlist/{songlist_id}/add_song/">
                <p>歌曲 ID：<input name="song_id" required></p>
                <button type="submit">添加</button>
            </form>
            <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
        """)

    # --------------------------
    # 4. POST：接收并校验数据
    # --------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        if "song_id" not in data:
            return HttpResponse(f"""
                <h2>添加失败：缺少 song_id</h2>
                <p><a href="/songlist/{songlist_id}/add_song/">返回添加页面</a></p>
            """, status=400)

        try:
            song_id = int(data.get("song_id"))
        except:
            return HttpResponse(f"""
                <h2>song_id 必须是数字</h2>
                <p><a href="/songlist/{songlist_id}/add_song/">返回添加页面</a></p>
            """, status=400)

        # --------------------------
        # 5. 检查歌曲是否存在
        # --------------------------
        sql_check_song = "SELECT song_id, song_title FROM Song WHERE song_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check_song, [song_id])
            song_row = cursor.fetchone()

        if not song_row:
            return HttpResponse(f"""
                <h2>歌曲不存在：ID = {song_id}</h2>
                <p><a href="/songlist/{songlist_id}/add_song/">返回添加页面</a></p>
            """, status=404)

        song_title = song_row[1]

        # --------------------------
        # 6. 检查是否已在歌单中
        # --------------------------
        sql_check_exist = """
            SELECT 1 FROM Songlist_Song
            WHERE songlist_id = %s AND song_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql_check_exist, [songlist_id, song_id])
            exists = cursor.fetchone()

        if exists:
            return HttpResponse(f"""
                <h2>添加失败：歌曲《{song_title}》已在歌单中</h2>
                <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
            """, status=400)

        # --------------------------
        # 7. SQL 插入关系记录
        # --------------------------
        sql_insert = """
            INSERT INTO Songlist_Song (songlist_id, song_id)
            VALUES (%s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_insert, [songlist_id, song_id])

        return HttpResponse(f"""
            <h2>成功添加歌曲：{song_title}</h2>
            <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 7. 删除歌单中的歌曲
# ================================
# http://127.0.0.1:8000/songlist/2/delete_song/6
@csrf_exempt
def songlist_delete_song(request, songlist_id, song_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行移除操作</h2>
            <p><a href="/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_songlist = """
        SELECT user_id, songlist_title
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songlist, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("""
            <h2>歌单不存在</h2>
            <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
        """, status=404)

    owner_id, songlist_title = row

    if owner_id != uid:
        return HttpResponse("""
            <h2>无权限：你不是该歌单的创建者</h2>
            <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
        """, status=403)

    # --------------------------
    # 3. 查询歌曲是否存在 + 是否在歌单中
    # --------------------------
    sql_song = "SELECT song_title FROM Song WHERE song_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_song, [song_id])
        song_row = cursor.fetchone()

    if not song_row:
        return HttpResponse(f"""
            <h2>歌曲不存在：ID = {song_id}</h2>
            <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
        """, status=404)

    song_title = song_row[0]

    sql_check = """
        SELECT 1 FROM Songlist_Song
        WHERE songlist_id = %s AND song_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_check, [songlist_id, song_id])
        exists = cursor.fetchone()

    if not exists:
        return HttpResponse(f"""
            <h2>歌曲《{song_title}》不在该歌单中</h2>
            <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
        """, status=400)

    # --------------------------
    # 4. GET：展示确认删除页面
    # --------------------------
    if request.method == "GET":
        return HttpResponse(f"""
            <h2>确认从歌单《{songlist_title}》移除歌曲：{song_title}</h2>
            <form method="POST" action="/songlist/{songlist_id}/delete_song/{song_id}/">
                <button type="submit">确认移除</button>
            </form>
            <p><a href="/songlist/profile/{songlist_id}/">取消</a></p>
        """)

    # --------------------------
    # 5. POST：执行删除
    # --------------------------
    if request.method == "POST":
        sql_delete = """
            DELETE FROM Songlist_Song
            WHERE songlist_id = %s AND song_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql_delete, [songlist_id, song_id])

        return HttpResponse(f"""
            <h2>已成功从歌单移除：{song_title}</h2>
            <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
        """)

    return json_cn({"error": "GET or POST required"}, 400)



# ================================
# 7. 对歌单中的歌曲排序
# ================================
# http://127.0.0.1:8000/songlist/sort_songlist/2
@csrf_exempt
def sort_songlist(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录后再进行排序操作</h2>
            <p><a href="/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单信息（获取权限）
    # --------------------------
    sql_info = """
        SELECT user_id, songlist_title, is_public
        FROM Songlist
        WHERE songlist_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_info, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("<h2>歌单不存在</h2>", status=404)

    owner_id, title, is_public = row

    # 私密歌单权限检查
    if is_public == 0 and uid != owner_id:
        return HttpResponse("<h2>无权查看私密歌单</h2>", status=403)

    # --------------------------
    # 3. 获取排序方式（默认按添加时间）
    # --------------------------
    sort = request.GET.get("sort", "add_time")  # add_time / duration / play_count

    # 白名单，安全避免 SQL 注入
    sort_map = {
        "add_time": "ss.add_time DESC",
        "duration": "s.duration DESC",
        "play_count": "s.play_count DESC",
    }

    if sort not in sort_map:
        sort = "add_time"

    order_sql = sort_map[sort]

    # --------------------------
    # 4. 查询排序后的歌曲列表
    # --------------------------
    sql_songs = f"""
        SELECT 
            s.song_id,
            s.song_title,
            s.duration,
            a.album_title AS album_title,
            sg.singer_name,
            ss.add_time
        FROM Songlist_Song ss
        JOIN Song s ON ss.song_id = s.song_id
        JOIN Album a ON s.album_id = a.album_id
        JOIN Song_Singer ss2 ON s.song_id = ss2.song_id
        JOIN Singer sg ON ss2.singer_id = sg.singer_id
        WHERE ss.songlist_id = %s
        ORDER BY {order_sql}
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songs, [songlist_id])
        rows = cursor.fetchall()

    # --------------------------
    # 5. 格式化 HTML
    # --------------------------

    songs_html = ""
    for sid, name, duration, album, singer, add_time in rows:
        songs_html += f"""
            <div style="border:1px solid #ccc; margin-bottom:10px; padding:10px;">
                <h4>{name}</h4>
                <p>歌手：{singer}</p>
                <p>专辑：{album}</p>
                <p>时长：{format_time(duration)}</p>
                <p>添加时间：{add_time.strftime("%Y-%m-%d %H:%M")}</p>
                <p><a href="/song/detail/{sid}/">查看歌曲</a></p>
            </div>
        """

    if not songs_html:
        songs_html = "<p>该歌单没有包含任何歌曲。</p>"

    # --------------------------
    # 6. 排序按钮
    # --------------------------
    sort_html = f"""
        <p>
            排序方式：
            <a href="/songlist/sort_songlist/{songlist_id}/?sort=add_time">按添加时间</a> |
            <a href="/songlist/sort_songlist/{songlist_id}/?sort=play_count">按播放次数</a> |
            <a href="/songlist/sort_songlist/{songlist_id}/?sort=duration">按时长</a>
        </p>
        <hr>
    """

    # --------------------------
    # 7. 最终输出
    # --------------------------
    return HttpResponse(f"""
        <h2>歌单排序：{title}</h2>
        {sort_html}
        {songs_html}
        <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
    """)





# ================================
# 8. 进行收藏操作
# ================================
@csrf_exempt
def favorite_add(request):
    # --------------------------
    # 1. 必须登录
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录再进行收藏</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 获取数据
    # --------------------------
    if request.method != "POST":
        return HttpResponse("""
            <h2>仅支持 POST</h2>
        """, status=400)

    # JSON OR form
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    fav_type = data.get("type")
    target_id = data.get("id")

    if not fav_type or not target_id:
        return HttpResponse("""
            <h2>缺少必要参数(type, id)</h2>
            <p><a href="/">返回首页</a></p>
        """, status=400)

    # --------------------------
    # 3. 判断类型，动态生成表名与字段
    # --------------------------
    table_map = {
        "song": ("Favorite_Song", "song_id"),
        "album": ("Favorite_Album", "album_id"),
        "songlist": ("Favorite_Songlist", "songlist_id"),
    }

    if fav_type not in table_map:
        return HttpResponse(f"""
            <h2>不支持的收藏类型：{fav_type}</h2>
            <p><a href="/">返回首页</a></p>
        """, status=400)

    table, col = table_map[fav_type]

    # --------------------------
    # 4. 检查是否已收藏
    # --------------------------
    sql_check = f"""
        SELECT 1
        FROM {table}
        WHERE user_id = %s AND {col} = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [uid, target_id])
        exists = cursor.fetchone()

    if exists:
        return HttpResponse(f"""
            <h2>已经收藏过了！</h2>
            <p><a href="/{fav_type}/{target_id}/">返回详情页</a></p>
        """)

    # --------------------------
    # 5. 插入收藏记录
    # --------------------------
    sql_insert = f"""
        INSERT INTO {table}(user_id, {col}, create_time)
        VALUES(%s, %s, NOW())
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, [uid, target_id])

    # --------------------------
    # 6. 返回成功页面
    # --------------------------
    return HttpResponse(f"""
        <h2>收藏成功！</h2>
        <p><a href="/{fav_type}/{target_id}/">返回详情页</a></p>
    """)
