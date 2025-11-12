TODO

```bash
sudo groupadd gitadmin
sudo usermod -aG gitadmin git
sudo usermod -aG gitadmin [main_user]
sudo usermod -aG gitadmin www-data

sudo mkdir -p /srv/git
sudo chown -R git:gitadmin /srv/git

sudo chmod -R 775 /srv/git

sudo chmod g+s /srv/git

sudo -u git git init --bare /srv/git/myproject.git
sudo chown -R git:gitadmin /srv/git/myproject.git
```

service

```
[Unit]
After=network.target

[Service]
User=[user]
Group=www-data
SupplementaryGroups=gitadmin
WorkingDirectory=/home/[user]/www/git-webview/
Environment="PATH=/home/[user]/www/git-webview/.venv/bin"
Environment="GIT_PYTHON_REFRESH=quiet"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="GIT_CONFIG_COUNT=1"
Environment="GIT_CONFIG_KEY_0=safe.directory"
Environment="GIT_CONFIG_VALUE_0=/srv/git/*"
ExecStart=/home/[user]/www/git-webview/.venv/bin/gunicorn --bind unix:git-webview.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```


permission fix

```
sudo apt install inotify-tools
```

```
#!/bin/bash
WATCH_DIR="/srv/git"
USER_GROUP="git:gitadmin"

inotifywait -m -r -e create,move "$WATCH_DIR" --format '%w%f' |
while read NEW_PATH; do
    if [ -d "$NEW_PATH" ]; then
        sleep 2
        chown -R "$USER_GROUP" "$NEW_PATH"
    else
        chown "$USER_GROUP" "$NEW_PATH"
    fi
done
```

```
sudo chmod 750 /usr/local/bin/gitrepo-watch.sh
sudo chown root:root /usr/local/bin/gitrepo-watch.sh
```

```
[Unit]
Description=asdfsadf
After=network.target

[Service]
ExecStart=/usr/local/bin/gitrepo-watch.sh
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
```