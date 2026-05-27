import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
BOT_TOKEN       = os.getenv("NORTH_AUTH_TOKEN", "")
ROLE_UNVERIFIED = "Unverfied"
ROLE_VERIFIED   = "Verfied"
WELCOME_CHANNEL = "welcome"
WELCOME_IMAGE   = "welcome_card.png"
KEEPALIVE_PORT  = 8080
class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"alive")
    def log_message(self, *args): pass
class _Server(HTTPServer):
    allow_reuse_address = True
threading.Thread(target=lambda: _Server(("0.0.0.0", KEEPALIVE_PORT), _Handler).serve_forever(), daemon=True).start()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
        verify_button = Button(label="🔒 Verify in North", style=discord.ButtonStyle.gray, custom_id="verify_button_persistent")
        verify_button.callback = self.verify_callback
        self.add_item(verify_button)
    async def verify_callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        unverified_role = discord.utils.get(guild.roles, name=ROLE_UNVERIFIED)
        verified_role = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
        if not verified_role:
            await interaction.response.send_message(f"❌ Could not find role **{ROLE_VERIFIED}**.", ephemeral=True)
            return
        if verified_role in member.roles:
            await interaction.response.send_message("✅ Already verified!", ephemeral=True)
            return
        try:
            await member.add_roles(verified_role)
            if unverified_role and unverified_role in member.roles:
                await member.remove_roles(unverified_role)
            await interaction.response.send_message("✅ Verified! Welcome to North.", ephemeral=True)
            welcome_channel = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL)
            if welcome_channel:
                embed = discord.Embed(description=f"👋 Welcome {member.mention} to **North**!", color=0xFFFFFF)
                image_path = os.path.join(os.path.dirname(__file__), WELCOME_IMAGE)
                if os.path.isfile(image_path):
                    file = discord.File(image_path, filename=WELCOME_IMAGE)
                    embed.set_image(url=f"attachment://{WELCOME_IMAGE}")
                    await welcome_channel.send(embed=embed, file=file)
                else:
                    await welcome_channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permission error — bot role must be higher than Verified/Unverified.", ephemeral=True)
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name} | Auth Active")
@bot.event
async def on_member_join(member):
    unverified_role = discord.utils.get(member.guild.roles, name=ROLE_UNVERIFIED)
    if unverified_role:
        try: await member.add_roles(unverified_role)
        except discord.Forbidden: pass
@bot.tree.command(name="setupverify", description="Post the verification panel (admin only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setupverify(interaction: discord.Interaction):
    embed = discord.Embed(title="Verify to access the server.", description="• Click **Verify** below\n• By verifying you agree to follow our rules", color=0xFFFFFF)
    await interaction.response.send_message(embed=embed, view=VerifyView())
bot.run(BOT_TOKEN)
