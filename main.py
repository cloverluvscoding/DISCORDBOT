import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUMROAD_PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID")


# Function to verify a license key using Gumroad API
def verify_license(license_key):
    url = "https://api.gumroad.com/v2/licenses/verify"
    payload = {
        "product_id": GUMROAD_PRODUCT_ID,
        "license_key": license_key,
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error verifying license: {e}")
        return None


# Set up the bot with intents
intents = discord.Intents.default()
intents.members = True  # Enable Guild Members Intent

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")


# Slash command for verifying a license key and assigning a role
@tree.command(name="redeem", description="Verify your Gumroad license")
async def redeem_command(interaction: discord.Interaction):
    # Create a modal to ask for the license key
    class LicenseModal(discord.ui.Modal, title="License Verification"):
        license_key_input = discord.ui.TextInput(
            label="Enter Your License Key",
            placeholder="Paste your Gumroad license key here",
            required=True,
        )

        async def on_submit(self, interaction: discord.Interaction):
            license_key = self.license_key_input.value.strip()

            # Verify the license key with Gumroad API
            result = verify_license(license_key)

            if result and result.get("success"):
                # Check if license has already been used
                uses_count = result.get("uses", 0)
                max_allowed_uses = 1  # Set to 1 for single use only

                if uses_count > max_allowed_uses:
                    await interaction.response.send_message(
                        "❌ This license key has already been redeemed by someone else.",
                        ephemeral=True,
                    )
                    return

                guild = interaction.guild
                role_name = "BUYER💪"

                # Find the role in the server by name
                role = discord.utils.get(guild.roles, name=role_name)

                if not role:
                    await interaction.response.send_message(
                        f"❌ Role '{role_name}' not found in this server. Please create it first.",
                        ephemeral=True,
                    )
                    return

                # Assign the role to the user who used the command
                member = guild.get_member(interaction.user.id)
                if member:
                    await member.add_roles(role)
                    await interaction.response.send_message(
                        f"✅ License verified successfully! The '{role_name}' role has been assigned to you.",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        "❌ Could not find your member information in this server.",
                        ephemeral=True,
                    )
            else:
                await interaction.response.send_message(
                    "❌ Invalid license key.", ephemeral=True)

    # Show modal to user
    await interaction.response.send_modal(LicenseModal())


# Run the bot using the token from .env file
bot.run(DISCORD_TOKEN)
