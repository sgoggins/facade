## Setup steps
1. Follow the utilities/setup.py to get database configured
2. Update the start date for the database using `update settings set value = CAST('2001-01-01 19:00:01' AS DATE) where setting='start_date';`
3. Load projects and repos into the database

