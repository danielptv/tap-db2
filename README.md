<h1 align="center">Tap-DB2 👑</h1>

<p align="center">
<a href="https://github.com/danielptv/tap-db2/actions/"><img alt="Actions Status" src="https://github.com/danielptv/tap-db2/actions/workflows/test.yml/badge.svg"></a>
<a href="https://github.com/danielptv/tap-db2/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<img alt="PyPI - Version" src="https://img.shields.io/pypi/v/tap-ibm-db2">
<img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/tap-ibm-db2">
</p>

`Tap-DB2` is a Singer tap for IBM DB2 data sources. Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Installation ⚙️

Install from PyPi:

```bash
pipx install tap-ibm-db2
```

Install from GitHub:

```bash
pipx install git+https://github.com/danielptv/tap-db2.git@main
```

## Configuration 📝

| Setting                      | Required | Default   | Description                                                                                                                                                     |
| :--------------------------- | :------: | --------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| host                         |   True   | localhost | The DB2 hostname.                                                                                                                                               |
| port                         |   True   | 50000     | The DB2 port.                                                                                                                                                   |
| database                     |   True   | None      | The DB2 database.                                                                                                                                               |
| schema                       |  False   | None      | The DB2 schema.                                                                                                                                                 |
| user                         |   True   | None      | The DB2 username.                                                                                                                                               |
| password                     |   True   | None      | The DB2 password.                                                                                                                                               |
| encryption                   |   True   | None      | Encryption settings for the DB2 connection. Disabled if omitted.                                                                                                |
| connection_parameters        |  False   | None      | Additional parameters to be appended to the connection string. This is an objects containing key-value pairs.                                                   |
| sqlalchemy_execution_options |  False   | None      | Additional execution options to be passed to SQLAlchemy. This is an objects containing key-value pairs.                                                         |
| query_partitioning           |  False   | None      | Partition query into smaller subsets.                                                                                                                           |
| filter                       |  False   | None      | Apply a custom WHERE condition per stream. Unlike the filter available in stream_maps, this will be evaluated BEFORE extracting the data.                       |
| ignore_supplied_tables       |  False   | True      | Ignore DB2-supplied user tables. For more info check out [Db2-supplied user tables](https://www.ibm.com/docs/en/db2-for-zos/12?topic=db2-supplied-user-tables). |
| ignore_views                 |  False   | False     | Ignore views.                                                                                                                                                   |
| stream_maps                  |  False   | None      | Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html).                     |
| stream_map_config            |  False   | None      | User-defined config values to be used within map expressions.                                                                                                   |

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-db2 --about --format json
```

### Configure using environment variables ✏️

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Configure encryption settings 🔒

This Singer tap supports encrypted connection settings to DB2 according to the [python-ibmdb driver](https://github.com/ibmdb/python-ibmdb#example-of-ssl-connection-string).

**SSL without additional options:**

```yaml
...
plugins:
  extractors:
  - name: tap-db2
    variant: danielptv
    pip_url: tap-ibm-db2
    config:
      ...
      encryption: {}
```

This will append `SECURITY=SSL;` to the connection string.

**SSL using SSLServerCertificate keyword:**

```yaml
...
plugins:
  extractors:
  - name: tap-db2
    variant: danielptv
    pip_url: tap-ibm-db2
    config:
      ...
      encryption:
        ssl_server_certificate: <Full path to the server certificate>
```

This will append `SECURITY=SSL;SSLServerCertificate=<Full path to the server certificate>;` to the connection string.

**SSL using SSLClientKeyStoreDB and SSLClientKeyStoreDBPassword keywords:**

```yaml
...
plugins:
  extractors:
  - name: tap-db2
    variant: danielptv
    pip_url: tap-ibm-db2
    config:
      ...
      encryption:
        ssl_client_key_store_db:
          database: <Full path to the client keystore database>
          password: <Keystore password>
```

This will append `SECURITY=SSL;SSLClientKeyStoreDB=<Full path to the client keystore database>;SSLClientKeyStoreDBPassword=<Keystore password>;` to the connection string.

**SSL using SSLClientKeyStoreDB and SSLClientKeyStash keywords:**

```yaml
...
plugins:
  extractors:
  - name: tap-db2
    variant: danielptv
    pip_url: tap-ibm-db2
    config:
      ...
      encryption:
        ssl_client_key_store_db:
          database: <Full path to the client keystore database>
          key_stash: <Full path to the client keystore stash>
```

This will append `SECURITY=SSL;SSLClientKeyStoreDB=<Full path to the client keystore database>;SSLClientKeyStash=<Full path to the client keystore stash>;` to the connection string.

### Configure query partitioning 🧩

This Singer tap supports the partitioning of SQL queries into smaller sub-queries to reduce the CPU load on the database. This is particularly useful when working with large amounts of data and a DB2 that has set strict resource limits per query. ***Note: This only works for streams with a numeric primary key.***

The configuration for query partitioning should look as follows:

```yaml
...
plugins:
  extractors:
  - name: tap-db2
    variant: danielptv
    pip_url: tap-ibm-db2
    config:
      ...
      query_partitioning:
      <stream>:
        primary_key: <primary key>
        partition_size: 1000
```

Replace `<stream>` with the stream name and `<primary key>` with the stream's primary key. Use `*` to apply a query partitioning setting to all streams not explicitly declared.

## Usage 👷‍♀️

You can easily run `tap-db2` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly 🔨

```bash
tap-db2 --version
tap-db2 --help
tap-db2 --config CONFIG --discover > ./catalog.json
```

## Developer Resources 👩🏼‍💻

Follow these instructions to contribute to this project.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests 🧪

Create tests within the `tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-db2` CLI interface directly using `poetry run`:

```bash
poetry run tap-db2 --help
```

### Testing with [Meltano](https://www.meltano.com)

***Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios.*

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-db2
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-db2 --version
# OR run a test `elt` pipeline:
meltano elt tap-db2 target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.
