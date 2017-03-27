#!/bin/bash


NAME="zmq-server"
PIDFILE=/var/run/$NAME.pid

# Start ZMQ server.
start() {
    rm /var/log/zmq-client.log
    rm /var/log/zmq-server.log
	printf "%s\n" "Starting $NAME..."

    # TODO Need to get install done so this isn't hard coded.
    # TODO Set up read port/bind from cli, then config file, then hardcode.
	/root/gits/zmq-handler/zero_mq.py -s -p 3333 -i 127.0.0.1 &
	PID=$( echo $!)

	if [ -z "$PID" ]; then
		 printf "%s\n" "Unable to start $NAME."
	else
		echo "${PID}" > $PIDFILE
		printf "%s\n" "$NAME started: $PID"
	fi
}

# Stop ZMQ server.
stop() {
	printf "%s\n" "Stopping $NAME..."
    # Check for PIDFILE for most graceful stopping.
	if [ -f $PIDFILE ]; then
		kill "$(cat $PIDFILE)"
		rm $PIDFILE
    # Attempt to handle stopping running process even without PIDFILE.
	else
		pkill "$(pgrep $NAME)"
	fi

    # Verify service stopped with above logic.
	if [ -z "$(ps awwfux | grep zmq.py | grep -v grep)" ]; then
		printf "%s\n" "$NAME stopped."
	else
		printf "%s\n" "Error stopping $NAME."
	fi
}

# Show status of ZMQ Server.
status() {
	if [ -f $PIDFILE ]; then
		if [ -z "$(ps awwfux | grep $NAME | grep -v grep)" ]; then
			printf "%s\n" "$NAME process not found, but pidfile exists."
		else
			printf "%s\n" "$NAME is running."
		fi
	else
		printf "%s\n" "$NAME is not running."
	fi
}

# Main #
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  status)
        status
        ;;
  restart|reload)
        stop
        start
        ;;
  *)
        echo $"Usage: $0 {start|stop|restart|reload|status}"
        exit 1
esac
  
exit 0
