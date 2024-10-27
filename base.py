#!/usr/bin/env python
from db_functions import DatabaseHandler
from lang.lang import LangHelper
from async_eval import eval
from discord.app_commands import Choice
from discord import app_commands
from datetime import datetime
import traceback
import logging
import asyncio
import discord
import json
import time
import sys
import os

##############################
#         Pre Launch         #
##############################

logging.disable(logging.INFO)

with open("config.json", "r") as f:
    config = json.load(f)

debug_guild = discord.Object(config["debug_guild"])

channel_last_updated = {}

##############################
#           Client           #
##############################

class Client(discord.Client):
    def __init__(self, config):
        self.config = config

        intents = discord.Intents.default()
        intents.members = True

        # start the bot
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.db = DatabaseHandler()
        self.lang = LangHelper()
        self.invite_data = {}

    async def setup_hook(self):
        self.tree.copy_global_to(guild=debug_guild)
        await self.tree.sync(guild=debug_guild) # sync commands into debug guild

    def run(self):
        super().run(self.config.get("token"))

client = Client(config)

def check_has_permission(interaction: discord.Interaction) -> bool:
    adminrole = client.db.get_config(guild=interaction.guild.id, key="AdminRole")

    # Check if the user have administrator permissions
    # Source : https://github.com/Rapptz/discord.py/blob/master/discord/app_commands/checks.py#L334
    perms = {"administrator": True}
    permissions = interaction.permissions
    missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
    if not missing:
        return True

    if interaction.user.get_role(adminrole):
        return True

    return False

def check_bot_rename_channel(channel_db):
    def predicate(interaction: discord.Interaction) -> bool:
        permissions = None
        channel = client.db.get_config(guild=interaction.guild.id, key=channel_db)
        channel = interaction.guild.get_channel(channel) if channel else None
        if not channel:
            permissions = interaction.guild.me.guild_permissions

        perms = {"connect": True, "manage_channels": True, "view_channel": True}

        # Check in the user have administrator permissions
        # Source : https://github.com/Rapptz/discord.py/blob/master/discord/app_commands/checks.py#L334
        if not permissions:
            permissions = channel.permissions_for(interaction.guild.me)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise app_commands.BotMissingPermissions(missing)

    return app_commands.check(predicate)

def check_bot_has_permission(**perms: bool):
    def predicate(interaction: discord.Interaction) -> bool:

        # Check in the user have administrator permissions
        # Source : https://github.com/Rapptz/discord.py/blob/master/discord/app_commands/checks.py#L334
        permissions = interaction.guild.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise app_commands.BotMissingPermissions(missing)

    return app_commands.check(predicate)

##############################
#           Events           #
##############################

@client.event
async def on_ready():
    await client.tree.sync()
    mems = 0
    for guild in client.guilds:
        mems += guild.member_count
    print(f"{client.user} | {len(client.guilds)} guilds | {mems} members")
    print(f"Ready | {datetime.now().strftime('%d/%m/%Y | %H:%M:%S')}")
    sys.stdout.flush()

    # presence
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help ⭐"))
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Verified and updated 🎉"))

    for guild in client.guilds:
        try:
            for invite in await guild.invites():
                client.invite_data[invite.code] = invite
        except discord.Forbidden:
            pass

# Search the inviter for new members

@client.event
async def on_invite_create(invite):
    client.invite_data[invite.code] = invite

@client.event
async def on_invite_delete(invite):
    try:
        del client.invite_data[invite.code]
    except KeyError:
        pass # to silence mysterious errors

