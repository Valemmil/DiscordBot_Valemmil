import discord
from discord.ext import commands


class Admin(commands.Cog):
    """Класс содержаший комманды для администрации"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Ког BotAdmin загружен')

    @commands.command(help=f'Проверка, работает ли бот')
    async def test(self, ctx):
        print(f'{ctx.author} приводит тестирование бота')
        await ctx.channel.purge(limit=1)
        await ctx.send('Работает как проклятый')

    @commands.command(help=f'Удаляет сообщения(по умолчанию 1)',
                      aliases=['clr'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, count=1):
        """Отчистка канала от нужного количества сообщений, доступен ролям с допуском к менеджменту сообщений"""
        await ctx.channel.purge(limit=1)
        await ctx.channel.purge(limit=count)
        await ctx.send(embed=discord.Embed(
            title='Уведомление',
            description=f':white_check_mark: Было отчищено {count} сообщений'
        ))
        print(f'Пользователем {ctx.author} произведена отчистка в канале {ctx.channel.name} на {count} сообщений')

    @commands.command(help=f'Бан пользователя на сервере')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason='Причина не указана'):
        """Бан пользователя, доступен ролям с допуском к бану пользователлей"""
        print(f'Пользватель {ctx.author} произвёл бан пользователя {member} по причине "{reason}"')
        await ctx.channel.purge(limit=1)
        await member.ban(reason=reason)
        await ctx.send(f'Пользователь {member.mention} был изгнан по причине "{reason}"')

    # @commands.command()
    # @commands.has_permissions(ban_members=True)
    # async def unban(ctx, member: discord.Member, *, reason='Причина не указана'):
    #     await ctx.channel.purge(limit=1)
    #     await member.unban(reason=reason)
    #     await ctx.send(f'Пользователь {member.mention} был разбанен по причине "{reason}"')

    @commands.command(help=f'Выгоняет пользователя с сервера')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Причина не указана'):
        """Функция выгоняет пользователя с сервера, доступен роям с допуском к кику пользователей"""
        print(f'Пользватель {ctx.author} произвёл кик пользователя {member} по причине "{reason}"')
        await ctx.channel.purge(limit=1)
        await member.kick(reason=reason)
        await ctx.send(f'Пользователь {member.mention} был кикнут по причине"{reason}"')


async def setup(bot):
    await bot.add_cog(Admin(bot))
