import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
    # -------------------- COMANDOS SLASH --------------------
@bot.command()
async def iniciar(ctx):
    """Inicia o quiz de anime"""
    ctx.quiz_perguntas = perguntas.copy()  # Faz uma cópia das perguntas para cada usuário
    if not ctx.quiz_perguntas:
        await ctx.send("Não há perguntas disponíveis no momento!")
        return
    pergunta_obj = random.choice(ctx.quiz_perguntas)
    ctx.quiz_perguntas.remove(pergunta_obj)
    await enviar_pergunta(ctx, pergunta_obj)


@bot.command()
async def next(ctx):
    """Mostra a próxima pergunta do quiz"""
    if not hasattr(ctx, "quiz_perguntas") or not ctx.quiz_perguntas:
        await ctx.send("Não há mais perguntas! Use /iniciar para começar novamente.")
        return
    pergunta_obj = random.choice(ctx.quiz_perguntas)
    ctx.quiz_perguntas.remove(pergunta_obj)
    await enviar_pergunta(ctx, pergunta_obj)


# -------------------- MINIGAMES SIMPLES --------------------
@bot.command()
async def pedrapapeltesoura(ctx):
    """Inicia Pedra, Papel ou Tesoura"""
    opcoes = ["Pedra","Papel","Tesoura"]
    escolha_bot = random.choice(opcoes)
    await ctx.send(f"O bot escolheu: {escolha_bot}\nFaça sua jogada com /jogar [Pedra/Papel/Tesoura]")

@bot.command()
async def jogar(ctx, escolha):
    """Joga Pedra, Papel ou Tesoura"""
    escolha = escolha.capitalize()
    opcoes = ["Pedra","Papel","Tesoura"]
    if escolha not in opcoes:
        await ctx.send("Escolha inválida! Pedra, Papel ou Tesoura.")
        return
    escolha_bot = random.choice(opcoes)
    resultado = ""
    if escolha == escolha_bot:
        resultado = "Empate!"
    elif (escolha=="Pedra" and escolha_bot=="Tesoura") or (escolha=="Tesoura" and escolha_bot=="Papel") or (escolha=="Papel" and escolha_bot=="Pedra"):
        resultado = "Você ganhou!"
    else:
        resultado = "Você perdeu!"
    await ctx.send(f"Você: {escolha}\nBot: {escolha_bot}\nResultado: {resultado}")


# -------------------- OUTROS MINIGAMES SIMPLES --------------------
@bot.command()
async def dado(ctx):
    """Joga um dado de 6 lados"""
    resultado = random.randint(1,6)
    await ctx.send(f"🎲 O dado caiu em: {resultado}")

@bot.command()
async def moeda(ctx):
    """Joga cara ou coroa"""
    resultado = random.choice(["Cara", "Coroa"])
    await ctx.send(f"🪙 O resultado foi: {resultado}")
    # -------------------- MODERAÇÃO AVANÇADA --------------------
@bot.event
async def on_member_ban(guild, user):
    # Envia log para o servidor (caso haja canal #logs)
    canal_log = discord.utils.get(guild.text_channels, name="logs")
    if canal_log:
        await canal_log.send(f"🚫 {user} foi banido do servidor {guild.name}")
    # Envia log para o dono do bot via DM
    dono = await bot.fetch_user(1327679436128129159)  # Substitua pelo seu ID
    await dono.send(f"🚫 {user} foi banido do servidor {guild.name}")

@bot.event
async def on_member_unban(guild, user):
    dono = await bot.fetch_user(YOUR_USER_ID)
    await dono.send(f"✅ {user} foi desbanido do servidor {guild.name}")

@bot.event
async def on_member_update(before, after):
    dono = await bot.fetch_user(YOUR_USER_ID)
    if before.nick != after.nick:
        await dono.send(f"✏️ {before} mudou o nickname para {after.nick} em {after.guild.name}")

# -------------------- MINIGAMES AVANÇADOS --------------------
@bot.command()
async def adivinhar(ctx):
    """Minigame: Adivinhe o número"""
    numero = random.randint(1,50)
    await ctx.send("🎯 Tente adivinhar o número entre 1 e 50 usando /palpite [número]")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for _ in range(5):  # 5 tentativas
        try:
            msg = await bot.wait_for("message", check=check, timeout=20)
            palpite = int(msg.content)
            if palpite == numero:
                await ctx.send(f"🎉 Correto! O número era {numero}")
                return
            elif palpite < numero:
                await ctx.send("⬆️ Mais alto!")
            else:
                await ctx.send("⬇️ Mais baixo!")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Tempo esgotado! O número era {numero}")
            return
        except ValueError:
            await ctx.send("Digite apenas números!")

# -------------------- START DO BOT --------------------
bot.run(os.environ["DISCORD_TOKEN"])
