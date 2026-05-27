import discord
from discord.ext import commands
from discord.ui import Select, View
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
BOT_TOKEN = os.getenv("NORTH_TICKETS_TOKEN", "")
KEEPALIVE_PORT = 8080
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
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="Get Help From Our Team", emoji="💬"),
            discord.SelectOption(label="Tweaks", description="Buy Tweaks", emoji="⚙️"),
        ]
        super().__init__(placeholder="Select Category", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")
    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        chosen = self.values[0]
        channel_name = f"{chosen.lower()}-{user.name.lower()}"
        existing = discord.utils.get(guild.channels, name=channel_name)
        if existing:
            await interaction.response.send_message(f"Already have a ticket: {existing.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        embed = discord.Embed(title=f"🎫 {chosen} Ticket", description=f"Welcome {user.mention}, our team will be with you shortly.", color=0xFFFFFF)
        await ticket_channel.send(embed=embed)
        await interaction.response.send_message(f"Ticket created! {ticket_channel.mention}", ephemeral=True)
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
@bot.event
async def on_ready():
    bot.add_view(TicketView())
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name} | Tickets Active")
@bot.tree.command(name="setupticket", description="Post the ticket panel (admin only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setupticket(interaction: discord.Interaction):
    embed = discord.Embed(title="North | Support Center", description="Choose a category to open a ticket.", color=0xFFFFFF)
    await interaction.response.send_message(embed=embed, view=TicketView())
bot.run(BOT_TOKEN)
