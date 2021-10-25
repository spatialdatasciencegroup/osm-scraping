import click
from lib import geoscraping as geo

@click.group()
def query():
  pass


@query.command(name='building')
@click.argument('bounds')
@click.argument('key')
@click.argument('value')
def buildingquery(bounds, key, value):
    result = geo.buildingquery(bounds, key, value)
    frame = geo.querytoframe(result)
    click.echo(frame)


@query.command(name='road')
@click.argument('bounds')
@click.argument('key')
@click.argument('value')
def roadquery(bounds, key, value):
    result = geo.roadquery(bounds, key, value)
    click.echo(result)

query.add_command(buildingquery)
query.add_command(roadquery)

if __name__ == '__main__':
    query()