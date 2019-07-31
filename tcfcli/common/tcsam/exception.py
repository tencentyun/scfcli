from click import ClickException
import click
import platform


class TcSamException(ClickException):
    def format_message(self):
        return self.message

    def show(self):
        version = platform.python_version()
        if version >= '3':
            click.secho(click.style(u"[×]", bg="red") + click.style(u' %s' % self.format_message(), fg="red"))
        else:
            click.secho(click.style(u"[x]", bg="red") + click.style(u' %s' % self.format_message().decode("utf-8"),
                                                                    fg="red"))


exit_code = 1
