SET GLOBAL connect_timeout = 280000;
SET GLOBAL deadlock_timeout_short = 100000;
SET GLOBAL deadlock_timeout_long = 50000000;
SET GLOBAL delayed_insert_timeout = 120000;
SET GLOBAL innodb_lock_wait_timeout = 200000;
SET GLOBAL lock_wait_timeout = 150000;
SET GLOBAL interactive_timeout = 86500;
SET GLOBAL net_read_timeout = 30000;
SET GLOBAL net_write_timeout = 50000;
SET GLOBAL slave_net_timeout = 40000;
SET GLOBAL wait_timeout = 1500000;
SET GLOBAL innodb_buffer_pool_size = 107374182400;
SET GLOBAL thread_pool_idle_timeout = 40000;
SET GLOBAL tmp_table_size = 16106127360;
SET GLOBAL max_heap_table_size = 16106127360;
SET GLOBAL sort_buffer_size = 3221225472;

# Speeds up sorting when building facade cache
sort_buffer_size = 3221225472
tmp_table_size = 16106127360
max_heap_table_size = 16106127360
query_cache_limit       = 4M
query_cache_size        = 512M
join_buffer_size        = 8M
# Timeouts deal with long running connections
# Mostly needed when first scanning a large
# Number of repos
thread_pool_idle_timeout = 40000
connect_timeout = 280000
deadlock_timeout_short = 100000
deadlock_timeout_long = 50000000
delayed_insert_timeout = 120000
innodb_lock_wait_timeout = 200000
lock_wait_timeout = 150000
interactive_timeout = 86500
net_read_timeout = 30000
net_write_timeout = 50000	
slave_net_timeout = 40000
wait_timeout = 1500000
# 128 Gigs of RAM on server. 
innodb_buffer_pool_size = 107374182400
# Helps with sorting
key_buffer              = 256M
max_allowed_packet      = 16M
thread_stack            = 192K
thread_cache_size       = 16
# Connections are not a facade issue
max_connections        = 250
# A little caching helps with some of the queries
table_cache            = 16K
# Nice to know
log_slow_queries        = /var/log/mysql/mysql-slow.log
long_query_time = 20
expire_logs_days        = 10
max_binlog_size         = 100M
