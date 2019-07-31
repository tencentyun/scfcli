import click
import platform

version = platform.python_version()


class Operation():
    def __init__(self, message):
        self.message = message

    def format_message(self):
        return self.message

    def success(self):
        if version >= '3':
            click.secho(click.style(u"[√]", bg="green") + click.style(u' %s' % self.format_message(), fg="green"))
        else:
            click.secho(click.style(u"[v]", bg="green") + click.style(u' %s' % self.format_message().decode("utf-8"),
                                                                      fg="green"))

    def warning(self):
        if version >= '3':
            click.secho(click.style(u"[!]", bg="magenta") + click.style(u' %s' % self.format_message(), fg="magenta"))
        else:
            click.secho(click.style(u"[!]", bg="magenta") + click.style(u' %s' % self.format_message().decode("utf-8"),
                                                                        fg="magenta"))

    def information(self):
        if version >= '3':
            click.secho(click.style(u"[*]", bg="yellow") + click.style(u' %s' % self.format_message(), fg="yellow"))
        else:
            click.secho(click.style(u"[*]", bg="yellow") + click.style(u' %s' % self.format_message().decode("utf-8"),
                                                                       fg="yellow"))

    def process(self):
        if version >= '3':
            click.secho(click.style(u"[>]", bg="cyan") + click.style(u' %s' % self.format_message(), fg="cyan"))
        else:
            click.secho(
                click.style(u"[>]", bg="cyan") + click.style(u' %s' % self.format_message().decode("utf-8"), fg="cyan"))
