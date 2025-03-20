import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
import os

# Load or create player data
if os.path.exists("all_rankings.csv"):
    players = pd.read_csv("all_rankings.csv")
else:
    players = pd.DataFrame(columns=["Name", "Rating", "Wins", "Losses"])

# Elo rating functions
def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_ratings(player_a, player_b, winner):
    global players

    # Get current ratings
    rating_a = players.loc[players["Name"] == player_a, "Rating"].values[0]
    rating_b = players.loc[players["Name"] == player_b, "Rating"].values[0]

    # Calculate expected scores
    expected_a = calculate_expected_score(rating_a, rating_b)
    expected_b = calculate_expected_score(rating_b, rating_a)

    # Update ratings and win/loss records
    if winner == player_a:
        new_rating_a = rating_a + 32 * (1 - expected_a)
        new_rating_b = rating_b + 32 * (0 - expected_b)
        players.loc[players["Name"] == player_a, "Wins"] += 1
        players.loc[players["Name"] == player_b, "Losses"] += 1
    elif winner == player_b:
        new_rating_a = rating_a + 32 * (0 - expected_a)
        new_rating_b = rating_b + 32 * (1 - expected_b)
        players.loc[players["Name"] == player_b, "Wins"] += 1
        players.loc[players["Name"] == player_a, "Losses"] += 1
    else:
        return "Invalid winner! Please enter a valid player name."

    # Update ratings in the DataFrame
    players.loc[players["Name"] == player_a, "Rating"] = new_rating_a
    players.loc[players["Name"] == player_b, "Rating"] = new_rating_b

    # Save updated data to CSV
    players.to_csv("player_rankings.csv", index=False)
    return f"Ratings updated! {player_a}: {new_rating_a}, {player_b}: {new_rating_b}"

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

# Slash command to add a player
@bot.tree.command(name="addplayer", description="Add a new player to the rankings.")
async def add_player(interaction: discord.Interaction, name: str):
    global players
    if name in players["Name"].values:
        await interaction.response.send_message(f"{name} is already in the rankings!")
    else:
        new_player = pd.DataFrame({"Name": [name], "Rating": [1000], "Wins": [0], "Losses": [0]})
        players = pd.concat([players, new_player], ignore_index=True)
        players.to_csv("player_rankings.csv", index=False)
        await interaction.response.send_message(f"{name} has been added to the rankings with an initial rating of 1000.")

# Slash command to record a match
@bot.tree.command(name="recordmatch", description="Record the result of a match.")
async def record_match(interaction: discord.Interaction, player_a: str, player_b: str, winner: str):
    if player_a not in players["Name"].values or player_b not in players["Name"].values:
        await interaction.response.send_message("One or both players not found in the rankings!")
    else:
        result = update_ratings(player_a, player_b, winner)
        await interaction.response.send_message(result)

# Slash command to view rankings
@bot.tree.command(name="rankings", description="View the current rankings.")
async def show_rankings(interaction: discord.Interaction):
    sorted_players = players.sort_values(by="Rating", ascending=False)
    rankings = "Current Rankings:\n"
    for index, row in sorted_players.iterrows():
        rankings += f"{row['Name']}: Rating = {row['Rating']}, Wins = {row['Wins']}, Losses = {row['Losses']}\n"
    await interaction.response.send_message(rankings)

# Run the bot
bot.run("MTM1MjI4MzQ2MDA4NTIyMzUzNA.GjRF31.4-4u8W1B2IE3dNVEkZUYezzLvsTLoT-WD3G1hY")
