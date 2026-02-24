import discord
from discord.ext import commands, tasks
import json
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# ---------------------------------------
# CARREGANDO TEMAS
# ---------------------------------------
temas_perguntas = {}
tema_files = ["temas.json"]
tema_nomes = ["Animes","História","Futebol","Matemática"]

for nome, arquivo in zip(tema_nomes, tema_files):
    with open(arquivo, "r", encoding="utf-8") as f:
        temas_perguntas[nome] = json.load(f)

# ---------------------------------------
# ESTRUTURAS DE CONTROLE
# ---------------------------------------
quiz_ativo = {}   # Canal: {tema, indice, modo}
quiz_top3 = {}    # Canal: {user_id: pontos}

# ---------------------------------------
# FUNÇÃO PARA CRIAR BOTÕES DE MÚLTIPLA ESCOLHA
# ---------------------------------------
def criar_view(pergunta_data, usuario_acertou):
    view = discord.ui.View(timeout=None)
    ja_clicou = set()
    
    for i, alt in enumerate(pergunta_data["alternativas"]):
        letra = chr(65+i)  # A, B, C, D
        btn = discord.ui.Button(label=f"{letra}. {alt}", style=discord.ButtonStyle.primary)
        
        async def button_callback(interaction, resposta=alt):
            if interaction.user.id in ja_clicou:
                await interaction.response.send_message("Você já clicou!", ephemeral=True)
                return
            ja_clicou.add(interaction.user.id)
            
            correto = any(resposta.lower() in r.lower() or r.lower() in resposta.lower() for r in pergunta_data["resposta"])
            if correto:
                usuario_acertou[interaction.user.id] = usuario_acertou.get(interaction.user.id, 0) + 1
                await interaction.response.send_message(f"✅ Você acertou, {interaction.user.name}!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Você errou! {interaction.user.name}", ephemeral=True)
        
        btn.callback = button_callback
        view.add_item(btn)
    return view

# ---------------------------------------
# FUNÇÃO PARA ENVIAR PERGUNTA COM TIMER
# ---------------------------------------
async def enviar_pergunta(interaction: discord.Interaction, tema, indice):
    pergunta_data = temas_perguntas[tema][indice]
    embed = discord.Embed(title=f"Pergunta {indice+1}/{len(temas_perguntas[tema])}", description=pergunta_data["pergunta"], color=discord.Color.blurple())
    if pergunta_data.get("imagem"):
        embed.set_image(url=pergunta_data["imagem"])
    
    usuario_acertou = {}
    view = criar_view(pergunta_data, usuario_acertou)
    
    msg = await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
    
    # Timer visível (atualiza a cada 5 segundos)
    tempo = 20
    while tempo > 0:
        await asyncio.sleep(5)
        tempo -= 5
        try:
            await msg.edit(embed=discord.Embed(
                title=f"Pergunta {indice+1}/{len(temas_perguntas[tema])}",
                description=f"{pergunta_data['pergunta']}\n⏱ Tempo restante: {tempo} segundos",
                color=discord.Color.blurple()
            ), view=view)
        except:
            pass
    
    # Se ninguém acertou
    if not usuario_acertou:
        await interaction.followup.send(f"⏰ Tempo esgotado! Ninguém acertou. Resposta correta: {', '.join(pergunta_data['resposta'])}")
    
    # Atualizando top3
    if interaction.channel.id not in quiz_top3:
        quiz_top3[interaction.channel.id] = {}
    for user_id, pontos in usuario_acertou.items():
        quiz_top3[interaction.channel.id][user_id] = quiz_top3[interaction.channel.id].get(user_id, 0) + pontos

# ---------------------------------------
# BOT PRONTO PARA REGISTRAR SLASH COMMANDS
# ---------------------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot logado como {bot.user}')
    # ---------------------------------------
# COMANDOS DO QUIZ / SLASH - DISCORD.PY 2.X
# ---------------------------------------

from discord import Option  # Para opções de slash command

@bot.tree.command(name="iniciar", description="Inicia um quiz com tema selecionado")
async def iniciar(interaction: discord.Interaction, tema: Option(str, "Escolha o tema", choices=tema_nomes)):
    if interaction.channel.id in quiz_ativo:
        await interaction.response.send_message("⚠️ Um quiz já está ativo neste canal!", ephemeral=True)
        return
    
    quiz_ativo[interaction.channel.id] = {"tema": tema, "indice": 0, "modo": "múltipla"}
    quiz_top3[interaction.channel.id] = {}
    
    await interaction.response.send_message(f"🎮 Quiz iniciado! Tema: **{tema}**\nUse `/next` para avançar manualmente ou `/auto` para automático.")

@bot.tree.command(name="next", description="Avança para a próxima pergunta")
async def next_pergunta(interaction: discord.Interaction):
    if interaction.channel.id not in quiz_ativo:
        await interaction.response.send_message("⚠️ Nenhum quiz ativo neste canal. Use /iniciar para começar.", ephemeral=True)
        return
    
    quiz_data = quiz_ativo[interaction.channel.id]
    indice = quiz_data["indice"]
    tema = quiz_data["tema"]
    
    if indice >= len(temas_perguntas[tema]):
        await interaction.response.send_message("✅ Quiz finalizado!", ephemeral=True)
        # Mostrar Top 3
        top3 = sorted(quiz_top3[interaction.channel.id].items(), key=lambda x: x[1], reverse=True)[:3]
        if top3:
            msg = "🏆 **Top 3:**\n"
            for user_id, pontos in top3:
                user = await bot.fetch_user(user_id)
                msg += f"{user.name}: {pontos} ponto(s)\n"
            await interaction.followup.send(msg)
        del quiz_ativo[interaction.channel.id]
        del quiz_top3[interaction.channel.id]
        return
    
    await enviar_pergunta(interaction, tema, indice)
    quiz_ativo[interaction.channel.id]["indice"] += 1

