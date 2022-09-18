CHECK_USER = """SELECT * FROM "Users" as u
                WHERE %(login)s = u.login AND %(password)s = u.password
            """

INSERT_FILE = """INSERT INTO "Files" VALUES(DEFAULT, %(hash)s, %(user_id)s)
"""

CHECK_FILE = """SELECT * FROM "Files" as f
                WHERE %(user_id)s = f.user_id AND %(hash)s = f.hash
            """