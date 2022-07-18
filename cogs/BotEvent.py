import discord
from discord.ext import commands

from psycopg2 import sql

from storage import prefix, add_member_in_tables, conn


class Event(commands.Cog):
    """Класс с реакциями на события"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        При запуске бота проверят все сервера к которым подключён
        и если нет таблицы этого сервера, то создаёт таблицу.

        После проверят всех пользователей для всех серверов и
        создаёт строку для него в нужной таблице
        """
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS shop (
            name text,
            rid numeric(18, 0) PRIMARY KEY,
            gid numeric(18, 0),
            unique_r boolean,
            cost integer)"""
        )
        for guild in self.bot.guilds:
            cur.execute(
                sql.SQL("""CREATE TABLE IF NOT EXISTS {table} (
                name text,
                time numeric(18, 4),
                uid  numeric(18, 0) PRIMARY KEY,
                start_time numeric(18, 4),
                coin integer,
                date_award text)""").format(table=sql.Identifier(f'{guild.id}'))
            )
        cur.close()
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f'{prefix}help'))
        print('Ког BotEvent загружен')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """При входе пользователя на сервер создаёт для него строку в таблице"""
        print(f'{member} зашёл на сервер {member.guild.name}')
        await add_member_in_tables(member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        Когда бота приглашают на новый сервер, то он создаёт
        таблицу этого сервера
        """
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""CREATE TABLE IF NOT EXISTS {} (
            name text,
            time integer,
            uid  numeric(18, 0) PRIMARY KEY,
            start_time numeric(18, 4),
            coin integer,
            date_award text)""").format(sql.Identifier(f'{guild.id}'))
        )
        cur.close()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Если человек покидает сервер, то удаляется строка с его данными из таблицы"""
        await add_member_in_tables(member)
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""DELETE FROM {} WHERE uid = %s""").format(sql.Identifier(f'{member.guild.id}'), (member.id,))
        )
        # db.get(f'{member.guild.id}').remove(Query().uid == member.id)
        cur.close()
        print(f'{member} вышел с сервера {member.guild.name}')

    # @commands.Cog.listener()
    # async def on_member_update(self, before, after):
    #     print(before.member.top_role)
    #     print(after.member.top_role)

    # @commands.Cog.listener()
    # async def on_guild_role_created(self, role):
    #     print('Role name:', role.name)
    #     print('Role color:', role.color)
    #     print('Role id:', role.id)
    #     print('Role permissions:', role.permissions)
    #     print('Role created_at:', role.created_at)

    # @commands.Cog.listener()
    # async def on_guild_channel_create(self, channel):
    #     print('Channel name: ', channel.name)
    #     print('Channel category: ', channel.category)
    #     print('Channel id: ', channel.id)
    #     print('Channel created at', channel.created_at)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Если человек написал команду которой не существует, его уведомит об этом"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=discord.Embed(description=f'** {ctx.author.name}, данной команды не существует.**\n'
                                                           f'Используйте {prefix}help для простмотра команд',
                                               color=0x0c0c0c))


async def setup(bot):
    await bot.add_cog(Event(bot))