@bot.tree.command(name="auto", description="Inicia o quiz automático até o fim")
async def auto_quiz(interaction: discord.Interaction, tema: Option(str, "Escolha o tema", choices=tema_nomes)):
    if interaction.channel.id in quiz_ativo:
        await interaction.response.send_message("⚠️ Um quiz já está ativo neste canal!", ephemeral=True)
        return
    
    quiz_ativo[interaction.channel.id] = {"tema": tema, "indice": 0, "modo": "múltipla"}
    quiz_top3[interaction.channel.id] = {}
    await interaction.response.send_message(f"🎮 Quiz automático iniciado! Tema: **{tema}**\nUse `/stop` para pausar.")

    while quiz_ativo.get(interaction.channel.id):
        indice = quiz_ativo[interaction.channel.id]["indice"]
        if indice >= len(temas_perguntas[tema]):
            # Terminar quiz
            top3 = sorted(quiz_top3[interaction.channel.id].items(), key=lambda x: x[1], reverse=True)[:3]
            msg = "🏆 **Top 3 Final:**\n"
            for user_id, pontos in top3:
                user = await bot.fetch_user(user_id)
                msg += f"{user.name}: {pontos} ponto(s)\n"
            await interaction.followup.send(msg)
            del quiz_ativo[interaction.channel.id]
            del quiz_top3[interaction.channel.id]
            break
        await enviar_pergunta(interaction, tema, indice)
        quiz_ativo[interaction.channel.id]["indice"] += 1
        await asyncio.sleep(2)  # Pequena pausa entre perguntas

@bot.tree.command(name="stop", description="Para o quiz em andamento")
async def stop_quiz(interaction: discord.Interaction):
    if interaction.channel.id not in quiz_ativo:
        await interaction.response.send_message("⚠️ Nenhum quiz ativo neste canal.", ephemeral=True)
        return
    del quiz_ativo[interaction.channel.id]
    await interaction.response.send_message("⏹ Quiz pausado.", ephemeral=True)
    # ---------------------------------------
# MODERAÇÃO AVANÇADA E MINIGAMES - DISCORD.PY 2.X
# ---------------------------------------

import random

# Substitua pelo seu ID
OWNER_ID = 1327679436128129159

# ---------- MODERAÇÃO ----------
@bot.event
async def on_member_ban(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name="mod-logs")
    if log_channel:
        await log_channel.send(f"🚫 {user.name} foi banido do servidor.")
    owner = await bot.fetch_user(OWNER_ID)
    await owner.send(f"[BAN] {user.name} foi banido do servidor {guild.name}.")

@bot.event
async def on_member_unban(guild, user):
    owner = await bot.fetch_user(OWNER_ID)
    await owner.send(f"[UNBAN] {user.name} foi desbanido do servidor {guild.name}.")

@bot.event
async def on_member_update(before, after):
    mute_role = discord.utils.get(after.guild.roles, name="Muted")
    owner = await bot.fetch_user(OWNER_ID)
    if mute_role:
        if mute_role in after.roles and mute_role not in before.roles:
            await owner.send(f"[MUTE] {after.name} foi mutado no servidor {after.guild.name}.")
        elif mute_role not in after.roles and mute_role in before.roles:
            await owner.send(f"[UNMUTE] {after.name} foi desmutado no servidor {after.guild.name}.")

# ---------- MINIGAMES ----------
@bot.tree.command(name="ppt", description="Jogue Pedra-Papel-Tesoura com o bot")
async def pedra_papel_tesoura(interaction: discord.Interaction, escolha: Option(str, "Sua escolha", choices=["Pedra","Papel","Tesoura"])):
    opcoes = ["Pedra","Papel","Tesoura"]
    bot_escolha = random.choice(opcoes)
    resultado = ""
    if escolha == bot_escolha:
        resultado = "Empate!"
    elif (escolha == "Pedra" and bot_escolha == "Tesoura") or \
         (escolha == "Papel" and bot_escolha == "Pedra") or \
         (escolha == "Tesoura" and bot_escolha == "Papel"):
        resultado = "Você venceu! 🎉"
    else:
        resultado = "Você perdeu 😢"
    await interaction.response.send_message(f"Você: {escolha}\nBot: {bot_escolha}\nResultado: {resultado}")

@bot.tree.command(name="adivinhar", description="Tente adivinhar o número que o bot pensou (1-10)")
async def adivinhar(interaction: discord.Interaction, numero: Option(int, "Escolha um número de 1 a 10", min_value=1, max_value=10)):
    bot_num = random.randint(1,10)
    if numero == bot_num:
        await interaction.response.send_message(f"🎉 Acertou! Eu pensei no número {bot_num}")
    else:
        await interaction.response.send_message(f"❌ Errou! Eu pensei no número {bot_num}")

# ---------- INICIALIZAÇÃO DO BOT ----------
bot.run(os.environ["DISCORD_TOKEN"])
