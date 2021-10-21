## Docker-compose deployment
* Change directory to FinanceVisualization
<pre>cd FinanceVisualization/</pre>
* In FinanceVisualization folder, run below command to run website,
you can change mysql_port and magi_web_port environment variables' values
<pre>MYSQL_PORT=3306 MAGI_WEB_PORT=5000 MYSQL_VOLUME_PATH=magi_live docker-compose up -d</pre>
<hr>

## Standalone deployment
* Install .net core sdk
<pre>
https://docs.microsoft.com/en-us/dotnet/core/install/linux-ubuntu#1804
</pre>

* Install dotnet ef
<pre>dotnet tool install --global dotnet-ef</pre>

* Edit .bashrc and append below command at the end of the file
<pre>export PATH="$PATH:$HOME/.dotnet/tools/"</pre>

* Install Nodejs with NVM
<pre>
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
* After curl command, restart terminal to take effect *
nvm install 14.4.0
</pre>

* Install MySQL Server
<pre>sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation</pre>

* Create a db user and change root user password in MySQL
<pre>sudo mysql
CREATE USER '<new_username>'@'localhost' IDENTIFIED BY 'passwordofnew_username';
GRANT ALL PRIVILEGES ON *.* TO '<new_username>'@'localhost' WITH GRANT OPTION;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'passwordofroot';
FLUSH PRIVILEGES;
exit</pre>

* Install NGINX
<pre>https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04</pre>

* Configure /etc/nginx/sites-available/default as following
<pre>server {
    listen        80;
    server_name   yoursite.com *.yoursite.com;
    location / {
        proxy_pass         http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection keep-alive;
        proxy_set_header   Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}</pre>

* Restart NGINX to take effect
<pre>sudo service restart nginx</pre>

* cd into solution folder then run the command
<pre>dotnet restore</pre>

* Update DefaultConnection in appsettings.json file as following
<pre>"DefaultConnection": "server=localhost;database=financevisualization;uid=<new_username>;pwd=passwordofnew_username;"</pre>

* cd into project folder in solution folder and apply db migrations
<pre>dotnet ef database update</pre>

* Publish the app in Release configuration
<pre>dotnet publish --configuration Release</pre>

* cd into publish files and run the app
<pre>
cd {project path}/bin/Release/netcoreapp3.1/publish/
dotnet {project file name}.dll
</pre>