@client.event
async def on_member_join(member):
    # needed in welcome message and goal channel
    guild = member.guild
    member_count = guild.member_count
    goal = client.db.get_goal(guild=guild.id, num=member_count)
    # add invite to inviter

    member_invite = None
    try:
        guild_invites = await guild.invites()
        for invite in guild_invites:
            if invite.code in client.invite_data and client.invite_data[invite.code]:
                old_invite = client.invite_data[invite.code]
                if old_invite.uses and invite.uses and invite.uses > old_invite.uses:
                    client.invite_data[invite.code] = invite
                    if member != invite.inviter:
                        client.db.add_invite(guild=guild.id, inviter=invite.inviter.id, invited=member.id)
                        client.db.update_invite_leave(leave=False, guild=guild.id, invited=member.id)
                    member_invite = invite
                    break
    except discord.Forbidden:
        pass

    # welcome message

    welcome_toggle = client.db.get_config(guild=guild.id, key="Welcome")
    welcome_channel = client.db.get_config(guild=guild.id, key="WelcomeChannel")
    welcome_channel = client.get_channel(welcome_channel) if welcome_channel else None
    welcome_message = client.db.get_config(guild=guild.id, key="WelcomeMessage")
    welcome_embed = client.db.get_config(guild=guild.id, key="WelcomeEmbed")
    if welcome_toggle:
        if welcome_channel:
            inviter = member_invite.inviter if member_invite else None
            # replace all {} texts by variables
            welcome_message = welcome_message.replace("{server}", guild.name)
            welcome_message = welcome_message.replace("{member}", f"{member}" if member else "Unknown")
            welcome_message = welcome_message.replace("{membermention}", member.mention if member else "Unknown")
            welcome_message = welcome_message.replace("{inviter}", f"{inviter}" if inviter else "Unknown")
            welcome_message = welcome_message.replace("{invitermention}", inviter.mention if inviter else "Unknown")
            welcome_message = welcome_message.replace("{membernum}", str(member_count) or "Unknown")
            welcome_message = welcome_message.replace("{goal}", str(goal) if goal else "No goal left")
            welcome_message = welcome_message.replace("{togoal}", str(goal - member_count) if goal else "No goal left")
            if "{invitercount}" in welcome_message:
                if inviter:
                    inviter_invite_count = client.db.get_invites_data(guild=guild.id, member=inviter.id)
                    inviter_invite_count = inviter_invite_count[0] + inviter_invite_count[2]
                else:
                    inviter_invite_count = "Unknown"
                welcome_message = welcome_message.replace("{invitercount}", str(inviter_invite_count))
            try:
                if welcome_embed:
                    embed = discord.Embed(title=guild.name, description=welcome_message, color=65280)
                    if guild.icon:
                        embed.set_thumbnail(url=guild.icon.url)

                    embed.timestamp = datetime.now()
                    await welcome_channel.send(embed=embed)
                else:
                    await welcome_channel.send(content=welcome_message)
            except discord.Forbidden:
                client.db.set_config(guild=guild.id, key="WelcomeChannel", value=None)
            except discord.NotFound:
                client.db.set_config(guild=guild.id, key="WelcomeChannel", value=None)
        else:
            client.db.set_config(guild=guild.id, key="WelcomeChannel", value=None)

    # goal channel update

    goal_channel = client.db.get_config(guild=guild.id, key="GoalID")
    if goal_channel:
        goal_channel = member.guild.get_channel(goal_channel)
        if goal_channel:
            goal_channel_name = client.db.get_config(guild=guild.id, key="GoalName")
            goal_channel_name = goal_channel_name.replace("{goal}", str(goal) if goal else "No goal left")
            try:
                await goal_channel.edit(name=goal_channel_name)
            except discord.Forbidden:
                client.db.set_config(guild=guild.id, key="GoalID", value=None)
            except discord.NotFound:
                client.db.set_config(guild=guild.id, key="GoalID", value=None)
        else:
            client.db.set_config(guild=guild.id, key="GoalID", value=None)

    # member channel update

    member_channel = client.db.get_config(guild=guild.id, key="MemberChannel")
    if member_channel:
        if not member_channel in channel_last_updated or not channel_last_updated[member_channel] + 100 > time.time():
            channel_last_updated[member_channel] = time.time()
            member_channel = member.guild.get_channel(member_channel)
            if member_channel:
                member_channel_name = client.db.get_config(guild=guild.id, key="MemberChannelName")
                member_channel_name = member_channel_name.replace("{memnumber}", str(member_count))
                try:
                    await member_channel.edit(name=member_channel_name)
                except discord.Forbidden:
                    client.db.set_config(guild=guild.id, key="MemberChannel", value=None)
                except discord.NotFound:
                    client.db.set_config(guild=guild.id, key="MemberChannel", value=None)
            else:
                client.db.set_config(guild=guild.id, key="MemberChannel", value=None)

    # bot channel update

    bot_channel = client.db.get_config(guild=guild.id, key="BotChannel")
    if bot_channel and member.bot:
        if not bot_channel in channel_last_updated or not channel_last_updated[bot_channel] + 100 > time.time():
            channel_last_updated[bot_channel] = time.time()
            bot_channel = member.guild.get_channel(bot_channel)
            if bot_channel:
                bots = client.db.get_config(guild=guild.id, key="NumBot")
                bots += 1
                client.db.set_config(guild=guild.id, key="NumBot", value=bots)
                bot_channel_name = client.db.get_config(guild=guild.id, key="BotChannelName")
                bot_channel_name = bot_channel_name.replace("{botnumber}", str(bots))
                try:
                    await bot_channel.edit(name=bot_channel_name)
                except discord.Forbidden:
                    client.db.set_config(guild=guild.id, key="BotChannel", value=None)
                except discord.NotFound:
                    client.db.set_config(guild=guild.id, key="BotChannel", value=None)
            else:
                client.db.set_config(guild=guild.id, key="BotChannel", value=None)

    # auto role

    auto_role = client.db.get_config(guild=guild.id, key="AutoRole")
    if auto_role:
        auto_role = member.guild.get_role(auto_role)
        if auto_role:
            try:
                await member.add_roles(auto_role)
            except discord.Forbidden:
                client.db.set_config(guild=guild.id, key="AutoRole", value=None)
            except discord.NotFound:
                client.db.set_config(guild=guild.id, key="AutoRole", value=None)
        else:
            client.db.set_config(guild=guild.id, key="AutoRole", value=None)

    # rank

    if member_invite:
        inviter = guild.get_member(member_invite.inviter.id) # can't use member_invite.inviter because it's a User not a Member
        if inviter:
            inviter_invite_count = client.db.get_invites_data(guild=guild.id, member=inviter.id)
            inviter_invite_count = inviter_invite_count[0] + inviter_invite_count[2]
            db_rank, db_old_rank = client.db.get_rank_count(guild=guild.id, count=inviter_invite_count)
            if db_rank:
                rank = member.guild.get_role(db_rank)
                if rank:
                    try:
                        await inviter.add_roles(rank)
                        if client.db.get_config(guild=guild.id, key="RemoveOldRankOnRankup") and db_old_rank:
                            old_rank = member.guild.get_role(db_old_rank)
                            if old_rank:
                                await inviter.remove_roles(old_rank)
                    except discord.Forbidden:
                        client.db.del_rank(rank=db_rank)
                    except discord.NotFound:
                        client.db.del_rank(rank=db_rank)
                else:
                    client.db.del_rank(rank=db_rank)

