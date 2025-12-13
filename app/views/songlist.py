# 歌单与收藏模块 (Songlist and Favorite Module)
# Consolidated from favoriteAndSonglist.py and songlistAndFavorite.py

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .tools import *


# ================================
# Helper Functions
# ================================
def check_user_auth(user_id, songlist_id):
    """检查用户是否有权限操作歌单"""
    if user_id == 1:  # 管理员
        return True

    sql = """
          SELECT 1
          FROM Songlist
          WHERE songlist_id = %s 
            AND user_id = %s
          """

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_id, user_id])
        row = cursor.fetchone()

    return row is not None


# ================================
# Songlist Management
# ================================

# 创建歌单 (API)
@csrf_exempt
def add_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    songlist_title = data.get("songlist_title")
    if not songlist_title:
        return json_cn({"error": "未检测到歌单名称"}, 400)

    description = data.get("description", None)
    cover_url = data.get("cover_url", '/images/default_songlist_cover.jpg')
    is_public = data.get("is_public", True)

    sql = """
        INSERT INTO Songlist(songlist_title, user_id, description, cover_url, is_public)
        VALUES(%s, %s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_title, current_user_id, description, cover_url, is_public])

    return json_cn({"message": "歌单已添加"})


# 创建歌单 (HTML界面)
@csrf_exempt
def create_songlist(request):
    if "user_id" not in request.session:
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>请先登录</title></head>
            <body>
                <h2>请先登录后再创建歌单</h2>
                <p><a href="/user/login/">返回登录</a></p>
            </body>
            </html>
        """, status=403)

    uid = request.session["user_id"]

    if request.method == "GET":
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>创建歌单</title></head>
            <body>
                <h2>创建歌单</h2>
                <form method="POST">
                    <label>歌单名称：</label><br>
                    <input name="songlist_title" required><br><br>

                    <label>简介：</label><br>
                    <textarea name="description"></textarea><br><br>

                    <label>封面URL：</label><br>
                    <input name="cover_url"><br><br>

                    <label>公开性：</label>
                    <input type="radio" name="is_public" value="1" checked>公开
                    <input type="radio" name="is_public" value="0">私密<br><br>

                    <button type="submit">创建</button>
                </form>
            </body>
            </html>
        """)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        title = data.get("songlist_title")
        description = data.get("description", "")
        cover_url = data.get("cover_url", "/images/default_songlist_cover.jpg")
        is_public = int(data.get("is_public", 1))

        sql = """
            INSERT INTO Songlist (songlist_title, user_id, description, cover_url, is_public)
            VALUES (%s, %s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [title, uid, description, cover_url, is_public])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>创建成功</title></head>
            <body>
                <h2>歌单创建成功！</h2>
                <p><a href="/songlist/list_songlists/">查看我的歌单</a></p>
            </body>
            </html>
        """)


# 删除歌单 (API)
@csrf_exempt
def delete_songlist(request, songlist_id=None):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    
    if songlist_id is None:
        data = json.loads(request.body)
        songlist_id = data.get("songlist_id")

    if not songlist_id:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    sql_delete_songlist_song = "DELETE FROM Songlist_Song WHERE songlist_id = %s"
    sql_delete_songlist = "DELETE FROM Songlist WHERE songlist_id = %s AND user_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_delete_songlist_song, [songlist_id])
        cursor.execute(sql_delete_songlist, [songlist_id, current_user_id])

    return json_cn({"message": "歌单已删除"})


# 修改歌单 (API)
@csrf_exempt
def update_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    songlist_id = data.get("songlist_id")
    if not songlist_id:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    if "songlist_title" in data:
        sql = "UPDATE Songlist SET songlist_title = %s WHERE songlist_id = %s AND user_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [data.get("songlist_title"), songlist_id, current_user_id])

    if "description" in data:
        sql = "UPDATE Songlist SET description = %s WHERE songlist_id = %s AND user_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [data.get("description"), songlist_id, current_user_id])

    if "is_public" in data:
        sql = "UPDATE Songlist SET is_public = %s WHERE songlist_id = %s AND user_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [data.get("is_public"), songlist_id, current_user_id])

    return json_cn({"message": "歌单修改已完成"})


# 编辑歌单 (HTML界面)
@csrf_exempt
def edit_songlist(request, songlist_id):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    uid = request.session["user_id"]

    if not check_user_auth(uid, songlist_id):
        return json_cn({"error": "无权编辑此歌单"}, 403)

    if request.method == "GET":
        sql = """
            SELECT songlist_title, description, cover_url, is_public
            FROM Songlist
            WHERE songlist_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [songlist_id])
            row = cursor.fetchone()

        if not row:
            return json_cn({"error": "歌单不存在"}, 404)

        title, desc, cover, is_public = row

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>编辑歌单</title></head>
            <body>
                <h2>编辑歌单</h2>
                <form method="POST">
                    <label>歌单名称：</label><br>
                    <input name="songlist_title" value="{title}" required><br><br>

                    <label>简介：</label><br>
                    <textarea name="description">{desc or ''}</textarea><br><br>

                    <label>封面URL：</label><br>
                    <input name="cover_url" value="{cover}"><br><br>

                    <label>公开性：</label>
                    <input type="radio" name="is_public" value="1" {'checked' if is_public else ''}>公开
                    <input type="radio" name="is_public" value="0" {'checked' if not is_public else ''}>私密<br><br>

                    <button type="submit">保存</button>
                </form>
            </body>
            </html>
        """)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        sql = """
            UPDATE Songlist
            SET songlist_title = %s, description = %s, cover_url = %s, is_public = %s
            WHERE songlist_id = %s AND user_id = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [
                data.get("songlist_title"),
                data.get("description"),
                data.get("cover_url"),
                int(data.get("is_public", 1)),
                songlist_id,
                uid
            ])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>编辑成功</title></head>
            <body>
                <h2>歌单编辑成功！</h2>
                <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
            </body>
            </html>
        """)


# 向歌单添加歌曲 (API)
@csrf_exempt
def add_song_to_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    songlist_id = data.get("songlist_id")
    song_id = data.get("song_id")

    if not songlist_id or not song_id:
        return json_cn({"error": "参数缺失"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    sql = "INSERT INTO Songlist_Song(songlist_id, song_id) VALUES(%s, %s)"

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_id, song_id])

    return json_cn({"message": "添加歌曲进歌单成功"})


# 向歌单添加歌曲 (HTML界面)
@csrf_exempt
def songlist_add_song(request, songlist_id):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    uid = request.session["user_id"]

    if not check_user_auth(uid, songlist_id):
        return json_cn({"error": "无权编辑此歌单"}, 403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        song_id = data.get("song_id")
        sql = "INSERT INTO Songlist_Song (songlist_id, song_id) VALUES (%s, %s)"

        with connection.cursor() as cursor:
            cursor.execute(sql, [songlist_id, song_id])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>添加成功</title></head>
            <body>
                <h2>歌曲已添加到歌单！</h2>
                <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
            </body>
            </html>
        """)


