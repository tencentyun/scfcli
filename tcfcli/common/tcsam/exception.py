from click import ClickException
import click


class TcSamException(ClickException):
    def format_message(self):
        return self.message

    def show(self):
        click.secho(click.style("[×]".decode("utf-8"), bg="red") + click.style(' %s' % self.format_message(), fg="red"))

    exit_code = 1