@client.event
async def on_member_remove(member):
    guild = member.guild
    client.db.update_invite_leave(leave=True, guild=guild.id, invited=member.id)
    member_count = guild.member_count
    goal = client.db.get_goal(guild=guild.id, num=member_count)

    #goodbye message

    goodbye_toggle = client.db.get_config(guild=guild.id, key="Goodbye")
    goodbye_channel = client.db.get_config(guild=guild.id, key="GoodbyeChannel")
    goodbye_channel = client.get_channel(goodbye_channel) if goodbye_channel else None
    goodbye_message = client.db.get_config(guild=guild.id, key="GoodbyeMessage")
    goodbye_embed = client.db.get_config(guild=guild.id, key="GoodbyeEmbed")
    if goodbye_toggle:
        if goodbye_channel:
            inviter = guild.get_member(client.db.get_inviter(guild=guild.id, invited=member.id)) if client.db.get_inviter(guild=guild.id, invited=member.id) else None
            # replace all {abc} texts by variables
            goodbye_message = goodbye_message.replace("{server}", guild.name)
            goodbye_message = goodbye_message.replace("{member}", f"{member}" if member else "Unknown")
            goodbye_message = goodbye_message.replace("{membermention}", member.mention if member else "Unknown")
            goodbye_message = goodbye_message.replace("{inviter}", f"{inviter}" if inviter else "Unknown")
            goodbye_message = goodbye_message.replace("{invitermention}", inviter.mention if inviter else "Unknown")
            goodbye_message = goodbye_message.replace("{membernum}", str(member_count) or "Unknown")
            goodbye_message = goodbye_message.replace("{goal}", str(goal) if goal else "No goal left")
            goodbye_message = goodbye_message.replace("{togoal}", str(goal - member_count) if goal else "No goal left")
            if "{invitercount}" in goodbye_message:
                if inviter:
                    inviter_invite_count = client.db.get_invites_data(guild=guild.id, member=inviter.id)
                    inviter_invite_count = inviter_invite_count[0] + inviter_invite_count[2]
                else:
                    inviter_invite_count = "Unknown"
                goodbye_message = goodbye_message.replace("{invitercount}", str(inviter_invite_count))
            try:
                if goodbye_embed:
                    embed = discord.Embed(title=guild.name, description=goodbye_message, color=16711680)
                    if guild.icon:
                        embed.set_thumbnail(url=guild.icon.url)

                    embed.timestamp = datetime.now()
                    await goodbye_channel.send(embed=embed)
                else:
                    await goodbye_channel.send(content=goodbye_message)
            except discord.Forbidden:
                client.db.set_config(guild=guild.id, key="GoodbyeChannel", value=None)
            except discord.NotFound:
                client.db.set_config(guild=guild.id, key="GoodbyeChannel", value=None)
        else:
            client.db.set_config(guild=guild.id, key="GoodbyeChannel", value=None)

    # goal channel update

    goal_channel = client.db.get_config(guild=guild.id, key="GoalID")
    if goal_channel:
        goal_channel = guild.get_channel(goal_channel)
        if goal_channel:
            goal_channel_name = client.db.get_config(guild=guild.id, key="GoalName")
            goal_channel_name = goal_channel_name.replace("{goal}", str(goal) if goal else "No goal left")
            try:
                await goal_channel.edit(name=goal_channel_name)
            except discord.Forbidden:
                client.db.set_config(guild=guild.id, key="GoalID", value=None)
            except discord.NotFound:
                client.db.set_config(guild=guild.id, key="GoalID", value=None)
        else:
            client.db.set_config(guild=guild.id, key="GoalID", value=None)

    # member channel update

    member_channel = client.db.get_config(guild=guild.id, key="MemberChannel")
    if member_channel:
        if not member_channel in channel_last_updated or not channel_last_updated[member_channel] + 100 > time.time():
            channel_last_updated[member_channel] = time.time()
            member_channel = guild.get_channel(member_channel)
            if member_channel:
                member_channel_name = client.db.get_config(guild=guild.id, key="MemberChannelName")
                member_channel_name = member_channel_name.replace("{memnumber}", str(member_count))
                try:
                    await member_channel.edit(name=member_channel_name)
                except discord.Forbidden:
                    client.db.set_config(guild=guild.id, key="MemberChannel", value=None)
                except discord.NotFound:
                    client.db.set_config(guild=guild.id, key="MemberChannel", value=None)
            else:
                client.db.set_config(guild=guild.id, key="MemberChannel", value=None)

    # bot channel update

    bot_channel = client.db.get_config(guild=guild.id, key="BotChannel")
    if bot_channel and member.bot:
        if not bot_channel in channel_last_updated or not channel_last_updated[bot_channel] + 100 > time.time():
            channel_last_updated[bot_channel] = time.time()
            bot_channel = guild.get_channel(bot_channel)
            if bot_channel:
                bots = client.db.get_config(guild=guild.id, key="NumBot")
                bots -= 1
                client.db.set_config(guild=guild.id, key="NumBot", value=bots)
                bot_channel_name = client.db.get_config(guild=guild.id, key="BotChannelName")
                bot_channel_name = bot_channel_name.replace("{botnumber}", str(bots))
                try:
                    await bot_channel.edit(name=bot_channel_name)
                except discord.Forbidden:
                    client.db.set_config(guild=guild.id, key="BotChannel", value=None)
                except discord.NotFound:
                    client.db.set_config(guild=guild.id, key="BotChannel", value=None)
            else:
                client.db.set_config(guild=guild.id, key="BotChannel", value=None)

    # rank

    inviter = client.db.get_inviter(guild=guild.id, invited=member.id)
    if inviter:
        inviter = guild.get_member(inviter)
        if inviter:
            inviter_invite_count = client.db.get_invites_data(guild=guild.id, member=inviter.id)
            inviter_invite_count = inviter_invite_count[0] + inviter_invite_count[2] + 1
            db_rank, db_old_rank = client.db.get_rank_count(guild=guild.id, count=inviter_invite_count)
            if db_rank:
                rank = member.guild.get_role(db_rank)
                if rank:
                    try:
                        await inviter.remove_roles(rank)
                        if client.db.get_config(guild=guild.id, key="RemoveOldRankOnRankup") and db_old_rank:
                            old_rank = member.guild.get_role(db_old_rank)
                            if old_rank:
                                await inviter.add_roles(old_rank)
                    except discord.Forbidden:
                        client.db.del_rank(rank=db_rank)
                    except discord.NotFound:
                        client.db.del_rank(rank=db_rank)
                else:
                    client.db.del_rank(rank=db_rank)

