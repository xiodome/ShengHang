from django.db import connection

def initialize_tables():
    """
    用于修复数据库中 Django 无法设置的默认值。
    修复数据库中自动生成的奇怪外键和级联删除属性(每次新建数据库要重新改这些奇奇怪怪外键名)
    删除django生成了无用表
    定义了触发器
    此函数会：
    """

    sql_fixes = [
        # user表
        # 修复 gender
        """
        ALTER TABLE user
        MODIFY gender ENUM('男','女','其他')
        NOT NULL DEFAULT '其他'
        """,

        # 修复 register_time
        """
        ALTER TABLE user
        MODIFY register_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复 status
        """
        ALTER TABLE user
        MODIFY status ENUM('正常','封禁中')
        NOT NULL DEFAULT '正常'
        """,

        # 修复 visibility
        """
        ALTER TABLE user
        MODIFY visibility ENUM('私密','仅关注者可见','所有人可见')
        NOT NULL DEFAULT '所有人可见'
        """,


        # singer表
        # 修复type
        """
        ALTER TABLE singer
        MODIFY type ENUM('男','女','组合')
        NOT NULL
        """,


        # album表
        # 修复发行日期
        """
        ALTER TABLE album
        MODIFY release_date DATE
        NOT NULL DEFAULT '1970-01-01'
        """,

        # 修复专辑封面路径
        """
        ALTER TABLE album
        MODIFY cover_url VARCHAR(255)
        NOT NULL DEFAULT '/images/default_album_cover.jpg'
        """,


        # song表
        # 修复歌曲总播放次数
        """
        ALTER TABLE song
        MODIFY play_count INT
        NOT NULL DEFAULT 0
        """,

        # songlist表
        # 修复创建时间
        """
        ALTER TABLE songlist
        MODIFY create_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复封面路径
        """
        ALTER TABLE songlist
        MODIFY cover_url VARCHAR(255)
        NOT NULL DEFAULT '/images/default_songlist_cover.jpg'
        """,

        # 修复点赞数
        """
        ALTER TABLE songlist
        MODIFY like_count INT
        NOT NULL DEFAULT 0
        """,

        # 修复公开性
        """
        ALTER TABLE songlist
        MODIFY is_public TINYINT
        NOT NULL DEFAULT true
        """,


        # comment表
        # 修复评论目标类型
        """
        ALTER TABLE comment.py
        MODIFY target_type ENUM('song','album','songlist') 
        """,

        # 修复点赞数
        """
        ALTER TABLE comment.py
        MODIFY like_count INT
        NOT NULL DEFAULT 0
        """,

        # 修复评论时间
        """
        ALTER TABLE comment.py
        MODIFY comment_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复评论状态
        """
        ALTER TABLE comment.py
        MODIFY status ENUM('审核中','举报中','正常')
        NOT NULL
        """,


        # favorite表
        # 修复收藏目标类型
        """
        ALTER TABLE favorite
        MODIFY target_type ENUM('song','album','songlist') 
        """,

        # 修复收藏时间
        """
        ALTER TABLE favorite
        MODIFY favorite_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # playhistory表
        # 修复播放时间
        """
        ALTER TABLE playhistory
        MODIFY play_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复实际播放时长
        """
        ALTER TABLE playhistory
        MODIFY play_duration INT
        NOT NULL DEFAULT 0
        """,


        # userfollow表
        # 修复关注时间
        """
        ALTER TABLE userfollow
        MODIFY follow_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # singerfollow表
        # 修复关注时间
        """
        ALTER TABLE singerfollow
        MODIFY follow_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # songlist_song表
        # 修复添加时间
        """
        ALTER TABLE songlist_song
        MODIFY add_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # systemlog表
        # 修复操作时间
        """
        ALTER TABLE systemlog
        MODIFY action_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修改操作结果状态
        """
        ALTER TABLE systemlog
        MODIFY result ENUM('success','fail')
        NOT NULL
        """,

        # 修改对应外键名称和属性
        # album表
        """
        ALTER TABLE album
        DROP FOREIGN KEY Album_singer_id_40707949_fk_Singer_singer_id;

        ALTER TABLE album
        ADD CONSTRAINT Album_singer_id_fk FOREIGN KEY (singer_id) REFERENCES singer(singer_id)
        ON DELETE CASCADE;
        """,

        # song表
        # 修改表中错误的外键名字
        """
        ALTER TABLE song
        DROP FOREIGN KEY Song_album_id_12171706_fk_Album_album_id;

        ALTER TABLE song
        ADD CONSTRAINT Song_album_id_fk FOREIGN KEY (album_id) REFERENCES album(album_id)
        ON DELETE CASCADE;
        """,

        # songlist表
        """
        ALTER TABLE songlist
        DROP FOREIGN KEY Songlist_user_id_8a517e4f_fk_User_user_id;

        ALTER TABLE songlist
        ADD CONSTRAINT Songlist_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        # comment表
        """
        ALTER TABLE comment
        DROP FOREIGN KEY Comment_user_id_1cbe86a2_fk_User_user_id;

        ALTER TABLE comment
        ADD CONSTRAINT Comment_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        # favorite表
        """
        ALTER TABLE favorite
        DROP FOREIGN KEY Favorite_user_id_5febe7a0_fk_User_user_id;

        ALTER TABLE favorite
        ADD CONSTRAINT Favorite_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        # playhistory表
        """
        ALTER TABLE playhistory
        DROP FOREIGN KEY PlayHistory_song_id_8d9897de_fk_Song_song_id;

        ALTER TABLE playhistory
        ADD CONSTRAINT PlayHistory_song_id_fk FOREIGN KEY (song_id) REFERENCES song(song_id)
        ON DELETE CASCADE;
        """,

        """
        ALTER TABLE playhistory
        DROP FOREIGN KEY PlayHistory_user_id_763a0bf1_fk_User_user_id;

        ALTER TABLE playhistory
        ADD CONSTRAINT PlayHistory_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        # userfollow表
        """
        ALTER TABLE userfollow
        DROP FOREIGN KEY UserFollow_followed_id_55f582a4_fk_User_user_id;

        ALTER TABLE userfollow
        ADD CONSTRAINT UserFollow_followed_id_fk FOREIGN KEY (followed_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        """
        ALTER TABLE userfollow
        DROP FOREIGN KEY UserFollow_follower_id_37f00a2f_fk_User_user_id;

        ALTER TABLE userfollow
        ADD CONSTRAINT UserFollow_follower_id_fk FOREIGN KEY (follower_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        # singerfollow表
        """
        ALTER TABLE singerfollow
        DROP FOREIGN KEY SingerFollow_singer_id_9c1efdb2_fk_Singer_singer_id;

        ALTER TABLE singerfollow
        ADD CONSTRAINT SingerFollow_singer_id_fk FOREIGN KEY (singer_id) REFERENCES singer(singer_id)
        ON DELETE CASCADE;
        """,

        """
        ALTER TABLE singerfollow
        DROP FOREIGN KEY SingerFollow_user_id_d929e3e8_fk_User_user_id;

        ALTER TABLE singerfollow
        ADD CONSTRAINT SingerFollow_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE;
        """,

        # songlist_song表
        """
        ALTER TABLE songlist_song
        DROP FOREIGN KEY Songlist_Song_song_id_77173337_fk_Song_song_id;

        ALTER TABLE songlist_song
        ADD CONSTRAINT Songlist_Song_song_id_fk FOREIGN KEY (song_id) REFERENCES song(song_id)
        ON DELETE CASCADE;
        """,

        """
        ALTER TABLE songlist_song
        DROP FOREIGN KEY Songlist_Song_songlist_id_8cd98c3a_fk_Songlist_songlist_id;

        ALTER TABLE songlist_song
        ADD CONSTRAINT Songlist_Song_songlist_id_fk FOREIGN KEY (songlist_id) REFERENCES songlist(songlist_id)
        ON DELETE CASCADE;
        """,

        # song_singer表
        """
        ALTER TABLE song_singer
        DROP FOREIGN KEY Song_Singer_singer_id_c7096906_fk_Singer_singer_id;

        ALTER TABLE song_singer
        ADD CONSTRAINT Song_Singer_singer_id_fk FOREIGN KEY (singer_id) REFERENCES singer(singer_id)
        ON DELETE CASCADE;
        """,

        """
        ALTER TABLE song_singer
        DROP FOREIGN KEY Song_Singer_song_id_c14193ef_fk_Song_song_id;

        ALTER TABLE song_singer
        ADD CONSTRAINT Song_Singer_song_id_fk FOREIGN KEY (song_id) REFERENCES song(song_id)
        ON DELETE CASCADE;
        """,

        # 触发器
        # 递归删除子评论触发器
        # 当评论被删除前，自动删除 parent_id 为该评论ID 的所有子评论
        # 数据库会因此再次触发本触发器，从而实现递归删除
        #"""
        #CREATE TRIGGER delete_comment_reply 
        #BEFORE DELETE ON Comment
        #FOR EACH ROW
        #BEGIN
        #    DELETE FROM Comment WHERE parent_id = OLD.comment_id;
        #END;
        #""",

        # 自动更新触发器
        """
        CREATE TRIGGER after_play_insert
        AFTER INSERT ON PlayHistory
        FOR EACH ROW
        BEGIN
            UPDATE Song 
            SET play_count = play_count + 1 
            WHERE song_id = NEW.song_id;
        END;
        """,


        # 删除无用表
        """DROP TABLE django_migrations""",
        """DROP TABLE django_admin_log""",
        """DROP TABLE auth_group_permissions""",
        """DROP TABLE auth_user_groups""",
        """DROP TABLE auth_group""",
        """DROP TABLE auth_user_user_permissions""", 
        """DROP TABLE auth_user""",
        """DROP TABLE auth_permission""",
        """DROP TABLE django_content_type""",
    ]

    with connection.cursor() as cursor:
        for sql in sql_fixes:
            try:
                cursor.execute(sql)
            except Exception as e:
                # 如果已修复或云数据库不允许重复修改，则忽略错误
                print(f"[InitialTable] Warning: {e}")

    print("[InitialTable] 建表初始化成功.")