# 从歌单移除歌曲 (API)
@csrf_exempt
def delete_song_from_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    songlist_id = data.get("songlist_id")
    song_id = data.get("song_id")

    if not songlist_id or not song_id:
        return json_cn({"error": "参数缺失"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    sql = "DELETE FROM Songlist_Song WHERE songlist_id = %s AND song_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_id, song_id])

    return json_cn({"message": "歌曲已从歌单移除"})


# 从歌单移除歌曲 (HTML界面)
@csrf_exempt
def songlist_delete_song(request, songlist_id, song_id):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    uid = request.session["user_id"]

    if not check_user_auth(uid, songlist_id):
        return json_cn({"error": "无权编辑此歌单"}, 403)

    sql = "DELETE FROM Songlist_Song WHERE songlist_id = %s AND song_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_id, song_id])

    return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>删除成功</title></head>
        <body>
            <h2>歌曲已从歌单移除！</h2>
            <p><a href="/songlist/profile/{songlist_id}/">返回歌单详情</a></p>
        </body>
        </html>
    """)


# 查看歌单列表 (API)
@csrf_exempt
def get_songlist_list(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    filter_user_id = request.GET.get("filter_user_id", None)
    keyword = request.GET.get("keyword", None)

    sql = """
          SELECT songlist_id, songlist_title, user_id, cover_url, like_count, is_public, create_time
          FROM Songlist
          WHERE 1 = 1
          """
    params = []

    if filter_user_id:
        sql += " AND user_id = %s"
        params.append(filter_user_id)

    current_user = request.session.get("user_id")
    if filter_user_id and str(filter_user_id) != str(current_user):
        sql += " AND is_public = 1"

    if keyword:
        sql += " AND songlist_title LIKE %s"
        params.append(f"%{keyword}%")

    sql += " ORDER BY create_time DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        result = dictfetchall(cursor)

    return json_cn({"songlists": result})


# 查看歌单列表 (HTML界面)
@csrf_exempt
def list_songlists(request):
    if "user_id" not in request.session:
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>请先登录</title></head>
            <body>
                <h2>请先登录后再查看歌单</h2>
                <p><a href="/user/login/">返回登录</a></p>
            </body>
            </html>
        """, status=403)

    uid = request.session["user_id"]

    is_public = request.GET.get("is_public")
    sort_by = request.GET.get("sort_by", "create_time")

    sql = """
        SELECT songlist_id, songlist_title, description, create_time, cover_url, like_count, is_public
        FROM Songlist
        WHERE user_id = %s
    """

    params = [uid]

    if is_public in ["0", "1"]:
        sql += " AND is_public = %s"
        params.append(int(is_public))

    if sort_by == "likes":
        sql += " ORDER BY like_count DESC"
    else:
        sql += " ORDER BY create_time DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

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
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>我的歌单</title></head>
        <body>
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

                <button type="submit">筛选</button>
            </form>

            <p><a href="/songlist/create_songlist/">创建新歌单</a></p>

            {html_rows if html_rows else '<p>暂无歌单</p>'}

            <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
        </body>
        </html>
    """)


# 查看歌单详情 (API)
@csrf_exempt
def get_songlist_detail(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)

    songlist_id = data.get("songlist_id")
    if not songlist_id:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    sort_by = data.get("sort_by", "add_time_desc")

    sql_info = """
               SELECT songlist_id, songlist_title, user_id, description, cover_url, like_count, create_time
               FROM Songlist
               WHERE songlist_id = %s
               """

    sql_total_duration = """
                         SELECT SUM(s.duration) as total_duration
                         FROM Song s
                                  JOIN Songlist_Song ss ON s.song_id = ss.song_id
                         WHERE ss.songlist_id = %s
                         """

    sql_songs = """
                SELECT s.song_id, s.song_title, s.duration, s.play_count, s.file_url, ss.add_time
                FROM Song s
                         JOIN Songlist_Song ss ON s.song_id = ss.song_id
                WHERE ss.songlist_id = %s
                """

    if sort_by == 'play_count':
        sql_songs += " ORDER BY s.play_count DESC"
    elif sort_by == 'duration':
        sql_songs += " ORDER BY s.duration DESC"
    elif sort_by == 'add_time_asc':
        sql_songs += " ORDER BY ss.add_time ASC"
    else:
        sql_songs += " ORDER BY ss.add_time DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql_info, [songlist_id])
        info = dictfetchall(cursor)
        if not info:
            return json_cn({"error": "歌单不存在"}, 404)
        songlist_info = info[0]

        cursor.execute(sql_total_duration, [songlist_id])
        duration_row = cursor.fetchone()
        total_duration = duration_row[0] if duration_row[0] else 0
        songlist_info['total_duration'] = total_duration

        cursor.execute(sql_songs, [songlist_id])
        songs = dictfetchall(cursor)

    return json_cn({
        "info": songlist_info,
        "songs": songs
    })


# 查看歌单详情 (HTML界面)
@csrf_exempt
def songlist_profile(request, songlist_id):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    sql_info = """
        SELECT sl.songlist_title, sl.description, sl.cover_url, sl.like_count, sl.create_time, sl.user_id, u.user_name
        FROM Songlist sl
        JOIN User u ON sl.user_id = u.user_id
        WHERE sl.songlist_id = %s
    """

    sql_songs = """
        SELECT s.song_id, s.song_title, s.duration, ss.add_time
        FROM Song s
        JOIN Songlist_Song ss ON s.song_id = ss.song_id
        WHERE ss.songlist_id = %s
        ORDER BY ss.add_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_info, [songlist_id])
        info_row = cursor.fetchone()

        if not info_row:
            return json_cn({"error": "歌单不存在"}, 404)

        title, desc, cover, likes, ctime, owner_id, owner_name = info_row

        cursor.execute(sql_songs, [songlist_id])
        songs = cursor.fetchall()

    html_songs = ""
    for sid, stitle, duration, add_time in songs:
        html_songs += f"""
            <li>
                {stitle} - {format_time(duration)}
                <small>(添加于 {add_time.strftime("%Y-%m-%d")})</small>
                <a href="/song/profile/{sid}/">详情</a>
            </li>
        """

    return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>{title}</title></head>
        <body>
            <h2>{title}</h2>
            <img src="{cover}" style="width:200px;height:200px;">
            <p>{desc or ''}</p>
            <p>创建者：{owner_name}</p>
            <p>创建时间：{ctime.strftime("%Y-%m-%d %H:%M")}</p>
            <p>点赞数：{likes}</p>

            <h3>歌曲列表</h3>
            <ul>
                {html_songs if html_songs else '<p>歌单为空</p>'}
            </ul>

            <p><a href="/songlist/list_songlists/">返回我的歌单</a></p>
        </body>
        </html>
    """)


# 排序歌单
@csrf_exempt
def sort_songlist(request, songlist_id):
    # 此功能可以在get_songlist_detail中通过sort_by参数实现
    return get_songlist_detail(request)


# 搜索歌单
@csrf_exempt
def search_songlist(request):
    if request.method == "GET":
        keyword = request.GET.get("keyword", "")

        sql = """
            SELECT sl.songlist_id, sl.songlist_title, sl.cover_url, sl.like_count, u.user_name
            FROM Songlist sl
            JOIN User u ON sl.user_id = u.user_id
            WHERE sl.is_public = 1 AND sl.songlist_title LIKE %s
            ORDER BY sl.like_count DESC
            LIMIT 20
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [f"%{keyword}%"])
            results = dictfetchall(cursor)

        return json_cn({"songlists": results, "count": len(results)})


