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
    