@client.event
async def on_guild_channel_delete(channel):
    guild = channel.guild

    goal_channel = client.db.get_config(guild=guild.id, key="GoalID")
    if goal_channel == channel.id:
        client.db.set_config(guild=guild.id, key="GoalID", value=None)

    member_channel = client.db.get_config(guild=guild.id, key="MemberChannel")
    if member_channel == channel.id:
        client.db.set_config(guild=guild.id, key="MemberChannel", value=None)

    bot_channel = client.db.get_config(guild=guild.id, key="BotChannel")
    if bot_channel == channel.id:
        client.db.set_config(guild=guild.id, key="BotChannel", value=None)

    welcome_channel = client.db.get_config(guild=guild.id, key="WelcomeChannel")
    if welcome_channel == channel.id:
        client.db.set_config(guild=guild.id, key="WelcomeChannel", value=None)

@client.event
async def on_guild_role_delete(role):
    guild = role.guild

    auto_role = client.db.get_config(guild=guild.id, key="AutoRole")
    if auto_role == role.id:
        client.db.set_config(guild=guild.id, key="AutoRole", value=None)

    admin_role = client.db.get_config(guild=guild.id, key="AdminRole")
    if admin_role == role.id:
        client.db.set_config(guild=guild.id, key="AdminRole", value=None)

    client.db.del_rank(rank=role.id)

@client.event
async def on_guild_join(guild):
    description = f"Server joined : **{guild.name}**\n" + \
    f"Total number of servers : **{len(client.guilds)}** servers\n\n" +  \
    f"📝 **Server Name** : `{guild.name}`\n" +  \
    f"🏷️ **Server ID** : `{guild.id}`\n" +  \
    f"👥 **Members** : `{guild.member_count}`\n" +  \
    f"👑 **Owner Mention** : {guild.owner.mention if guild.owner else '🤷‍♂️'}\n" +  \
    f"🤴 **Owner Info** : `{guild.owner}` `{guild.owner.id if guild.owner else '🤷‍♂️'}`\n"
    embed = discord.Embed(color=0x00FF00, title="📈 Join Server", description=description)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.timestamp = datetime.now()
    await client.get_channel(client.config["join_channel"]).send(embed=embed)
    if str(guild.preferred_locale) in client.lang.langs:
        lang = client.lang.langs[str(guild.preferred_locale)]
        client.db.set_config(guild=guild.id, key="Lang", value=lang)


@client.event
async def on_guild_remove(guild):
    description = f"Server left : **{guild.name}**\n" +  \
    f"Total number of servers : **{len(client.guilds)}** servers\n\n" +  \
    f"📝 **Server Name** : `{guild.name}`\n" +  \
    f"🏷️ **Server ID** : `{guild.id}`\n" +  \
    f"👥 **Members** : `{guild.member_count}`\n" +  \
    f"👑 **Owner Mention** : {guild.owner.mention if guild.owner else '🤷‍♂️'}\n" +  \
    f"🤴 **Owner Info** : `{guild.owner}` `{guild.owner.id if guild.owner else '🤷‍♂️'}`\n"
    embed = discord.Embed(color=0xFF0000, title="📉 Left Server", description=description)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.timestamp = datetime.now()
    await client.get_channel(client.config["join_channel"]).send(embed=embed)

##############################
#          Commands          #
##############################

## Config commands

ConfigGroup = app_commands.Group(name="config", description="Configure the bot")


# goal config


GoalSubGroup = app_commands.Group(name="goal", description="Configure the server goals", parent=ConfigGroup)

@GoalSubGroup.command(name="set", description="Set the goal list (number of members to reach)")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("GoalID")
@app_commands.describe(goal_list='List of all goals separated by spaces')
async def config_goal_set(interaction: discord.Interaction, goal_list: str):
    goal_list = [int(s) for s in goal_list.split() if s.isdigit()]
    if not goal_list:
        await interaction.response.send_message(embed=client.lang.error_no_goal_list(interaction))
        return
    client.db.set_goals(guild=interaction.guild.id, goals=goal_list)
    goal = client.db.get_goal(guild=interaction.guild.id, num=interaction.guild.member_count)
    goal_channel = client.db.get_config(guild=interaction.guild.id, key="GoalID")
    goal_channel = interaction.guild.get_channel(goal_channel) if goal_channel else None
    goal_channel_name = client.db.get_config(guild=interaction.guild.id, key="GoalName")
    goal_channel_name = goal_channel_name.replace("{goal}", str(goal) if goal else "No goal left")
    if goal_channel:
        await goal_channel.edit(name=goal_channel_name)
    await interaction.response.send_message(embed=client.lang.command_config_goal_set(interaction, goal_list))

@GoalSubGroup.command(name="list", description="List all current goals")
@app_commands.check(check_has_permission)
async def config_goal_list(interaction: discord.Interaction):
    goal_list = client.db.get_goals(guild=interaction.guild.id)
    await interaction.response.send_message(
        embed=client.lang.command_config_goal_list(interaction, goal_list) if goal_list else client.lang.command_config_goal_list_no_goals(interaction)
    )

