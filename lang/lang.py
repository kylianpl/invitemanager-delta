import os
import json
from datetime import datetime

from discord import Embed
from discord import Role
from discord import Member
from discord import TextChannel
from discord import Interaction
# reload lang function

class LangHelper:
    def __init__(self):
        self.embed_color = 0x5662f6
        self.embed_error_color = 0xFF3030
        self.lang_data = {}
        self.langs = {}

        self.load_jsons()

    def load_jsons(self):
        """
        (re)load all jsons from ./lang
        """
        self.lang_data = {}
        for langpath in os.listdir("./lang"):
            if not langpath.endswith(".json"):
                continue
            with open(os.path.join("./lang", langpath)) as langfile:
                langjson = json.load(langfile)
            langname = langjson.get("locale_name")
            if langname:
                self.lang_data[langname] = langjson
                for l in langjson.get("discord_locale_names"):
                    self.langs[l] = langname

    def get_lang(self, interaction: Interaction) -> str:
        return interaction.client.db.get_config(guild=interaction.guild.id, key="Lang").lower()

    def get_output_value(self, interaction: Interaction, key: str, fallback=False) -> str:
        if not fallback:
            lang = self.get_lang(interaction)
        else:
            lang = "en"
        return (self.lang_data[lang]["output"].get(key) if lang in self.lang_data else self.get_output_value(interaction, key, True)) or self.get_output_value(interaction, key, True)

    def get_help_cmds(self, interaction: Interaction, category: str, fallback=False) -> str:
        if not fallback:
            lang = self.get_lang(interaction)
        else:
            lang = "en"
        return (self.lang_data[lang]["commands"].get(category) if lang in self.lang_data else self.get_help_cmds(interaction, category, True)) or self.get_help_cmds(interaction, category, True)

    def get_error(self, interaction: Interaction, key: str, fallback=False) -> str:
        if not fallback:
            lang = self.get_lang(interaction)
        else:
            lang = "en"
        return (self.lang_data[lang]["errors"].get(key) if lang in self.lang_data else self.get_output_value(interaction, key, True)) or self.get_output_value(interaction, key, True)

    ######################
    #  command functions #
    ######################

    def command_config_goal_set(self, interaction: Interaction, goals: list) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goal_title")
        )
        embed.timestamp = datetime.now()
        goals = [str(g) for g in goals]
        goals.sort()
        embed.add_field(
            name=self.get_output_value(interaction, "config_goal_set_field_name"),
            value="`" + "`; `".join(goals) + "`"
        )
        return embed

    def command_config_goal_list(self, interaction: Interaction, goals: list) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goal_title")
        )
        embed.timestamp = datetime.now()
        goals = [str(g) for g in goals]
        goals.sort()
        embed.add_field(
            name=self.get_output_value(interaction, "config_goal_list_field_name"),
            value="`" + "`; `".join(goals) + "`"
        )
        return embed

    def command_config_goal_list_no_goals(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goal_title"),
            description=self.get_output_value(interaction, "config_goal_list_no_goals_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_goal_rename(self, interaction: Interaction, name: str) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goal_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_goal_rename_field_name"),
            value=name
        )
        return embed

    def command_config_goal_create(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goal_title"),
            description=self.get_output_value(interaction, "config_goal_create_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_goal_delete(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goal_title"),
            description=self.get_output_value(interaction, "config_goal_delete_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_member_counter_rename(self, interaction: Interaction, name: str) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_member_counter_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_member_counter_rename_field_name"),
            value=name
        )
        return embed

    def command_config_member_counter_create(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_member_counter_title"),
            description=self.get_output_value(interaction, "config_member_counter_create_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_member_counter_delete(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_member_counter_title"),
            description=self.get_output_value(interaction, "config_member_counter_delete_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_bot_counter_rename(self, interaction: Interaction, name: str) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_bot_counter_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_bot_counter_rename_field_name"),
            value=name
        )
        return embed

    def command_config_bot_counter_create(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_bot_counter_title"),
            description=self.get_output_value(interaction, "config_member_counter_create_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_bot_counter_delete(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_bot_counter_title"),
            description=self.get_output_value(interaction, "config_bot_counter_delete_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_welcome_channel(self, interaction: Interaction, channel: TextChannel) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_welcome_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_welcome_channel_field_name"),
            value=channel.mention
        )
        return embed

    def command_config_welcome_message(self, interaction: Interaction, message: str) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_welcome_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_welcome_message_field_name"),
            value=message
        )
        return embed

    def command_config_welcome_embed(self, interaction: Interaction, status: bool) -> Embed:
        if status:
            desc = self.get_output_value(interaction, "config_welcome_embed_description_yes")
        else:
            desc = self.get_output_value(interaction, "config_welcome_embed_description_no")
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_welcome_title"),
            description=desc
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_welcome_toggle(self, interaction: Interaction, status: bool) -> Embed:
        if status:
            desc = self.get_output_value(interaction, "config_welcome_toggle_description_yes")
        else:
            desc = self.get_output_value(interaction, "config_welcome_toggle_description_no")
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_welcome_title"),
            description=desc
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_goodbye_channel(self, interaction: Interaction, channel: TextChannel) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goodbye_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_goodbye_channel_field_name"),
            value=channel.mention
        )
        return embed

    def command_config_goodbye_message(self, interaction: Interaction, message: str) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goodbye_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_goodbye_message_field_name"),
            value=message
        )
        return embed

    def command_config_goodbye_embed(self, interaction: Interaction, status: bool) -> Embed:
        if status:
            desc = self.get_output_value(interaction, "config_goodbye_embed_description_yes")
        else:
            desc = self.get_output_value(interaction, "config_goodbye_embed_description_no")
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goodbye_title"),
            description=desc
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_goodbye_toggle(self, interaction: Interaction, status: bool) -> Embed:
        if status:
            desc = self.get_output_value(interaction, "config_goodbye_toggle_description_yes")
        else:
            desc = self.get_output_value(interaction, "config_goodbye_toggle_description_no")
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_goodbye_title"),
            description=desc
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_language(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_language_title"),
            description=self.get_output_value(interaction, "config_language_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_config_autorole(self, interaction: Interaction, role: Role) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_autorole_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_autorole_field_name"),
            value=role.mention
        )
        return embed

    def command_config_adminrole(self, interaction: Interaction, role: Role) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_adminrole_title")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_adminrole_field_name"),
            value=role.mention
        )
        return embed

    def command_config_view(self, interaction: Interaction, variables) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_view_title"),
            description=self.get_output_value(interaction, "config_view_description")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_lang"),
            value=self.get_output_value(interaction, "config_view_lang_value"),
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_admin_role"),
            value=f"<@&{variables[11]}>" if variables[11] else self.get_output_value(interaction, "config_view_no_admin_role"),
            inline=True
        )

        embed.add_field(
            name=self.get_output_value(interaction, "config_view_auto_role"),
            value=f"<@&{variables[12]}>" if variables[12] else self.get_output_value(interaction, "config_view_no_value"),
            inline=True
        )

        embed.add_field(
            name=self.get_output_value(interaction, "config_view_remove_old_rank_on_rankup"),
            value=self.get_output_value(interaction, "config_view_yes") if variables[19] else self.get_output_value(interaction, "config_view_no"),
            inline=True
        )



        embed.add_field(
            name=self.get_output_value(interaction, "config_view_welcome_channel"),
            value=f"<#{variables[3]}>" if variables[3] else self.get_output_value(interaction, "config_view_no_value"),
            inline=False
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_welcome"),
            value=self.get_output_value(interaction, "config_view_yes") if variables[2] else self.get_output_value(interaction, "config_view_no"),
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_welcome_embed"),
            value=self.get_output_value(interaction, "config_view_yes") if variables[5] else self.get_output_value(interaction, "config_view_no"),
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_welcome_message"),
            value=variables[4],
            inline=True
        )



        embed.add_field(
            name=self.get_output_value(interaction, "config_view_goodbye_channel"),
            value=f"<#{variables[16]}>" if variables[16] else self.get_output_value(interaction, "config_view_no_value"),
            inline=False
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_goodbye"),
            value=self.get_output_value(interaction, "config_view_yes") if variables[15] else self.get_output_value(interaction, "config_view_no"),
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_goodbye_embed"),
            value=self.get_output_value(interaction, "config_view_yes") if variables[18] else self.get_output_value(interaction, "config_view_no"),
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_goodbye_message"),
            value=variables[17],
            inline=True
        )



        embed.add_field(
            name=self.get_output_value(interaction, "config_view_member_channel"),
            value=f"<#{variables[9]}>" if variables[9] else self.get_output_value(interaction, "config_view_no_value"),
            inline=False
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_member_channel_name"),
            value=variables[10],
            inline=True
        )



        embed.add_field(
            name=self.get_output_value(interaction, "config_view_bot_channel"),
            value=f"<#{variables[7]}>" if variables[7] else self.get_output_value(interaction, "config_view_no_value"),
            inline=False
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_bot_channel_name"),
            value=variables[8],
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_goal_channel"),
            value=f"<#{variables[14]}>" if variables[14] else self.get_output_value(interaction, "config_view_no_value"),
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "config_view_goal_channel_name"),
            value=variables[13],
            inline=True
        )
        return embed

    def command_config_remove_old_rank_on_rankup(self, interaction: Interaction, status: bool) -> Embed:
        if status:
            desc = self.get_output_value(interaction, "config_remove_old_rank_on_rankup_description_yes")
        else:
            desc = self.get_output_value(interaction, "config_remove_old_rank_on_rankup_description_no")
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "config_remove_old_rank_on_rankup_title"),
            description=desc
        )
        embed.timestamp = datetime.now()
        return embed

    def command_rank_add(self, interaction: Interaction, role: Role, number: int) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "rank_add_title"),
            description=self.get_output_value(interaction, "rank_add_description").format(role=role.mention, number=number)
        )
        embed.timestamp = datetime.now()
        return embed

    def command_rank_remove(self, interaction: Interaction, role: Role) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "rank_remove_title"),
            description=self.get_output_value(interaction, "rank_remove_description").format(role=role.mention)
        )
        embed.timestamp = datetime.now()
        return embed

    def command_rank_list(self, interaction: Interaction, ranks: list) -> list[Embed]:
        if not ranks:
            return [[Embed(
                color=self.embed_color,
                title=self.get_output_value(interaction, "rank_list_title"),
                description=self.get_output_value(interaction, "rank_list_no_rank_description")
            )]]
        ranks = list(ranks.items())
        ranks_by_embeds = [ranks[i:i+25] for i in range(0, len(ranks), 25)]
        embeds = []
        for r in ranks_by_embeds:
            embed = Embed(
                color=self.embed_color,
                title=self.get_output_value(interaction, "rank_list_title")
            )
            embed.timestamp = datetime.now()
            for rank, num in r:
                embed.add_field(
                    name=rank,
                    value=self.get_output_value(interaction, "rank_list_field_value").format(number=str(num))
                )
            embeds.append(embed)
        embeds_per_messages = [embeds[i:i+10] for i in range(0, len(embeds), 10)]
        return embeds_per_messages

    def command_info(self, interaction: Interaction, member: Member, member_data: list) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "info_title").format(member=f"{member}")
        )
        embed.timestamp = datetime.now()
        embed.add_field(
            name=self.get_output_value(interaction, "info_invite"),
            value=member_data[0],
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "info_leave"),
            value=member_data[1],
            inline=True
        )
        embed.add_field(
            name=self.get_output_value(interaction, "info_bonus"),
            value=member_data[2],
            inline=True
        )
        return embed

    def command_top(self, interaction: Interaction, top: dict) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "top_title")
        )
        embed.timestamp = datetime.now()
        if not top:
            embed.description = self.get_output_value(interaction, "top_no_data_description")
            return embed
        for i, (member, number) in enumerate(top.items()):
            embed.add_field(
                name=f"{i+1}. {member}",
                value=self.get_output_value(interaction, "top_field_value").format(number=number)
            )
        return embed

    def command_bonus(self, interaction: Interaction, member: Member, number: int) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "bonus_title"),
            description=self.get_output_value(interaction, "bonus_description").format(member=member.mention, number=number)
        )
        embed.timestamp = datetime.now()
        return embed

    def command_bot_support(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "bot_support_title"),
            description=self.get_output_value(interaction, "bot_support_description")
        )
        embed.timestamp = datetime.now()
        return embed

    def command_help(self, interaction: Interaction, category: str) -> Embed:
        embed = Embed(
            color=self.embed_color,
            title=self.get_output_value(interaction, "help_title"),
            description=self.get_output_value(interaction, "help_description")
        )
        cmds = self.get_help_cmds(interaction, category)
        for cmd in cmds.values():
            embed.add_field(
                name=cmd["command"],
                value=cmd["description_long"],
                inline=False
            )
        embed.timestamp = datetime.now()
        return embed


    ######################
    #  error functions   #
    ######################

    def error_unknown(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "unknown")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_bot_permission_manage_role(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "bot_permission_manage_role")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_bot_permission_manage_channels(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "bot_permission_manage_channels")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_bot_permission_view_channel(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "bot_permission_view_channel")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_bot_permission_connect(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "bot_permission_connect")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_bot_permission_send_messages(self, interaction: Interaction, channel: TextChannel) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "bot_permission_send_messages").format(channel=channel.mention)
        )
        embed.timestamp = datetime.now()
        return embed

    def error_role_default(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "role_default")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_role_managed(self, interaction: Interaction, role: Role) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "role_managed").format(role=role.mention)
        )
        embed.timestamp = datetime.now()
        return embed

    def error_role_above_bot(self, interaction: Interaction, role: Role) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "role_above_bot").format(role=role.mention)
        )
        embed.timestamp = datetime.now()
        return embed

    def error_member_not_admin(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "member_not_admin")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_no_goal_list(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "no_goal_list")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_no_goal_channel(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "no_goal_channel")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_no_member_channel(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "no_member_channel")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_no_bot_channel(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "no_bot_channel")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_not_rank(self, interaction: Interaction, role: Role) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "not_rank").format(role=role.mention)
        )
        embed.timestamp = datetime.now()
        return embed

    def error_channel_name_too_long(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "channel_name_too_long")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_welcome_message_too_long(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "welcome_message_too_long")
        )
        embed.timestamp = datetime.now()
        return embed

    def error_goodbye_message_too_long(self, interaction: Interaction) -> Embed:
        embed = Embed(
            color=self.embed_error_color,
            title=self.get_error(interaction, "title"),
            description=self.get_error(interaction, "welcome_goodbye_too_long")
        )
        embed.timestamp = datetime.now()
        return embed
