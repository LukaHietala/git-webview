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