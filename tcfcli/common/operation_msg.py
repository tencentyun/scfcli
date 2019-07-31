import click


class Operation():
    def __init__(self, message):
        self.message = message

    def format_message(self):
        return self.message

    def success(self):
        click.secho(click.style(u"[O]", bg="green") + click.style(u' %s' % self.format_message(), fg="green"))

    def warning(self):
        click.secho(click.style(u"[!]", bg="magenta") + click.style(u' %s' % self.format_message(), fg="magenta"))

    def information(self):
        click.secho(click.style(u"[*]", bg="yellow") + click.style(u' %s' % self.format_message(), fg="yellow"))

    def process(self):
        click.secho(click.style(u"[>]", bg="cyan") + click.style(u' %s' % self.format_message(), fg="cyan"))