# 点赞歌单
@csrf_exempt
def like_songlist(request, songlist_id):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    sql = "UPDATE Songlist SET like_count = like_count + 1 WHERE songlist_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_id])

    return json_cn({"message": "点赞成功"})


# ================================
# Favorite Management
# ================================

# 收藏/取消收藏 (API)
@csrf_exempt
def manage_favorite(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    action = data.get("action")  # 'add' or 'remove'
    target_type = data.get("target_type")  # 'song', 'album', 'songlist'
    target_id = data.get("target_id")

    if not all([action, target_type, target_id]):
        return json_cn({"error": "参数不完整"}, 400)

    if target_type not in ['song', 'album', 'songlist']:
        return json_cn({"error": "无效的收藏类型"}, 400)

    if action == "add":
        sql_check = "SELECT favorite_id FROM Favorite WHERE user_id=%s AND target_type=%s AND target_id=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check, [current_user_id, target_type, target_id])
            if cursor.fetchone():
                return json_cn({"error": "已收藏，请勿重复操作"}, 400)

            sql_insert = "INSERT INTO Favorite (user_id, target_type, target_id) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, [current_user_id, target_type, target_id])

        return json_cn({"message": "收藏成功"})

    elif action == "remove":
        sql_delete = "DELETE FROM Favorite WHERE user_id=%s AND target_type=%s AND target_id=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql_delete, [current_user_id, target_type, target_id])
        return json_cn({"message": "已取消收藏"})

    return json_cn({"error": "无效操作"}, 400)


# 添加收藏 (HTML界面)
@csrf_exempt
def add_favorite(request):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    uid = request.session["user_id"]

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        target_type = data.get("target_type")
        target_id = data.get("target_id")

        if target_type not in ["song", "album", "songlist"]:
            return json_cn({"error": "非法收藏对象"}, 400)

        sql_check = "SELECT 1 FROM Favorite WHERE user_id = %s AND target_type = %s AND target_id = %s"

        with connection.cursor() as cursor:
            cursor.execute(sql_check, [uid, target_type, target_id])
            if cursor.fetchone():
                return json_cn({"error": "已收藏，请勿重复操作"}, 400)

            sql_insert = "INSERT INTO Favorite(user_id, target_type, target_id) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, [uid, target_type, target_id])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>收藏成功</title></head>
            <body>
                <h2>收藏成功！</h2>
                <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
            </body>
            </html>
        """)


# 删除收藏 (HTML界面)
@csrf_exempt
def delete_favorite(request):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    uid = request.session["user_id"]

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        target_type = data.get("target_type")
        target_id = data.get("target_id")

        if target_type not in ["song", "album", "songlist"]:
            return json_cn({"error": "非法的收藏类型"}, 400)

        sql_delete = "DELETE FROM Favorite WHERE user_id = %s AND target_type = %s AND target_id = %s"

        with connection.cursor() as cursor:
            cursor.execute(sql_delete, [uid, target_type, target_id])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>取消收藏成功</title></head>
            <body>
                <h2>取消收藏成功！</h2>
                <p><a href="/favorite/list_favorite/">返回我的收藏</a></p>
            </body>
            </html>
        """)


