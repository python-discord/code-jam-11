<!-- vi: tw=119
-->

# Welcome to `alembic-migrations` directory

This directory contains all of our database migrations.

## What are database migrations?

In case you aren't familiar, a database migration is essentially just a set of SQL instructions that should be
performed, to get your database into the state that we expect it to be in.

The thing is, as software changes, the requirements for the database structure change alongside with it and that means
that anyone who would like to update this application to a newer version will also need to find a way to get their
database up to date with any changes that were made.

If people had to do this manually, it would mean going through diffs and checking what exactly changed in the relevant
files, then using some tool where they can run SQL commands, figuring out what commands to even run to properly get
everything up to date without losing any existing information and finally actually running them.

Clearly, this isn't ideal, especially for people who just want to use this bot as it's being updated and don't know
much about SQL and databases. For that reason, we decided to instead keep the instructions for these migrations in
individual version files, which people can simply execute to get their database up to date (or even to downgrade it,
in case someone needs to test out an older version of the bot).

## How to use these migrations?

We're using [`alembic`](https://alembic.sqlalchemy.org/en/latest/index.html), which is a tool that makes generating and
applying migrations very easy. Additionally, we have some custom logic in place, to make sure that all migrations that
weren't yet applied will automatically be ran once the application is started, so you don't actually need to do
anything to apply them.

That said, if you would want to apply the migrations manually, without having to start the bot first, you can do so
with the command below:

```bash
alembic upgrade head
```

This will run all of the migrations one by one, from the last previously executed migrations (if you haven't run the
command before, it will simply run each one). Alembic will then keep track of the revision id (basically the specific
migration file) that was applied and store that id into your database (Alembic will create it's own database table for
this). That way, alembic will always know what version is your current database at.

> [!TIP]
> You can also run `alembic check`, to see if there are any pending migrations that you haven't yet applied.

## How to create migrations? (for developers)

If you're adding a new database table, deleting it, or just changing it somehow, you will want to create a new
migration file for it. Thankfully, alembic makes this very easy. All you need to do is run:

```bash
alembic revision --autogenerate -m "Some message (e.g.: Added users table)"
```

Alembic will actually load the python classes that represent all of the tables and compare that with what you currently
have in the database, automatically generating all of the instructions that need to be ran in a new migration script.
This script will be stored in `alembic-migrations/versions/` directory.

Note that after you did this, you will want to apply the migrations. You can do that by simply running the bot for a
while, to let the custom logic we have in place run alembic migrations for you, or you can run them manually with
`alembic upgrade head`.

### Manual migrations

In most cases, running the command to auto-generate the migration will be all that you need to do.

That said, alembic has it's limitations and in some cases, the automatic generation doesn't work, or doesn't do what
we'd like it to do. For example, if you rename a table, alembic can't understand that this was a rename, rather than a
deletion of one table and a creation of another. This is a problem, because instead of simply renaming while keeping
the old existing data, alembic will generate instructions that would lead to losing those old data.

In these cases, you will need to do some extra work and edit the migration files yourself. In case auto-generation
fails completely, you can run the same command without that `--autogenerate` flag, which will generate an empty
migration file, that you'll need to fill out.

That said, in vast majority of cases, you will not need to write your migrations manually. For more info on when you
might need to, check [the documentation][alembic-autogeneration-autodetection].

[alembic-autogeneration-autodetection]: https://guide.pycord.dev/getting-started/creating-your-first-bot#creating-the-bot-application

### Stamping

In case you've made modifications to your database already (perhaps by manually running some SQL commands to test out a
manually written migration), you might want to skip applying a migration and instead just tell Alembic that the
database is already up to date with the latest revision.

Thankfully, alembic makes this really simple, all you need to do is run:

```bash
alembic stamp head
```
