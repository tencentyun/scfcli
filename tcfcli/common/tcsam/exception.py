from click import ClickException
import click


class TcSamException(ClickException):
    def format_message(self):
        return self.message

    def show(self):
        try:
            click.secho(
                click.style("[x]", bg="red") + click.style(u' %s' % self.format_message().decode("utf-8"), fg="red"))
        except:
            click.secho(
                click.style("u[×]", bg="red") + click.style(u' %s' % self.format_message(), fg="red"))
        click.secho(click.style("[×]".decode("utf-8"), bg="red") + click.style(' %s' % self.format_message(), fg="red"))

    exit_code = 1
