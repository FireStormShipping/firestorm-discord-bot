# firestorm-discord-bot

A discord bot that has the following functionality:
 - Allows users to suggest prompts for the Bingo Dataset.
 - Ability for specific roles to approve prompts for the Bingo Dataset
 - Ability for specific roles to sync the updated or new datasets to [firestorm-bingo](https://github.com/FireStormShipping/firestorm-bingo) easily, by constructing the JSON files required for the Pull Request.

## Privacy

This bot was designed with the intention of collecting and storing the bare minimal amount of information needed to provide new/updated datasets to the [firestorm-bingo app](https://github.com/FireStormShipping/firestorm-bingo). For more information on what is stored, please check out the [Privacy Policy](docs/privacy_policy.md).

## Deploying

### Pre-requisites
- One of the commands implemented by this discord bot, `/sync-dataset`, requires a Github account that has forked the firestorm-bingo repository.
    - Ensure that the Github user that you intend to use in the `.env` file has forked the repo before deploying.

### Running the bot

```bash
cp .env.example .env
# Modify the values in .env as needed
vim .env
docker compose up -d
```

## Development
### Dependencies (If running without Docker)
```bash
sudo apt-get install -y libmariadb-dev python3-venv
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt pytest
```

### Running with Docker
- Same instructions as the deployment

### Running without Docker
```bash
# Option 1
source venv/bin/activate
python3 -m app.main

# Option 2
./venv/bin/python3 -m app.main
```

### Running unittests
```bash
# Option 1
source venv/bin/activate
pytest

# Option 2
./venv/bin/pytest
```

## Misc. Scripts
### Porting a JSON dataset to the Database
To port an existing JSON dataset to the database, run the following:

```bash
cp scripts/.env.example scripts/.env
# Fill up the .env information with your DB connection details
vim scripts/.env
python3 scripts/json_to_db.py path_to_json_dataset.json
```
