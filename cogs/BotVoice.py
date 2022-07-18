import time
from decimal import *

import discord
from discord.ext import commands

from storage import add_member_in_tables, conn
from psycopg2 import sql


class Voice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Ког BotVoice загружен')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Обработка события "Изменение значения в поле войс", изменяет
        значения в базе данных в зависимости от начальных значений
        """
        await add_member_in_tables(member)
        # tb = db.get(f'{member.guild.id}')
        cur = conn.cursor()
        if str(before.channel) == "None":
            print(member.name + " joined " + str(after.channel))
            cur.execute(
                sql.SQL("""SELECT time FROM {} WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                (member.id, )
            )
            getdata = cur.fetchone()
            get_start_point = time.monotonic()
            cur.execute(
                sql.SQL("""UPDATE {} 
                        SET start_time = %s WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                (get_start_point, member.id)
            )
            conn.commit()
            # tb.update({'start_time': get_start_point}, where('uid') == member.id)
            print('Startpoint is ' + str(getdata[0]))

        elif str(after.channel) == "None":
            cur.execute(
                sql.SQL("""SELECT start_time, coin, time 
                FROM {} 
                WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                (member.id, )
            )
            getdata = cur.fetchone()
            if getdata[0] >= 0:
                time_fir = int(time.monotonic() - getdata[0])
                if (getdata[2] + time_fir) < 0:
                    print(f'Ошибка Подсчёта времени start = {getdata[0]}, coin = {getdata[1]}, time = {getdata[2]}')
                    cur.execute(
                        sql.SQL("""UPDATE {} 
                                   SET start_time = %s 
                                   WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                        (-1, member.id)
                    )
                    return
                cur.execute(
                    sql.SQL("""UPDATE {} 
                                   SET time = %s, 
                                       start_time = %s, 
                                       coin = %s 
                                   WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                    (getdata[2] + time_fir, -1, getdata[1] + int(time_fir / 300), member.id)
                )
                # tb.update({'time': getdata[0][2] + time_fir},
                #           where('uid') == member.id)
                # tb.update({'start_time': -1},
                #           where('uid') == member.id)
                # tb.update({'coin': getdata[0][1] + int(time_fir / 300)}, where('uid') == member.id)
                print(member.name + " left " + str(before.channel))
                print('Endpoint is ' + str(getdata[2] + time_fir) + ', coin is ' + str(int(time_fir / 300)))
            else:
                print(member.name + " left " + str(before.channel))
        cur.close()

    @commands.command(help=f'Топ 10 сервера по времени проведённого в войсе\n')
    async def topv(self, ctx):
        """Выводит топ 10 пользователей на сервере"""
        await ctx.channel.purge(limit=1)
        print(f'Запрос от пользователя {ctx.author} на вывод топа по времени в голосовом канале')
        await add_member_in_tables(ctx.author)
        # topvjson = json.load(open('json/db.json'))
        # stats = topvjson[f'{ctx.guild.id}']
        # stats.sort(key=lambda entry_tmp: int(entry_tmp['time']), reverse=True)

        cur = conn.cursor()
        cur.execute(
            sql.SQL("""SELECT name, time FROM {} ORDER BY time DESC""").format(sql.Identifier(str(ctx.guild.id)))
        )
        stats = cur.fetchmany(10)

        em = discord.Embed(title='Топ 10 в голосовом канале',
                           description='Здесь показаны ТОП 10 людей которые провели в голосовом канале.',
                           colour=0x80a842)
        for entry in stats:
            playername = "%s" % (entry[0])
            playertime = "%s" % (int(entry[1]))
            postfix = ' с.'
            if float(playertime) > (60 * 60 * 24):
                playertime = float(playertime) / (60 * 60 * 24)
                postfix = ' д.'
            elif float(playertime) > (60 * 60):
                playertime = float(playertime) / (60 * 60)
                postfix = ' ч.'
            elif float(playertime) > 60:
                playertime = float(playertime) / 60
                postfix = ' м.'

            em.add_field(name=playername, value=f'{float(playertime):.2f}{postfix}', inline=False)
        await ctx.send(embed=em)
        cur.close()


async def setup(bot):
    await bot.add_cog(Voice(bot))
