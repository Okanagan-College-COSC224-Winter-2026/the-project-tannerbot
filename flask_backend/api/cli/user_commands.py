import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from ..models import User
from ..models.db import db


@click.command("change_password")
@click.argument("email")
@with_appcontext
def change_password_command(email):
    """Change the password for an existing user account.

    EMAIL is the email address of the account to update.

    Example:
        flask change_password user@example.com
    """
    user = User.get_by_email(email)
    if not user:
        click.echo(f"Error: No user found with email '{email}'", err=True)
        return

    click.echo(f"Changing password for {user.name} ({user.email}, role={user.role})")
    new_password = click.prompt("New password", hide_input=True, confirmation_prompt=True)

    user.hash_pass = generate_password_hash(new_password, method="pbkdf2:sha256")
    db.session.commit()
    click.echo("Password updated successfully.")


def init_app(app):
    """Register user management CLI commands with the Flask app."""
    app.cli.add_command(change_password_command)
