import collections

from discord.ext.commands import CommandError, Context, GroupMixin

from Util import Utils


async def command_list(bot, ctx:Context):
    command_tree = dict()
    longest = 0
    for cog in bot.cogs:
        commands, l = await cog_commands(bot, ctx, cog)
        if commands is not None:
            command_tree[cog] = commands
            if l > longest:
                longest = l
    command_tree = collections.OrderedDict(sorted(command_tree.items()))


    output_tree = collections.OrderedDict()
    for cog, commands in command_tree.items():
        output = f'- {cog}\n'
        for command_name, info in commands.items():
            output += "  " + command_name + (" " * (longest - len(command_name) + 2)) + info + "\n"
        output_tree[cog] = output
    return dict_to_pages(output_tree, f"You can get more info about a command (params and subcommands) by using '{ctx.prefix}help <command>'\nCommands followed by ↪  have subcommands".replace(ctx.me.mention, f"@{ctx.me.name}"))


async def cog_commands(bot, ctx, cog):
    longest = 0
    commands = bot.get_cog_commands(cog)
    if len(commands) == 0:
        return None, None
    command_list = dict()
    for command in commands:
        try:
            runnable = await command.can_run(ctx)
        except CommandError:
            # not sure if needed, lib does it prob best to catch it just in case
            runnable = False
        except Exception as ex:
            if ctx is None:
                # we don't always have a valid context, in this case assume all context dependant commands as not available
                runnable = False
            else:
                # we have a context so error is not due to it being missing, raise it up
                raise ex
        if not command.hidden and runnable:
            indicator = "\n  ↪" if isinstance(command, GroupMixin) else ""
            command_list[command.name] = Utils.trim_message(command.short_doc, 120) + indicator
            if len(command.name) > longest:
                longest = len(command.name)
    if len(command_list) > 0:
        return collections.OrderedDict(sorted(command_list.items())), longest
    else:
        return None, None

async def gen_cog_help(bot, ctx, cog):
    commands, longest = await cog_commands(bot, ctx, cog)
    output = f'- {cog}\n'
    for command_name, info in commands.items():
        output += command_name + (" " * (longest - len(command_name) + 4)) + info + "\n"
    return [output]

def dict_to_pages(dict, suffix=""):
    pages = []
    output = ""
    for out in dict.values():
        if len(output) + len(out) > 1000:
            pages.append(f"{output}\n{suffix}")
            output = out
        else:
            if output == "":
                output = Utils.trim_message(out, 2000 - 15 - len(suffix))
            else:
                output += out + "\n"
    pages.append(f"{output}\n{suffix}")
    return pages