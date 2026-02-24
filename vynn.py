import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import asyncio
import random
import json
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# -------------------- JOGADORES --------------------
# Estrutura para armazenar jogadores
jogadores = {}

class Jogador:
    def __init__(self, nome, classe="Civil"):
        self.nome = nome
        self.classe = classe  # Civil, Aprendiz, Mago, Mestre
        self.forca = 5
        self.inteligencia = 5
        self.magia = 5
        self.energia = 10
        self.experiencia = 0
        self.inventario = []

    def stats(self):
        return (
            f"🧙 Nome: {self.nome}\n"
            f"🏷️ Classe: {self.classe}\n"
            f"💪 Força: {self.forca}\n"
            f"🧠 Inteligência: {self.inteligencia}\n"
            f"✨ Magia: {self.magia}\n"
            f"⚡ Energia: {self.energia}\n"
            f"📈 Experiência: {self.experiencia}\n"
            f"🎒 Inventário: {', '.join(self.inventario) if self.inventario else 'Vazio'}"
        )
        # -------------------- COMANDOS DE PERSONAGEM --------------------
@bot.command()
async def registrar(ctx, nome):
    """Registra um novo personagem"""
    if ctx.author.id in jogadores:
        await ctx.send(f"❌ Você já tem um personagem, {ctx.author.name}!")
        return
    jogador = Jogador(nome)
    jogadores[ctx.author.id] = jogador
    await ctx.send(f"✅ Personagem {nome} criado com sucesso! Classe: Civil")
    
@bot.command()
async def perfil(ctx):
    """Mostra stats do jogador"""
    jogador = jogadores.get(ctx.author.id)
    if not jogador:
        await ctx.send("❌ Você ainda não tem um personagem. Use /registrar [nome]")
        return
    await ctx.send(jogador.stats())
    # -------------------- TREINO --------------------
@bot.command()
async def treinar(ctx, tipo):
    """Treina atributos: forca, inteligencia, magia"""
    jogador = jogadores.get(ctx.author.id)
    if not jogador:
        await ctx.send("❌ Você ainda não tem um personagem. Use /registrar [nome]")
        return
    tipo = tipo.lower()
    ganho = random.randint(1,3)
    if tipo == "força":
        jogador.forca += ganho
        jogador.experiencia += ganho
        await ctx.send(f"💪 Você treinou força e ganhou {ganho} pontos!")
    elif tipo == "inteligencia":
        jogador.inteligencia += ganho
        jogador.experiencia += ganho
        await ctx.send(f"🧠 Você treinou inteligência e ganhou {ganho} pontos!")
    elif tipo == "magia":
        jogador.magia += ganho
        jogador.experiencia += ganho
        await ctx.send(f"✨ Você treinou magia e ganhou {ganho} pontos!")
    else:
        await ctx.send("❌ Tipo inválido! Use: força, inteligencia ou magia")

# -------------------- AVENTURA --------------------
aventuras_ativas = {}  # jogador_id: estado atual

@bot.command()
async def aventura(ctx):
    """Inicia uma aventura interativa"""
    jogador = jogadores.get(ctx.author.id)
    if not jogador:
        await ctx.send("❌ Você ainda não tem um personagem. Use /registrar [nome]")
        return
    if ctx.author.id in aventuras_ativas:
        await ctx.send("⚠️ Você já está em uma aventura!")
        return
    aventuras_ativas[ctx.author.id] = {"capitulo": 1}
    await ctx.send(
        f"🌲 {jogador.nome}, você entra na floresta misteriosa. Dois caminhos se apresentam: esquerda ou direita.\n"
        f"Use /decidir [esquerda/direita] para continuar sua aventura."
    )

@bot.command()
async def decidir(ctx, escolha):
    jogador = jogadores.get(ctx.author.id)
    estado = aventuras_ativas.get(ctx.author.id)
    if not jogador or not estado:
        await ctx.send("❌ Você não está em uma aventura. Use /aventura")
        return
    escolha = escolha.lower()
    capitulo = estado["capitulo"]

    if capitulo == 1:
        if escolha == "esquerda":
            resultado = f"🦉 Você encontrou um corvo mágico que te dá uma poção de energia!"
            jogador.inventario.append("Poção de Energia")
        else:
            resultado = f"🐺 Um lobo selvagem aparece e você perde 2 de energia!"
            jogador.energia = max(jogador.energia - 2, 0)
        estado["capitulo"] += 1
    elif capitulo == 2:
        if escolha == "esquerda":
            resultado = "🏰 Você encontra um velho mago que te ensina uma magia básica!"
            jogador.magia += 2
        else:
            resultado = "🌊 Você cai em um rio e perde 1 de energia!"
            jogador.energia = max(jogador.energia -1, 0)
        estado["capitulo"] += 1
    else:
        resultado = "🎉 Sua aventura terminou! Volte outro dia para novas aventuras."
        del aventuras_ativas[ctx.author.id]

    await ctx.send(resultado)
    # -------------------- MINIGAMES SIMPLES --------------------
@bot.command()
async def pedrapapeltesoura(ctx):
    opcoes = ["Pedra","Papel","Tesoura"]
    escolha_bot = random.choice(opcoes)
    await ctx.send(f"O bot escolheu: {escolha_bot}\nFaça sua jogada com /jogar [Pedra/Papel/Tesoura]")

@bot.command()
async def jogar(ctx, escolha):
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

# -------------------- LOGS PRIVADOS --------------------
@bot.event
async def on_member_update(before, after):
    dono = await bot.fetch_user(1327679436128129159)  # seu ID
    if before.nick != after.nick:
        await dono.send(f"✏️ {before} mudou nickname para {after.nick} em {after.guild.name}")

# -------------------- INÍCIO DO BOT --------------------
bot.run(os.environ["DISCORD_TOKEN"])
