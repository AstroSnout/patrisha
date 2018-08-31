from discord.ext.commands import HelpFormatter, Paginator, Command
import itertools
import asyncio


class Helper(HelpFormatter):
    def __init__(self):
        super(Helper, self).__init__()
        self.category = ''

    def _add_subcommands_to_page(self, max_width, commands):
        for name, command in commands:
            if name in command.aliases:
                # skip aliases
                continue

            entry = '`!{0:<{width}}` - {1}'.format(name, command.short_doc, width=max_width)
            shortened = self.shorten(entry)
            self._paginator.add_line(shortened)

    @asyncio.coroutine
    def format(self):
        self._paginator = Paginator(prefix='', suffix='')
        # description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)

        # if description:
        #     self._paginator.add_line(description, empty=True)

        # If command subgroup
        if isinstance(self.command, Command):
            # <signature portion>
            line = '`'+self.get_command_signature()+'` - '

            # <long doc> section
            if self.command.help:
                line += '**'+self.command.help+'**'

            self._paginator.add_line(line, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.

            return '**'+cog + ':**' if cog is not None else '**\u200bNo Category:**'

        filtered = yield from self.filter_command_list()
        if self.is_bot():
            data = sorted(filtered, key=category)
            print(data)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = sorted(commands)

                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, commands)
                self._paginator.add_line()
        else:
            filtered = sorted(filtered)
            if filtered:
                self._paginator.add_line('__Commands within this sub-group:__', empty=True)
                self._add_subcommands_to_page(max_width, filtered)

        # add the ending note
        self._paginator.add_line()
        self._paginator.add_line('*Type* `!help <command name>` *for more info on a command.*')
        self._paginator.add_line('*You can also type* `!help <command category>` *for more info on a category.*')
        return self._paginator.pages
