import os
from argparse import ArgumentParser

from Bot import TheRealGearBot
from Bot.GearBot import GearBot
from Util import Configuration, GearbotLogging
from discord import Intents, MemberCacheFlags

def prefix_callable(bot, message):
    return TheRealGearBot.prefix_callable(bot, message)

gearbot = GearBot(command_prefix=prefix_callable, case_insensitive=True, max_messages = 100) #100 is the min for some reason




if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--token", help="Specify your Discord token")

    GearbotLogging.init_logger()

    clargs = parser.parse_args()
    GearbotLogging.init_logger(int(clargs.offset) if clargs.offset else 0)
    if 'gearbotlogin' in os.environ:
        token = os.environ['gearbotlogin']
    elif clargs.token:
        token = clargs.token
    elif not Configuration.get_master_var("LOGIN_TOKEN", "0") is "0":
        token = Configuration.get_master_var("LOGIN_TOKEN")
    else:
        token = input("Please enter your Discord token: ")

    args = {
        "command_prefix": prefix_callable,
        "case_insensitive": True,
        "max_messages": None,
        "intents": Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            integrations=False,
            webhooks=False,
            invites=False,
            voice_states=True,
            presences=False,
            messages=True,
            reactions=True,
            typing=False,
        ),
        "member_cache_flags": MemberCacheFlags(
            online=False,
            voice=True,
            joined=True,
        )
    }
    if clargs.total_shards:
        total_shards = int(clargs.total_shards)
        offset = int(clargs.offset)
        num_shards = int(clargs.num_shards)
        args.update({
            "shard_count": total_shards,
            "cluster": offset,
            "shard_ids": [*range(offset * num_shards, (offset * num_shards) + num_shards)]
        })

    gearbot = GearBot(**args)

    gearbot.remove_command("help")
    GearbotLogging.info("Ready to go, spinning up the gears")
    gearbot.run(token)
    GearbotLogging.info("GearBot shutting down, cleaning up")
    gearbot.database_connection.close()
    GearbotLogging.info("Cleanup complete")

