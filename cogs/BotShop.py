import discord
from Cybernator import Paginator as Pag
from discord.ext import commands

from storage import add_member_in_tables, conn
from psycopg2 import sql


class Shop(commands.Cog):
    """Класс с командами для взаимодействий с магазином"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Ког BotShop загружен')

    @commands.command(name='shop',
                      help=f'Вывод ролей находящихся в магазине',
                      aliases=['магаз', 'магазин'])
    async def _shop(self, ctx):
        """Вывод магазина со всеми ролями для этого сервера"""
        await ctx.channel.purge(limit=1)
        print(f'{ctx.author} открывает магазин')
        await add_member_in_tables(ctx.author)
        # shop.table('shop')
        # shop_tmp = shop.get('shop')
        embeds = []
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""SELECT name, cost, unique_r_r FROM shop WHERE gid = %s"""),
            (ctx.guild.id, )
        )
        # items = shop_tmp.search(Query().gid == ctx.guild.id)
        items = cur.fetchall()
        cur.close()
        if items[0][0] is not None:
            for i in range((len(items) - 1) // 5 + 1):
                embeds.append(discord.Embed(title='Магазин'))
                for j in range(5):
                    j_now = (5 * i) + j
                    embeds[i].add_field(name=f'{j_now + 1}:', value=('{} - '.format(items[j_now]['name']) +
                                                                     'Стоймость: {} - Уникальность: {}'.format(
                                                                     items[j_now]['cost'], items[j_now]['unique_r'])),
                                        inline=False)
                    if (j_now + 1) == len(items):
                        break

            massage = await ctx.send(embed=embeds[0])
            page = Pag(self.bot, massage, only=ctx.author, use_more=False, embeds=embeds)
            await page.start()
        else:
            return await ctx.send(embed=discord.Embed(
                title='Уведомление',
                description='В магазине нет ролей'
            ))

    @commands.command(help=f'Покупка роли из магазина, '
                           f'для покупки введите индекс из магазина\n',
                      aliases=['br', 'buy', 'b_role'])
    async def buy_role(self, ctx, index: int = None):
        """Покупка роли по индексу из магазина"""
        await ctx.channel.purge(limit=1)
        print(f'Инициализация покупки роли пользователем {ctx.author}')
        await add_member_in_tables(ctx.author)
        if index is None:
            print('Не выбран индекс роли')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, не записан индекс роли'
            ))

        if index < 1:
            print('Выбран не правильный индекс роли')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, индекс не может быть меньше единицы'
            ))

        # shop.table('shop')
        # shop_tmp = shop.get('shop')
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""SELECT cost, rid, unique_r FROM shop WHERE gid = %s"""),
            (ctx.guild.id, )
        )
        # items = shop_tmp.search(Query().gid == ctx.guild.id)
        items = cur.fetchall()
        if len(items) < index:
            print('Выбран не правильный индекс роли')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, переданный индекс не найден'
            ))

        # db.table(f'{ctx.guild.id}')
        # tdb = db.get(f'{ctx.guild.id}')
        cur.execute(
            sql.SQL("""SELECT coin FROM {} WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
            (ctx.author.id, )
        )
        # user_coin = tdb.search(Query().uid == ctx.author.id)
        user_coin = cur.fetchone()
        if user_coin[0] < items[index - 1][0]:
            print(f'Пользователю {ctx.author} не хватило коинов на покупку роли')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, у вас не хватает :feather: на покупку этой роли'
            ))

        cur.execute(
            sql.SQL("""UPDATE {} SET coin = %s WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
            (user_coin[0] - items[index - 1][0], ctx.author.id)
        )
        # tdb.update({'coin': user_coin[0][0] - items[index - 1]['cost']}, where('uid') == ctx.author.id)
        new_role = discord.utils.get(ctx.guild.roles, id=items[index - 1][1])
        await ctx.author.add_roles(new_role, reason='Покупка этой роли')
        cost = items[index - 1][0]
        print(f'Покупка пользователем {ctx.author} роли {new_role.name} (ID: {new_role.id}) успешно окончена')
        await ctx.author.send(f'Покупка роли {new_role.name} (ID: {new_role.id}) за {cost} успешно окончена')
        if items[index - 1][2] == 1:
            cur.execute(
                """DELETE FROM shop WHERE rid = %s""",
                (items[index - 1][1], )
            )
            # shop_tmp.remove(Query().rid == items[index - 1][1])
        cur.close()

    @commands.command(help=f'Добавляет роль в магазин\n',
                      aliases=['ar', 'a_role'])
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, unique_r: int = None, cost: int = None, *, name: str = None):
        """Добавление роли в магазин, доступен ролям с доступом к менеджменту ролей"""
        await ctx.channel.purge(limit=1)
        print(f'{ctx.author} добавление в магазин роли(name:{name}, cost:{cost}, уникальность:{unique_r})')
        await add_member_in_tables(ctx.author)
        if (unique_r != 0 and unique_r != 1) or unique_r is None:
            print(f'{ctx.author.mention}, второй параметр не указан или может принимать **только** 0 или 1')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, второй параметр не указан или может принимать **только** 0 или 1'
            ))

        if cost < 0 or cost is None:
            print(f'{ctx.author.mention}, стоймость роли не указана или не может быть меньше 0')
            return await ctx.send(enbed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, стоймость роли не указана или не может быть меньше 0'
            ))

        if len(name) > 100 or name is None:
            print(f'{ctx.author.mention}, имя не указано или длиннее 100 символов')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, имя не указано или длиннее 100 символов'
            ))

        # shop.table('shop')
        # shop_tmp = shop.get('shop')
        cur = conn.cursor()
        cur.execute(
            """SELECT name FROM shop WHERE name = %s, gid = %s""",
            (name, ctx.guild.id)
        )
        if cur.fetchone()[0] is not None:
            print(f'{ctx.author.mention}, роль с таким именем уже есть')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, роль с таким именем уже есть'
            ))

        new_role = await ctx.guild.create_role(name=name, colour=discord.Colour.dark_gray(), hoist=False,
                                               mentionable=True, reason='Добавление в магазин')
        print(f'{ctx.author} добавление в магазин роли'
              f'(name:{name}, cost:{cost}, уникальность:{unique_r}) успешно окончено')
        await ctx.send(embed=discord.Embed(
            description=f'Роль(name:{name}, cost:{cost}, уникальность:{unique_r}) успешно добавлена в магазин'
        ))
        cur.execute(
            """INSERT INTO shop VALUES (%s, %s, %s, %s, %s)""",
            (name, new_role.id, ctx.guild.id, unique_r, cost)
        )
        # cur.close()
        # shop_tmp.insert({
        #     'name': name,
        #     'rid': new_role.id,
        #     'gid': ctx.guild.id,
        #     'unique_r': unique_r,
        #     'cost': cost
        # })
        cur.close()

    @commands.command(help=f'Удаляет роль из магазина\n', aliases=['dr', 'd_role'])
    @commands.has_permissions(manage_roles=True)
    async def delete_role(self, ctx, *, name: str = None):
        """Удаление роли из магазина и с сервера, доступен ролям с доступом к менеджменту ролей"""
        await ctx.channel.purge(limit=1)
        if len(name) > 100 or name is None:
            print(f'{ctx.author.mention}, имя не указано или длиннее 100 символов')
            return await ctx.send(embed=discord.Embed(
                title='Ошибка',
                description=f'{ctx.author.mention}, имя не указано или длиннее 100 символов'
            ))
        print(f'{ctx.author} производит удаление роли')
        await add_member_in_tables(ctx.author)
        # shop.table('shop')
        # shop_tmp = shop.get('shop')
        cur = conn.cursor()
        cur.execute(
            """SELECT rid FROM shop WHERE name = %s, gid = %s""",
            (name, ctx.guild.id)
        )
        item = cur.fetchone()
        new_role = discord.utils.get(ctx.guild.roles, id=item[0])
        if new_role:
            cur.execute(
                """DELETE FROM shop WHERE name = %s, gid = %s""",
                (name, ctx.guild.id)
            )
            # shop_tmp.remove((Query().name == name) & (Query().gid == ctx.guild.id))
            await ctx.send(f'Удаление роли {name} из магазина успешно завершёно')
            print(f'Удаление роли {name} из магазина успешно завершёно')
        cur.close()

    # @commands.command(help='Показывает инвентарь ролей игрока', aliases=['show_i', 'si'])
    # async def show_inventory(self, ctx):
    #     await ctx.channel.purge(limit=1)
    #     shop.table(f'{ctx.guild.id}_{ctx.author.id}')
    #     invent_memb = shop.get(f'{ctx.guild.id}_{ctx.author.id}').all()
    #     if len(invent_memb) > 0:
    #         for i in range((len(invent_memb) - 1) // 5 + 1):
    #             embeds.append(discord.Embed(title='Инвентарь'))
    #             for j in range(5):
    #                 j_now = (5 * i) + j
    #                 tmp_role = ctx.guild.get_role(invent_memb[j_now]['rid'])
    #                 embeds[i].add_field(name=f'{j_now + 1}:', value=f'{tmp_role.mention}',
    #                                     inline=False)
    #                 if (j_now + 1) == len(invent_memb):
    #                     break

    #         massage = await ctx.send(embed=embeds[0])
    #         page = Pag(self.bot, massage, only=ctx.author, use_more=False, embeds=embeds)
    #         await page.start()
    #     else:
    #         return await ctx.send(embed=discord.Embed(
    #             title='Уведомление',
    #             description='В инвентаре нет ролей'
    #         ))


async def setup(bot):
    await bot.add_cog(Shop(bot))
