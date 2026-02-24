import discord
from discord.ext import commands, tasks
import asyncio, random, datetime, os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

ADMIN_ID = 1327679436128129159  # Seu ID para logs privados

# ---------------------------
# Leaderboard
# ---------------------------
leaderboard = {}  # {user_id: pontos}

def add_pontos(user_id, pontos=1):
    leaderboard[user_id] = leaderboard.get(user_id, 0) + pontos

# ---------------------------
# Funções de Logs
# ---------------------------
async def enviar_log_privado(guild, usuario, acao, motivo=None):
    admin = await bot.fetch_user(ADMIN_ID)
    embed = discord.Embed(
        title="Log de Moderação",
        color=0xFF0000,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Servidor", value=guild.name, inline=False)
    embed.add_field(name="Usuário", value=str(usuario), inline=False)
    embed.add_field(name="Ação", value=acao, inline=False)
    if motivo:
        embed.add_field(name="Motivo", value=motivo, inline=False)
    await admin.send(embed=embed)

async def enviar_log_servidor(guild, usuario, acao, motivo=None):
    log_channel = discord.utils.get(guild.text_channels, name="logs")
    if log_channel:
        embed = discord.Embed(
            title="Log de Moderação",
            color=0xFF0000,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Usuário", value=str(usuario), inline=False)
        embed.add_field(name="Ação", value=acao, inline=False)
        if motivo:
            embed.add_field(name="Motivo", value=motivo, inline=False)
        await log_channel.send(embed=embed)

# ---------------------------
# Bot Ready
# ---------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online! {bot.user}")
    # ---------------------------
# /perfil
# ---------------------------
@bot.tree.command(name="perfil", description="Mostra estatísticas do usuário")
async def perfil(interaction: discord.Interaction, usuario: discord.Member = None):
    usuario = usuario or interaction.user
    pontos = leaderboard.get(usuario.id, 0)
    embed = discord.Embed(
        title=f"Perfil de {usuario}",
        description=f"Pontos: {pontos}",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# ---------------------------
# /temas
# ---------------------------
@bot.tree.command(name="temas", description="Lista todos os temas disponíveis")
async def temas(interaction: discord.Interaction):
    lista = ["Animes", "História", "Geografia", "Futebol", "Matemática", "Curiosidades"]
    embed = discord.Embed(
        title="Temas disponíveis",
        description="\n".join(f"- {t}" for t in lista),
        color=0x1ABC9C
    )
    await interaction.response.send_message(embed=embed)

# ---------------------------
# /ban
# ---------------------------
@bot.tree.command(name="ban", description="Banir usuário com logs")
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    await usuario.ban(reason=motivo)
    await interaction.response.send_message(f"{usuario} banido! 🛑")
    await enviar_log_privado(interaction.guild, usuario, "BAN", motivo)
    await enviar_log_servidor(interaction.guild, usuario, "BAN", motivo)

# ---------------------------
# /kick
# ---------------------------
@bot.tree.command(name="kick", description="Expulsar usuário com logs")
@commands.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    await usuario.kick(reason=motivo)
    await interaction.response.send_message(f"{usuario} expulso! 👢")
    await enviar_log_privado(interaction.guild, usuario, "KICK", motivo)
    await enviar_log_servidor(interaction.guild, usuario, "KICK", motivo)

# ---------------------------
# /mute
# ---------------------------
@bot.tree.command(name="mute", description="Mutar usuário por tempo determinado")
@commands.has_permissions(manage_roles=True)
async def mute(interaction: discord.Interaction, usuario: discord.Member, tempo: str = "10m"):
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not role:
        role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(role, send_messages=False, add_reactions=False)
    await usuario.add_roles(role)
    await interaction.response.send_message(f"{usuario} mutado por {tempo} ⏱️")
    await enviar_log_privado(interaction.guild, usuario, "MUTE", tempo)
    await enviar_log_servidor(interaction.guild, usuario, "MUTE", tempo)

    multipliers = {"s":1,"m":60,"h":3600,"d":86400}
    t = int(tempo[:-1]) * multipliers[tempo[-1]]
    await asyncio.sleep(t)
    if role in usuario.roles:
        await usuario.remove_roles(role)
        await interaction.channel.send(f"{usuario} foi desmutado ✅")

# ---------------------------
# /limpar
# ---------------------------
@bot.tree.command(name="limpar", description="Apaga mensagens do canal ou de um usuário")
@commands.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, quantidade: int = 10, usuario: discord.Member = None):
    if usuario:
        msgs = [m async for m in interaction.channel.history(limit=100) if m.author == usuario]
        await interaction.channel.delete_messages(msgs[:quantidade])
        await interaction.response.send_message(f"{quantidade} mensagens de {usuario} apagadas!")
    else:
        await interaction.channel.purge(limit=quantidade)
        await interaction.response.send_message(f"{quantidade} mensagens apagadas!")
        # ---------------------------
# Minigame: Pedra, Papel ou Tesoura
# ---------------------------
class PPTView(discord.ui.View):
    def __init__(self, bot_escolha):
        super().__init__(timeout=20)
        self.bot_escolha = bot_escolha
        self.clicked_users = []

    async def resultado(self, interaction, escolha_user):
        if interaction.user.id in self.clicked_users:
            await interaction.response.send_message("Você já clicou!", ephemeral=True)
            return
        self.clicked_users.append(interaction.user.id)

        if escolha_user == self.bot_escolha:
            resultado = "Empate!"
        elif (escolha_user=="Pedra" and self.bot_escolha=="Tesoura") or \
             (escolha_user=="Papel" and self.bot_escolha=="Pedra") or \
             (escolha_user=="Tesoura" and self.bot_escolha=="Papel"):
            resultado = "Você ganhou!"
            add_pontos(interaction.user.id)
        else:
            resultado = "Você perdeu!"

        await interaction.response.send_message(
            f"Você: **{escolha_user}**\nBot: **{self.bot_escolha}**\n**{resultado}**"
        )

    @discord.ui.button(label="Pedra", style=discord.ButtonStyle.primary)
    async def pedra(self, button, interaction):
        await self.resultado(interaction, "Pedra")
    @discord.ui.button(label="Papel", style=discord.ButtonStyle.success)
    async def papel(self, button, interaction):
        await self.resultado(interaction, "Papel")
    @discord.ui.button(label="Tesoura", style=discord.ButtonStyle.danger)
    async def tesoura(self, button, interaction):
        await self.resultado(interaction, "Tesoura")

@bot.tree.command(name="ppt", description="Jogue Pedra, Papel ou Tesoura com o bot")
async def ppt(interaction: discord.Interaction):
    escolhas = ["Pedra", "Papel", "Tesoura"]
    bot_escolha = random.choice(escolhas)
    embed = discord.Embed(
        title="Pedra, Papel ou Tesoura",
        description="Escolha sua opção abaixo:",
        color=0xFFD700
    )
    await interaction.response.send_message(embed=embed, view=PPTView(bot_escolha))

# ---------------------------
# Minigame: Lançar Moeda
# ---------------------------
class CoinFlipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.clicked_users = []

    async def resultado(self, interaction, escolha_user):
        if interaction.user.id in self.clicked_users:
            await interaction.response.send_message("Você já clicou!", ephemeral=True)
            return
        self.clicked_users.append(interaction.user.id)

        bot_escolha = random.choice(["Cara", "Coroa"])
        if escolha_user == bot_escolha:
            resultado = "Você ganhou!"
            add_pontos(interaction.user.id)
        else:
            resultado = "Você perdeu!"

        await interaction.response.send_message(
            f"Você: **{escolha_user}**\nResultado: **{bot_escolha}**\n**{resultado}**"
        )

    @discord.ui.button(label="Cara", style=discord.ButtonStyle.primary)
    async def cara(self, button, interaction):
        await self.resultado(interaction, "Cara")
    @discord.ui.button(label="Coroa", style=discord.ButtonStyle.success)
    async def coroa(self, button, interaction):
        await self.resultado(interaction, "Coroa")

@bot.tree.command(name="moeda", description="Jogue cara ou coroa")
async def moeda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Moeda",
        description="Escolha Cara ou Coroa:",
        color=0x00FFFF
    )
    await interaction.response.send_message(embed=embed, view=CoinFlipView())

# ---------------------------
# Minigame: Lançar Dado
# ---------------------------
class DiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.clicked_users = []

    async def resultado(self, interaction):
        if interaction.user.id in self.clicked_users:
            await interaction.response.send_message("Você já rolou!", ephemeral=True)
            return
        self.clicked_users.append(interaction.user.id)

        valor = random.randint(1, 6)
        add_pontos(interaction.user.id)
        await interaction.response.send_message(
            f"{interaction.user.mention} rolou o dado e caiu: **{valor}** 🎲\nVocê ganhou 1 ponto!"
        )

    @discord.ui.button(label="Rolar Dado", style=discord.ButtonStyle.primary)
    async def rolar(self, button, interaction):
        await self.resultado(interaction)

@bot.tree.command(name="dado", description="Role um dado de 6 lados")
async def dado(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Dado",
        description="Clique para rolar o dado:",
        color=0xFFA500
    )
    await interaction.response.send_message(embed=embed, view=DiceView())
    # ---------------------------------------
# QUIZ - FUNÇÕES PRINCIPAIS
# ---------------------------------------

# Estruturas de controle do quiz
quiz_ativo = {}   # Canal: {tema, indice, modo}
quiz_timer = {}   # Canal: tempo restante
quiz_top3 = {}    # Canal: {user_id: pontos}

# Função para criar view dos botões de múltipla escolha
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

# Função para enviar próxima pergunta
async def enviar_pergunta(ctx, tema, indice):
    pergunta_data = temas_perguntas[tema][indice]
    embed = discord.Embed(title=f"Pergunta {indice+1}/{len(temas_perguntas[tema])}", description=pergunta_data["pergunta"], color=discord.Color.blurple())
    if pergunta_data.get("imagem"):
        embed.set_image(url=pergunta_data["imagem"])
    
    usuario_acertou = {}
    view = criar_view(pergunta_data, usuario_acertou)
    
    msg = await ctx.send(embed=embed, view=view)
    
    # Timer visível
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
        await ctx.send(f"⏰ Tempo esgotado! Ninguém acertou. Resposta correta: {', '.join(pergunta_data['resposta'])}")
    
    # Atualizando top3
    if ctx.channel.id not in quiz_top3:
        quiz_top3[ctx.channel.id] = {}
    for user_id, pontos in usuario_acertou.items():
        quiz_top3[ctx.channel.id][user_id] = quiz_top3[ctx.channel.id].get(user_id, 0) + pontos
        # ---------------------------------------
# COMANDOS DO QUIZ / SLASH
# ---------------------------------------

@bot.slash_command(name="iniciar", description="Inicia um quiz com tema selecionado")
async def iniciar(ctx, tema: discord.Option(str, "Escolha o tema", choices=tema_nomes)):
    if ctx.channel.id in quiz_ativo:
        await ctx.respond("⚠️ Um quiz já está ativo neste canal!")
        return
    
    quiz_ativo[ctx.channel.id] = {"tema": tema, "indice": 0, "modo": "múltipla"}
    quiz_top3[ctx.channel.id] = {}
    
    await ctx.respond(f"🎮 Quiz iniciado! Tema: **{tema}**\nUse `/next` para avançar manualmente ou `/auto` para automático.")

@bot.slash_command(name="next", description="Avança para a próxima pergunta")
async def next_pergunta(ctx):
    if ctx.channel.id not in quiz_ativo:
        await ctx.respond("⚠️ Nenhum quiz ativo neste canal. Use /iniciar para começar.")
        return
    
    quiz_data = quiz_ativo[ctx.channel.id]
    indice = quiz_data["indice"]
    tema = quiz_data["tema"]
    
    if indice >= len(temas_perguntas[tema]):
        await ctx.respond("✅ Quiz finalizado!")
        # Mostrar Top 3
        top3 = sorted(quiz_top3[ctx.channel.id].items(), key=lambda x: x[1], reverse=True)[:3]
        if top3:
            msg = "🏆 **Top 3:**\n"
            for user_id, pontos in top3:
                user = await bot.fetch_user(user_id)
                msg += f"{user.name}: {pontos} ponto(s)\n"
            await ctx.send(msg)
        del quiz_ativo[ctx.channel.id]
        del quiz_top3[ctx.channel.id]
        return
    
    await enviar_pergunta(ctx, tema, indice)
    quiz_ativo[ctx.channel.id]["indice"] += 1

@bot.slash_command(name="auto", description="Inicia o quiz automático até o fim")
async def auto_quiz(ctx, tema: discord.Option(str, "Escolha o tema", choices=tema_nomes)):
    if ctx.channel.id in quiz_ativo:
        await ctx.respond("⚠️ Um quiz já está ativo neste canal!")
        return
    
    quiz_ativo[ctx.channel.id] = {"tema": tema, "indice": 0, "modo": "múltipla"}
    quiz_top3[ctx.channel.id] = {}
    await ctx.respond(f"🎮 Quiz automático iniciado! Tema: **{tema}**\nUse `/stop` para pausar.")
    
    while quiz_ativo.get(ctx.channel.id):
        indice = quiz_ativo[ctx.channel.id]["indice"]
        if indice >= len(temas_perguntas[tema]):
            # Terminar quiz
            top3 = sorted(quiz_top3[ctx.channel.id].items(), key=lambda x: x[1], reverse=True)[:3]
            msg = "🏆 **Top 3 Final:**\n"
            for user_id, pontos in top3:
                user = await bot.fetch_user(user_id)
                msg += f"{user.name}: {pontos} ponto(s)\n"
            await ctx.send(msg)
            del quiz_ativo[ctx.channel.id]
            del quiz_top3[ctx.channel.id]
            break
        await enviar_pergunta(ctx, tema, indice)
        quiz_ativo[ctx.channel.id]["indice"] += 1
        await asyncio.sleep(2)  # Pequena pausa entre perguntas

@bot.slash_command(name="stop", description="Para o quiz em andamento")
async def stop_quiz(ctx):
    if ctx.channel.id not in quiz_ativo:
        await ctx.respond("⚠️ Nenhum quiz ativo neste canal.")
        return
    del quiz_ativo[ctx.channel.id]
    await ctx.respond("⏹ Quiz pausado.")
    # ---------------------------------------
# MODERAÇÃO AVANÇADA
# ---------------------------------------

# Substitua pelo seu ID
OWNER_ID = 1327679436128129159

@bot.event
async def on_member_ban(guild, user):
    # Log público no canal padrão (se existir)
    log_channel = discord.utils.get(guild.text_channels, name="mod-logs")
    if log_channel:
        await log_channel.send(f"🚫 {user.name} foi banido do servidor.")
    # Envia DM para o dono do bot
    owner = await bot.fetch_user(OWNER_ID)
    await owner.send(f"[BAN] {user.name} foi banido do servidor {guild.name}.")

@bot.event
async def on_member_unban(guild, user):
    owner = await bot.fetch_user(OWNER_ID)
    await owner.send(f"[UNBAN] {user.name} foi desbanido do servidor {guild.name}.")

@bot.event
async def on_member_update(before, after):
    # Logs de mute (exemplo se usar roles)
    mute_role = discord.utils.get(after.guild.roles, name="Muted")
    owner = await bot.fetch_user(OWNER_ID)
    if mute_role:
        if mute_role in after.roles and mute_role not in before.roles:
            await owner.send(f"[MUTE] {after.name} foi mutado no servidor {after.guild.name}.")
        elif mute_role not in after.roles and mute_role in before.roles:
            await owner.send(f"[UNMUTE] {after.name} foi desmutado no servidor {after.guild.name}.")

# ---------------------------------------
# MINIGAMES AVANÇADOS
# ---------------------------------------

import random

@bot.slash_command(name="ppt", description="Jogue Pedra-Papel-Tesoura com o bot")
async def pedra_papel_tesoura(ctx, escolha: discord.Option(str, "Sua escolha", choices=["Pedra","Papel","Tesoura"])):
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
    await ctx.respond(f"Você: {escolha}\nBot: {bot_escolha}\nResultado: {resultado}")

@bot.slash_command(name="adivinhar", description="Tente adivinhar o número que o bot pensou (1-10)")
async def adivinhar(ctx, numero: discord.Option(int, "Escolha um número de 1 a 10", min_value=1, max_value=10)):
    bot_num = random.randint(1,10)
    if numero == bot_num:
        await ctx.respond(f"🎉 Acertou! Eu pensei no número {bot_num}")
    else:
        await ctx.respond(f"❌ Errou! Eu pensei no número {bot_num}")

# Você pode adicionar mais minigames aqui seguindo o mesmo padrão

# ---------------------------------------
# INICIALIZAÇÃO DO BOT
# ---------------------------------------
bot.run(os.environ["DISCORD_TOKEN"])
