#!/bin/bash

# Receive password and user as options from cli
while getopts u:p: flag
do
    case "${flag}" in
        u) DB_USER=${OPTARG};;
        p) DB_PASSWORD=${OPTARG};;
    esac
done

SQL_QUERY=$(cat ./migrations.sql)
if [[ -z "$SQL_QUERY" ]]; then
    echo "Error: Unable to read the SQL file or the file is empty."
fi
docker exec -i "new-eews-postgres" sh -c "PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres" <<< "$SQL_QUERY"
if [[ $? -eq 0 ]]; then
    echo "SQL query executed successfully inside the Docker container."
else
    echo "Error: Failed to execute the SQL query inside the Docker container."
fi

