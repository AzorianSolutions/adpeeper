# ADPeeper

ADPeeper is a Python 3 / FastAPI app that exports ADP HR worker data to standard formats for consumption
in third-party systems.

## TL;DR

To get started quickly with a simple deployment, execute the following `bash` commands on a *nix based system
with `git`, `python3`, `python3-pip`, and `python3-venv` installed:

```
git clone https://github.com/AzorianSolutions/adpeeper.git
cd adpeeper
python3 -m venv venv
source venv/bin/activate
pip install .
cp $(pwd)/deploy/config/defaults.env $(pwd)/deploy/config/local.env
export ADP_ENV_FILE=$(pwd)/deploy/config/local.env
ADP_SALT=$(adp gen_salt -r)
ADP_SECRET_KEY=$(adp gen_salt -r)
echo "" >> $ADP_ENV_FILE
echo "ADP_SALT=$ADP_SALT" >> $ADP_ENV_FILE
echo "ADP_SECRET_KEY=$ADP_SECRET_KEY" >> $ADP_ENV_FILE
ADP_ENV_FILE=$(pwd)/deploy/config/local.env adp run
```

## Project Documentation

### Configuration

ADPeeper is configured via environment variables. Until I can provide more in-depth documentation of the project,
please refer to the default values in [deploy/config/defaults.env](./deploy/config/defaults.env) for a list of the
environment variables that can be set.

To see the concrete implementation of the settings associated with the environment variables, please see the
[src/app/config.py](./src/app/config.py) file.

### Contributing

This project is not currently accepting outside contributions. If you're interested in participating in the project,
please contact the project owner.

## [Security Policy](./.github/SECURITY.md)

Please see our [Security Policy](./.github/SECURITY.md).

## [Support Policy](./.github/SUPPORT.md)

Please see our [Support Policy](./.github/SUPPORT.md).

## [Code of Conduct](./.github/CODE_OF_CONDUCT.md)

Please see our [Code of Conduct](./.github/CODE_OF_CONDUCT.md).

## [License](./LICENSE)

This project is released under the MIT license. For additional information, [see the full license](./LICENSE).

## [Donate](https://www.buymeacoffee.com/AzorianMatt)

Like my work?

<a href="https://www.buymeacoffee.com/AzorianMatt" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

**Want to sponsor me?** Please visit my organization's [sponsorship page](https://github.com/sponsors/AzorianSolutions).
