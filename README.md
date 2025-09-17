# Setup

## Installing MetaDrive

```shell
cd src/api/
git clone https://github.com/metadriverse/metadrive.git --single-branch
```

## Starting Compose

```shell
cd ..
sudo docker compose up --build -d
```


# Usage

If setup was successful, app can be accessed on `80` port

## Login

Pre-created user credentials are:

`username`: `admin`

`password`: `admin`

## Swagger

To see available endpoints and test them you can use Swagger UI.

http://127.0.0.1/api/docs

Some endpoints require authentication first.


