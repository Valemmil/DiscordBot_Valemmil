import os
import time

import discord
from discord.ext import commands
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

result = urlparse(os.getenv("DATABASE_URL"))
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

conn = psycopg2.connect(
    database=database,
    user=username,
    password=password,
    host=hostname,
    port=port
)

conn.autocommit = True

prefix = 'p.'
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())


X = int((time.monotonic() * 2388786075) % 1000000000)
Y = int((X * 7932822396) % 1000000000)
Z = int((Y * 4980207256) % 1000000000)
W = int((Z * 3815850835) % 1000000000)


async def add_member_in_tables(member: discord.Member):
    cur = conn.cursor()
    # cur.execute(
    #     sql.SQL("""CREATE TABLE IF NOT EXISTS {} (
    #     name text,
    #     time integer,
    #     uid  numeric(18, 0) PRIMARY KEY,
    #     start_time real,
    #     coin integer,
    #     date_award text)""").format(sql.Identifier(f'{member.guild.id}'))
    # )
    # print('Поиск профиля в базе данных')
    cur.execute(
        sql.SQL("""SELECT name FROM {} WHERE uid = %s""").format(sql.Identifier(f'{member.guild.id}')), (member.id, )
    )
    if not cur.fetchone():
        print(f'Создан профиль для {member}')
        cur.execute(
            sql.SQL("""INSERT INTO {}  
                    VALUES (%s, %s, %s, %s, %s, %s)""").format(sql.Identifier(f'{member.guild.id}')),
            (member.name, 0, member.id, -1, 0, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(0)))
        )
    cur.close()


async def xor_shift():
    """Функция для получения псевдо-рандомного числа"""
    global X, Y, Z, W
    t = X ^ (X << 11)
    X = Y
    Y = Z
    Z = W
    W = W ^ (W >> 19) ^ t ^ (t >> 8)
    return W