# 查看收藏列表 (API)
@csrf_exempt
def get_favorite_list(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    target_type = data.get("target_type")
    if not target_type:
        return json_cn({"error": "没有指定查询类型"}, 400)

    if target_type == 'song':
        sql = """
              SELECT f.favorite_id, f.favorite_time, f.target_id, s.song_title as name, s.file_url
              FROM Favorite f
                       JOIN Song s ON f.target_id = s.song_id
              WHERE f.user_id = %s
                AND f.target_type = 'song'
              ORDER BY f.favorite_time DESC
              """
    elif target_type == 'album':
        sql = """
              SELECT f.favorite_id, f.favorite_time, f.target_id, a.album_title as name, a.cover_url
              FROM Favorite f
                       JOIN Album a ON f.target_id = a.album_id
              WHERE f.user_id = %s
                AND f.target_type = 'album'
              ORDER BY f.favorite_time DESC
              """
    elif target_type == 'songlist':
        sql = """
              SELECT f.favorite_id, f.favorite_time, f.target_id, sl.songlist_title as name, sl.cover_url
              FROM Favorite f
                       JOIN Songlist sl ON f.target_id = sl.songlist_id
              WHERE f.user_id = %s
                AND f.target_type = 'songlist'
              ORDER BY f.favorite_time DESC
              """
    else:
        return json_cn({"error": "未知的target_type"}, 400)

    with connection.cursor() as cursor:
        cursor.execute(sql, [current_user_id])
        result = dictfetchall(cursor)

    return json_cn({"favorites": result, "type": target_type})


# 查看收藏列表 (HTML界面)
@csrf_exempt
def list_favorite(request):
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 401)

    uid = request.session["user_id"]

    # 查询收藏的歌曲
    sql_song = """
        SELECT s.song_id, s.song_title, f.favorite_time
        FROM Favorite f
        JOIN Song s ON s.song_id = f.target_id
        WHERE f.user_id = %s AND f.target_type = 'song'
        ORDER BY f.favorite_time DESC
    """

    # 查询收藏的专辑
    sql_album = """
        SELECT a.album_id, a.album_title, f.favorite_time
        FROM Favorite f
        JOIN Album a ON a.album_id = f.target_id
        WHERE f.user_id = %s AND f.target_type = 'album'
        ORDER BY f.favorite_time DESC
    """

    # 查询收藏的歌单
    sql_songlist = """
        SELECT sl.songlist_id, sl.songlist_title, f.favorite_time
        FROM Favorite f
        JOIN Songlist sl ON sl.songlist_id = f.target_id
        WHERE f.user_id = %s AND f.target_type = 'songlist'
        ORDER BY f.favorite_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_song, [uid])
        songs = cursor.fetchall()

        cursor.execute(sql_album, [uid])
        albums = cursor.fetchall()

        cursor.execute(sql_songlist, [uid])
        songlists = cursor.fetchall()

    html_songs = "<h3>收藏的歌曲</h3><ul>"
    for sid, title, ftime in songs:
        html_songs += f'<li>{title} <a href="/song/profile/{sid}/">详情</a></li>'
    html_songs += "</ul>"

    html_albums = "<h3>收藏的专辑</h3><ul>"
    for aid, title, ftime in albums:
        html_albums += f'<li>{title} <a href="/album/profile/{aid}/">详情</a></li>'
    html_albums += "</ul>"

    html_songlists = "<h3>收藏的歌单</h3><ul>"
    for slid, title, ftime in songlists:
        html_songlists += f'<li>{title} <a href="/songlist/profile/{slid}/">详情</a></li>'
    html_songlists += "</ul>"

    return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>我的收藏</title></head>
        <body>
            <h2>我的收藏</h2>
            {html_songs}
            {html_albums}
            {html_songlists}
            <p><a href="/user/profile/{uid}/">返回个人中心</a></p>
        </body>
        </html>
    """)


