import discord
from discord.ext import commands
from psycopg2 import sql

from storage import xor_shift, add_member_in_tables, conn


class DuelCallback(discord.ui.View):
    """Класс с кнопкой и реакцией на её нажатие"""

    member_button: discord.Member
    author_button: discord.Member
    bet: int

    def __ini__(self):
        super().__init__()

    @discord.ui.button(style=discord.ButtonStyle.blurple, label='Вступить в поединок!', emoji='⚔️')
    async def duel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка дуэли и реакция на неё"""
        # await add_member_in_tables(interaction.user)
        # db.table(f'{interaction.guild.id}')
        if interaction.user.id == self.author_button.id:
            await interaction.response.send_message('Нельзя биться с самим собой', ephemeral=True)
            print(f'Запрос {interaction.user.name} на битву с самим собой')
            return
        cur = conn.cursor()
        if self.member_button is None:
            cur.execute(
                sql.SQL("""SELECT coin, uid 
                FROM {} WHERE uid = %s""").format(sql.Identifier(f'{interaction.guild.id}'), (interaction.user.id, ))
            )
            getdatamember = cur.fetchone()
            print('Битва для всех')
        else:
            if interaction.user.id != self.member_button.id:
                await interaction.response.send_message('Это не Ваша битва', ephemeral=True)
                print('Это не Ваша битва')
                return
            else:
                cur.execute(
                    sql.SQL("""SELECT coin, uid FROM {} 
                    WHERE uid = %s""").format(sql.Identifier(str(self.member_button.guild.id))),
                    (self.member_button.id, )
                )
                getdatamember = cur.fetchone()
                # getdatamember = db.get(f'{self.member_button.guild.id}').search(Query().uid == self.member_button.id)
                print('Битва против определённого противника')

        cur.execute(
            sql.SQL("""SELECT coin, uid FROM {} WHERE uid = %s""").format(sql.Identifier(str(interaction.guild.id))),
            (self.author_button.id, )
        )
        getdataauthor = cur.fetchone()
        if getdatamember[0] < self.bet:
            print('У противника нет столько коинов для ставки')
            await interaction.channel.send(embed=discord.Embed(
                description=f'У противника нет столько :feather: для ставки'
            ))
            return

        rand_count = await xor_shift()
        if rand_count % 2 != 0:
            tmp = getdataauthor
            getdataauthor = getdatamember
            getdatamember = tmp

        cur.execute(
            sql.SQL("""UPDATE {} 
            SET coin = %s 
            WHERE uid = %s""").format(sql.Identifier(str(interaction.guild.id))),
            (getdataauthor[0] - self.bet, getdataauthor[1])
        )
        cur.execute(
            sql.SQL("""UPDATE {} 
            SET coin = %s 
            WHERE uid = %s""").format(sql.Identifier(str(interaction.guild.id))),
            (getdatamember[0] + int(self.bet * 0.96), getdatamember[1])
        )
        # db.get(f'{interaction.guild.id}').update({'coin': getdataauthor[0][0] - self.bet},
        #                                          where('uid') == getdataauthor[0][1])
        # db.get(f'{interaction.guild.id}').update({'coin': getdatamember[0][0] + int(self.bet * 0.96)},
        #                                          where('uid') == getdatamember[0][1])

        button.style = discord.ButtonStyle.gray
        button.disabled = True
        button.label = 'Конец'
        button.emoji = ''
        print('Битва окончена')
        print('Победа за {} и выйгрыш составил **{}**:feather:!'.format(
            interaction.user.guild.get_member(getdatamember[1]),
            int(self.bet * 0.96)))
        await interaction.response.edit_message(embed=discord.Embed(
            description='Победа за {} и выйгрыш составил **{}**:feather:!'.format(
                interaction.user.guild.get_member(getdatamember[1]).mention,
                int(self.bet * 0.96))
        ), view=self)
        cur.close()


class Fun(commands.Cog):
    """Класс с фановыми командами"""
    def __ini__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Ког BotFun загружен')

    @commands.command(help=f'Выводит случайное число\n')
    async def rand(self, ctx, num1: int = 100, num2: int = None):
        """Команда для вывода случайного числа в разных вариациях"""
        await add_member_in_tables(ctx.author)
        await ctx.channel.purge(limit=1)
        rand_num = await xor_shift()
        if num2 is None:
            await ctx.send(embed=discord.Embed(
                description=f'Случайное число от 0 до {num1}: {int(rand_num % (num1 + 1))}'
            ))
        else:
            if num1 < num2:
                await ctx.send(embed=discord.Embed(
                    description=f'Случайное число от {num1} до {num2}: {int((rand_num % (num2 + 1 - num1)) + num1)}'
                ))
            else:
                await ctx.send(embed=discord.Embed(description='Первое число должно быть меньше чем второе число'))

    @commands.command(help=f'Дуэль с другим пользователем', aliases=['дуэль', 'поединок'])
    async def duel(self, ctx, bet: int = None, member: discord.Member = None):
        """Функция запуска дуэли мужду игроками"""
        print(f'Инициализация поединка от {ctx.author}')
        await add_member_in_tables(ctx.author)
        if member:
            await add_member_in_tables(member)
        # db.table(f'{ctx.guild.id}')
        await ctx.channel.purge(limit=1)
        # getdataauthor = db.get(f'{ctx.guild.id}').search(Query().uid == ctx.author.id)
        if bet is None:
            print('Не указанна ставка')
            return await ctx.send(embed=discord.Embed(description=f'Вы не указали ставку'))

        if bet < 0:
            print(f'Попытка пользователем {ctx.author} (ID:{ctx.author.id}) '
                  f'выставить отрицательное значение ставки для дуэли')
            return await ctx.send(embed=discord.Embed(description=f'Нельзя ставить отрицательную ставку'))
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""SELECT coin FROM {} WHERE uid = %s""").format(sql.Identifier(str(ctx.guild.id))),
            (ctx.author.id,)
        )
        if cur.fetchone()[0] < bet:
            print('Нехватка коинов для ставки')
            return await ctx.send(embed=discord.Embed(description=f'У вас нет столько :feather: для ставки'))

        view1 = DuelCallback()
        view1.author_button = ctx.author
        view1.member_button = member
        view1.bet = bet

        if member is None:
            await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention}, вызывает на "Поединок Птичников" '
                                                           f'всех со ставкой **{bet}**:feather:!'), view=view1)
        else:
            cur.execute(
                sql.SQL("""SELECT coin FROM {} WHERE uid = %s""").format(sql.Identifier(str(member.guild.id))),
                (member.id,)
            )
            if cur.fetchone()[0] < bet:
                return await ctx.send(embed=discord.Embed(description=f'У противника нет столько :feather: для ставки'))
            await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention}, вызывает на "Поединок Птичников" '
                                                           f'{member.mention} со ставкой **{bet}**:feather:!'),
                           content=f'{member.mention}', view=view1)
        cur.close()


async def setup(bot):
    await bot.add_cog(Fun(bot))
