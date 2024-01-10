pip install django-debug-toolbar
pip install django-filter
pip install django-notifications-hq
pip install python-memcached
apt-get install memcached
pip install redis
/usr/bin/memcached -u memcache -m 1024 -p 11222 -l 0.0.0.0 -d start
apt-get install redis
redis-server --daemonize yes
pip install celery
pip install django-ratelimit
pip install python-dateutilsu
pip install happybase
# install thrift to connect to HBase
#sudo apt-get install automake bison flex g++ git libboost-all-dev libevent-dev libssl-dev libtool make pkg-config
# cd hbase-2.5.7/
# sudo ./bin/start-hbase.sh
# sudo ./bin/hbase-daemon.sh start thrift