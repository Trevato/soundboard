import sqlite3 as sl


sql_mappings = {
    "new": "INSERT INTO sounds (user_id, sound_name, sound_path) VALUES (?, ?, ?)",
    "get": "SELECT * FROM sounds WHERE user_id = ? AND sound_name = ?",
    "list": "SELECT * FROM sounds WHERE user_id = ?",
    "delete": "DELETE FROM sounds WHERE user_id = ? AND sound_name = ?",
    "create_table": "CREATE TABLE IF NOT EXISTS sounds (id INTEGER PRIMARY KEY, user_id INTEGER, sound_name TEXT, sound_path TEXT)",
}


def connect():
    conn = sl.connect("database.db")
    # create the table if it doesn't exist
    # Schema: (id, user_id, sound_name, sound_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sounds (id INTEGER PRIMARY KEY, user_id INTEGER, sound_name TEXT, sound_path TEXT)"
    )
    return conn


def list_sounds(ctx, conn):
    c = conn.cursor()
    return c.execute(sql_mappings["list"], (ctx.author.id,)).fetchall()


def create_yt_sound(ctx, conn):
    # First ensure that the url is a valid youtube link
    # Currently, only basic youtube links are allowed due to added complexity when implementing shorts and start/end times

    # Get the seperate arguments
    _, name, url = ctx.message.content.split()

    if not (
        url.startswith("https://youtu.be/")
        or url.startswith("https://www.youtube.com/")
    ):
        return f"This does not appear to be a YouTube link:\n`{url}`"

    if "/shorts/" in ctx.message.content.split()[2]:
        return "Shorts are not supported"

    if "?t=" in ctx.message.content.split()[2]:
        return "Start times are not supported"

    # Validation is passed so we can add the sound to the db
    c = conn.cursor()
    c.execute(sql_mappings["new"], (ctx.author.id, name, url))

    return "Successfully created new sound"


def create_mp3_sound(ctx, conn):
    # Ensure only one attachment
    if len(ctx.message.attachments) != 1:
        return "Please only send one file at a time"
    elif ctx.message.attachments[0].filename[-4:] != ".mp3":
        return "Only mp3 files are allowed"

    name = ctx.message.content.split()[1]
    url = ctx.message.attachments[0].url

    c = conn.cursor()
    c.execute(sql_mappings["new"], (ctx.author.id, name, url))

    return "Successfully created new sound"


def get_url(ctx, conn):
    name = ctx.message.content.split()[1]

    c = conn.cursor()
    return c.execute(sql_mappings["get"], (ctx.author.id, name)).fetchone()[3]


def delete_sound(ctx, conn):
    name = ctx.message.content.split()[1]
    c = conn.cursor()

    if c.execute(sql_mappings["get"], (ctx.author.id, name)).fetchone() is None:
        return "Cannot find sound with that name"

    c.execute(sql_mappings["delete"], (ctx.author.id, name))
    return "Successfully deleted sound"