# 我收藏的歌曲 (默认歌单模式，统计总时长)
@csrf_exempt
def get_my_favorite_songs_stats(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)

    sql_duration = """
                   SELECT SUM(s.duration)
                   FROM Favorite f
                            JOIN Song s ON f.target_id = s.song_id
                   WHERE f.user_id = %s
                     AND f.target_type = 'song'
                   """

    sql_list = """
               SELECT s.song_id, s.song_title, s.duration, s.play_count, f.favorite_time
               FROM Favorite f
                        JOIN Song s ON f.target_id = s.song_id
               WHERE f.user_id = %s
                 AND f.target_type = 'song'
               ORDER BY f.favorite_time DESC
               """

    with connection.cursor() as cursor:
        cursor.execute(sql_duration, [current_user_id])
        duration_row = cursor.fetchone()
        total_duration = duration_row[0] if duration_row and duration_row[0] else 0

        cursor.execute(sql_list, [current_user_id])
        songs = dictfetchall(cursor)

    return json_cn({
        "list_name": "我收藏的歌曲",
        "total_duration": total_duration,
        "count": len(songs),
        "songs": songs
    })


# 平台排行：展示收藏次数最多的 歌曲/专辑/歌单
@csrf_exempt
def get_platform_top_favorites(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)
    target_type = data.get("target_type", "song")
    limit = data.get("limit", 10)

    if target_type == 'song':
        sql = """
              SELECT f.target_id, COUNT(*) as fav_count, s.song_title as name
              FROM Favorite f
                       JOIN Song s ON f.target_id = s.song_id
              WHERE f.target_type = 'song'
              GROUP BY f.target_id, s.song_title
              ORDER BY fav_count DESC
              LIMIT %s
              """
    elif target_type == 'album':
        sql = """
              SELECT f.target_id, COUNT(*) as fav_count, a.album_title as name
              FROM Favorite f
                       JOIN Album a ON f.target_id = a.album_id
              WHERE f.target_type = 'album'
              GROUP BY f.target_id, a.album_title
              ORDER BY fav_count DESC
              LIMIT %s
              """
    elif target_type == 'songlist':
        sql = """
              SELECT f.target_id, COUNT(*) as fav_count, sl.songlist_title as name
              FROM Favorite f
                       JOIN Songlist sl ON f.target_id = sl.songlist_id
              WHERE f.target_type = 'songlist'
              GROUP BY f.target_id, sl.songlist_title
              ORDER BY fav_count DESC
              LIMIT %s
              """
    else:
        return json_cn({"error": "类型错误"}, 400)

    with connection.cursor() as cursor:
        cursor.execute(sql, [limit])
        result = dictfetchall(cursor)

    return json_cn({"ranking": result, "type": target_type})
