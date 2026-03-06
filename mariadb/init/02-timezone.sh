#!/bin/bash
# Load timezone data into MariaDB
# This is required for DMOJ date/time handling on certain pages

echo "Loading timezone data..."
mysql_tzinfo_to_sql /usr/share/zoneinfo | MYSQL_PWD="${MYSQL_ROOT_PASSWORD}" mariadb -u root mysql
echo "Timezone data loaded successfully"
