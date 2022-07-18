import calendar
import time

import discord
from discord.ext import commands

from storage import prefix, add_member_in_tables, conn
from psycopg2 import sql


class Money(commands.Cog):
    """Класс с командами для взаимодействиями с экономикой"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Ког BotMoney загружен')

    @commands.command(
        help=f'Вывод баланса пользователя',
        aliases=['баланс', 'деньги', 'cash'])
    async def balance(self, ctx, member: discord.Member = None):
        """Провека баланса пользователя"""
        print(f'Начало запроса {ctx.author} на проверку баланса')
        await add_member_in_tables(ctx.author)
        await ctx.channel.purge(limit=1)
        cur = conn.cursor()
        if member:
            await add_member_in_tables(member)
            cur.execute(
                sql.SQL("""SELECT coin FROM {} WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
                (member.id,)
            )
            # getdata = db.get(f'{ctx.guild.id}').search(Query().uid == member.id)
            user = member
        else:
            cur.execute(
                sql.SQL("""SELECT coin FROM {} WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
                (ctx.author.id,)
            )
            # getdata = db.get(f'{ctx.guild.id}').search(Query().uid == ctx.author.id)
            user = ctx.author

        await ctx.send(embed=discord.Embed(
            description='Баланс пользователя **{}** равен **{}**:feather:'.format(user.mention,
                                                                                  cur.fetchone()[0])
        ))
        print(f'Запрос {ctx.author} на проверку баланса {user}')
        cur.close()

    @commands.command(
        help=f'Получить интервальную награду',
        aliases=['награда', 'дейлик', 'reward'])
    async def daily(self, ctx):
        """Получение награды каждые 12 часов"""
        print(f'Запрос на ежедневную награду от {ctx.author}')
        await ctx.channel.purge(limit=1)
        await add_member_in_tables(ctx.author)
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""SELECT date_award, uid, coin 
                    FROM {} WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
            (ctx.author.id, )
        )
        getdata = cur.fetchone()
        now_date = calendar.timegm(time.gmtime()) - calendar.timegm(
            time.strptime(getdata[0], '%Y-%m-%d %H:%M:%S'))
        if now_date >= 60*60*12:
            cur.execute(
                sql.SQL("""UPDATE {} 
                SET date_award = %s, 
                    coin = %s 
                WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
                (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), (getdata[2] + 30), getdata[1])
            )
            # db.get(f'{ctx.guild.id}').update({'date_award': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())},
            #                                  where('uid') == getdata[0]['uid'])
            # db.get(f'{ctx.guild.id}').update({'coin': getdata[0]['coin'] + 30},
            #                                  where('uid') == getdata[0]['uid'])
            await ctx.send(embed=discord.Embed(
                description=f'{ctx.author.mention}, Вы собрали **30**:feather: в лесу'
            ))
            print(f'Запрос {ctx.author} на ежедневную награду одобрен')
        else:
            await ctx.send(embed=discord.Embed(
                description='{}, Вы ещё не отдохнули от прошлой прогулки, подождите {}'.format(
                    ctx.author.mention, time.strftime("%H:%M:%S", time.gmtime(60*60*12 - now_date)))
            ))
            print(f'Запрос {ctx.author} на ежедневную награду отклонён')
        cur.close()

    @commands.command(help=f'Перевод другому пользователю',
                      aliases=['передать', 'отдать', 'give'])
    async def transfer(self, ctx, count_coin: int = None, member: discord.Member = None):
        """Перевод денег другим пользователям"""
        print(f'Запрос трансфера "{ctx.author} to {member}"')
        await add_member_in_tables(ctx.author)
        await add_member_in_tables(member)
        await ctx.channel.purge(limit=1)
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""SELECT coin, uid FROM {} WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
            (ctx.author.id,)
        )
        # getdataauthor = db.get(f'{ctx.guild.id}').search(Query().uid == ctx.author.id)
        getdataauthor = cur.fetchone()
        if count_coin is None or member is None:
            await ctx.send(embed=discord.Embed(
                description=f'{ctx.author.mention}, у вас указаны не все обязательные пункты!\n'
                            f'Пример правильного использования **{prefix}transfer 100 @user#0000**'
            ))
            print(f'Ошибка трансфера "{ctx.author} to {member}" причина: Указано отрицательное значение')
        elif ctx.author.id == member.id:
            await ctx.send(embed=discord.Embed(
                description='Передавать самому себе :feather: нельзя'
            ))
            print(f'Трансфер "{ctx.author} to {member}" был направлен на самого себя')

        elif count_coin < 1:
            await ctx.send(embed=discord.Embed(
                description=f'{ctx.author.mention}, нельзя передавать отрицательные значения для перевода!'
            ))
            print(f'Ошибка трансфера "{ctx.author} to {member}" причина: Указано отрицательное значение')
        elif getdataauthor[0] >= count_coin:
            print(f'Начало осуществления трансфера "{ctx.author} to {member}"')
            cur.execute(
                sql.SQL("""SELECT coin, uid FROM {} WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                (member.id,)
            )
            getdatamember = cur.fetchone()
            cur.execute(
                sql.SQL("""UPDATE {} 
                SET coin = %s 
                WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
                (getdataauthor[0] - count_coin, getdataauthor[1])
            )
            cur.execute(
                sql.SQL("""UPDATE {} 
                SET coin = %s 
                WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
                (getdatamember[0] + int(count_coin * 0.96), getdatamember[1])
            )
            # db.get(f'{ctx.guild.id}').update({'coin': getdataauthor[0][0] - count_coin},
            #                                  where('uid') == getdataauthor[0][1])
            # db.get(f'{ctx.guild.id}').update({'coin': getdatamember[0][0] + int(count_coin * 0.96)},
            #                                  where('uid') == getdatamember[0][1])
            await ctx.send(embed=discord.Embed(
                description=f'{ctx.author.mention} передал {member.mention} '
                            f'**{int(count_coin * 0.96)}**:feather: из {count_coin}'
            ))
            print(f'Трансфер "{ctx.author} to {member}" был завершён успешно')

        else:
            print(f'Ошибка трансфера "{ctx.author} to {member}" причина: Недостаточно перьев')
            await ctx.send(embed=discord.Embed(
                description=f'{ctx.author.mention}, у вас не хватает :feather: для передачи их {member.mention}'
            ))
        cur.close()


async def setup(bot):
    await bot.add_cog(Money(bot))
