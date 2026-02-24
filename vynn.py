import discord
from discord.ext import commands, tasks
from discord import app_commands
import random, asyncio, datetime

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
# Logs Privados e Servidor
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
    if motivo: embed.add_field(name="Motivo", value=motivo, inline=False)
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
        if motivo: embed.add_field(name="Motivo", value=motivo, inline=False)
        await log_channel.send(embed=embed)

# ---------------------------
# Minigames
# ---------------------------

# Pedra, Papel, Tesoura
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

@bot.slash_command(name="ppt", description="Jogue Pedra, Papel ou Tesoura")
async def ppt(ctx):
    escolhas = ["Pedra","Papel","Tesoura"]
    bot_escolha = random.choice(escolhas)
    await ctx.respond(embed=discord.Embed(title="Pedra, Papel ou Tesoura", description="Escolha abaixo:", color=0xFFD700),
                      view=PPTView(bot_escolha))

# Moeda
class MoedaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.clicked_users = []

    async def resultado(self, interaction, escolha_user):
        if interaction.user.id in self.clicked_users:
            await interaction.response.send_message("Você já clicou!", ephemeral=True)
            return
        self.clicked_users.append(interaction.user.id)
        resultado = random.choice(["Cara","Coroa"])
        msg = "Acertou!" if escolha_user==resultado else "Errou!"
        if msg=="Acertou!": add_pontos(interaction.user.id)
        await interaction.response.send_message(f"Você: **{escolha_user}**\nResultado: **{resultado}**\n**{msg}**")

    @discord.ui.button(label="Cara", style=discord.ButtonStyle.primary)
    async def cara(self, button, interaction):
        await self.resultado(interaction, "Cara")
    @discord.ui.button(label="Coroa", style=discord.ButtonStyle.success)
    async def coroa(self, button, interaction):
        await self.resultado(interaction, "Coroa")

@bot.slash_command(name="moeda", description="Jogue Cara ou Coroa")
async def moeda(ctx):
    await ctx.respond(embed=discord.Embed(title="Cara ou Coroa", description="Clique abaixo:", color=0x00FFFF),
                      view=MoedaView())

# Dado
class DadoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.clicked_users = []

    async def resultado(self, interaction):
        if interaction.user.id in self.clicked_users:
            await interaction.response.send_message("Você já clicou!", ephemeral=True)
            return
        self.clicked_users.append(interaction.user.id)
        valor = random.randint(1,6)
        add_pontos(interaction.user.id, valor)
        await interaction.response.send_message(f"{interaction.user.mention} tirou: **{valor}**")

@bot.slash_command(name="dado", description="Rola um dado de 1 a 6")
async def dado(ctx):
    await ctx.respond(embed=discord.Embed(title="Rolar Dado", description="Clique abaixo para rolar!", color=0xFF8C00),
                      view=DadoView())

# ---------------------------
# Emoji Battle
# ---------------------------
class EmojiBattleView(discord.ui.View):
    def __init__(self, bot_escolha, regra):
        super().__init__(timeout=20)
        self.bot_escolha = bot_escolha
        self.regra = regra
        self.clicked_users = []

    async def resultado(self, interaction, escolha_user):
        if interaction.user.id in self.clicked_users:
            await interaction.response.send_message("Você já clicou!", ephemeral=True)
            return
        self.clicked_users.append(interaction.user.id)
        if escolha_user == self.bot_escolha:
            msg = "Empate!"
        elif self.regra[escolha_user] == self.bot_escolha:
            msg = "Você ganhou!"
            add_pontos(interaction.user.id)
        else:
            msg = "Você perdeu!"
        await interaction.response.send_message(f"Bot: {self.bot_escolha}\nVocê: {escolha_user}\n**{msg}**")

@bot.slash_command(name="emojibattle", description="Batalha de Emojis!")
async def emojibattle(ctx):
    escolhas = ["🐍","🐇","🐢"]
    regra = {"🐍":"🐇","🐇":"🐢","🐢":"🐍"}
    bot_escolha = random.choice(escolhas)
    view = EmojiBattleView(bot_escolha, regra)
    for emoji in escolhas:
        view.add_item(discord.ui.Button(label=emoji, style=discord.ButtonStyle.primary, custom_id=emoji))
    await ctx.respond(embed=discord.Embed(title="Emoji Battle", description="Escolha seu emoji!", color=0xFF69B4), view=view)

# ---------------------------
# Comandos de Moderação
# ---------------------------
@bot.slash_command(name="ban", description="Banir usuário com logs")
@commands.has_permissions(ban_members=True)
async def ban(ctx, usuario: discord.Member, motivo: str="Sem motivo"):
    await usuario.ban(reason=motivo)
    await ctx.respond(f"{usuario} banido! 🛑")
    await enviar_log_privado(ctx.guild, usuario, "BAN", motivo)
    await enviar_log_servidor(ctx.guild, usuario, "BAN", motivo)

@bot.slash_command(name="kick", description="Expulsar usuário com logs")
@commands.has_permissions(kick_members=True)
async def kick(ctx, usuario: discord.Member, motivo: str="Sem motivo"):
    await usuario.kick(reason=motivo)
    await ctx.respond(f"{usuario} expulso! 👢")
    await enviar_log_privado(ctx.guild, usuario, "KICK", motivo)
    await enviar_log_servidor(ctx.guild, usuario, "KICK", motivo)

@bot.slash_command(name="mute", description="Mutar usuário")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, usuario: discord.Member, tempo: str="10m"):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, add_reactions=False)
    await usuario.add_roles(role)
    await ctx.respond(f"{usuario} mutado por {tempo} ⏱️")
    await enviar_log_privado(ctx.guild, usuario, "MUTE", tempo)
    await enviar_log_servidor(ctx.guild, usuario, "MUTE", tempo)
    multipliers = {"s":1,"m":60,"h":3600,"d":86400}
    t = int(tempo[:-1]) * multipliers[tempo[-1]]
    await asyncio.sleep(t)
    if role in usuario.roles:
        await usuario.remove_roles(role)
        await ctx.channel.send(f"{usuario} foi desmutado ✅")

@bot.slash_command(name="limpar", description="Apaga mensagens")
@commands.has_permissions(manage_messages=True)
async def limpar(ctx, quantidade: int=10, usuario: discord.Member=None):
    if usuario:
        msgs = [m async for m in ctx.channel.history(limit=100) if m.author==usuario]
        await ctx.channel.delete_messages(msgs[:quantidade])
        await ctx.respond(f"{quantidade} mensagens de {usuario} apagadas!")
    else:
        await ctx.channel.purge(limit=quantidade)
        await ctx.respond(f"{quantidade} mensagens apagadas!")

# ---------------------------
# Perfil e Temas
# ---------------------------
@bot.slash_command(name="perfil", description="Mostra estatísticas do usuário")
async def perfil(ctx, usuario: discord.Member=None):
    usuario = usuario or ctx.author
    pontos = leaderboard.get(usuario.id,0)
    await ctx.respond(embed=discord.Embed(title=f"Perfil de {usuario}", description=f"Pontos: {pontos}", color=0x00FF00))

@bot.slash_command(name="temas", description="Lista todos os temas disponíveis")
async def temas(ctx):
    await ctx.respond("Temas disponíveis: Animes, História, Geografia, Futebol, Matemática, Curiosidades")

# ---------------------------
# Rodar Bot
# ---------------------------
bot.run("SEU_DISCORD_TOKEN_AQUI")
