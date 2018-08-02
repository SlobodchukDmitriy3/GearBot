import asyncio
from datetime import datetime

import discord
from discord.ext import commands

from Util import Permissioncheckers, Configuration, Confirmation, Emoji, Translator
from database.DatabaseConnector import CustomCommand


class CustCommands:
    critical = False
    cog_perm = 0

    def __init__(self, bot):
        self.bot:commands.Bot = bot
        self.commands = dict()
        self.bot.loop.create_task(self.reloadCommands())

    async def __local_check(self, ctx):
        return Permissioncheckers.check_permission(ctx, True)


    async def reloadCommands(self):
        while not self.bot.STARTUP_COMPLETE:
            await asyncio.sleep(1)
        for guild in self.bot.guilds:
            self.commands[guild.id] = dict()
            for command in CustomCommand.select().where(CustomCommand.serverid == guild.id):
                self.commands[guild.id][command.trigger] = command.response

    async def on_guild_join(self, guild):
        self.commands[guild.id] = dict()

    async def on_guild_remove(self, guild):
        del self.commands[guild.id]
        for command in CustomCommand.select().where(CustomCommand.serverid == guild.id):
            command.delete_instance()

    @commands.group(name="commands", aliases=['command'])
    @commands.guild_only()
    async def command(self, ctx:commands.Context):
        """Lists all custom commands for this server, also the base command to making, updating and removing them"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(timestamp=datetime.now(), color=0x663399, title=Translator.translate("custom_command_list", ctx.guild.id, server_name=ctx.guild.name))
            value = ""
            if len(self.commands[ctx.guild.id].keys()) > 0:
                for trigger in self.commands[ctx.guild.id].keys():
                    if len(value) + len(trigger) > 1000:
                        embed.add_field(name="\u200b", value=value)
                        value = ""
                    value = f"{value}{trigger}\n"
                embed.add_field(name="\u200b", value=value)
                await ctx.send(embed=embed)
            else:
                await ctx.send(Translator.translate("custom_command_no_commands", ctx.guild.id))

    @command.command(aliases=["new", "add"])
    @commands.guild_only()
    @Permissioncheckers.mod_only()
    async def create(self, ctx:commands.Context, trigger:str, *, reply:str = None):
        """Create a new command"""
        if len(trigger) == 0:
            await ctx.send(f"{Emoji.get_chat_emoji('WHAT')} {Translator.translate('custom_command_empty_trigger', ctx.guild.id)}")
        elif reply is None or reply == "":
            await ctx.send(f"{Emoji.get_chat_emoji('WHAT')} {Translator.translate('custom_command_empty_reply')}")
        else:
            trigger = trigger.lower()
            command = CustomCommand.get_or_none(serverid = ctx.guild.id, trigger=trigger)
            if command is None:
                CustomCommand.create(serverid = ctx.guild.id, trigger=trigger, response=reply)
                self.commands[ctx.guild.id][trigger] = reply
                await ctx.send(f"{Emoji.get_chat_emoji('YES')} {Translator.translate('custom_command_added', ctx.guild.id, trigger=trigger)}")
            else:
                async def yes():
                    await ctx.send(Translator.translate('updating', ctx.guild.id))
                    await ctx.invoke(self.update, trigger, reply=reply)
                async def no():
                    await ctx.send(Translator.translate('custom_command_not_updating', ctx.guild.id))
                await Confirmation.confirm(ctx, Translator.translate('custom_command_override_confirmation', ctx.guild.id), on_yes=yes , on_no=no)

    @command.command()
    @commands.guild_only()
    @Permissioncheckers.mod_only()
    async def remove(self, ctx:commands.Context, trigger:str):
        """Removes a custom command"""
        trigger = trigger.lower()
        if trigger in self.commands[ctx.guild.id]:
            CustomCommand.get(serverid = ctx.guild.id, trigger=trigger).delete_instance()
            del self.commands[ctx.guild.id][trigger]
            await ctx.send(f"{Emoji.get_chat_emoji('YES')} {Translator.translate('custom_command_removed', ctx.guild.id, trigger=trigger)}")
        else:
            await ctx.send(f"{Emoji.get_chat_emoji('NO')} {Translator.translate('custom_command_not_found', ctx.guild.id, trigger=trigger)}")

    @command.command()
    @commands.guild_only()
    @Permissioncheckers.mod_only()
    async def update (self, ctx:commands.Context, trigger:str, *, reply:str = None):
        """Sets a new reply for the specified command"""
        trigger = trigger.lower()
        if reply is None:
            ctx.send(f"{Emoji.get_chat_emoji('NO')} Please provide a response as well")
        else:
            command = CustomCommand.get_or_none(serverid = ctx.guild.id, trigger=trigger)
            if command is None:
                await ctx.send(f":warning: This command does not exist, making it for you instead")
                await ctx.invoke(self.create, trigger, response=reply)
            else:
                command.response = reply
                command.save()
                self.commands[ctx.guild.id][trigger] = reply
                await ctx.send(f"{Emoji.get_chat_emoji('YES')} Command `{trigger}` has been updated")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not hasattr(message.channel, "guild") or message.channel.guild is None:
            return
        prefix = Configuration.getConfigVar(message.guild.id, "PREFIX")
        if message.content.startswith(prefix, 0):
            for trigger in self.commands[message.guild.id]:
                if message.content.lower() == prefix+trigger or (message.content.lower().startswith(trigger, len(prefix)) and message.content.lower()[len(prefix+trigger)] == " "):
                    await message.channel.send(self.commands[message.guild.id][trigger])
                    self.bot.commandCount = self.bot.commandCount + 1





def setup(bot):
    bot.add_cog(CustCommands(bot))