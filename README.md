# capmandocker
CapManagement Solution for Sleeper Fantasy Football Leagues


## Deploy

To deploy:
    cd web
    flaskctl deploy

## Database

To activate psql shell:
    flyctl postgres connect -a capman-db
    \c capman

## SSH

To access shell:
    flyctl ssh console