<!-- vi: tw=119
-->

# Welcome to `db_tables` directory

This directory defines all of our database tables. To do so, we're using [`SQLAlchemy`](https://docs.sqlalchemy.org)
ORM. That means our database tables are defined as python classes, that follow certain special syntax to achieve this.

All of these tables must inherit from the `Base` class, that can be imported from `src.utils.database` module.

There is no need to register newly created classes / files anywhere, as all files in this directory (except those
starting with `_`) will be automatically imported and picked up by SQLAlchemy.