@GoalSubGroup.command(name="rename", description="Rename the goal channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("GoalID")
@app_commands.describe(name='The goal channel name, {goal} is replaced by the current goal')
async def config_goal_rename(interaction: discord.Interaction, name: str):
    if len(name) > 100:
        await interaction.response.send_message(embed=client.lang.error_channel_name_too_long(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="GoalName", value=name)
    # rename the channel in discord
    goal = client.db.get_goal(guild=interaction.guild.id, num=interaction.guild.member_count)
    goal_channel = client.db.get_config(guild=interaction.guild.id, key="GoalID")
    goal_channel = interaction.guild.get_channel(goal_channel) if goal_channel else None
    goal_channel_name = name.replace("{goal}", str(goal) if goal else "No goal left")
    if goal_channel:
        await goal_channel.edit(name=goal_channel_name)
    await interaction.response.send_message(embed=client.lang.command_config_goal_rename(interaction, name))

@GoalSubGroup.command(name="create", description="Create the goal channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("GoalID")
async def config_goal_create(interaction: discord.Interaction):
    # delete the old channel
    goal_channel = client.db.get_config(guild=interaction.guild.id, key="GoalID")
    goal_channel = interaction.guild.get_channel(goal_channel) if goal_channel else None
    if goal_channel:
        await goal_channel.delete()

    goal = client.db.get_goal(guild=interaction.guild.id, num=interaction.guild.member_count)
    goal_channel_name = client.db.get_config(guild=interaction.guild.id, key="GoalName")
    goal_channel_name = goal_channel_name.replace("{goal}", str(goal) if goal else "No goal left")
    # create the new channel
    overwrite = {
        interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
        interaction.guild.me: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True)
    }
    goal_channel = await interaction.guild.create_voice_channel(name=goal_channel_name, overwrites=overwrite)
    client.db.set_config(guild=interaction.guild.id, key="GoalID", value=goal_channel.id)
    await interaction.response.send_message(embed=client.lang.command_config_goal_create(interaction))

@GoalSubGroup.command(name="delete", description="Delete the goal channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("GoalID")
async def config_goal_delete(interaction: discord.Interaction):
    goal_channel = client.db.get_config(guild=interaction.guild.id, key="GoalID")
    goal_channel = interaction.guild.get_channel(goal_channel) if goal_channel else None
    if goal_channel:
        await goal_channel.delete()
    else:
        await interaction.response.send_message(embed=client.lang.error_no_goal_channel(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="GoalID", value=None)
    await interaction.response.send_message(embed=client.lang.command_config_goal_delete(interaction))


# member counter config


MemberCounterSubGroup = app_commands.Group(name="member_counter", description="Configure the member counter", parent=ConfigGroup)

@MemberCounterSubGroup.command(name="create", description="Create the member counter channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("MemberChannel")
async def config_member_counter_create(interaction: discord.Interaction):
    # delete the old channel
    member_channel = client.db.get_config(guild=interaction.guild.id, key="MemberChannel")
    member_channel = interaction.guild.get_channel(member_channel) if member_channel else None
    if member_channel:
        await member_channel.delete()

    member_channel_name = client.db.get_config(guild=interaction.guild.id, key="MemberChannelName")
    member_channel_name = member_channel_name.replace("{memnumber}", str(interaction.guild.member_count))
    # create the new channel
    overwrite = {
        interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
        interaction.guild.me: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True)
    }
    member_channel = await interaction.guild.create_voice_channel(name=member_channel_name, overwrites=overwrite)
    client.db.set_config(guild=interaction.guild.id, key="MemberChannel", value=member_channel.id)
    await interaction.response.send_message(embed=client.lang.command_config_member_counter_create(interaction))

@MemberCounterSubGroup.command(name="delete", description="Delete the member counter channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("MemberChannel")
async def config_member_counter_delete(interaction: discord.Interaction):
    member_channel = client.db.get_config(guild=interaction.guild.id, key="MemberChannel")
    member_channel = interaction.guild.get_channel(member_channel) if member_channel else None
    if member_channel:
        await member_channel.delete()
    else:
        await interaction.response.send_message(embed=client.lang.error_no_member_channel(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="MemberChannel", value=None)
    await interaction.response.send_message(embed=client.lang.command_config_member_counter_delete(interaction))

@MemberCounterSubGroup.command(name="rename", description="Rename the member counter channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("MemberChannel")
@app_commands.describe(name='The member counter channel name, {memnumber} is replaced by the current member count')
async def config_member_counter_rename(interaction: discord.Interaction, name: str):
    if len(name) > 100:
        await interaction.response.send_message(embed=client.lang.error_channel_name_too_long(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="MemberChannelName", value=name)
    # rename the channel in discord
    member_channel = client.db.get_config(guild=interaction.guild.id, key="MemberChannel")
    member_channel = interaction.guild.get_channel(member_channel) if member_channel else None
    member_channel_name = name.replace("{memnumber}", str(interaction.guild.member_count))
    if member_channel:
        await member_channel.edit(name=member_channel_name)
    await interaction.response.send_message(embed=client.lang.command_config_member_counter_rename(interaction, name))


# bot counter config


BotCounterSubGroup = app_commands.Group(name="bot_counter", description="Configure the bot counter", parent=ConfigGroup)


@BotCounterSubGroup.command(name="create", description="Create the bot counter channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("BotChannel")
async def config_bot_counter_create(interaction: discord.Interaction):
    # delete the old channel
    bot_channel = client.db.get_config(guild=interaction.guild.id, key="BotChannel")
    bot_channel = interaction.guild.get_channel(bot_channel) if bot_channel else None
    if bot_channel:
        await bot_channel.delete()

    bot_channel_name = client.db.get_config(guild=interaction.guild.id, key="BotChannelName")
    bots = 0
    for mem in interaction.guild.members:
        bots += 1 if mem.bot else 0
    client.db.set_config(guild=interaction.guild.id, key="NumBot", value=bots)
    bot_channel_name = bot_channel_name.replace("{botnumber}", str(bots))
    # create the new channel
    overwrite = {
        interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
        interaction.guild.me: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True)
    }
    bot_channel = await interaction.guild.create_voice_channel(name=bot_channel_name, overwrites=overwrite)
    client.db.set_config(guild=interaction.guild.id, key="BotChannel", value=bot_channel.id)
    await interaction.response.send_message(embed=client.lang.command_config_bot_counter_create(interaction))

@BotCounterSubGroup.command(name="delete", description="Delete the bot counter channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("BotChannel")
async def config_bot_counter_delete(interaction: discord.Interaction):
    bot_channel = client.db.get_config(guild=interaction.guild.id, key="BotChannel")
    bot_channel = interaction.guild.get_channel(bot_channel) if bot_channel else None
    if bot_channel:
        await bot_channel.delete()
    else:
        await interaction.response.send_message(embed=client.lang.error_no_bot_channel(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="BotChannel", value=None)
    await interaction.response.send_message(embed=client.lang.command_config_bot_counter_delete(interaction))

@BotCounterSubGroup.command(name="rename", description="Rename the bot counter channel")
@app_commands.check(check_has_permission)
@check_bot_rename_channel("BotChannel")
@app_commands.describe(name='The bot counter channel name, {botnumber} is replaced by the current bot count')
async def config_bot_counter_rename(interaction: discord.Interaction, name: str):
    if len(name) > 100:
        await interaction.response.send_message(embed=client.lang.error_channel_name_too_long(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="BotChannelName", value=name)
    # rename the channel in discord
    bot_channel = client.db.get_config(guild=interaction.guild.id, key="BotChannel")
    bot_channel = interaction.guild.get_channel(bot_channel) if bot_channel else None
    bots = client.db.get_config(guild=interaction.guild.id, key="NumBot")
    bot_channel_name = name.replace("{botnumber}", str(bots))
    if bot_channel:
        await bot_channel.edit(name=bot_channel_name)
    await interaction.response.send_message(embed=client.lang.command_config_bot_counter_rename(interaction, name))


# welcome config


WelcomeSubGroup = app_commands.Group(name="welcome", description="Configure the welcome message", parent=ConfigGroup)

@WelcomeSubGroup.command(name="channel", description="Choose the channel where the bot will send welcome messages")
@app_commands.check(check_has_permission)
@app_commands.describe(channel='The welcome channel')
async def config_welcome_channel(interaction: discord.Interaction, channel: discord.channel.TextChannel):
    bot_permissions = channel.permissions_for(interaction.guild.me)
    if not bot_permissions.send_messages:
        await interaction.response.send_message(embed=client.lang.error_bot_permission_send_messages(interaction, channel))
        return
    client.db.set_config(guild=interaction.guild.id, key="WelcomeChannel", value=channel.id)
    await interaction.response.send_message(embed=client.lang.command_config_welcome_channel(interaction, channel))

@WelcomeSubGroup.command(name="message", description="Change the welcome message")
@app_commands.check(check_has_permission)
@app_commands.describe(message='See all variables with /help config')
async def config_welcome_message(interaction: discord.Interaction, message: str):
    if len(message) > 1024:
        await interaction.response.send_message(embed=client.lang.error_welcome_message_too_long(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="WelcomeMessage", value=message)
    await interaction.response.send_message(embed=client.lang.command_config_welcome_message(interaction, message))

@WelcomeSubGroup.command(name="embed", description="Choose if the welcome message will be in an embed")
@app_commands.check(check_has_permission)
async def config_welcome_embed(interaction: discord.Interaction, toggle: bool):
    client.db.set_config(guild=interaction.guild.id, key="WelcomeEmbed", value=toggle)
    await interaction.response.send_message(embed=client.lang.command_config_welcome_embed(interaction, toggle))

@WelcomeSubGroup.command(name="toggle", description="Choose if the bot should send welcome messages")
@app_commands.check(check_has_permission)
async def config_welcome_toggle(interaction: discord.Interaction, toggle: bool):
    client.db.set_config(guild=interaction.guild.id, key="Welcome", value=toggle)
    await interaction.response.send_message(embed=client.lang.command_config_welcome_toggle(interaction, toggle))


# goodbye config


GoodbyeSubGroup = app_commands.Group(name="goodbye", description="Configure the goodbye message", parent=ConfigGroup)

@GoodbyeSubGroup.command(name="channel", description="Choose the channel where the bot will send goodbye messages")
@app_commands.check(check_has_permission)
@app_commands.describe(channel='The goodbye channel')
async def config_goodbye_channel(interaction: discord.Interaction, channel: discord.channel.TextChannel):
    bot_permissions = channel.permissions_for(interaction.guild.me)
    if not bot_permissions.send_messages:
        await interaction.response.send_message(embed=client.lang.error_bot_permission_send_messages(interaction, channel))
        return
    client.db.set_config(guild=interaction.guild.id, key="GoodbyeChannel", value=channel.id)
    await interaction.response.send_message(embed=client.lang.command_config_goodbye_channel(interaction, channel))

@GoodbyeSubGroup.command(name="message", description="Change the goodbye message")
@app_commands.check(check_has_permission)
@app_commands.describe(message='See all variables with /help config')
async def config_goodbye_message(interaction: discord.Interaction, message: str):
    if len(message) > 1024:
        await interaction.response.send_message(embed=client.lang.error_goodbye_message_too_long(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="GoodbyeMessage", value=message)
    await interaction.response.send_message(embed=client.lang.command_config_goodbye_message(interaction, message))

@GoodbyeSubGroup.command(name="embed", description="Choose if the goodbye message will be in an embed")
@app_commands.check(check_has_permission)
async def config_goodbye_embed(interaction: discord.Interaction, toggle: bool):
    client.db.set_config(guild=interaction.guild.id, key="GoodbyeEmbed", value=toggle)
    await interaction.response.send_message(embed=client.lang.command_config_goodbye_embed(interaction, toggle))

@GoodbyeSubGroup.command(name="toggle", description="Choose if the bot should send goodbye messages")
@app_commands.check(check_has_permission)
async def config_goodbye_toggle(interaction: discord.Interaction, toggle: bool):
    client.db.set_config(guild=interaction.guild.id, key="Goodbye", value=toggle)
    await interaction.response.send_message(embed=client.lang.command_config_goodbye_toggle(interaction, toggle))


# other configs


@ConfigGroup.command(name="language", description="Choose the language of the bot")
@app_commands.check(check_has_permission)
@app_commands.choices(lang=[
    Choice(name='Français 🇫🇷', value="fr"),
    Choice(name='English 🇬🇧', value="en"),
])
async def config_language(interaction: discord.Interaction, lang: Choice[str]):
    client.db.set_config(guild=interaction.guild.id, key="Lang", value=lang.value)
    await interaction.response.send_message(embed=client.lang.command_config_language(interaction))

@ConfigGroup.command(name="view", description="View current configuration")
@app_commands.check(check_has_permission)
async def config_view(interaction: discord.Interaction):
    configs = client.db.get_all_config(guild=interaction.guild.id)
    await interaction.response.send_message(embed=client.lang.command_config_view(interaction, configs))

@ConfigGroup.command(name="auto_role", description="Choose a role to add to all new members")
@check_bot_has_permission(manage_roles=True)
@app_commands.check(check_has_permission)
async def config_auto_role(interaction: discord.Interaction, role: discord.Role):
    if role.managed:
        await interaction.response.send_message(embed=client.lang.error_role_managed(interaction, role))
        return
    bot_role = interaction.guild.me.top_role
    if role.position > bot_role.position:
        await interaction.response.send_message(embed=client.lang.error_role_above_bot(interaction, role))
        return
    if role.is_default():
        await interaction.response.send_message(embed=client.lang.error_role_default(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="AutoRole", value=role.id)
    await interaction.response.send_message(embed=client.lang.command_config_autorole(interaction, role))

@ConfigGroup.command(name="admin_role", description="Choose a role who can use admin commands")
@app_commands.check(check_has_permission)
async def config_admin_role(interaction: discord.Interaction, role: discord.Role):
    if role.is_default():
        await interaction.response.send_message(embed=client.lang.error_role_default(interaction))
        return
    client.db.set_config(guild=interaction.guild.id, key="AdminRole", value=role.id)
    await interaction.response.send_message(embed=client.lang.command_config_adminrole(interaction, role))

client.tree.add_command(ConfigGroup)

@ConfigGroup.command(name="remove_old_rank_on_rankup", description="Remove old rank when a member get a new rank")
@check_bot_has_permission(manage_roles=True)
@app_commands.check(check_has_permission)
async def config_remove_old_rank_on_rankup(interaction: discord.Interaction, toggle: bool):
    client.db.set_config(guild=interaction.guild.id, key="RemoveOldRankOnRankup", value=toggle)
    await interaction.response.send_message(embed=client.lang.command_config_remove_old_rank_on_rankup(interaction, toggle))

## Rank command


RankGroup = app_commands.Group(name="rank", description="A rank system to reward members who invited other members")

@RankGroup.command(name="add", description="Add a rank for rewarding members with invites")
@check_bot_has_permission(manage_roles=True)
@app_commands.check(check_has_permission)
@app_commands.describe(role='The role to get when getting the number of invites', invite_count='The number of invite to get the role')
async def rank_add_command(interaction: discord.Interaction, role: discord.Role, invite_count: int):
    if role.managed:
        await interaction.response.send_message(embed=client.lang.error_role_managed(interaction, role))
        return
    bot_role = interaction.guild.me.top_role
    if role.position > bot_role.position:
        await interaction.response.send_message(embed=client.lang.error_role_above_bot(interaction, role))
        return
    if role.is_default():
        await interaction.response.send_message(embed=client.lang.error_role_default(interaction))
        return
    client.db.set_rank(guild=interaction.guild.id, rank=role.id, count=invite_count)
    await interaction.response.send_message(embed=client.lang.command_rank_add(interaction, role, invite_count))

@RankGroup.command(name="remove", description="Remove a rank with the role")
@app_commands.check(check_has_permission)
@app_commands.describe(role='The role to remove from ranks')
async def rank_remove_command(interaction: discord.Interaction, role: discord.Role):
    if not client.db.get_rank_with_id(rank_id=role.id):
        await interaction.response.send_message(embed=client.lang.error_not_rank(interaction, role))
        return
    client.db.del_rank(rank=role.id)
    await interaction.response.send_message(embed=client.lang.command_rank_remove(interaction, role))

@RankGroup.command(name="list", description="List ranks of the server")
@app_commands.check(check_has_permission)
async def rank_list_command(interaction: discord.Interaction):
    ranks = client.db.get_ranks(guild=interaction.guild.id)
    if ranks:
        ranks = {interaction.guild.get_role(rank[1]).name: rank[2] for rank in ranks if interaction.guild.get_role(rank[1])}
    embeds_per_messages = client.lang.command_rank_list(interaction, ranks)
    message_num = 0
    for embeds in embeds_per_messages:
        if message_num == 0:
            await interaction.response.send_message(embeds=embeds)
        else:
            await interaction.followup.send(embeds=embeds)
        message_num += 1

client.tree.add_command(RankGroup)


## Info command


@client.tree.context_menu(name="Member info")
async def member_info_context(interaction: discord.Interaction, member: discord.Member):
    member_data = client.db.get_invites_data(guild=interaction.guild.id, member=member.id)
    await interaction.response.send_message(embed=client.lang.command_info(interaction, member, member_data), ephemeral=True)

@client.tree.command(name="info", description="Get the number of invite for the member")
@app_commands.describe(member='The member to see the invite number')
async def info_command(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    member_data = client.db.get_invites_data(guild=interaction.guild.id, member=member.id)
    await interaction.response.send_message(embed=client.lang.command_info(interaction, member, member_data))

@client.tree.command(name="bot_support", description="Get an invite to the bot support server")
async def bot_support_command(interaction: discord.Interaction):
    await interaction.response.send_message(embed=client.lang.command_bot_support(interaction))

@client.tree.command(name="help", description="Get informations about commands")
@app_commands.choices(category=[
    Choice(name='Config', value="config"),
])
async def help_command(interaction: discord.Interaction, category: Choice[str] = "globals"):
    if isinstance(category, Choice):
        category = category.value
    await interaction.response.send_message(embed=client.lang.command_help(interaction, category))

# Top command

@client.tree.command(name="top", description="Get the top 10 members with the most invites.")
async def top_command(interaction: discord.Interaction):
    top = client.db.get_top_invites(interaction.guild.id, 10)
    if top:
        top = {interaction.guild.get_member(member[0]): member[1] for member in top if interaction.guild.get_member(member[0])}
    else:
        top = {}
    await interaction.response.send_message(embed=client.lang.command_top(interaction, top))

# Bonus command


@client.tree.command(name="bonus", description="Add or remove bonus invites of a member")
@app_commands.check(check_has_permission)
@app_commands.describe(member='The member to see the invite number')
@app_commands.choices(action=[
    Choice(name='Add Bonus', value="add"),
    Choice(name='Remove Bonus', value="remove"),
    Choice(name='Set Bonus', value="set"),
])
async def bonus_command(interaction: discord.Interaction, action: Choice[str], member: discord.Member, number: int):
    if action.value == "set":
        bonus = number
    elif action.value == "add":
        bonus = client.db.get_bonus(guild=interaction.guild.id, member=member.id)
        bonus += number
    elif action.value == "remove":
        bonus = client.db.get_bonus(guild=interaction.guild.id, member=member.id)
        bonus -= number
    bonus = 0 if bonus < 0 else bonus
    client.db.set_bonus(guild=interaction.guild.id, member=member.id, bonus=bonus)
    await interaction.response.send_message(embed=client.lang.command_bonus(interaction, member, bonus))


def check_is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.id in config["admin_ids"]

ManageBotGroup = app_commands.Group(name="manage_bot", description="Manage the bot")

@ManageBotGroup.command(name="sync", description="Sync commands")
@app_commands.check(check_is_admin)
async def manage_bot_sync_command(interaction: discord.Interaction):
    commands = await client.tree.sync()
    await interaction.response.send_message(f"{len(commands)} commands synced :white_check_mark:")

@ManageBotGroup.command(name="eval", description="Eval code")
@app_commands.check(check_is_admin)
async def manage_bot_eval_command(interaction: discord.Interaction, code: str):
    try:
        embed = discord.Embed(
            title=f"__Eval__",
            description=f"```{eval(code)}```"
        )
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        tb = "".join(traceback.format_exception(e))
        if len(tb) > 4090:
            print(tb)
            sys.stdout.flush()
            await interaction.response.send_message("error printed to console")
        else:
            embed = discord.Embed(
                title=f"__Eval Error__",
                description=f"```{tb}```"
            )
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)

@ManageBotGroup.command(name="exec", description="Exec code")
@app_commands.check(check_is_admin)
async def manage_bot_exec_command(interaction: discord.Interaction, code: str):
    try:
        exec(
            f'async def __ex():' +
            ''.join(f'\n {l}' for l in code.split('\\n'))
        )
        print(f'async def __ex():' +
            ''.join(f'\n {l}' for l in code.split('\\n')))
        embed = discord.Embed(
            title=f"__Exec__",
            description=f"```{await locals()['__ex']()}```"
        )
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        tb = "".join(traceback.format_exception(e))
        if len(tb) > 4090:
            print(tb)
            sys.stdout.flush()
            await interaction.response.send_message("error printed to console")
        else:
            embed = discord.Embed(
                title=f"__Exec Error__",
                description=f"```{tb}```"
            )
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)

async def on_manage_bot_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message("Nuh uh") # Internal, shouldn't be seen by users as manage commands are hidden
        interaction.extras["internal"] = True

ManageBotGroup.on_error = on_manage_bot_command_error

client.tree.add_command(ManageBotGroup, guild=discord.Object(client.config["debug_guild"]))

##############################
#           Error            #
##############################

async def on_command_error(interaction: discord.Interaction, error):
    if "internal" in interaction.extras:
        return # if a user tries to use the super secret commands
    if isinstance(error, app_commands.errors.BotMissingPermissions) and "manage_roles" in error.missing_permissions:
        await interaction.response.send_message(embed=client.lang.error_bot_permission_manage_role(interaction))
    elif isinstance(error, app_commands.errors.BotMissingPermissions) and "manage_channels" in error.missing_permissions:
        await interaction.response.send_message(embed=client.lang.error_bot_permission_manage_channels(interaction))
    elif isinstance(error, app_commands.errors.BotMissingPermissions) and "view_channel" in error.missing_permissions:
        await interaction.response.send_message(embed=client.lang.error_bot_permission_view_channel(interaction))
    elif isinstance(error, app_commands.errors.BotMissingPermissions) and "connect" in error.missing_permissions:
        await interaction.response.send_message(embed=client.lang.error_bot_permission_connect(interaction))
    elif isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message(embed=client.lang.error_member_not_admin(interaction))
    else:
        if isinstance(error, app_commands.errors.CommandInvokeError):
            error = error.original
        if not interaction.is_expired:
            await interaction.response.send_message(embed=client.lang.error_unknown(interaction))
        errorchannel = client.get_channel(client.config["error_channel"])
        if errorchannel:
            tb = "".join(traceback.format_exception(error))
            if len(tb) > 4090:
                print(tb)
                sys.stdout.flush()
                await errorchannel.send("error printed to console")
            else:
                embed = discord.Embed(
                    title=f"__Command {interaction.command.qualified_name} Error__",
                    description=f"```{tb}```"
                )
                embed.timestamp = datetime.now()
                await errorchannel.send(embed=embed)

@client.event
async def on_error(event, *args, **kwargs):
    error = sys.exc_info()
    # if rate limit, wait the time
    if isinstance(args[0], discord.HTTPException) and args[0].status == 429:
        retry_after = args[0].headers.get("Retry-After")
        if retry_after:
            await asyncio.sleep(int(retry_after) + 1)  # Wait for the suggested time before retrying
        else:
            await asyncio.sleep(5)
    errorchannel = client.get_channel(client.config["error_channel"])
    if errorchannel:
        tb = "".join(traceback.format_exception(error[1]))
        if len(tb) > 4090:
            print(tb)
            sys.stdout.flush()
            await errorchannel.send("error printed to console")
        else:
            embed = discord.Embed(
                title=f"__Event {event} Error__",
                description=f"```{tb}```"
            )
            embed.timestamp = datetime.now()
            await errorchannel.send(embed=embed)
    else:
        print("No error channel")
        print(tb)

client.tree.on_error = on_command_error

##############################
#           Start            #
##############################

if __name__ == "__main__":
    client.run()
