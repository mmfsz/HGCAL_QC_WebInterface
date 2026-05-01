# Starting the Database and Web Interface

## 1. Start the Services

Start MariaDB (the database) and Apache (the web server):

```bash
sudo systemctl start mariadb
sudo systemctl start httpd
```

Verify both are running:

```bash
sudo systemctl status mariadb
sudo systemctl status httpd
```

Both should show `Active: active (running)`.

## 2. Find the Current IP Address

This machine uses DHCP, so its IP address may change between sessions. Get the current IP with:

```bash
hostname -I
```

## 3. Access the Webpage

Open a browser and navigate to:

```
http://<IP_ADDRESS>/Factory/exampleDB/home_page.py
```

Replace `<IP_ADDRESS>` with the output from the previous step. For example:

```
http://128.186.110.131/Factory/exampleDB/home_page.py
```

## Notes

- Because the machine uses DHCP, the IP address changes when it reconnects to the network. Always run `hostname -I` to get the current address.
- If the services were previously enabled with `systemctl enable`, they start automatically on reboot and you only need to find the new IP.
- If the page fails to load, check the Apache error log: `sudo tail /var/log/httpd/error_log`
