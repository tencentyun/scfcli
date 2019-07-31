import click


class Operation():
    def __init__(self, message):
        self.message = message

    def format_message(self):
        return self.message

    def success(self):
        try:
            click.secho(click.style(u"[√]", bg="green") + click.style(u' %s' % self.format_message().decode("utf-8"), fg="green"))
        except:
            click.secho(click.style(u"[√]", bg="green") + click.style(u' %s' % self.format_message(), fg="green"))

    def warning(self):
        try:
            click.secho(click.style(u"[!]", bg="magenta") + click.style(u' %s' % self.format_message().decode("utf-8"), fg="magenta"))
        except:
            click.secho(click.style(u"[!]", bg="magenta") + click.style(u' %s' % self.format_message(), fg="magenta"))

    def information(self):
        try:
            click.secho(click.style(u"[*]", bg="yellow") + click.style(u' %s' % self.format_message().decode("utf-8"), fg="yellow"))
        except:
            click.secho(click.style(u"[*]", bg="yellow") + click.style(u' %s' % self.format_message(), fg="yellow"))

    def process(self):
        try:
            click.secho(click.style(u"[>]", bg="cyan") + click.style(u' %s' % self.format_message().decode("utf-8"), fg="cyan"))
        except:
            click.secho(click.style(u"[>]", bg="cyan") + click.style(u' %s' % self.format_message(), fg="cyan"))