SET GLOBAL connect_timeout = 280;
SET GLOBAL deadlock_timeout_short = 100000;
SET GLOBAL deadlock_timeout_long = 50000000;
SET GLOBAL delayed_insert_timeout = 12000;
SET GLOBAL innodb_lock_wait_timeout = 2000;
SET GLOBAL lock_wait_timeout = 150000;
SET GLOBAL interactive_timeout = 86500;
SET GLOBAL net_read_timeout = 300;
SET GLOBAL net_write_timeout = 500;
SET GLOBAL slave_net_timeout = 400;
SET GLOBAL wait_timeout = 150000;
SET GLOBAL innodb_buffer_pool_size = 107374182400;


connect_timeout = 280
deadlock_timeout_short = 100000
deadlock_timeout_long = 50000000
delayed_insert_timeout = 12000
innodb_lock_wait_timeout = 2000
lock_wait_timeout = 150000
interactive_timeout = 86500
net_read_timeout = 300
net_write_timeout = 500		
slave_net_timeout = 400
wait_timeout = 150000
innodb_buffer_pool_size = 107374182400


key_buffer              = 256M
max_allowed_packet      = 16M
thread_stack            = 192K
thread_cache_size       = 16

max_connections        = 250
table_cache            = 16K
# wait_timeout            = 1200

query_cache_limit       = 4M
query_cache_size        = 512M
join_buffer_size        = 8M

#log_error = /var/log/mysql/error.log

log_slow_queries        = /var/log/mysql/mysql-slow.log
long_query_time = 20

expire_logs_days        = 10
max_binlog_size         = 100M

# innodb_buffer_pool_size = 5G