import asyncio
import os

import discord

from storage import bot


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id}) | Connected to ' + str(len(bot.guilds))
          + ' servers | Connected to ' + str(len(set(bot.get_all_members()))) + ' users')


@bot.command(hidden=True, aliases=['lg'])
async def load_cog(ctx, extension):
    """Функция загрузки кога"""
    if ctx.author.id != 469865189341134848:
        return await ctx.send(embed=discord.Embed(
            description='Вы не являетесь разработчиком'
        ))
    await bot.load_extension(f'cogs.{extension}')
    await ctx.send(embed=discord.Embed(
        description=f'Ког {extension} загружается'
    ))


@bot.command(hidden=True, aliases=['ug'])
async def unload_cog(ctx, extension):
    """Функция выгрузки кога"""
    if ctx.author.id != 469865189341134848:
        return await ctx.send(embed=discord.Embed(
            description='Вы не являетесь разработчиком'
        ))
    await bot.unload_extension(f'cogs.{extension}')
    await ctx.send(embed=discord.Embed(
        description=f'Ког {extension} выгружается'
    ))


@bot.command(hidden=True, aliases=['rg'])
async def reload_cog(ctx, extension):
    """Функция перезагрузки кога"""
    if ctx.author.id != 469865189341134848:
        return await ctx.send(embed=discord.Embed(
            description='Вы не являетесь разработчиком'
        ))
    await bot.unload_extension(f'cogs.{extension}')
    await bot.load_extension(f'cogs.{extension}')
    await ctx.send(embed=discord.Embed(
        description=f'Ког {extension} перезагружается'
    ))


async def init_main():
    """Функция загрузки всех когов при старте бота"""
    for file_name in os.listdir('./cogs'):
        if file_name.endswith('.py'):
            await bot.load_extension(f'cogs.{file_name[:-3]}')


async def main():
    """Функция инициализации и соединения с сервером бота"""
    async with bot:
        await init_main()
        await bot.start(os.getenv('TOKEN'))


asyncio.run(main())
